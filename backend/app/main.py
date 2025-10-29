import hashlib
import os
import shutil
import sys
import tempfile
import time
import zipfile
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from .ctc import CTCAnalyzer


def verify_startup_token() -> None:
    """验证启动token，确保只能通过前端启动"""
    token = os.environ.get("FASTAPI_STARTUP_TOKEN")
    if not token:
        print("错误：缺少启动token，此应用只能通过前端启动")
        sys.exit(1)

    try:
        timestamp_str, hash_part = token.split("_", 1)
        timestamp = int(timestamp_str)
        current_time = int(time.time())

        if current_time - timestamp > 60:
            print("错误：启动token已过期")
            sys.exit(1)

        expected_hash = hashlib.sha256(f"fastapi_startup_{timestamp}".encode()).hexdigest()[:16]
        if hash_part != expected_hash:
            print("错误：无效的启动token")
            sys.exit(1)

        print("启动token验证成功")
    except (ValueError, IndexError):
        print("错误：启动token格式无效")
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
    species: str,
    sample_type: str,
    mass_location: str,
    notes: str,
) -> OrderedDict:
    entries: OrderedDict[str, str] = OrderedDict()
    entries["宠物姓名"] = pet_name or "未填写"
    entries["主人姓名"] = owner_name or "未填写"
    entries["年龄"] = age or "未填写"
    entries["性别"] = gender or "未填写"
    entries["品种"] = species or "未填写"
    entries["样本类型"] = sample_type or "未填写"
    entries["同侧是否有肿块及部位"] = mass_location or "未填写"
    entries["备注"] = notes or "无"
    return entries


def _apply_font_size(paragraphs: Iterable) -> None:
    for paragraph in paragraphs:
        for run in paragraph.runs:
            run.font.size = Pt(12)
            run.font.name = "SimSun"


def _populate_table(table, rows: List[List[str]]) -> None:
    for row_idx, row_values in enumerate(rows):
        row = table.rows[row_idx]
        for cell, value in zip(row.cells, row_values):
            cell.text = value
            _apply_font_size(cell.paragraphs)


def _build_report_document(analyzer: CTCAnalyzer, metadata: OrderedDict[str, str], output_path: Path) -> None:
    document = Document()
    title = document.add_heading("检测报告", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    document.add_paragraph(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")

    document.add_heading("最新输入的信息", level=1)
    meta_table = document.add_table(rows=len(metadata), cols=2)
    meta_table.style = "Table Grid"
    _populate_table(meta_table, [[label, value] for label, value in metadata.items()])

    document.add_paragraph()
    document.add_heading("检测结果", level=1)

    doc_names = analyzer.results.get("doc_names", [])
    ctc_counts = analyzer.results.get("green_single_channel", [])
    wbc_counts = analyzer.results.get("white_single_channel", [])

    if doc_names:
        summary_table = document.add_table(rows=len(doc_names) + 1, cols=3)
        summary_table.style = "Table Grid"
        header_values = ["检测区域", "CTC计数", "白细胞计数"]
        _populate_table(summary_table, [header_values] + [[doc_names[i], str(ctc_counts[i]), str(wbc_counts[i])] for i in range(len(doc_names))])

        total_ctc = sum(ctc_counts)
        total_wbc = sum(wbc_counts)
        document.add_paragraph(
            f"综合分析：在上传的数据集中共识别出 {total_ctc} 个疑似CTC细胞，"
            f"{total_wbc} 个疑似白细胞。"
        )
    else:
        document.add_paragraph("未从上传的数据中提取到有效的统计结果。")

    document.add_paragraph()
    document.add_heading("结论与建议", level=1)
    document.add_paragraph("结果：经实验室检验，在不同荧光通道中检出疑似CTC细胞。")
    document.add_paragraph("建议：本检测报告仅供临床诊断参考，请结合临床症状综合评估。")
    document.add_paragraph("备注信息：" + metadata.get("备注", "无"))

    signature = document.add_paragraph("医师签名：____________________")
    signature.alignment = WD_ALIGN_PARAGRAPH.RIGHT

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


@app.post("/ctc/report")
async def generate_ctc_report(
    file: UploadFile | None = File(None),
    files: List[UploadFile] | None = File(None),
    pet_name: str = Form("", alias="petName"),
    owner_name: str = Form("", alias="ownerName"),
    age: str = Form("", alias="age"),
    gender: str = Form("", alias="gender"),
    species: str = Form("", alias="species"),
    sample_type: str = Form("", alias="sampleType"),
    mass_location: str = Form("", alias="massLocation"),
    notes: str = Form("", alias="notes"),
    roundness_threshold: float = Form(0.3, alias="roundnessThreshold"),
) -> FileResponse:
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
        elif files:
            work_dir, dataset_root, output_dir = await _prepare_workdir_from_files(files)
        else:
            raise HTTPException(status_code=400, detail="未提供有效的影像数据")

        analyzer = CTCAnalyzer(str(dataset_root), str(output_dir), roundness_threshold=roundness_threshold)
        analyzer.process_all_images()

        metadata = _create_metadata_entries(
            pet_name,
            owner_name,
            age,
            gender,
            species,
            sample_type,
            mass_location,
            notes,
        )

        report_path = output_dir / "ctc_report.docx"
        _build_report_document(analyzer, metadata, report_path)

        background = BackgroundTask(lambda: shutil.rmtree(work_dir, ignore_errors=True))
        return FileResponse(
            report_path,
            filename="ctc_report.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            background=background,
        )
    except zipfile.BadZipFile as exc:
        if work_dir is not None:
            shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail="压缩包文件损坏或格式错误") from exc
    except HTTPException:
        if work_dir is not None:
            shutil.rmtree(work_dir, ignore_errors=True)
        raise
    except Exception as exc:
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
        print(f"警告：FASTAPI_PORT 设置无效（{port_str}），使用默认端口 8001")
        port = 8001

    uvicorn.run(app, host="0.0.0.0", port=port)
