from __future__ import annotations

import sys
from pathlib import Path

# Streamlit 以文件路径启动时，工作目录未必在仓库根；保证可 ``import cv_course``
_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import cv2
import numpy as np
import streamlit as st

from cv_course.algo_descriptions import get_algo_doc_parts, get_doc_title
from cv_course.algorithms.registry import apply_image_algorithm, iter_algorithms
from cv_course.algo_doc_layout import normalize_algo_doc_for_display
from cv_course.md_html import fence_algo_doc_cell
from cv_course.state import ImageSettings
from cv_course.util_cv import bgr_to_rgb, fit_display


def _init_session() -> None:
    if "sl_page" not in st.session_state:
        st.session_state.sl_page = "upload"
    if "sl_bgr" not in st.session_state:
        st.session_state.sl_bgr = None
    if "sl_lang" not in st.session_state:
        st.session_state.sl_lang = "zh"


def _page_label(v: str) -> str:
    lang = st.session_state.get("sl_lang", "zh")
    zh = {"upload": "首页与上传", "image": "图像处理", "video": "视频算法说明"}
    en = {"upload": "Home & upload", "image": "Image processing", "video": "Video (docs only)"}
    return (en if lang == "en" else zh).get(v, v)


def _render_algo_doc(sp_id: str, lang: str) -> None:
    p_raw, fd_raw, ex_raw, u_raw, ext_raw = get_algo_doc_parts(sp_id, lang)
    p_md, f_md, u_md = normalize_algo_doc_for_display(lang, p_raw, fd_raw, ex_raw, u_raw, ext_raw)
    for block in (p_md, f_md):
        if block.strip():
            st.markdown(block)
    if u_md.strip():
        st.markdown(fence_algo_doc_cell(u_md))


def _ordered_image_specs():
    specs = list(iter_algorithms("image"))
    idx = next((i for i, s in enumerate(specs) if s.id == "img_original"), None)
    if idx is not None and idx > 0:
        o = specs[idx]
        specs = [o] + specs[:idx] + specs[idx + 1 :]
    return specs


def _ordered_video_specs():
    specs = list(iter_algorithms("video"))
    idx = next((i for i, s in enumerate(specs) if s.id == "vid_original"), None)
    if idx is not None and idx > 0:
        o = specs[idx]
        specs = [o] + specs[:idx] + specs[idx + 1 :]
    return specs


def _read_image_settings_from_session() -> ImageSettings:
    p = ImageSettings()
    p.rotate_angle = float(st.session_state.get("sl_img_rotate_angle", 15.0))
    p.scale_factor = float(st.session_state.get("sl_img_scale_factor", 1.0))
    p.canny_t1 = int(st.session_state.get("sl_img_canny_t1", 50))
    p.canny_t2 = int(st.session_state.get("sl_img_canny_t2", 150))
    p.binary_thresh = int(st.session_state.get("sl_img_binary_thresh", 127))
    p.morph_kernel = int(st.session_state.get("sl_img_morph_kernel", 5))
    p.gaussian_ksize = int(st.session_state.get("sl_img_gaussian_ksize", 5))
    return p


