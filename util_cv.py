from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageTk


def bgr_to_rgb(img: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def fit_display(img: np.ndarray, max_side: int) -> np.ndarray:
    h, w = img.shape[:2]
    m = max(h, w)
    if m <= max_side:
        return img
    scale = max_side / m
    nw, nh = int(w * scale), int(h * scale)
    return cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)


def np_to_photoimage(img_bgr: np.ndarray, max_side: int) -> ImageTk.PhotoImage:
    disp = fit_display(img_bgr, max_side)
    rgb = bgr_to_rgb(disp)
    pil = Image.fromarray(rgb)
    return ImageTk.PhotoImage(pil)


def ensure_bgr(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    if img.shape[2] == 4:
        return cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img
