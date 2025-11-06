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
from typing import Iterable, List, Dict, Any

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

ANALYSIS_SNAPSHOT_FILE = "analysis.json"


def _snapshot_file_path(output_dir: Path) -> Path:
    return output_dir / ANALYSIS_SNAPSHOT_FILE


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


def _ensure_within_directory(path: Path, base_dir: Path) -> Path:
    base_resolved = base_dir.resolve()
    candidate = path.resolve()
    try:
        candidate.relative_to(base_resolved)
    except ValueError as exc:  # pragma: no cover - 安全检查
        raise HTTPException(status_code=400, detail="所选文件路径无效") from exc
    return candidate


def _normalize_relative_path(path_value: str | Path, base_dir: Path) -> str:
    candidate = Path(path_value)
    resolved = candidate.resolve()
    base_resolved = base_dir.resolve()
    try:
        relative = resolved.relative_to(base_resolved)
    except ValueError as exc:  # pragma: no cover - 安全检查
        raise HTTPException(status_code=400, detail="生成的文件路径越界") from exc
    return str(relative)


def _normalize_image_set_paths(image_set: Dict[str, Any], base_dir: Path) -> Dict[str, Any]:
    normalized: Dict[str, Any] = {}
    for key, value in image_set.items():
        if key == "sub_folder":
            normalized[key] = value
            continue
        if isinstance(value, str) or isinstance(value, Path):
            normalized[key] = _normalize_relative_path(value, base_dir)
        else:
            normalized[key] = value
    return normalized


def _resolve_snapshot_path(relative_path: str, base_dir: Path) -> Path:
    candidate = base_dir / relative_path
    if not candidate.exists():
        raise HTTPException(status_code=404, detail="所选文件不存在，请重新生成报告")
    return _ensure_within_directory(candidate, base_dir)


def _resolve_image_sets(relative_sets: List[Dict[str, Any]], base_dir: Path) -> List[Dict[str, Any]]:
    resolved_sets: List[Dict[str, Any]] = []
    for image_set in relative_sets:
        resolved: Dict[str, Any] = {}
        for key, value in image_set.items():
            if key == "sub_folder":
                resolved[key] = value
            elif isinstance(value, str):
                resolved[key] = _resolve_snapshot_path(value, base_dir)
            else:
                resolved[key] = value
        resolved_sets.append(resolved)
    return resolved_sets


def _ordered_metadata_from_snapshot(snapshot: Dict[str, Any]) -> OrderedDict[str, str]:
    ordered = OrderedDict()
    for item in snapshot.get("metadata", []):
        label = item.get("label", "") if isinstance(item, dict) else ""
        value = item.get("value", "") if isinstance(item, dict) else ""
        ordered[label] = value
    return ordered


