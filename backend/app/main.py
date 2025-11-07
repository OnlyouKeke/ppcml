import hashlib
import logging
import os
import re
import sys
# 设置环境变量确保UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 确保标准输出流使用 UTF-8 编码
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# 设置默认编码为UTF-8
if sys.version_info[0] == 3 and sys.version_info[1] >= 7:
    # 对于Python 3.7及以上版本
    import io
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer,
        encoding='utf-8',
        errors='replace',
        line_buffering=True
    )
    sys.stderr = io.TextIOWrapper(
        sys.stderr.buffer,
        encoding='utf-8',
        errors='replace',
        line_buffering=True
    )

import base64
import json
import shutil
import io
import mimetypes
import tempfile
import time
import zipfile
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Iterable, List

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor, Inches
import cv2
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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

LOG_DIR = Path(__file__).resolve().parent.parent / "log"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"

_file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
_stream_handler = logging.StreamHandler(sys.stdout)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(name)s - %(message)s",
    handlers=[_file_handler, _stream_handler],
)



logger = logging.getLogger("ctc_app")

INLINE_SUPPORTED_MIME_TYPES = {"image/png", "image/jpeg", "image/gif"}


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


def _normalize_field(value: str) -> str:
    return value.strip()


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
    entries["宠物姓名:"] = _normalize_field(pet_name)
    entries["宠主姓名:"] = _normalize_field(owner_name)
    entries["年龄:"] = _normalize_field(age)
    entries["性别:"] = _normalize_field(gender)
    entries["标本类型:"] = _normalize_field(sample_type)

    intake_value = _normalize_field(medication_intake)
    entries["一周内是否有药物摄入"] = intake_value

    if intake_value == "是":
        entries["药物名称:"] = _format_medication_schedule(medication_details)
    elif intake_value == "否":
        entries["药物名称:"] = "无（近期未使用药物）"
    else:
        formatted_details = _format_medication_schedule(medication_details)
        entries["药物名称:"] = formatted_details or _normalize_field(medication_details)

    entries["备注:"] = _normalize_field(notes)
    return entries


def _format_medication_schedule(medication_details: str) -> str:
    """将药物明细格式化为更易读的排班列表"""
    normalized = _normalize_field(medication_details)
    if not normalized:
        return ""

    parts = [part.strip() for part in re.split(r"[、,，;；\n\r]+", normalized) if part.strip()]
    if not parts:
        return normalized

    if len(parts) == 1:
        return parts[0]

    formatted_lines = [f"{index + 1}. {item}" for index, item in enumerate(parts)]
    return "\n".join(formatted_lines)


def _encode_preview_image(image_path: Path) -> tuple[str, str] | None:
    """读取图像并转换为可预览的Base64格式"""
    try:
        mime_type, _ = mimetypes.guess_type(str(image_path))
        if mime_type in INLINE_SUPPORTED_MIME_TYPES:
            image_bytes = image_path.read_bytes()
            return mime_type, base64.b64encode(image_bytes).decode("ascii")

        image = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
        if image is None:
            image_bytes = image_path.read_bytes()
            return (mime_type or "image/png", base64.b64encode(image_bytes).decode("ascii"))

        success, buffer = cv2.imencode(".png", image)
        if not success:
            logger.warning("图像编码为PNG失败：%s", image_path)
            image_bytes = image_path.read_bytes()
            return (mime_type or "image/png", base64.b64encode(image_bytes).decode("ascii"))

        return "image/png", base64.b64encode(buffer.tobytes()).decode("ascii")
    except OSError:
        logger.warning("无法读取预览图像：%s", image_path)
        return None
    except Exception:
        logger.exception("处理预览图像时出现错误：%s", image_path)
        return None


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
    lines = text.splitlines() or [""]
    for index, line in enumerate(lines):
        run = paragraph.add_run(line)
        _apply_run_style(run, 12, bold=bold, color=color)
        if index < len(lines) - 1:
            run.add_break()
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


