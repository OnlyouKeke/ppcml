import hashlib
import logging
import os
import sys
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 确保标准输出流使用 UTF-8 编码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
    
import base64
import shutil
import io
import mimetypes
import tempfile
import time
import zipfile
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Inches
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse,JSONResponse

try:
    from .ctc import CTCAnalyzer
except ImportError:
    # 当直接运行脚本时使用绝对导入
    from ctc import CTCAnalyzer

for _stream_name in ("stdout", "stderr"):
    _stream = getattr(sys, _stream_name, None)
    if _stream is None:
        continue
    encoding = getattr(_stream, "encoding", None)
    if encoding and encoding.lower() == "utf-8":
        continue
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except AttributeError:
        buffer = getattr(_stream, "buffer", None)
        if buffer is not None:
            setattr(sys, _stream_name, io.TextIOWrapper(buffer, encoding="utf-8", errors="replace"))

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s - %(message)s",
    stream=sys.stdout,
    encoding='utf-8'
)



logger = logging.getLogger("ctc_app")


def verify_startup_token() -> None:
    """验证启动token，确保只能通过前端启动"""
    token = os.environ.get("FASTAPI_STARTUP_TOKEN")
    if not token:
        logger.error("错误：缺少启动token，此应用只能通过前端启动")
        sys.exit(1)

    try:
        timestamp_str, hash_part = token.split("_", 1)
        timestamp = int(timestamp_str)
        current_time = int(time.time())

        if current_time - timestamp > 60:
            logger.error("错误：启动token已过期")
            sys.exit(1)

        expected_hash = hashlib.sha256(f"fastapi_startup_{timestamp}".encode()).hexdigest()[:16]
        if hash_part != expected_hash:
            logger.error("错误：无效的启动token")
            sys.exit(1)

        logger.info("启动token验证成功")
    except (ValueError, IndexError):
        logger.error("错误：启动token格式无效")
        sys.exit(1)