def _render_video_page(lang: str) -> None:
    if lang == "en":
        st.markdown(
            """
<div style="font-size:1.65rem;line-height:1.7;font-weight:600;background:#eef4fb;padding:1.35rem 1.6rem;
border-radius:12px;border-left:8px solid #2563eb;margin-bottom:1.25rem;">
<strong>Video / camera is not available in this Streamlit page.</strong><br/><br/>
Real-time camera, file video, and per-frame algorithm previews run in the
<strong>desktop Tkinter application</strong> only.<br/><br/>
<span style="font-size:1.45rem;">Open a terminal in the project folder and run:</span><br/>
<code style="font-size:1.35rem;display:inline-block;margin-top:0.6rem;">python -m cv_course</code>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown(
            "Below are the **same teaching notes** as in the Tk flip-cards (from `algo_descriptions.csv`)."
        )
    else:
        st.markdown(
            """
<div style="font-size:1.65rem;line-height:1.75;font-weight:600;background:#eef4fb;padding:1.35rem 1.6rem;
border-radius:12px;border-left:8px solid #2563eb;margin-bottom:1.25rem;">
<strong>本页不提供摄像头或视频画面预览。</strong><br/><br/>
实时摄像头、视频文件、逐帧算法演示请在 <strong>桌面 Tkinter 版</strong> 中使用。<br/><br/>
<span style="font-size:1.45rem;">请在项目目录打开终端，执行：</span><br/>
<code style="font-size:1.35rem;display:inline-block;margin-top:0.6rem;">python -m cv_course</code>
</div>
""",
            unsafe_allow_html=True,
        )
        st.markdown(
            "以下为各**视频类算法**的教学说明（与 Tk 卡牌背面同源，来自 `algo_descriptions.csv`）。"
        )

    st.divider()
    st.subheader("各视频算法文档" if lang == "zh" else "Video algorithm documentation")
    for sp in _ordered_video_specs():
        title = get_doc_title(lang, sp)
        with st.expander(title, expanded=False):
            _render_algo_doc(sp.id, lang)


def run_streamlit() -> None:
    _init_session()
    st.set_page_config(page_title="CV 教学软件 (Streamlit)", layout="wide")
    st.title("CV 库学习软件 — Streamlit 模式")
    st.caption(
        "Streamlit 负责图像实验与视频算法文档；实时视频请在 Tk 版运行 `python -m cv_course`。"
    )

    with st.sidebar:
        st.subheader("导航")
        page_choice = st.radio(
            "当前模块",
            options=["upload", "image", "video"],
            format_func=_page_label,
            index=["upload", "image", "video"].index(st.session_state.sl_page),
        )
        st.session_state.sl_page = page_choice

        lang_ui = st.selectbox(
            "界面与说明语言",
            options=[("zh", "中文"), ("en", "English")],
            format_func=lambda x: x[1],
            index=0 if st.session_state.sl_lang == "zh" else 1,
        )
        st.session_state.sl_lang = lang_ui[0]

        if st.session_state.sl_bgr is not None:
            if st.button("清除已载入的图像"):
                st.session_state.sl_bgr = None
                st.session_state.sl_page = "upload"
                st.rerun()

        if page_choice == "image" and st.session_state.sl_bgr is not None:
            st.subheader("常用参数（与 Tk 版一致）")
            st.slider("旋转角度", -180.0, 180.0, 15.0, key="sl_img_rotate_angle")
            st.slider("缩放系数", 0.1, 3.0, 1.0, key="sl_img_scale_factor")
            st.slider("Canny 低", 0, 255, 50, key="sl_img_canny_t1")
            st.slider("Canny 高", 0, 255, 150, key="sl_img_canny_t2")
            st.slider("二值/掩码阈值", 0, 255, 127, key="sl_img_binary_thresh")
            st.slider("形态学核", 3, 31, 5, step=2, key="sl_img_morph_kernel")
            st.slider("高斯核", 3, 31, 5, step=2, key="sl_img_gaussian_ksize")
            st.slider("缩略图最大边（像素）", 200, 640, 320, step=20, key="sl_img_thumb_max")

    lang = st.session_state.sl_lang

    if st.session_state.sl_page == "upload":
        st.markdown(
            "在此上传图像后，图像会保存在会话中；然后可在侧边栏切换到 **图像处理** 查看各算法（含原图）。"
        )
        up = st.file_uploader("上传图像", type=["jpg", "jpeg", "png", "bmp", "tif"])
        if up:
            data = up.read()
            arr = np.frombuffer(data, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                st.error("无法解码图像")
            else:
                st.session_state.sl_bgr = img
                st.success("图像已载入。请在侧边栏切换到「图像处理」。")
        if st.session_state.sl_bgr is None:
            st.info(
                "尚未载入图像。也可通过命令行运行 `python -m cv_course` 使用完整 Tkinter 界面（含实时视频）。"
            )
        return

    if st.session_state.sl_page == "video":
        _render_video_page(lang)
        return

    img = st.session_state.sl_bgr
    if img is None:
        st.warning("会话中还没有图像。请切换到「首页与上传」上传一张图。")
        if st.button("前往上传"):
            st.session_state.sl_page = "upload"
            st.rerun()
        return

    p = _read_image_settings_from_session()
    thumb = int(st.session_state.get("sl_img_thumb_max", 320))

    st.subheader("各算法输出（含原图，与注册表一致）" if lang == "zh" else "Algorithm outputs (incl. original)")
    specs = _ordered_image_specs()
    cols = st.columns(3)
    for i, sp in enumerate(specs):
        col = cols[i % 3]
        with col:
            title = get_doc_title(lang, sp)
            st.markdown(f"**{title}**")
            try:
                out = apply_image_algorithm(sp.id, img, p)
                rgb = bgr_to_rgb(fit_display(out, thumb))
                st.image(rgb, use_container_width=True)
            except Exception as e:
                st.warning(str(e))
            with st.expander(f"{title} — {'Doc' if lang == 'en' else '教学说明'}"):
                _render_algo_doc(sp.id, lang)


if __name__ == "__main__":
    run_streamlit()