def _build_mask_options_payload(output_dir: Path, mask_candidates: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    payload: List[Dict[str, Any]] = []
    for channel in sorted(mask_candidates.keys()):
        items_payload: List[Dict[str, Any]] = []
        for relative_path in mask_candidates[channel]:
            try:
                absolute_path = _resolve_snapshot_path(relative_path, output_dir)
            except HTTPException:
                continue
            encoded_preview = _encode_preview_image(absolute_path)
            if not encoded_preview:
                continue
            mime_type, encoded_data = encoded_preview
            items_payload.append(
                {
                    "label": absolute_path.name,
                    "relativePath": relative_path,
                    "mimeType": mime_type or "image/png",
                    "data": encoded_data,
                }
            )
        if items_payload:
            payload.append({"channel": channel, "items": items_payload})
    return payload


def _create_analysis_snapshot(
    output_dir: Path,
    metadata: OrderedDict[str, str],
    analyzer: CTCAnalyzer,
    channel_summary_texts: list[str],
    result_text: str,
    remark_text: str,
    selection_text: str,
) -> Dict[str, Any]:
    doc_names = analyzer.results.get("doc_names", [])
    ctc_counts = analyzer.results.get("green_single_channel", [])
    wbc_counts = analyzer.results.get("white_single_channel", [])

    totals = {"totalCtc": sum(ctc_counts), "totalWbc": sum(wbc_counts)}

    raw_ctc_image_sets = analyzer.results.get("ctc_image_sets", [])
    normalized_ctc_sets = [
        _normalize_image_set_paths(image_set, output_dir) for image_set in raw_ctc_image_sets
    ]

    raw_mask_candidates = analyzer.results.get("mask_candidates", {}) or {}
    normalized_mask_candidates: Dict[str, List[str]] = {}
    for channel, paths in raw_mask_candidates.items():
        normalized_mask_candidates[channel] = [
            _normalize_relative_path(path, output_dir) for path in paths
        ]

    snapshot = {
        "metadata": [{"label": label, "value": value} for label, value in metadata.items()],
        "docNames": doc_names,
        "ctcCounts": ctc_counts,
        "wbcCounts": wbc_counts,
        "ctcImageSets": normalized_ctc_sets,
        "channelSummaryTexts": channel_summary_texts,
        "resultText": result_text,
        "remarkText": remark_text,
        "selectionText": selection_text,
        "totals": totals,
        "maskCandidates": normalized_mask_candidates,
        "analysisCompletedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    return snapshot


def _write_analysis_snapshot(output_dir: Path, snapshot: Dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = _snapshot_file_path(output_dir)
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_analysis_snapshot(output_dir: Path) -> Dict[str, Any]:
    snapshot_path = _snapshot_file_path(output_dir)
    if not snapshot_path.exists():
        raise HTTPException(status_code=404, detail="未找到分析记录，请重新上传影像文件生成报告")
    try:
        return json.loads(snapshot_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - 理论上不会触发
        raise HTTPException(status_code=500, detail="分析记录损坏，请重新生成报告") from exc


def _build_image_set_payload(snapshot: Dict[str, Any], output_dir: Path) -> Dict[str, Any] | None:
    relative_sets = snapshot.get("ctcImageSets", []) or []
    if not relative_sets:
        return None

    first_set = relative_sets[0]
    images_payload: List[Dict[str, Any]] = []

    def _encode_from_keys(label: str, keys: Iterable[str]) -> None:
        for key in keys:
            relative_path = first_set.get(key)
            if not relative_path:
                continue
            try:
                absolute_path = _resolve_snapshot_path(relative_path, output_dir)
            except HTTPException:
                continue
            encoded_preview = _encode_preview_image(absolute_path)
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
            break

    _encode_from_keys("蓝色通道", ("blue_path", "blue_original"))
    _encode_from_keys("绿色通道", ("green_path", "green_original"))
    _encode_from_keys("红色通道", ("mask_path", "red_path", "red_original"))

    if images_payload:
        return {"items": images_payload}
    return None


def _build_response_payload(
    snapshot: Dict[str, Any],
    output_dir: Path,
    session_id: str,
    generated_at: datetime,
    file_bytes: bytes | None = None,
) -> Dict[str, Any]:
    metadata_items = snapshot.get("metadata", []) or []
    doc_names = snapshot.get("docNames", []) or []
    ctc_counts = snapshot.get("ctcCounts", []) or []
    wbc_counts = snapshot.get("wbcCounts", []) or []

    channel_stats = [
        {"channel": name, "ctc": ctc, "wbc": wbc}
        for name, ctc, wbc in zip(doc_names, ctc_counts, wbc_counts)
    ]

    totals = snapshot.get("totals") or {
        "totalCtc": sum(ctc_counts),
        "totalWbc": sum(wbc_counts),
    }

    mask_options = _build_mask_options_payload(output_dir, snapshot.get("maskCandidates", {}) or {})
    image_set_payload = _build_image_set_payload(snapshot, output_dir)

    file_content = ""
    if file_bytes is not None:
        file_content = base64.b64encode(file_bytes).decode("ascii")

    response_payload: Dict[str, Any] = {
        "fileName": "ctc_report.docx",
        "fileContent": file_content,
        "generatedAt": generated_at.isoformat().replace("+00:00", "Z"),
        "metadata": metadata_items,
        "channels": channel_stats,
        "totals": totals,
        "resultText": snapshot.get("resultText", ""),
        "remarkText": snapshot.get("remarkText", ""),
        "selectionText": snapshot.get("selectionText", ""),
        "hasCtcImages": bool(image_set_payload),
        "imageSet": image_set_payload,
        "channelSummaryTexts": snapshot.get("channelSummaryTexts", []),
        "warnings": snapshot.get("warnings", []),
        "sessionId": session_id,
        "maskOptions": mask_options,
    }

    return response_payload
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


def _build_report_document_from_snapshot(
    metadata: OrderedDict[str, str],
    doc_names: List[str],
    ctc_counts: List[int],
    wbc_counts: List[int],
    ctc_image_sets: List[Dict[str, Any]],
    output_path: Path,
    channel_summary_texts: list[str] | None = None,
    result_text: str | None = None,
    remark_text: str | None = None,
    selection_text: str | None = None,
    selected_mask_path: Path | None = None,
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

    total_ctc = sum(ctc_counts)
    total_wbc = sum(wbc_counts)

    selection_paragraph = document.add_paragraph()
    selection_run = selection_paragraph.add_run(
        selection_text or "选三张不同荧光同一区域的照片，有方框标出是CTC。"
    )
    _apply_run_style(selection_run, 12, color=RGBColor(55, 65, 81))

    if ctc_image_sets:
        image_set = ctc_image_sets[0]

        for summary_text in channel_summary_texts or []:
            if not summary_text:
                continue
            summary_paragraph = document.add_paragraph()
            summary_paragraph.paragraph_format.space_after = Pt(2)
            summary_run = summary_paragraph.add_run(summary_text)
            _apply_run_style(summary_run, 10, color=RGBColor(55, 65, 81))

        def _resolve_preview_path(primary_key: str, *fallback_keys: str) -> Path | None:
            keys = (primary_key,) + fallback_keys
            for key in keys:
                candidate = image_set.get(key)
                if isinstance(candidate, Path) and candidate.exists():
                    return candidate
                if isinstance(candidate, str):
                    candidate_path = Path(candidate)
                    if candidate_path.exists():
                        return candidate_path
            return None

        labels_and_paths: List[tuple[str, Path | None]] = [
            ("蓝色通道", _resolve_preview_path("blue_path", "blue_original")),
            ("绿色通道", _resolve_preview_path("green_path", "green_original")),
        ]

        mask_label = "掩膜通道"
        mask_path: Path | None = None
        if selected_mask_path and selected_mask_path.exists():
            mask_path = selected_mask_path
        else:
            mask_path = _resolve_preview_path("mask_path", "red_path", "red_original")
            mask_label = "红色通道"

        labels_and_paths.append((mask_label, mask_path))

        image_table = document.add_table(rows=2, cols=3)
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

    computed_result_text = (
        f"结果说明：经实验结果判定，在一二通道中找到CD45 {total_wbc}个，CK {total_ctc}个。"
        if doc_names
        else "结果说明：未能识别出有效的检测结果，请检查上传的影像资料。"
    )
    result_text_to_use = result_text or computed_result_text
    result_paragraph = document.add_paragraph()
    result_run = result_paragraph.add_run(result_text_to_use)
    _apply_run_style(
        result_run,
        12,
        color=RGBColor(220, 38, 38) if doc_names else RGBColor(107, 114, 128),
    )

    remark_text_to_use = remark_text
    if not remark_text_to_use:
        notes_value = (metadata.get("备注") or "").strip()
        biomarker_text = notes_value if notes_value else "______________"
        remark_text_to_use = f"备注：生物标记物染色选用{biomarker_text}。"
    remark_paragraph = document.add_paragraph()
    remark_run = remark_paragraph.add_run(remark_text_to_use)
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

OUTPUT_ROOT = Path(__file__).resolve().parents[1] / "var"

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
    generate_docx: bool = Form(False, alias="generateDocx"),
    session_id: str = Form("", alias="sessionId"),
    selected_mask: str = Form("", alias="selectedMask"),
) -> JSONResponse:
    uploaded_files = files or []
    logger.info(
        "收到CTC报告生成请求：zip文件=%s，多文件数量=%d，圆度阈值=%.2f",
        bool(file and file.filename),
        len(uploaded_files),
        roundness_threshold,
    )

    # 记录初始参数，便于调试
    logger.debug(
        "generate_docx=%s, session_id=%s, selected_mask=%s",
        generate_docx,
        session_id,
        selected_mask,
    )

    work_dir: Path | None = None
    dataset_root: Path | None = None
    output_dir: Path | None = None

    try:
        if generate_docx and session_id:
            output_dir = _ensure_within_directory(OUTPUT_ROOT / session_id, OUTPUT_ROOT)
            if not output_dir.exists():
                raise HTTPException(status_code=404, detail="未找到对应的分析记录，请重新生成报告")

            snapshot = _load_analysis_snapshot(output_dir)
            metadata_ordered = _ordered_metadata_from_snapshot(snapshot)
            doc_names = snapshot.get("docNames", []) or []
            ctc_counts = snapshot.get("ctcCounts", []) or []
            wbc_counts = snapshot.get("wbcCounts", []) or []
            channel_summary_texts = snapshot.get("channelSummaryTexts", []) or []
            result_text = snapshot.get("resultText", "")
            remark_text = snapshot.get("remarkText", "")
            selection_text = snapshot.get("selectionText", "")

            resolved_image_sets = _resolve_image_sets(snapshot.get("ctcImageSets", []) or [], output_dir)

            selected_mask_path: Path | None = None
            if selected_mask:
                try:
                    selected_mask_path = _resolve_snapshot_path(selected_mask, output_dir)
                except HTTPException:
                    logger.warning("用户选择的掩膜路径无效：%s", selected_mask)
                    selected_mask_path = None

            report_path = output_dir / "ctc_report.docx"
            _build_report_document_from_snapshot(
                metadata_ordered,
                doc_names,
                ctc_counts,
                wbc_counts,
                resolved_image_sets,
                report_path,
                channel_summary_texts=channel_summary_texts,
                result_text=result_text,
                remark_text=remark_text,
                selection_text=selection_text,
                selected_mask_path=selected_mask_path,
            )

            report_bytes = report_path.read_bytes()
            snapshot["selectedMask"] = selected_mask
            snapshot["lastGeneratedAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            _write_analysis_snapshot(output_dir, snapshot)

            response_payload = _build_response_payload(
                snapshot,
                output_dir,
                session_id,
                datetime.now(timezone.utc),
                file_bytes=report_bytes,
            )
            if work_dir is not None:
                shutil.rmtree(work_dir, ignore_errors=True)
            return JSONResponse(content=response_payload)

        if (file is None or not file.filename) and not files:
            raise HTTPException(status_code=400, detail="请上传包含影像数据的ZIP文件或文件夹")

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

        channel_summary_texts = _format_channel_summary_texts(analyzer)

        doc_names = analyzer.results.get("doc_names", [])
        ctc_counts = analyzer.results.get("green_single_channel", [])
        wbc_counts = analyzer.results.get("white_single_channel", [])

        total_ctc = sum(ctc_counts)
        total_wbc = sum(wbc_counts)

        selection_text = "选三张不同荧光同一区域的照片，有方框标出是CTC。"
        result_text = (
            f"结果说明：经实验结果判定，在一二通道中找到CD45 {total_wbc}个，CK {total_ctc}个。"
            if doc_names
            else "结果说明：未识别出有效的检测结果，请检查上传的影像资料。"
        )

        notes_value = (metadata.get("备注") or "").strip()
        biomarker_text = notes_value if notes_value else "______________"
        remark_text = f"备注：生物标记物染色选用{biomarker_text}。"

        snapshot = _create_analysis_snapshot(
            output_dir,
            metadata,
            analyzer,
            channel_summary_texts,
            result_text,
            remark_text,
            selection_text,
        )

        _write_analysis_snapshot(output_dir, snapshot)

        report_bytes: bytes | None = None
        if generate_docx:
            resolved_image_sets = _resolve_image_sets(snapshot.get("ctcImageSets", []) or [], output_dir)
            selected_mask_path: Path | None = None
            if selected_mask:
                try:
                    selected_mask_path = _resolve_snapshot_path(selected_mask, output_dir)
                except HTTPException:
                    logger.warning("用户选择的掩膜路径无效：%s", selected_mask)
                    selected_mask_path = None

            report_path = output_dir / "ctc_report.docx"
            _build_report_document_from_snapshot(
                metadata,
                snapshot.get("docNames", []) or [],
                snapshot.get("ctcCounts", []) or [],
                snapshot.get("wbcCounts", []) or [],
                resolved_image_sets,
                report_path,
                channel_summary_texts=channel_summary_texts,
                result_text=result_text,
                remark_text=remark_text,
                selection_text=selection_text,
                selected_mask_path=selected_mask_path,
            )
            report_bytes = report_path.read_bytes()
            snapshot["selectedMask"] = selected_mask
            snapshot["lastGeneratedAt"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            _write_analysis_snapshot(output_dir, snapshot)

        response_payload = _build_response_payload(
            snapshot,
            output_dir,
            output_dir.name,
            datetime.now(timezone.utc),
            file_bytes=report_bytes,
        )
        if work_dir is not None:
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


if __name__ == "__main__":
    import uvicorn

    port_str = os.environ.get("FASTAPI_PORT", "8001")
    try:
        port = int(port_str)
    except ValueError:
        logger.warning("警告：FASTAPI_PORT 设置无效（%s），使用默认端口 8001", port_str)
        port = 8001

    uvicorn.run(app, host="0.0.0.0", port=port)
