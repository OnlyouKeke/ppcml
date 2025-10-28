from __future__ import annotations

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List

try:
    from ultralytics import YOLO
except ImportError as exc:  # pragma: no cover - import guard for clearer message
    raise RuntimeError(
        "未找到 `ultralytics` 依赖，请在后端环境中安装后再运行。"
    ) from exc


def _load_model() -> YOLO:
    """加载YOLO模型，优先使用环境变量指定的模型权重。"""
    #model_name = os.getenv("..\model\yolo12n.pt", "..\model\yolov8n.pt")
    model_path = Path("..\model\yolo12n.pt", "..\model\yolov8n.pt")
    if not model_path.exists():
        # 让ultralytics在首次调用时自动下载官方模型权重
        model = YOLO(model_name)
    else:
        model = YOLO(model_path)
    return model


_model_lock = asyncio.Lock()
_model: YOLO | None = None


async def _get_model() -> YOLO:
    """获取单例模型实例，避免重复加载。"""
    global _model
    if _model is not None:
        return _model

    async with _model_lock:
        if _model is None:
            loop = asyncio.get_running_loop()
            _model = await loop.run_in_executor(None, _load_model)
    return _model


def _serialize_detections(result: Any) -> List[Dict[str, Any]]:
    """将YOLO的预测结果转换成可序列化的结构。"""
    detections: List[Dict[str, Any]] = []
    names = result.names or {}
    boxes = getattr(result, "boxes", None)

    if boxes is None or boxes.cls is None:
        return detections

    cls_list = boxes.cls.tolist() if hasattr(boxes.cls, "tolist") else boxes.cls
    conf_list = boxes.conf.tolist() if hasattr(boxes.conf, "tolist") else boxes.conf
    coords_list = boxes.xyxy.tolist() if hasattr(boxes.xyxy, "tolist") else boxes.xyxy

    for cls_id, conf, coords in zip(cls_list, conf_list, coords_list):
        x_min, y_min, x_max, y_max = [float(x) for x in coords]
        class_id = int(cls_id)
        detections.append(
            {
                "class_id": class_id,
                "class_name": names.get(class_id, str(class_id)),
                "confidence": float(conf),
                "box": {
                    "xmin": x_min,
                    "ymin": y_min,
                    "xmax": x_max,
                    "ymax": y_max,
                },
            }
        )

    return detections


async def predict_image_bytes(image_bytes: bytes, *, suffix: str = "") -> List[Dict[str, Any]]:
    """对上传的图片内容进行YOLO预测并返回检测结果。"""

    if not image_bytes:
        return []

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(image_bytes)
        tmp_path = Path(tmp.name)

    try:
        model = await _get_model()
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(None, model.predict, str(tmp_path))

        if results:
            return _serialize_detections(results[0])
        return []
    finally:
        tmp_path.unlink(missing_ok=True)