def _safe_extract(zip_file: zipfile.ZipFile, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    target_root = target_dir.resolve()
    for member in zip_file.infolist():
        member_path = target_root / member.filename
        try:
            member_path.resolve().relative_to(target_root)
        except ValueError as exc:  # pragma: no cover - 安全检查
            raise HTTPException(status_code=400, detail="压缩包包含非法路径，无法解压") from exc
    zip_file.extractall(target_dir)


def _find_dataset_root(extracted_dir: Path) -> Path:
    expected_dirs = {str(i) for i in range(1, 6)}
    extracted_dir.mkdir(parents=True, exist_ok=True)

    def has_expected_children(path: Path) -> bool:
        return any((path / child).exists() for child in expected_dirs)

    if has_expected_children(extracted_dir):
        return extracted_dir

    candidates = [p for p in extracted_dir.iterdir() if p.is_dir()]
    for candidate in candidates:
        if has_expected_children(candidate):
            return candidate

    if len(candidates) == 1:
        return candidates[0]

    raise HTTPException(status_code=400, detail="未找到符合CTC分析目录结构的文件夹")


def _create_metadata_entries(
    pet_name: str,
    owner_name: str,
    age: str,
    gender: str,
    sample_type: str,
    medication_intake: str,
    medication_details: str,
    notes: str,
) -> OrderedDict:
    entries: OrderedDict[str, str] = OrderedDict()
    entries["宠物姓名"] = pet_name or "未填写"
    entries["宠主姓名"] = owner_name or "未填写"
    entries["年龄"] = age or "未填写"
    entries["性别"] = gender or "未填写"
    entries["标本类型"] = sample_type or "未填写"
    intake_value = medication_intake or "未填写"
    entries["一周内是否有药物摄入"] = intake_value
    if intake_value == "是":
        entries["药物名称"] = medication_details or "未填写"
    else:
        entries["药物名称"] = "无"
    entries["备注"] = notes or "无"
    return entries


def _apply_run_style(run, size: int, bold: bool = False, color: RGBColor | None = None) -> None:
    font = run.font
    font.size = Pt(size)
    font.bold = bold
    font.name = "SimSun"
    if color is not None:
        font.color.rgb = color

    r_pr = run._element.get_or_add_rPr()
    r_fonts = r_pr.rFonts
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.append(r_fonts)
    r_fonts.set(qn("w:eastAsia"), "SimSun")


def _apply_font_size(paragraphs: Iterable, *, size: int = 12) -> None:
    for paragraph in paragraphs:
        for run in paragraph.runs:
            _apply_run_style(run, size)


def _set_cell_text(
    cell,
    text: str,
    *,
    bold: bool = False,
    color: RGBColor | None = None,
    fill: str | None = None,
) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    run = paragraph.add_run(text)
    _apply_run_style(run, 12, bold=bold, color=color)
    paragraph.paragraph_format.space_after = Pt(0)

    if fill is not None:
        tc_pr = cell._tc.get_or_add_tcPr()
        for child in list(tc_pr):
            if child.tag == qn("w:shd"):
                tc_pr.remove(child)
        shading = OxmlElement("w:shd")
        shading.set(qn("w:val"), "clear")
        shading.set(qn("w:color"), "auto")
        shading.set(qn("w:fill"), fill)
        tc_pr.append(shading)


def _add_section_heading(document: Document, text: str, *, color: RGBColor) -> None:
    paragraph = document.add_paragraph()
    run = paragraph.add_run(text)
    _apply_run_style(run, 16, bold=True, color=color)
    paragraph.paragraph_format.space_before = Pt(12)
    paragraph.paragraph_format.space_after = Pt(6)


def _populate_table(table, rows: List[List[str]]) -> None:
    for row_idx, row_values in enumerate(rows):
        row = table.rows[row_idx]
        for cell, value in zip(row.cells, row_values):
            cell.text = value
            _apply_font_size(cell.paragraphs)


def _build_report_document(analyzer: CTCAnalyzer, metadata: OrderedDict[str, str], output_path: Path) -> None:
    document = Document()

    logo_path = Path(__file__).resolve().parent / "assets" / "HBI.jpg"
    if logo_path.exists():
        logo_paragraph = document.add_paragraph()
        logo_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        logo_run = logo_paragraph.add_run()
        logo_run.add_picture(str(logo_path), width=Inches(1.4))
        logo_paragraph.paragraph_format.space_after = Pt(6)

    title_paragraph = document.add_paragraph()
    title_run = title_paragraph.add_run("检测报告")
    _apply_run_style(title_run, 28, bold=True, color=RGBColor(31, 41, 55))
    title_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

    if metadata:
        _add_section_heading(document, "基础信息", color=RGBColor(37, 99, 235))

        rows = (len(metadata) + 1) // 2
        info_table = document.add_table(rows=rows, cols=4)
        info_table.autofit = True

        for index, (label, value) in enumerate(metadata.items()):
            row = info_table.rows[index // 2]
            label_cell_index = (index % 2) * 2
            label_cell = row.cells[label_cell_index]
            value_cell = row.cells[label_cell_index + 1]

            _set_cell_text(label_cell, label, bold=True, color=RGBColor(37, 99, 235))
            _set_cell_text(value_cell, value or "", color=RGBColor(31, 41, 55))

        if len(metadata) % 2 == 1:
            last_row = info_table.rows[-1]
            _set_cell_text(last_row.cells[2], "", color=RGBColor(31, 41, 55))
            _set_cell_text(last_row.cells[3], "", color=RGBColor(31, 41, 55))


    result_heading = document.add_paragraph()
    result_heading_run = result_heading.add_run("检测结果")
    _apply_run_style(result_heading_run, 16, bold=True, color=RGBColor(37, 99, 235))
    result_heading.paragraph_format.space_before = Pt(12)
    result_heading.paragraph_format.space_after = Pt(6)

    doc_names = analyzer.results.get("doc_names", [])
    ctc_counts = analyzer.results.get("green_single_channel", [])
    wbc_counts = analyzer.results.get("white_single_channel", [])

    total_ctc = sum(ctc_counts)
    total_wbc = sum(wbc_counts)

    selection_paragraph = document.add_paragraph()
    selection_run = selection_paragraph.add_run("选三张不同荧光同一区域的照片，有方框标出是CTC。")
    _apply_run_style(selection_run, 12, color=RGBColor(55, 65, 81))

    ctc_image_sets = analyzer.results.get("ctc_image_sets", [])
    if ctc_image_sets:
        image_set = ctc_image_sets[0]
        labels_and_paths = [
            ("蓝色通道", image_set["blue_path"]),
            ("绿色通道", image_set["green_path"]),
            ("红色通道", image_set["red_path"]),
        ]

        image_table = document.add_table(rows=2, cols=3)
        image_table.autofit = True

        first_row = image_table.rows[0]
        second_row = image_table.rows[1]

        for idx, (label, path) in enumerate(labels_and_paths):
            if not path or not os.path.exists(path):
                continue

            cell = first_row.cells[idx]
            paragraph = cell.paragraphs[0]
            run = paragraph.add_run()
            run.add_picture(path, width=Inches(2.0))
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER

            label_cell = second_row.cells[idx]
            _set_cell_text(label_cell, label, bold=True, color=RGBColor(31, 41, 55))
            label_cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        no_image_paragraph = document.add_paragraph()
        no_image_run = no_image_paragraph.add_run("当前未检测到可用于展示的CTC图像。")
        _apply_run_style(no_image_run, 12, color=RGBColor(107, 114, 128))

    result_text = (
        f"结果说明：经实验结果判定，在一二通道中找到CD45 {total_wbc}个，CK {total_ctc}个。"
        if doc_names
        else "结果说明：未能识别出有效的检测结果，请检查上传的影像资料。"
    )
    result_paragraph = document.add_paragraph()
    result_run = result_paragraph.add_run(result_text)
    _apply_run_style(result_run, 12, color=RGBColor(220, 38, 38) if doc_names else RGBColor(107, 114, 128))

    notes_value = metadata.get("备注", "无") or "无"
    biomarker_text = notes_value if notes_value not in {"无", "未填写"} else "______________"
    remark_paragraph = document.add_paragraph()
    remark_run = remark_paragraph.add_run(f"备注：生物标记物染色选用{biomarker_text}。")
    _apply_run_style(remark_run, 12, color=RGBColor(30, 64, 45))
    
    separator = document.add_paragraph()
    separator_run = separator.add_run("-------------------------------")
    _apply_run_style(separator_run, 12, color=RGBColor(239, 68, 68))
    separator.alignment = WD_ALIGN_PARAGRAPH.CENTER


    footer = document.add_paragraph()
    footer_run = footer.add_run("检测人：___________    审核人：___________    报告日期：___________")
    _apply_run_style(footer_run, 12, color=RGBColor(75, 85, 99))
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER

    document.save(output_path)


def _prepare_workdir(contents: bytes) -> tuple[Path, Path, Path]:
    work_dir = Path(tempfile.mkdtemp(prefix="ctc-analysis-"))
    try:
        archive_path = work_dir / "upload.zip"
        archive_path.write_bytes(contents)

        with zipfile.ZipFile(archive_path) as archive:
            extracted_dir = work_dir / "extracted"
            _safe_extract(archive, extracted_dir)

        dataset_root = _find_dataset_root(work_dir / "extracted")
        output_dir = work_dir / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise

    return work_dir, dataset_root, output_dir


async def _prepare_workdir_from_files(files: List[UploadFile]) -> tuple[Path, Path, Path]:
    work_dir = Path(tempfile.mkdtemp(prefix="ctc-analysis-"))
    dataset_root = work_dir / "uploaded"

    try:
        dataset_root.mkdir(parents=True, exist_ok=True)
        root_resolved = dataset_root.resolve()

        for upload in files:
            filename = upload.filename
            if not filename:
                continue

            target_path = root_resolved / filename
            target_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                target_path.resolve().relative_to(root_resolved)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="上传的文件路径无效") from exc

            content = await upload.read()
            if not content:
                continue
            target_path.write_bytes(content)

        dataset_dir = _find_dataset_root(dataset_root)
        output_dir = work_dir / "results"
        output_dir.mkdir(parents=True, exist_ok=True)
    except Exception:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise

    return work_dir, dataset_dir, output_dir


verify_startup_token()

APP_START_TIME = time.time()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str) -> dict[str, str]:
    return {"message": f"Hello {name}"}


