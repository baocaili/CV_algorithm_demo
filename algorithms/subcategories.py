"""算法子类（用于设置里按子类多选展示）。"""

from __future__ import annotations

from collections import defaultdict

from cv_course.algorithms.registry import AlgorithmSpec, iter_algorithms

# 图像算法 id -> 子类名（与设计说明中的知识结构对应）
IMAGE_SUBGROUP: dict[str, str] = {
    "img_original": "基础",
    "img_rotate": "几何变换",
    "img_scale": "几何变换",
    "img_flip_h": "几何变换",
    "img_flip_v": "几何变换",
    "img_affine": "几何变换",
    "img_add": "像素与算术",
    "img_sub": "像素与算术",
    "img_mul": "像素与算术",
    "img_threshold": "二值化与阈值",
    "img_mask": "二值化与阈值",
    "img_q_single": "二值化与阈值",
    "img_q_double": "二值化与阈值",
    "img_thresh_zero": "二值化与阈值",
    "img_adaptive": "二值化与阈值",
    "img_ch_b": "色彩与通道",
    "img_ch_g": "色彩与通道",
    "img_ch_merge": "色彩与通道",
    "img_hsv": "色彩与通道",
    "img_hist_gray": "直方图",
    "img_hist_color": "直方图",
    "img_hist_eq": "直方图",
    "img_hist_cmp": "直方图",
    "img_conv2d": "滤波与卷积",
    "filt_blur": "滤波与卷积",
    "filt_sharpen": "滤波与卷积",
    "morph_erode": "形态学",
    "morph_dilate": "形态学",
    "morph_close": "形态学",
    "morph_open": "形态学",
    "morph_grad": "形态学",
    "morph_tophat": "形态学",
    "morph_blackhat": "形态学",
    "edge_laplace": "边缘检测",
    "edge_canny": "边缘检测",
    "edge_sobel": "边缘检测",
    "edge_scharr": "边缘检测",
    "img_contours": "轮廓与拼接",
    "img_stitch": "轮廓与拼接",
    "filt_gray": "艺术滤镜",
    "filt_vintage": "艺术滤镜",
    "filt_emboss": "艺术滤镜",
}

VIDEO_SUBGROUP: dict[str, str] = {
    "vid_original": "基础",
    "vid_gray": "基础",
    "vid_haar": "经典检测",
    "vid_hog": "经典检测",
    "vid_match_sqdiff": "模板匹配",
    "vid_match_sqdiff_n": "模板匹配",
    "vid_match_ccorr": "模板匹配",
    "vid_match_ccorr_n": "模板匹配",
    "vid_match_coeff": "模板匹配",
    "vid_match_coeff_n": "模板匹配",
    "vid_motion": "运动与跟踪",
    "vid_meanshift": "运动与跟踪",
    "vid_camshift": "运动与跟踪",
    "vid_mog": "背景建模",
    "vid_mog2": "背景建模",
    "vid_yolo_det": "YOLO (Ultralytics)",
    "vid_yolo_rec": "YOLO (Ultralytics)",
}


def subgroup_for(spec: AlgorithmSpec) -> str:
    if spec.category == "image":
        return IMAGE_SUBGROUP.get(spec.id, "其他")
    if spec.category == "video":
        return VIDEO_SUBGROUP.get(spec.id, "其他")
    return "其他"


def group_specs_by_subgroup(category: str) -> dict[str, list[AlgorithmSpec]]:
    out: dict[str, list[AlgorithmSpec]] = defaultdict(list)
    for s in iter_algorithms(category):
        out[subgroup_for(s)].append(s)
    for k in out:
        out[k].sort(key=lambda x: x.title)
    return dict(out)


def all_ids_for_category(category: str) -> list[str]:
    return [s.id for s in iter_algorithms(category)]
