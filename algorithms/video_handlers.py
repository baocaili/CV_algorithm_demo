from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import cv2
import numpy as np

from cv_course.state import VideoSettings


@dataclass
class MeanShiftEngine:
    track_window: tuple[int, int, int, int] | None = None
    roi_hist: np.ndarray | None = None


@dataclass
class CamShiftEngine:
    track_window: tuple[int, int, int, int] | None = None
    roi_hist: np.ndarray | None = None


@dataclass
class VideoEngine:
    mog: Any | None = None
    mog2: Any | None = None
    first_gray: np.ndarray | None = None
    template: np.ndarray | None = None
    meanshift: MeanShiftEngine = field(default_factory=MeanShiftEngine)
    camshift: CamShiftEngine = field(default_factory=CamShiftEngine)
    yolo_model: Any | None = None
    yolo_path_loaded: str | None = None

    def reset(self) -> None:
        self.mog = None
        self.mog2 = None
        self.first_gray = None
        self.template = None
        self.meanshift = MeanShiftEngine()
        self.camshift = CamShiftEngine()
        self.yolo_model = None
        self.yolo_path_loaded = None


def _ensure_engine(ctx: VideoEngine | None) -> VideoEngine:
    if ctx is None:
        return VideoEngine()
    return ctx


def apply_video_gray(frame: np.ndarray, _p: VideoSettings, _ctx: VideoEngine | None) -> np.ndarray:
    g = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)


def apply_video_original(frame: np.ndarray, _p: VideoSettings, _ctx: VideoEngine | None) -> np.ndarray:
    """原始彩色画面（对照其它算法子窗口）。"""
    return frame.copy()


def apply_haar(frame: np.ndarray, p: VideoSettings, _ctx: VideoEngine | None) -> np.ndarray:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(path)
    faces = cascade.detectMultiScale(gray, p.haar_scale, p.haar_neighbors)
    out = frame.copy()
    for (x, y, w, h) in faces:
        cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return out


def apply_hog(frame: np.ndarray, _p: VideoSettings, _ctx: VideoEngine | None) -> np.ndarray:
    hog = cv2.HOGDescriptor()
    hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
    rects, _w = hog.detectMultiScale(frame, winStride=(8, 8), padding=(8, 8), scale=1.05)
    out = frame.copy()
    for (x, y, w, h) in rects:
        cv2.rectangle(out, (x, y), (x + w, y + h), (255, 0, 0), 2)
    return out


def _template_from_frame(frame: np.ndarray, ctx: VideoEngine) -> np.ndarray:
    if ctx.template is not None:
        return ctx.template
    h, w = frame.shape[:2]
    tw, th = max(20, w // 8), max(20, h // 8)
    cx, cy = w // 2, h // 2
    ctx.template = frame[cy - th // 2 : cy + th // 2, cx - tw // 2 : cx + tw // 2].copy()
    return ctx.template


def _match(frame: np.ndarray, p: VideoSettings, ctx: VideoEngine, method: int) -> np.ndarray:
    tpl = _template_from_frame(frame, ctx)
    if tpl.size == 0:
        return frame
    res = cv2.matchTemplate(frame, tpl, method)
    out = frame.copy()
    th, tw = tpl.shape[:2]
    if method in (cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED):
        _, _min_val, _, min_loc = cv2.minMaxLoc(res)
        top_left = min_loc
    else:
        _, _max_val, _, max_loc = cv2.minMaxLoc(res)
        top_left = max_loc
    cv2.rectangle(out, top_left, (top_left[0] + tw, top_left[1] + th), (0, 255, 255), 2)
    cv2.putText(out, f"match m={method}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    return out


def apply_match_sqdiff(frame: np.ndarray, p: VideoSettings, ctx: VideoEngine | None) -> np.ndarray:
    c = _ensure_engine(ctx)
    return _match(frame, p, c, cv2.TM_SQDIFF)


def apply_match_sqdiff_norm(frame: np.ndarray, p: VideoSettings, ctx: VideoEngine | None) -> np.ndarray:
    c = _ensure_engine(ctx)
    return _match(frame, p, c, cv2.TM_SQDIFF_NORMED)


def apply_match_ccorr(frame: np.ndarray, p: VideoSettings, ctx: VideoEngine | None) -> np.ndarray:
    c = _ensure_engine(ctx)
    return _match(frame, p, c, cv2.TM_CCORR)


def apply_match_ccorr_norm(frame: np.ndarray, p: VideoSettings, ctx: VideoEngine | None) -> np.ndarray:
    c = _ensure_engine(ctx)
    return _match(frame, p, c, cv2.TM_CCORR_NORMED)


def apply_match_coeff(frame: np.ndarray, p: VideoSettings, ctx: VideoEngine | None) -> np.ndarray:
    c = _ensure_engine(ctx)
    return _match(frame, p, c, cv2.TM_CCOEFF)


def apply_match_coeff_norm(frame: np.ndarray, p: VideoSettings, ctx: VideoEngine | None) -> np.ndarray:
    c = _ensure_engine(ctx)
    return _match(frame, p, c, cv2.TM_CCOEFF_NORMED)


def apply_motion(frame: np.ndarray, _p: VideoSettings, ctx: VideoEngine | None) -> np.ndarray:
    c = _ensure_engine(ctx)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if c.first_gray is None:
        c.first_gray = gray
        return frame
    diff = cv2.absdiff(c.first_gray, gray)
    _, th = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    c.first_gray = gray
    return cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)


def apply_mog(frame: np.ndarray, _p: VideoSettings, ctx: VideoEngine | None) -> np.ndarray:
    c = _ensure_engine(ctx)
    if c.mog is None:
        try:
            c.mog = cv2.bgsegm.createBackgroundSubtractorMOG()
        except AttributeError:
            c.mog = cv2.createBackgroundSubtractorKNN()
    mask = c.mog.apply(frame)
    return cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)


def apply_mog2(frame: np.ndarray, p: VideoSettings, ctx: VideoEngine | None) -> np.ndarray:
    c = _ensure_engine(ctx)
    if c.mog2 is None:
        c.mog2 = cv2.createBackgroundSubtractorMOG2(
            history=p.mog2_history, varThreshold=p.mog2_var_threshold, detectShadows=True
        )
    mask = c.mog2.apply(frame)
    return cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)