@app.get("/healthz")
async def heartbeat() -> dict[str, float | str]:
    """简单的心跳检测端点，供前端检测后端状态"""
    uptime_seconds = time.time() - APP_START_TIME
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime": round(uptime_seconds, 3),
    }


@app.post("/ctc/report")
async def generate_ctc_report(
    file: UploadFile | None = File(None),
    files: List[UploadFile] | None = File(None),
    pet_name: str = Form("", alias="petName"),
    owner_name: str = Form("", alias="ownerName"),
    age: str = Form("", alias="age"),
    gender: str = Form("", alias="gender"),
    sample_type: str = Form("", alias="sampleType"),
    medication_intake: str = Form("", alias="medicationIntake"),
    medication_details: str = Form("", alias="medicationDetails"),
    notes: str = Form("", alias="notes"),
    roundness_threshold: float = Form(0.3, alias="roundnessThreshold"),
) -> FileResponse:
    uploaded_files = files or []
    logger.info(
        "收到CTC报告生成请求：zip文件=%s，多文件数量=%d，圆度阈值=%.2f",
        bool(file and file.filename),
        len(uploaded_files),
        roundness_threshold,
    )

    if (file is None or not file.filename) and not files:
        raise HTTPException(status_code=400, detail="请上传包含影像数据的ZIP文件或文件夹")

    work_dir: Path | None = None
    dataset_root: Path | None = None
    output_dir: Path | None = None
    try:
        if file is not None and file.filename:
            if not file.filename.lower().endswith(".zip"):
                raise HTTPException(status_code=400, detail="请上传ZIP格式的影像压缩包")

            contents = await file.read()
            if not contents:
                raise HTTPException(status_code=400, detail="上传文件内容为空")

            work_dir, dataset_root, output_dir = _prepare_workdir(contents)
            logger.info("已从ZIP文件提取数据，工作目录：%s", work_dir)
        elif files:
            work_dir, dataset_root, output_dir = await _prepare_workdir_from_files(files)
            logger.info("已接收多文件上传，工作目录：%s", work_dir)
        else:
            raise HTTPException(status_code=400, detail="未提供有效的影像数据")

        analyzer = CTCAnalyzer(str(dataset_root), str(output_dir), roundness_threshold=roundness_threshold)
        logger.info("开始处理影像数据，数据根目录：%s", dataset_root)
        analyzer.process_all_images()
        logger.info("图像处理完成，生成统计结果：%s", analyzer.results.get("doc_names", []))

        metadata = _create_metadata_entries(
            pet_name,
            owner_name,
            age,
            gender,
            sample_type,
            medication_intake,
            medication_details,
            notes,
        )
        logger.info(
            "报告元数据：%s",
            {key: metadata[key] for key in metadata},
        )

        report_path = output_dir / "ctc_report.docx"
        _build_report_document(analyzer, metadata, report_path)
        logger.info("报告已生成：%s", report_path)

        report_bytes = report_path.read_bytes()
        encoded_report = base64.b64encode(report_bytes).decode("ascii")

        metadata_items = [
            {"label": label, "value": value}
            for label, value in metadata.items()
        ]

        doc_names = analyzer.results.get("doc_names", [])
        ctc_counts = analyzer.results.get("green_single_channel", [])
        wbc_counts = analyzer.results.get("white_single_channel", [])
        channel_stats = [
            {"channel": name, "ctc": ctc, "wbc": wbc}
            for name, ctc, wbc in zip(doc_names, ctc_counts, wbc_counts)
        ]

        total_ctc = sum(ctc_counts)
        total_wbc = sum(wbc_counts)

        selection_text = "选三张不同荧光同一区域的照片，有方框标出是CTC。"

        ctc_image_sets = analyzer.results.get("ctc_image_sets", [])
        image_set_payload: dict | None = None
        if ctc_image_sets:
            first_set = ctc_image_sets[0]
            images_payload = []
            for label, key in (
                ("蓝色通道", "blue_path"),
                ("绿色通道", "green_path"),
                ("红色通道", "red_path"),
            ):
                image_path = first_set.get(key)
                if not image_path or not os.path.exists(image_path):
                    continue
                mime_type, _ = mimetypes.guess_type(image_path)
                try:
                    image_bytes = Path(image_path).read_bytes()
                except OSError:
                    logger.warning("无法读取预览图像：%s", image_path)
                    continue
                images_payload.append(
                    {
                        "label": label,
                        "mimeType": mime_type or "image/png",
                        "data": base64.b64encode(image_bytes).decode("ascii"),
                    }
                )

            if images_payload:
                image_set_payload = {"items": images_payload}

        result_text = (
            f"结果说明：经实验结果判定，在一二通道中找到CD45 {total_wbc}个，CK {total_ctc}个。"
            if doc_names
            else "结果说明：未识别出有效的检测结果，请检查上传的影像资料。"
        )

        notes_value = metadata.get("备注", "无") or "无"
        biomarker_text = notes_value if notes_value not in {"无", "未填写"} else "______________"
        remark_text = f"备注：生物标记物染色选用{biomarker_text}。"

        response_payload = {
            "fileName": "ctc_report.docx",
            "fileContent": encoded_report,
            "generatedAt": datetime.utcnow().isoformat() + "Z",
            "metadata": metadata_items,
            "channels": channel_stats,
            "totals": {
                "totalCtc": total_ctc,
                "totalWbc": total_wbc,
            },
            "resultText": result_text,
            "remarkText": remark_text,
            "selectionText": selection_text,
            "hasCtcImages": bool(image_set_payload),
            "imageSet": image_set_payload,
            "warnings": [],
        }

        shutil.rmtree(work_dir, ignore_errors=True)
        return JSONResponse(content=response_payload)
    except zipfile.BadZipFile as exc:
        if work_dir is not None:
            shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="压缩包文件损坏或格式错误") from exc
    except HTTPException:
        if work_dir is not None:
            shutil.rmtree(work_dir, ignore_errors=True)
        raise
    except Exception as exc:
        logger.exception("生成CTC报告时出现未预期错误")
        if work_dir is not None:
            shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail="生成报告时发生未知错误") from exc
    finally:
        if file is not None:
            await file.close()
        if files:
            for upload in files:
                await upload.close()


if __name__ == "__main__":
    import uvicorn

    port_str = os.environ.get("FASTAPI_PORT", "8001")
    try:
        port = int(port_str)
    except ValueError:
        logger.warning("警告：FASTAPI_PORT 设置无效（%s），使用默认端口 8001", port_str)
        port = 8001

    uvicorn.run(app, host="0.0.0.0", port=port)
