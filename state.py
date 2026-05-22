from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class AppMode(Enum):
    NONE = auto()
    IMAGE = auto()
    VIDEO = auto()
    CAMERA = auto()
    DRAW = auto()


@dataclass
class ImageSettings:
    kernel_size: int = 5
    canny_t1: int = 50
    canny_t2: int = 150
    rotate_angle: float = 15.0
    scale_factor: float = 1.0
    binary_thresh: int = 127
    adaptive_block: int = 11
    adaptive_c: int = 2
    hsv_h_low: int = 0
    hsv_h_high: int = 179
    hsv_s_low: int = 50
    hsv_s_high: int = 255
    hsv_v_low: int = 50
    hsv_v_high: int = 255
    morph_kernel: int = 5
    gaussian_ksize: int = 5
    enabled_algorithm_ids: list[str] | None = None  # None = all


@dataclass
class VideoSettings:
    haar_scale: float = 1.05
    haar_neighbors: int = 5
    match_method: int = 0  # cv2.TM_SQDIFF etc.
    mog2_history: int = 500
    mog2_var_threshold: int = 16
    enabled_algorithm_ids: list[str] | None = field(
        default_factory=lambda: ["vid_original", "vid_gray", "vid_haar"]
    )
    """None 表示展示全部视频算法子窗口；默认仅 3 个以加快摄像头/视频预览。"""
    yolo_weights_path: str = "yolo11n.pt"
    """Ultralytics 导出/官方权重路径（.pt 或导出的 engine/onnx 等 YOLO 支持的格式）。"""


@dataclass
class LayoutSettings:
    """展示窗口：行优先时每行子窗口数；列优先时每列子窗口数。"""

    row_major: bool = True
    per_line: int = 3
    card_max_side: int = 600


@dataclass
class AppState:
    """Application state; ``language`` is UI locale: ``en`` (default) or ``zh``."""

    mode: AppMode = AppMode.NONE
    language: str = "en"
    dirty: bool = False
    current_path: str | None = None
    image_settings: ImageSettings = field(default_factory=ImageSettings)
    video_settings: VideoSettings = field(default_factory=VideoSettings)
    layout: LayoutSettings = field(default_factory=LayoutSettings)
    video_capture: Any = None
    template_roi: tuple[int, int, int, int] | None = None  # for template match demo
    extra: dict[str, Any] = field(default_factory=dict)
