from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from cv_course.state import ImageSettings


def apply_original(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    return img.copy()


def apply_rotate(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    h, w = img.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), p.rotate_angle, 1.0)
    return cv2.warpAffine(img, m, (w, h))


def apply_scale(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    f = max(0.05, float(p.scale_factor))
    h, w = img.shape[:2]
    return cv2.resize(img, (int(w * f), int(h * f)), interpolation=cv2.INTER_LINEAR)


def apply_flip_h(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    return cv2.flip(img, 1)


def apply_flip_v(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    return cv2.flip(img, 0)


def apply_add(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    return cv2.add(img, np.full_like(img, 40))


def apply_sub(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    return cv2.subtract(img, np.full_like(img, 40))


def apply_mul_safe(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    return np.clip(img.astype(np.float32) * 1.2, 0, 255).astype(np.uint8)


def apply_threshold_binary(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, p.binary_thresh, 255, cv2.THRESH_BINARY)
    return cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)


def apply_mask(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, p.binary_thresh, 255, cv2.THRESH_BINARY)
    return cv2.bitwise_and(img, img, mask=mask)


def apply_channel_split_b(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    b, g, r = cv2.split(img)
    z = np.zeros_like(b)
    return cv2.merge([b, z, z])


def apply_channel_split_g(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    b, g, r = cv2.split(img)
    z = np.zeros_like(b)
    return cv2.merge([z, g, z])


def apply_channel_merge(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    b, g, r = cv2.split(img)
    return cv2.merge([b, g, r])


def apply_hsv_mask(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    low = np.array([p.hsv_h_low, p.hsv_s_low, p.hsv_v_low])
    high = np.array([p.hsv_h_high, p.hsv_s_high, p.hsv_v_high])
    mask = cv2.inRange(hsv, low, high)
    return cv2.bitwise_and(img, img, mask=mask)


def apply_affine(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    h, w = img.shape[:2]
    pts1 = np.float32([[50, 50], [200, 50], [50, 200]])
    pts2 = np.float32([[10, 100], [200, 50], [100, 250]])
    m = cv2.getAffineTransform(pts1, pts2)
    return cv2.warpAffine(img, m, (w, h))


def apply_hist_gray(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    from cv_course.algorithms.hist_vis import render_gray_histogram_panel

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).reshape(-1).astype(np.float64)
    out_w = min(1024, max(520, int(img.shape[1])))
    return render_gray_histogram_panel(gray, hist, out_w, thumb_max_h=200, hist_h=420)


def apply_hist_color(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    from cv_course.algorithms.hist_vis import render_rgb_histograms

    out_w = min(1024, max(520, int(img.shape[1])))
    return render_rgb_histograms(img, out_w, thumb_max_h=200, hist_h=420)


def apply_hist_compare(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    from cv_course.algorithms.hist_vis import render_hist_compare_panel

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    eq = cv2.equalizeHist(gray)
    h1 = cv2.calcHist([gray], [0], None, [256], [0, 256])
    h2 = cv2.calcHist([eq], [0], None, [256], [0, 256])
    cv2.normalize(h1, h1, 0, 1, cv2.NORM_MINMAX)
    cv2.normalize(h2, h2, 0, 1, cv2.NORM_MINMAX)
    d = float(cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL))
    return render_hist_compare_panel(gray, eq, d, 900, 620)


def apply_hist_equal(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = cv2.split(ycrcb)
    y_eq = cv2.equalizeHist(y)
    merged = cv2.merge([y_eq, cr, cb])
    return cv2.cvtColor(merged, cv2.COLOR_YCrCb2BGR)


def apply_quantize_single(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, p.binary_thresh, 255, cv2.THRESH_BINARY)
    return cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)


def apply_quantize_double(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, p.binary_thresh, 255, cv2.THRESH_BINARY_INV)
    return cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)


def apply_threshold_zero(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, p.binary_thresh, 255, cv2.THRESH_TOZERO)
    return cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)


def apply_adaptive(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    b = max(3, p.adaptive_block | 1)
    th = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, b, p.adaptive_c
    )
    return cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)


def apply_conv2d(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    k = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]], dtype=np.float32)
    out = cv2.filter2D(gray, -1, k)
    out = np.clip(out, 0, 255).astype(np.uint8)
    return cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)


def apply_morph_erode(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    k = max(3, p.morph_kernel | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    e = cv2.erode(gray, kernel)
    return cv2.cvtColor(e, cv2.COLOR_GRAY2BGR)


def apply_morph_dilate(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    k = max(3, p.morph_kernel | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    d = cv2.dilate(gray, kernel)
    return cv2.cvtColor(d, cv2.COLOR_GRAY2BGR)


def apply_morph_close(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    k = max(3, p.morph_kernel | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel), cv2.COLOR_GRAY2BGR)


def apply_morph_open(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    k = max(3, p.morph_kernel | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(cv2.morphologyEx(gray, cv2.MORPH_OPEN, kernel), cv2.COLOR_GRAY2BGR)


def apply_morph_gradient(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    k = max(3, p.morph_kernel | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, kernel), cv2.COLOR_GRAY2BGR)


def apply_morph_tophat(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    k = max(9, p.morph_kernel | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel), cv2.COLOR_GRAY2BGR)


def apply_morph_blackhat(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    k = max(9, p.morph_kernel | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k, k))
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(cv2.morphologyEx(gray, cv2.MORPH_BLACKHAT, kernel), cv2.COLOR_GRAY2BGR)


def apply_edge_laplacian(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    lap = cv2.Laplacian(gray, cv2.CV_16S, ksize=3)
    lap = cv2.convertScaleAbs(lap)
    return cv2.cvtColor(lap, cv2.COLOR_GRAY2BGR)


def apply_edge_canny(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    e = cv2.Canny(gray, p.canny_t1, p.canny_t2)
    return cv2.cvtColor(e, cv2.COLOR_GRAY2BGR)


def apply_edge_sobel(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gx = cv2.Sobel(gray, cv2.CV_16S, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_16S, 0, 1, ksize=3)
    mag = cv2.convertScaleAbs(cv2.addWeighted(cv2.convertScaleAbs(gx), 0.5, cv2.convertScaleAbs(gy), 0.5, 0))
    return cv2.cvtColor(mag, cv2.COLOR_GRAY2BGR)


def apply_edge_scharr(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gx = cv2.Scharr(gray, cv2.CV_16S, 1, 0)
    gy = cv2.Scharr(gray, cv2.CV_16S, 0, 1)
    mag = cv2.convertScaleAbs(cv2.addWeighted(cv2.convertScaleAbs(gx), 0.5, cv2.convertScaleAbs(gy), 0.5, 0))
    return cv2.cvtColor(mag, cv2.COLOR_GRAY2BGR)


def apply_contours(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, th = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    out = img.copy()
    cv2.drawContours(out, contours, -1, (0, 255, 0), 2)
    return out


def apply_stitch(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    h, w = img.shape[:2]
    part1 = img[:, : w // 2]
    part2 = img[:, w // 2 :]
    stitcher = cv2.Stitcher_create()
    status, pano = stitcher.stitch([part1, part2])
    if status != cv2.Stitcher_OK:
        return np.hstack([part1, part2])
    return pano


def apply_filter_gray(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)


def apply_filter_vintage(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    t = np.array([[0.272, 0.534, 0.131], [0.349, 0.686, 0.168], [0.393, 0.769, 0.189]])
    x = img.astype(np.float32) @ t.T
    return np.clip(x, 0, 255).astype(np.uint8)


def apply_filter_emboss(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    kernel = np.array([[-2, -1, 0], [-1, 1, 1], [0, 1, 2]], dtype=np.float32)
    out = cv2.filter2D(gray, cv2.CV_32F, kernel)
    out = (out + 128).clip(0, 255).astype(np.uint8)
    return cv2.cvtColor(out, cv2.COLOR_GRAY2BGR)


def apply_filter_blur(img: np.ndarray, p: ImageSettings) -> np.ndarray:
    k = max(3, p.gaussian_ksize | 1)
    return cv2.GaussianBlur(img, (k, k), 0)


def apply_filter_sharpen(img: np.ndarray, _p: ImageSettings) -> np.ndarray:
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], dtype=np.float32)
    return np.clip(cv2.filter2D(img, cv2.CV_32F, kernel), 0, 255).astype(np.uint8)


IMAGE_HANDLERS: dict[str, Any] = {
    "img_original": apply_original,
    "img_rotate": apply_rotate,
    "img_scale": apply_scale,
    "img_flip_h": apply_flip_h,
    "img_flip_v": apply_flip_v,
    "img_add": apply_add,
    "img_sub": apply_sub,
    "img_mul": apply_mul_safe,
    "img_threshold": apply_threshold_binary,
    "img_mask": apply_mask,
    "img_ch_b": apply_channel_split_b,
    "img_ch_g": apply_channel_split_g,
    "img_ch_merge": apply_channel_merge,
    "img_hsv": apply_hsv_mask,
    "img_affine": apply_affine,
    "img_hist_gray": apply_hist_gray,
    "img_hist_color": apply_hist_color,
    "img_hist_eq": apply_hist_equal,
    "img_hist_cmp": apply_hist_compare,
    "img_q_single": apply_quantize_single,
    "img_q_double": apply_quantize_double,
    "img_thresh_zero": apply_threshold_zero,
    "img_adaptive": apply_adaptive,
    "img_conv2d": apply_conv2d,
    "morph_erode": apply_morph_erode,
    "morph_dilate": apply_morph_dilate,
    "morph_close": apply_morph_close,
    "morph_open": apply_morph_open,
    "morph_grad": apply_morph_gradient,
    "morph_tophat": apply_morph_tophat,
    "morph_blackhat": apply_morph_blackhat,
    "edge_laplace": apply_edge_laplacian,
    "edge_canny": apply_edge_canny,
    "edge_sobel": apply_edge_sobel,
    "edge_scharr": apply_edge_scharr,
    "img_contours": apply_contours,
    "img_stitch": apply_stitch,
    "filt_gray": apply_filter_gray,
    "filt_vintage": apply_filter_vintage,
    "filt_emboss": apply_filter_emboss,
    "filt_blur": apply_filter_blur,
    "filt_sharpen": apply_filter_sharpen,
}