def _set_table_transparent(table) -> None:
    tbl = table._tbl
    # 使用xpath获取tblPr，如果不存在则创建
    tblPr_elements = tbl.xpath('w:tblPr')
    if tblPr_elements:
        tblPr = tblPr_elements[0]
    else:
        tblPr = OxmlElement('w:tblPr')
        tbl.insert(0, tblPr)
    borders = tblPr.find(qn("w:tblBorders"))
    if borders is None:
        borders = OxmlElement("w:tblBorders")
        tblPr.append(borders)

    for border_name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border = borders.find(qn(f"w:{border_name}"))
        if border is None:
            border = OxmlElement(f"w:{border_name}")
            borders.append(border)
        border.set(qn("w:val"), "nil")

    for row in table.rows:
        for cell in row.cells:
            tc_pr = cell._tc.get_or_add_tcPr()

            shading = tc_pr.find(qn("w:shd"))
            if shading is not None:
                tc_pr.remove(shading)

            tc_borders = tc_pr.find(qn("w:tcBorders"))
            if tc_borders is None:
                tc_borders = OxmlElement("w:tcBorders")
                tc_pr.append(tc_borders)

            for border_name in ("top", "left", "bottom", "right"):
                border = tc_borders.find(qn(f"w:{border_name}"))
                if border is None:
                    border = OxmlElement(f"w:{border_name}")
                    tc_borders.append(border)
                border.set(qn("w:val"), "nil")


def _format_channel_summary_texts(analyzer: CTCAnalyzer) -> list[str]:
    channel_summary_pairs = (
        ("green_single_channel", analyzer.results.get("green_single_channel", [])),
        ("white_single_channel", analyzer.results.get("white_single_channel", [])),
    )
    return [f"{label} {values}" for label, values in channel_summary_pairs]


def _build_report_document(
    analyzer: CTCAnalyzer,
    metadata: OrderedDict[str, str],
    output_path: Path,
    channel_summary_texts: list[str] | None = None,
    mask_option: dict | None = None,
    *,
    mask_options: list[dict] | None = None,
) -> None:
    document = Document()
    logo_path = Path(__file__).resolve().parent.parent / "HBI.jpg"
    if logo_path.exists():
        logo_paragraph = document.add_paragraph()
        logo_run = logo_paragraph.add_run()
        logo_run.add_picture(str(logo_path), width=Inches(1.6))
        logo_paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
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
        info_table.style = None
        _set_table_transparent(info_table)

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

        for summary_text in channel_summary_texts or []:
            if not summary_text:
                continue
            summary_paragraph = document.add_paragraph()
            summary_paragraph.paragraph_format.space_after = Pt(2)
            summary_run = summary_paragraph.add_run(summary_text)
            _apply_run_style(summary_run, 10, color=RGBColor(55, 65, 81))

        def _resolve_preview_path(primary_key: str, *fallback_keys: str) -> str | None:
            keys = (primary_key,) + fallback_keys
            for key in keys:
                candidate = image_set.get(key)
                if candidate and os.path.exists(candidate):
                    return candidate
            return None

        selected_labels_and_paths: list[tuple[str, str]] = []

        if mask_options:
            for index, option in enumerate(mask_options):
                candidate_path = option.get("path")
                if not candidate_path or not os.path.exists(candidate_path):
                    logger.warning(
                        "所选掩码图像不存在或不可访问：%s", candidate_path
                    )
                    continue
                label = option.get("label") or f"掩码图像 {index + 1}"
                selected_labels_and_paths.append((label, candidate_path))

        mask_override_path: str | None = None
        mask_override_label: str | None = None
        if mask_option and not selected_labels_and_paths:
            candidate_path = mask_option.get("path")
            if candidate_path and os.path.exists(candidate_path):
                mask_override_path = candidate_path
                mask_override_label = mask_option.get("label")
            else:
                logger.warning("指定的掩码图像不存在或不可访问：%s", candidate_path)

        if selected_labels_and_paths:
            labels_and_paths = selected_labels_and_paths
        else:
            labels_and_paths = [
                ("蓝色通道", _resolve_preview_path("blue_path", "blue_original")),
                ("绿色通道", _resolve_preview_path("green_path", "green_original")),
                ("红色通道", _resolve_preview_path("red_path", "red_original")),
            ]

            if mask_override_path:
                labels_and_paths[2] = (
                    mask_override_label or "掩码图像",
                    mask_override_path,
                )

        column_count = max(1, len(labels_and_paths))
        image_table = document.add_table(rows=2, cols=column_count)
        image_table.autofit = True
        image_table.style = None
        _set_table_transparent(image_table)

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

    notes_value = (metadata.get("备注") or "").strip()
    biomarker_text = notes_value if notes_value else "______________"
    remark_paragraph = document.add_paragraph()
    remark_run = remark_paragraph.add_run(f"备注：生物标记物染色选用{biomarker_text}。")
    _apply_run_style(remark_run, 12, color=RGBColor(30, 64, 45))
    
    separator = document.add_paragraph()
    separator_run = separator.add_run("--------------------------------------------------------------------")
    _apply_run_style(separator_run, 12, color=RGBColor(75, 85, 99))
    separator.alignment = WD_ALIGN_PARAGRAPH.CENTER


    footer = document.add_paragraph()
    footer_run = footer.add_run("检测人：___________    审核人：___________    报告日期：___________")
    _apply_run_style(footer_run, 12, color=RGBColor(75, 85, 99))
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER

    document.save(output_path)