def apply_meanshift(frame: np.ndarray, _p: VideoSettings, ctx: VideoEngine | None) -> np.ndarray:
    c = _ensure_engine(ctx)
    ms = c.meanshift
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    if ms.track_window is None:
        h, w = frame.shape[:2]
        ms.track_window = (w // 2 - 50, h // 2 - 50, 100, 100)
        x, y, ww, hh = ms.track_window
        roi = hsv[y : y + hh, x : x + ww]
        mask = cv2.inRange(roi, np.array((0.0, 60.0, 32.0)), np.array((180.0, 255.0, 255.0)))
        ms.roi_hist = cv2.calcHist([roi], [0], mask, [180], [0, 180])
        cv2.normalize(ms.roi_hist, ms.roi_hist, 0, 255, cv2.NORM_MINMAX)
    dst = cv2.calcBackProject([hsv], [0], ms.roi_hist, [0, 180], 1)
    _, ms.track_window = cv2.meanShift(
        dst, ms.track_window, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
    )
    x, y, ww, hh = ms.track_window
    out = frame.copy()
    cv2.rectangle(out, (x, y), (x + ww, y + hh), (0, 255, 255), 2)
    return out


def apply_camshift(frame: np.ndarray, _p: VideoSettings, ctx: VideoEngine | None) -> np.ndarray:
    c = _ensure_engine(ctx)
    cs = c.camshift
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    if cs.track_window is None:
        h, w = frame.shape[:2]
        cs.track_window = (w // 2 - 60, h // 2 - 60, 120, 120)
        x, y, ww, hh = cs.track_window
        roi = hsv[y : y + hh, x : x + ww]
        mask = cv2.inRange(roi, np.array((0.0, 60.0, 32.0)), np.array((180.0, 255.0, 255.0)))
        cs.roi_hist = cv2.calcHist([roi], [0], mask, [180], [0, 180])
        cv2.normalize(cs.roi_hist, cs.roi_hist, 0, 255, cv2.NORM_MINMAX)
    dst = cv2.calcBackProject([hsv], [0], cs.roi_hist, [0, 180], 1)
    rr, cs.track_window = cv2.CamShift(
        dst, cs.track_window, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)
    )
    out = frame.copy()
    try:
        box = cv2.boxPoints(rr)
        box = np.int32(box)
        cv2.polylines(out, [box], True, (255, 0, 255), 2)
    except cv2.error:
        pass
    return out


def _yolo_model(ctx: VideoEngine, weights: str):
    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise RuntimeError("请安装 ultralytics：pip install ultralytics") from e
    w = (weights or "").strip() or "yolo11n.pt"
    if ctx.yolo_path_loaded != w or ctx.yolo_model is None:
        ctx.yolo_model = YOLO(w)
        ctx.yolo_path_loaded = w
    return ctx.yolo_model


def apply_yolo_det(frame: np.ndarray, p: VideoSettings, ctx: VideoEngine | None) -> np.ndarray:
    c = _ensure_engine(ctx)
    model = _yolo_model(c, p.yolo_weights_path)
    results = model.predict(frame, verbose=False)
    return results[0].plot()


def apply_yolo_rec(frame: np.ndarray, p: VideoSettings, ctx: VideoEngine | None) -> np.ndarray:
    """与检测共用 Ultralytics 导出模型；本视图强调类别名称汇总（识别）。"""
    c = _ensure_engine(ctx)
    model = _yolo_model(c, p.yolo_weights_path)
    results = model.predict(frame, verbose=False)
    r0 = results[0]
    out = r0.plot()
    names: list[str] = []
    if r0.boxes is not None and len(r0.boxes):
        cls_t = r0.boxes.cls
        if hasattr(cls_t, "cpu"):
            cls_t = cls_t.cpu()
        if hasattr(cls_t, "numpy"):
            cls_ids = [int(x) for x in cls_t.numpy().flatten()]
        else:
            cls_ids = [int(x) for x in cls_t]
        nmap = r0.names or {}
        seen: list[str] = []
        for ci in cls_ids:
            nm = str(nmap.get(int(ci), ci))
            if nm not in seen:
                seen.append(nm)
        names = seen
    msg = "识别: " + ("、".join(names) if names else "未检出")
    cv2.putText(out, msg[:70], (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 0), 2)
    return out


VIDEO_HANDLERS: dict[str, Any] = {
    "vid_original": apply_video_original,
    "vid_gray": apply_video_gray,
    "vid_haar": apply_haar,
    "vid_hog": apply_hog,
    "vid_match_sqdiff": apply_match_sqdiff,
    "vid_match_sqdiff_n": apply_match_sqdiff_norm,
    "vid_match_ccorr": apply_match_ccorr,
    "vid_match_ccorr_n": apply_match_ccorr_norm,
    "vid_match_coeff": apply_match_coeff,
    "vid_match_coeff_n": apply_match_coeff_norm,
    "vid_motion": apply_motion,
    "vid_meanshift": apply_meanshift,
    "vid_camshift": apply_camshift,
    "vid_mog": apply_mog,
    "vid_mog2": apply_mog2,
    "vid_yolo_det": apply_yolo_det,
    "vid_yolo_rec": apply_yolo_rec,
}
