"""OpenCV 直方图可视化：坐标轴、刻度、足够高的画布（教学展示）。"""

from __future__ import annotations

import cv2
import numpy as np


def _draw_xy_axes(
    canvas: np.ndarray,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    x_ticks: list[tuple[int, str]],
    y_ticks: list[tuple[int, str]],
    title: str,
) -> None:
    """在 BGR 画布上画坐标轴与刻度（英文/数字，避免 OpenCV 对中文 putText 的限制）。"""
    cv2.rectangle(canvas, (x0, y0), (x1, y1), (40, 40, 40), 1)
    cv2.line(canvas, (x0, y1), (x1, y1), (0, 0, 0), 2)
    cv2.line(canvas, (x0, y0), (x0, y1), (0, 0, 0), 2)
    font = cv2.FONT_HERSHEY_SIMPLEX
    fs = 0.45
    for x, lab in x_ticks:
        cv2.line(canvas, (x, y1), (x, y1 + 5), (0, 0, 0), 1)
        cv2.putText(canvas, lab, (x - 10, y1 + 22), font, fs, (0, 0, 0), 1, cv2.LINE_AA)
    for y, lab in y_ticks:
        cv2.line(canvas, (x0 - 5, y), (x0, y), (0, 0, 0), 1)
        cv2.putText(canvas, lab, (max(4, x0 - 48), y + 4), font, fs, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.putText(canvas, title, (x0, max(18, y0 - 8)), font, 0.55, (20, 20, 120), 1, cv2.LINE_AA)
    cv2.putText(canvas, "gray level k", (x1 - 120, y1 + 38), font, 0.42, (60, 60, 60), 1, cv2.LINE_AA)
    cv2.putText(canvas, "norm h(k)", (max(4, x0 - 88), y0 + 4), font, 0.42, (60, 60, 60), 1, cv2.LINE_AA)


def render_gray_histogram(hist256: np.ndarray, out_w: int, out_h: int) -> np.ndarray:
    """灰度直方图：白底、坐标轴、柱状图。hist256 长度 256。"""
    h = np.asarray(hist256, dtype=np.float64).reshape(-1)
    if h.size != 256:
        h = np.pad(h, (0, max(0, 256 - h.size)))[:256]
    canvas = np.full((out_h, out_w, 3), 255, dtype=np.uint8)
    ml, mr, mt, mb = 56, 24, 48, 56
    xi0, yi0, xi1, yi1 = ml, mt, out_w - mr, out_h - mb
    hmax = float(np.max(h)) + 1e-9
    hn = h / hmax
    plot_w = xi1 - xi0
    for k in range(256):
        x = int(xi0 + k * plot_w / 255)
        x2 = int(xi0 + (k + 1) * plot_w / 255)
        bar_h = int(hn[k] * (yi1 - yi0 - 1))
        y_top = yi1 - bar_h
        cv2.rectangle(canvas, (x, y_top), (max(x + 1, x2), yi1), (70, 70, 70), -1)
    x_ticks = []
    for v in (0, 64, 128, 192, 255):
        x = int(xi0 + v * plot_w / 255)
        x_ticks.append((x, str(v)))
    y_ticks = []
    for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        y = int(yi1 - t * (yi1 - yi0))
        y_ticks.append((y, f"{t:.2f}"))
    _draw_xy_axes(canvas, xi0, yi0, xi1, yi1, x_ticks, y_ticks, "Gray histogram h(k)")
    return canvas


def render_gray_histogram_panel(
    gray: np.ndarray,
    hist256: np.ndarray,
    out_w: int,
    thumb_max_h: int = 200,
    hist_h: int = 420,
) -> np.ndarray:
    """灰度缩略图 + 直方图，排版与 :func:`render_rgb_histograms` 一致，便于子图对齐。"""
    h0, w0 = int(gray.shape[0]), int(gray.shape[1])
    scale = min(out_w / max(w0, 1), thumb_max_h / max(h0, 1), 1.0)
    tw, th = max(1, int(w0 * scale)), max(1, int(h0 * scale))
    thumb_gray = cv2.resize(gray, (tw, th), interpolation=cv2.INTER_AREA)
    thumb = cv2.cvtColor(thumb_gray, cv2.COLOR_GRAY2BGR)
    pad_w = max(out_w, tw)
    if tw < pad_w:
        pad = np.full((th, pad_w - tw, 3), 240, dtype=np.uint8)
        thumb = np.hstack([thumb, pad])
    hist_strip = render_gray_histogram(hist256, pad_w, hist_h)
    return np.vstack([thumb, hist_strip])


def render_rgb_histograms(
    img_bgr: np.ndarray,
    out_w: int,
    thumb_max_h: int,
    hist_h: int,
) -> np.ndarray:
    """缩略图 + 三通道曲线同坐标系，带轴与图例。"""
    h0, w0 = img_bgr.shape[:2]
    scale = min(out_w / max(w0, 1), thumb_max_h / max(h0, 1), 1.0)
    tw, th = max(1, int(w0 * scale)), max(1, int(h0 * scale))
    thumb = cv2.resize(img_bgr, (tw, th), interpolation=cv2.INTER_AREA)
    pad_w = max(out_w, tw)
    if tw < pad_w:
        pad = np.full((th, pad_w - tw, 3), 240, dtype=np.uint8)
        thumb = np.hstack([thumb, pad])
    hist_canvas = np.full((hist_h, pad_w, 3), 255, dtype=np.uint8)
    ml, mr, mt, mb = 56, 24, 44, 52
    xi0, yi0, xi1, yi1 = ml, mt, pad_w - mr, hist_h - mb
    plot_w = xi1 - xi0
    colors = [(255, 0, 0), (0, 180, 0), (0, 0, 255)]  # B,G,R in BGR order for B,G,R channels
    labels = ("B", "G", "R")
    for ch, col, lab in zip((0, 1, 2), colors, labels):
        hist = cv2.calcHist([img_bgr], [ch], None, [256], [0, 256]).reshape(-1).astype(np.float64)
        hn = hist / (float(np.max(hist)) + 1e-9)
        pts = []
        for k in range(256):
            x = int(xi0 + k * plot_w / 255)
            y = int(yi1 - hn[k] * (yi1 - yi0 - 1))
            pts.append((x, y))
        for i in range(len(pts) - 1):
            cv2.line(hist_canvas, pts[i], pts[i + 1], col, 2, cv2.LINE_AA)
        cv2.putText(hist_canvas, lab, (pad_w - 80 + ch * 22, mt + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, col, 1, cv2.LINE_AA)
    x_ticks = [(int(xi0 + v * plot_w / 255), str(v)) for v in (0, 64, 128, 192, 255)]
    y_ticks = [(int(yi1 - t * (yi1 - yi0)), f"{t:.2f}") for t in (0.0, 0.5, 1.0)]
    _draw_xy_axes(hist_canvas, xi0, yi0, xi1, yi1, x_ticks, y_ticks, "B/G/R histograms")
    return np.vstack([thumb, hist_canvas])


def render_hist_compare_panel(
    gray: np.ndarray,
    eq: np.ndarray,
    corr: float,
    out_w: int,
    out_h: int,
) -> np.ndarray:
    """并排显示原灰度图与均衡图 + 叠加两条归一化直方图 + 相关系数。"""
    mid = out_w // 2
    tw = max(1, mid - 16)
    th = max(1, out_h // 3 - 8)
    g_small = cv2.resize(gray, (tw, th))
    e_small = cv2.resize(eq, (tw, th))
    top = np.hstack([g_small, e_small])
    top = cv2.cvtColor(top, cv2.COLOR_GRAY2BGR)
    if top.shape[1] != out_w:
        top = cv2.resize(top, (out_w, top.shape[0]))
    mt = 40
    rest_h = max(220, out_h - top.shape[0] - mt)
    plot = np.full((rest_h, out_w, 3), 255, dtype=np.uint8)
    h1 = cv2.calcHist([gray], [0], None, [256], [0, 256]).reshape(-1).astype(np.float64)
    h2 = cv2.calcHist([eq], [0], None, [256], [0, 256]).reshape(-1).astype(np.float64)
    h1 /= float(np.max(h1)) + 1e-9
    h2 /= float(np.max(h2)) + 1e-9
    px0, py0, px1, py1 = 56, 36, out_w - 24, rest_h - 48
    pw = px1 - px0
    pts1 = [(int(px0 + k * pw / 255), int(py1 - h1[k] * (py1 - py0))) for k in range(256)]
    pts2 = [(int(px0 + k * pw / 255), int(py1 - h2[k] * (py1 - py0))) for k in range(256)]
    for i in range(255):
        cv2.line(plot, pts1[i], pts1[i + 1], (200, 80, 80), 2, cv2.LINE_AA)
        cv2.line(plot, pts2[i], pts2[i + 1], (80, 120, 200), 2, cv2.LINE_AA)
    x_ticks = [(int(px0 + v * pw / 255), str(v)) for v in (0, 128, 255)]
    y_ticks = [(int(py1 - t * (py1 - py0)), f"{t:.2f}") for t in (0.0, 0.5, 1.0)]
    _draw_xy_axes(plot, px0, py0, px1, py1, x_ticks, y_ticks, "compare: orig vs eq-hist")
    cv2.putText(plot, "orig hist", (px1 - 200, py0 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 80, 80), 1, cv2.LINE_AA)
    cv2.putText(plot, "eq hist", (px1 - 100, py0 + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (80, 120, 200), 1, cv2.LINE_AA)
    banner = np.full((mt, out_w, 3), 245, dtype=np.uint8)
    cv2.putText(
        banner,
        f"HISTCMP_CORREL = {corr:.6f}",
        (12, 26),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (20, 20, 100),
        1,
        cv2.LINE_AA,
    )
    out = np.vstack([banner, top, plot])
    if out.shape[0] > out_h:
        out = cv2.resize(out, (out_w, out_h), interpolation=cv2.INTER_AREA)
    elif out.shape[0] < out_h:
        pad = np.full((out_h - out.shape[0], out_w, 3), 255, dtype=np.uint8)
        out = np.vstack([out, pad])
    return out