def _prepare_workdir(contents: bytes) -> tuple[Path, Path]:
    work_dir = Path(tempfile.mkdtemp(prefix="ctc-analysis-"))
    try:
        archive_path = work_dir / "upload.zip"
        archive_path.write_bytes(contents)

        with zipfile.ZipFile(archive_path) as archive:
            extracted_dir = work_dir / "extracted"
            _safe_extract(archive, extracted_dir)

        dataset_root = _find_dataset_root(work_dir / "extracted")
    except Exception:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise

    return work_dir, dataset_root


async def _prepare_workdir_from_files(files: List[UploadFile]) -> tuple[Path, Path]:
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
    except Exception:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise

    return work_dir, dataset_dir


def _sanitize_pet_name(pet_name: str) -> str:
    """Sanitize the pet name for safe filesystem usage."""

    stripped = pet_name.strip()
    if not stripped:
        return ""

    sanitized = re.sub(r"[^\w\-\u4e00-\u9fff]+", "_", stripped)
    return sanitized.strip("_")


def _prepare_output_directory(pet_name: str) -> Path:
    """Create the persistent output directory for generated artifacts."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_pet_name = _sanitize_pet_name(pet_name)
    folder_name = f"{timestamp}_{safe_pet_name}" if safe_pet_name else timestamp

    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    target_dir = OUTPUT_ROOT / folder_name
    suffix = 1
    while target_dir.exists():
        target_dir = OUTPUT_ROOT / f"{folder_name}_{suffix}"
        suffix += 1

    target_dir.mkdir(parents=True, exist_ok=False)
    return target_dir


verify_startup_token()

APP_START_TIME = time.time()

def _determine_output_root() -> Path:
    """Return a writable directory for generated artifacts."""
    if getattr(sys, "frozen", False):
        base_dir = Path(sys.executable).resolve().parent
    else:
        base_dir = Path(__file__).resolve().parents[1]

    output_root = base_dir / "var"
    output_root.mkdir(parents=True, exist_ok=True)
    return output_root


OUTPUT_ROOT = _determine_output_root()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def heartbeat() -> dict[str, float | str]:
    """简单的心跳检测端点，供前端检测后端状态"""
    uptime_seconds = time.time() - APP_START_TIME
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
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
    preview_only: str = Form("false", alias="previewOnly"),
) -> JSONResponse:
    uploaded_files = files or []
    preview_only_flag = str(preview_only).lower() in {"1", "true", "yes", "on"}
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

            work_dir, dataset_root = _prepare_workdir(contents)
            logger.info("已从ZIP文件提取数据，工作目录：%s", work_dir)
        elif files:
            work_dir, dataset_root = await _prepare_workdir_from_files(files)
            logger.info("已接收多文件上传，工作目录：%s", work_dir)
        else:
            raise HTTPException(status_code=400, detail="未提供有效的影像数据")

        output_dir = _prepare_output_directory(pet_name)
        logger.info("报告输出目录：%s", output_dir)

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
        channel_summary_texts = _format_channel_summary_texts(analyzer)

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

        mask_options_payload: list[dict] = []
        mask_paths_map = analyzer.results.get("mask_paths", {}) or {}
        for channel, mask_paths in mask_paths_map.items():
            for index, mask_path in enumerate(mask_paths):
                mask_path_obj = Path(mask_path)
                if not mask_path_obj.exists():
                    continue
                try:
                    relative_path = mask_path_obj.relative_to(output_dir)
                except ValueError:
                    relative_path = Path(mask_path_obj.name)
                encoded_preview = _encode_preview_image(mask_path_obj)
                if not encoded_preview:
                    continue
                mime_type, encoded_data = encoded_preview
                option_id = f"{channel}-{mask_path_obj.stem}-{index}"
                option_label = (
                    f"{channel}通道掩码"
                    if len(mask_paths) == 1
                    else f"{channel}通道掩码 {index + 1}"
                )
                mask_options_payload.append(
                    {
                        "id": option_id,
                        "channel": str(channel),
                        "label": option_label,
                        "relativePath": str(relative_path).replace(os.sep, "/"),
                        "mimeType": mime_type or "image/png",
                        "data": encoded_data,
                    }
                )

        ctc_image_sets = analyzer.results.get("ctc_image_sets", [])
        image_set_payload: dict | None = None
        if ctc_image_sets:
            first_set = ctc_image_sets[0]

            def _resolve_image(primary_key: str, *fallback_keys: str) -> Path | None:
                keys = (primary_key,) + fallback_keys
                for key in keys:
                    candidate = first_set.get(key)
                    if candidate:
                        candidate_path = Path(candidate)
                        if candidate_path.exists():
                            return candidate_path
                return None

            images_payload = []
            for label, keys in (
                ("蓝色通道", ("blue_path", "blue_original")),
                ("绿色通道", ("green_path", "green_original")),
                ("红色通道", ("red_path", "red_original")),
            ):
                image_path = _resolve_image(*keys)
                if not image_path:
                    continue
                encoded_preview = _encode_preview_image(image_path)
                if not encoded_preview:
                    continue
                mime_type, encoded_data = encoded_preview
                images_payload.append(
                    {
                        "label": label,
                        "mimeType": mime_type or "image/png",
                        "data": encoded_data,
                    }
                )

            if images_payload:
                image_set_payload = {"items": images_payload}

        result_text = (
            f"结果说明：经实验结果判定，在一二通道中找到CD45 {total_wbc}个，CK {total_ctc}个。"
            if doc_names
            else "结果说明：未识别出有效的检测结果，请检查上传的影像资料。"
        )

        notes_value = (metadata.get("备注") or "").strip()
        biomarker_text = notes_value if notes_value else "______________"
        remark_text = f"备注：生物标记物染色选用{biomarker_text}。"

        metadata_items = [
            {"label": label, "value": value}
            for label, value in metadata.items()
        ]

        report_token = output_dir.name
        state_payload = {
            "metadata": {key: metadata[key] for key in metadata},
            "results": analyzer.results,
            "channelSummaryTexts": channel_summary_texts,
            "selectionText": selection_text,
            "resultText": result_text,
            "remarkText": remark_text,
            "maskOptions": [
                {
                    "id": option["id"],
                    "channel": option["channel"],
                    "label": option["label"],
                    "relativePath": option["relativePath"],
                }
                for option in mask_options_payload
            ],
            "createdAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        (output_dir / "report_state.json").write_text(
            json.dumps(state_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        response_payload = {
            "fileName": "ctc_report.docx",
            "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
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
            "channelSummaryTexts": channel_summary_texts,
            "warnings": [],
            "reportToken": report_token,
            "maskOptions": mask_options_payload,
        }

        if not preview_only_flag:
            _build_report_document(
                analyzer,
                metadata,
                report_path,
                channel_summary_texts=channel_summary_texts,
            )
            logger.info("报告已生成：%s", report_path)
            report_bytes = report_path.read_bytes()
            encoded_report = base64.b64encode(report_bytes).decode("ascii")
            response_payload["fileContent"] = encoded_report

        shutil.rmtree(work_dir, ignore_errors=True)
        return JSONResponse(content=response_payload)
    except zipfile.BadZipFile as exc:
        if work_dir is not None:
            shutil.rmtree(work_dir, ignore_errors=True)
        if output_dir is not None and output_dir.exists() and not any(output_dir.iterdir()):
            output_dir.rmdir()
        raise HTTPException(status_code=400, detail="压缩包文件损坏或格式错误") from exc
    except HTTPException:
        if work_dir is not None:
            shutil.rmtree(work_dir, ignore_errors=True)
        if output_dir is not None and output_dir.exists() and not any(output_dir.iterdir()):
            output_dir.rmdir()
        raise
    except Exception as exc:
        logger.exception("生成CTC报告时出现未预期错误")
        if work_dir is not None:
            shutil.rmtree(work_dir, ignore_errors=True)
        if output_dir is not None and output_dir.exists() and not any(output_dir.iterdir()):
            output_dir.rmdir()
        raise HTTPException(status_code=500, detail="生成报告时发生未知错误") from exc
    finally:
        if file is not None:
            await file.close()
        if files:
            for upload in files:
                await upload.close()


@app.post("/ctc/report/export")
async def export_ctc_report(
    report_token: str = Form(..., alias="reportToken"),
    mask_option_id: str = Form("", alias="maskOptionId"),
    mask_option_ids: str = Form("", alias="maskOptionIds"),
) -> JSONResponse:
    logger.info(
        "收到报告导出请求：report_token=%s, mask_option_id=%s, mask_option_ids=%s",
        report_token,
        mask_option_id,
        mask_option_ids,
    )

    if not report_token:
        raise HTTPException(status_code=400, detail="缺少报告标识")

    output_root = OUTPUT_ROOT.resolve()
    output_dir = (output_root / report_token).resolve()
    try:
        output_dir.relative_to(output_root)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="报告标识无效") from exc

    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="报告数据不存在")

    state_path = output_dir / "report_state.json"
    if not state_path.exists():
        raise HTTPException(status_code=400, detail="报告状态文件不存在")

    try:
        state_data = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.exception("报告状态文件解析失败：%s", state_path)
        raise HTTPException(status_code=500, detail="报告状态文件已损坏") from exc

    metadata_dict = state_data.get("metadata") or {}
    metadata = OrderedDict((key, metadata_dict[key]) for key in metadata_dict)
    results = state_data.get("results") or {}
    channel_summary_texts = state_data.get("channelSummaryTexts") or []
    mask_options_state = state_data.get("maskOptions") or []

    selected_mask_option_ids: list[str] = []
    if mask_option_ids:
        try:
            parsed_ids = json.loads(mask_option_ids)
        except json.JSONDecodeError as exc:
            logger.warning("掩码图像选择解析失败：%s", mask_option_ids)
            raise HTTPException(status_code=400, detail="掩码图像选择格式无效") from exc

        if not isinstance(parsed_ids, list):
            raise HTTPException(status_code=400, detail="掩码图像选择格式无效")

        for item in parsed_ids:
            if not isinstance(item, str):
                raise HTTPException(status_code=400, detail="掩码图像选择格式无效")
            normalized = item.strip()
            if normalized and normalized not in selected_mask_option_ids:
                selected_mask_option_ids.append(normalized)

    elif mask_option_id:
        normalized = mask_option_id.strip()
        if normalized:
            selected_mask_option_ids.append(normalized)

    required_mask_count = 3
    if selected_mask_option_ids and len(selected_mask_option_ids) != required_mask_count:
        raise HTTPException(
            status_code=400,
            detail=f"必须选择{required_mask_count}张掩码图像",
        )

    mask_option_payloads: list[dict] = []
    if selected_mask_option_ids:
        for option_id in selected_mask_option_ids:
            option = next((item for item in mask_options_state if item.get("id") == option_id), None)
            if option is None:
                raise HTTPException(status_code=400, detail="所选掩码图像不存在")

            relative_path = option.get("relativePath")
            if not relative_path:
                raise HTTPException(status_code=400, detail="所选掩码图像路径无效")

            mask_path = (output_dir / relative_path).resolve()
            try:
                mask_path.relative_to(output_dir)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail="掩码图像路径无效") from exc

            if not mask_path.exists():
                raise HTTPException(status_code=400, detail="所选掩码图像文件不存在")

            mask_option_payloads.append(
                {
                    "path": str(mask_path),
                    "label": option.get("label") or f"{option.get('channel', '')}通道掩码",
                }
            )

    analyzer_stub = SimpleNamespace(results=results)
    report_path = output_dir / "ctc_report.docx"

    _build_report_document(
        analyzer_stub,  # type: ignore[arg-type]
        metadata,
        report_path,
        channel_summary_texts=channel_summary_texts,
        mask_options=mask_option_payloads or None,
    )
    logger.info("报告文档已生成：%s", report_path)

    report_bytes = report_path.read_bytes()
    encoded_report = base64.b64encode(report_bytes).decode("ascii")

    return JSONResponse(
        content={
            "fileName": "ctc_report.docx",
            "fileContent": encoded_report,
            "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "reportToken": report_token,
        }
    )


if __name__ == "__main__":
    import uvicorn

    port_str = os.environ.get("FASTAPI_PORT", "15000")
    try:
        port = int(port_str)
    except ValueError:
        logger.warning("警告：FASTAPI_PORT 设置无效（%s），使用默认端口 15000", port_str)
        port = 15000

    uvicorn.run(app, host="0.0.0.0", port=port)
