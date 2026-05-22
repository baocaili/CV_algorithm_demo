from __future__ import annotations

import sys
import time
import tkinter as tk
import tkinter.font as tkfont
from tkinter import colorchooser, filedialog, messagebox, scrolledtext, ttk

import cv2
import numpy as np

from cv_course import __version__
from cv_course.algo_text_en import algo_back_body
from cv_course.algorithms.registry import (
    AlgorithmSpec,
    apply_image_algorithm,
    apply_video_algorithm,
    iter_algorithms,
)
from cv_course.algorithms.video_handlers import VideoEngine
from cv_course.md_html import fence_algo_doc_cell, markdown_to_html_document
from cv_course.md_plain import markdown_to_display_plain
from cv_course.algo_descriptions import get_doc_title
from cv_course.i18n import SUPPORTED_LANGS, mode_display, t
from cv_course.state import AppMode, AppState
from cv_course.ui_tk.algorithm_picker import show_algorithm_picker
from cv_course.util_cv import ensure_bgr, np_to_photoimage


class FlipCard(tk.Frame):
    def __init__(self, master: tk.Widget, spec: AlgorithmSpec, max_side: int, app: "CVCourseApp", on_flip=None):
        super().__init__(
            master,
            highlightthickness=2,
            highlightbackground="#5b7ee8",
            highlightcolor="#9db4ff",
            bd=0,
        )
        self._app = app
        self.spec = spec
        self.max_side = max_side
        self._front = True
        self._photo: tk.PhotoImage | None = None
        self.on_flip = on_flip
        self._last_txt_dim: tuple[int, int] | None = None
        self._txt_layout_after: str | None = None
        self._txt_layout_after2: str | None = None
        self._txt_layout_after3: str | None = None
        self._flip_busy = False
        self._flip_steps = 12
        self._back_doc_built = False
        # 正面布局稳定后的 _body 像素尺寸，用于背面文字区与正面子图同 footprint
        self._cached_body_w = 0
        self._cached_body_h = 0

        self.title_lbl = ttk.Label(self, text=get_doc_title(app.state.language, spec), font=("Segoe UI", 10, "bold"))
        self.title_lbl.pack(anchor="w", padx=4, pady=(2, 0))
        self._flip_hint_lbl = ttk.Label(
            self,
            text=self._tr("flip_rmb_hint"),
            font=("Segoe UI", 7),
            foreground="#6a7588",
        )
        self._flip_hint_lbl.pack(anchor="w", padx=4, pady=(0, 1))

        self._body = tk.Frame(self, bg="#eef1f6")
        self._body.pack(fill=tk.BOTH, expand=True)
        self._front_host = tk.Frame(self._body, bg="#eef1f6")
        self._front_host.pack(fill=tk.BOTH, expand=True)

        self.img_lbl = ttk.Label(self._front_host)
        self._back_html_shell: tk.Frame | None = None
        self._back_pack_master: tk.Widget
        self._create_back_view()
        self.img_lbl.pack(fill=tk.BOTH, expand=True)
        flip_targets: list[tk.Misc] = [self, self.title_lbl, self._flip_hint_lbl, self.img_lbl]
        if isinstance(self._back, scrolledtext.ScrolledText):
            flip_targets.extend([self._back_pack_master, self._back.vbar])
        for w in flip_targets:
            w.bind("<Button-3>", self._toggle)
        self._bind_back_mousewheel()

    def _create_back_view(self) -> None:
        """优先使用 TkinterWeb 渲染 Markdown；失败则退回 ``ScrolledText`` 纯文本。Html 放在固定尺寸壳 ``Frame`` 内，避免撑大子图区域。"""
        try:
            import markdown  # noqa: F401
            from tkinterweb import HtmlFrame

            shell = tk.Frame(self._body, bg="#eef1f6")
            f = HtmlFrame(
                shell,
                messages_enabled=False,
                vertical_scrollbar="auto",
                horizontal_scrollbar=False,
            )
            f.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._back_html_shell = shell
            self._back_kind = "html"
            self._back = f
            self._back_pack_master = shell
        except Exception:
            self._back_html_shell = None
            self._back_kind = "text"
            self._back = scrolledtext.ScrolledText(self._body, wrap=tk.WORD, font=("Consolas", 9), width=28, height=18)
            self._back_pack_master = self._back

    def _install_html_interactions(self) -> None:
        """HtmlFrame 内点击落在子控件上，事件不会冒泡到外壳；滚轮也需绑定到子树。``HtmlFrame.yview_scroll`` 驱动垂直滚动。"""
        if self._back_kind != "html":
            return

        def on_flip(_e: tk.Event | None = None) -> None:
            self._toggle(_e)

        def on_wheel(event: tk.Event) -> str | None:
            try:
                hf = self._back
                if getattr(event, "delta", 0):
                    hf.yview_scroll(int(-1 * (event.delta / 120)), "units")
                elif getattr(event, "num", None) == 4:
                    hf.yview_scroll(-3, "units")
                elif getattr(event, "num", None) == 5:
                    hf.yview_scroll(3, "units")
            except (tk.TclError, AttributeError):
                pass
            return None

        def walk(w: tk.Misc, depth: int = 0) -> None:
            if depth > 24:
                return
            w.bind("<Button-3>", on_flip)
            w.bind("<MouseWheel>", on_wheel)
            w.bind("<Button-4>", on_wheel)
            w.bind("<Button-5>", on_wheel)
            try:
                kids = w.winfo_children()
            except tk.TclError:
                return
            for c in kids:
                walk(c, depth + 1)

        try:
            root = self._back_html_shell if self._back_html_shell is not None else self._back
            walk(root)
        except tk.TclError:
            pass

    def _bind_back_mousewheel(self) -> None:
        if self._back_kind != "text":
            def _focus_back(_e=None) -> None:
                try:
                    self._back.focus_set()
                except tk.TclError:
                    pass

            self._back.bind("<Enter>", lambda _e: _focus_back())
            if self._back_html_shell is not None:
                self._back_html_shell.bind("<Enter>", lambda _e: _focus_back())
            return

        txt = self._back
        assert isinstance(txt, scrolledtext.ScrolledText)

        def on_wheel(event: tk.Event) -> str | None:
            try:
                if getattr(event, "delta", 0):
                    txt.yview_scroll(int(-1 * (event.delta / 120)), "units")
                elif getattr(event, "num", None) == 4:
                    txt.yview_scroll(-3, "units")
                elif getattr(event, "num", None) == 5:
                    txt.yview_scroll(3, "units")
            except tk.TclError:
                pass
            return None

        for w in (txt, txt.vbar):
            w.bind("<MouseWheel>", on_wheel, add="+")
            w.bind("<Button-4>", on_wheel, add="+")
            w.bind("<Button-5>", on_wheel, add="+")

        def _focus_back(_e=None) -> None:
            try:
                txt.focus_set()
            except tk.TclError:
                pass

        txt.bind("<Enter>", lambda _e: _focus_back())

    def _tr(self, key: str, **kwargs: object) -> str:
        return t(self._app.state.language, key, **kwargs)

    def _cancel_txt_layout_callbacks(self) -> None:
        for aid in (self._txt_layout_after, self._txt_layout_after2, self._txt_layout_after3):
            if aid is not None:
                try:
                    self.after_cancel(aid)
                except tk.TclError:
                    pass
        self._txt_layout_after = self._txt_layout_after2 = self._txt_layout_after3 = None

    def _cache_front_body_geometry(self) -> None:
        if not self._front:
            return
        try:
            self.update_idletasks()
        except tk.TclError:
            return
        w = max(self._body.winfo_width(), self._body.winfo_reqwidth(), 1)
        h = max(self._body.winfo_height(), self._body.winfo_reqheight(), 1)
        if w >= 20 and h >= 20:
            self._cached_body_w = int(w)
            self._cached_body_h = int(h)

    def _sync_back_layout(self) -> None:
        if self._front:
            return
        try:
            self.update_idletasks()
        except tk.TclError:
            pass
        cw, ch = self._cached_body_w, self._cached_body_h
        bw = max(self._body.winfo_width(), 1)
        bh = max(self._body.winfo_height(), 1)
        if cw >= 20 and ch >= 20:
            wpx, hpx = cw, ch
        else:
            wpx = max(bw, 80)
            hpx = max(bh, 60)
        if isinstance(self._back, scrolledtext.ScrolledText):
            txt = self._back
            fn = tkfont.Font(font=txt.cget("font"))
            char_px = max(fn.measure("0"), fn.measure("W"), 1)
            line_px = max(fn.metrics("linespace"), 1)
            chars = max(12, min(96, wpx // char_px))
            lines = max(10, min(56, hpx // line_px))
            old = self._last_txt_dim
            if old is not None and chars >= 20 and lines >= 12:
                oc, ol = old
                if abs(chars - oc) < 2 and abs(lines - ol) < 2:
                    return
            self._last_txt_dim = (chars, lines)
            txt.configure(width=chars, height=lines)
        elif self._back_html_shell is not None:
            self._back_html_shell.configure(width=wpx, height=hpx)
            self._back_html_shell.pack_propagate(False)

    def _schedule_back_txt_layout(self) -> None:
        self._cancel_txt_layout_callbacks()
        self._txt_layout_after = self.after_idle(self._sync_back_layout)
        self._txt_layout_after2 = self.after(100, self._sync_back_layout)
        self._txt_layout_after3 = self.after(260, self._sync_back_layout)

    def _ensure_back_doc(self) -> None:
        """背面说明（Markdown→HTML）较重，延迟到首次翻面再构建，避免打开摄像头时主线程长时间卡住。"""
        if self._back_doc_built:
            return
        self._build_back_text()

    def _build_back_text(self) -> None:
        s = self.spec
        p, fd, _ex, usage, _ext = algo_back_body(self._app.state.language, s)
        usage = fence_algo_doc_cell(usage)
        chunks = [x for x in (p.strip(), fd.strip(), usage.strip()) if x]
        body = "\n\n".join(chunks) + "\n"
        back = self._back
        if isinstance(back, scrolledtext.ScrolledText):
            back.delete("1.0", tk.END)
            back.insert(tk.END, markdown_to_display_plain(body))
        else:
            back.load_html(markdown_to_html_document(body))
            self.after_idle(self._install_html_interactions)
        self._back_doc_built = True

    def _finish_flip_to_back(self) -> None:
        self._front_host.place_forget()
        self._front = False
        self._back_pack_master.pack(fill=tk.BOTH, expand=True)
        self._last_txt_dim = None
        self._schedule_back_txt_layout()
        if self._back_kind == "html":
            self.after_idle(self._install_html_interactions)
        self._flip_busy = False
        if self.on_flip:
            self.on_flip()

    def _step_shrink_front(self, step: int) -> None:
        n = self._flip_steps
        if step == 0:
            self._cancel_txt_layout_callbacks()
            try:
                self.update_idletasks()
            except tk.TclError:
                pass
            w = max(self._body.winfo_width(), self._body.winfo_reqwidth(), 1)
            h = max(self._body.winfo_height(), self._body.winfo_reqheight(), 1)
            if w >= 20 and h >= 20:
                self._cached_body_w = int(w)
                self._cached_body_h = int(h)
            self._front_host.pack_forget()
        rw = max(0.04, 1.0 - (step + 1) / n)
        self._front_host.place(relx=0, rely=0, relwidth=rw, relheight=1.0)
        if step + 1 < n:
            self.after(22, lambda: self._step_shrink_front(step + 1))
        else:
            self._finish_flip_to_back()

    def _finish_flip_to_front(self) -> None:
        self._front_host.place_forget()
        self._front_host.pack(fill=tk.BOTH, expand=True)
        self.img_lbl.pack(fill=tk.BOTH, expand=True)
        self._flip_busy = False
        self.after_idle(self._cache_front_body_geometry)
        if self.on_flip:
            self.on_flip()

    def _step_grow_front(self, step: int) -> None:
        n = self._flip_steps
        if step == 0:
            self._back_pack_master.pack_forget()
            self._cancel_txt_layout_callbacks()
            self._front = True
            if self._front_host.winfo_manager() == "pack":
                self._front_host.pack_forget()
            self._front_host.place(relx=0, rely=0, relwidth=0.06, relheight=1.0)
        rw = min(1.0, (step + 1) / n)
        self._front_host.place_configure(relwidth=max(0.06, rw))
        if step + 1 < n:
            self.after(22, lambda: self._step_grow_front(step + 1))
        else:
            self._finish_flip_to_front()

    def _toggle(self, _e=None) -> None:
        if self._flip_busy:
            return
        self._flip_busy = True
        if self._front:
            self._ensure_back_doc()
            self._step_shrink_front(0)
        else:
            self._step_grow_front(0)

    def set_max_side(self, m: int) -> None:
        self.max_side = m
        if not self._front:
            self._last_txt_dim = None
            self._schedule_back_txt_layout()

    def apply_language(self) -> None:
        self.title_lbl.configure(text=get_doc_title(self._app.state.language, self.spec))
        self._flip_hint_lbl.configure(text=self._tr("flip_rmb_hint"))
        self._build_back_text()
        if not self._front:
            self._last_txt_dim = None
            self._schedule_back_txt_layout()

    def set_image(self, img_bgr: np.ndarray | None) -> None:
        if not self._front:
            return
        if img_bgr is None or img_bgr.size == 0:
            self.img_lbl.configure(image="", text=self._tr("flip_no_image"))
            self._photo = None
            self.after_idle(self._cache_front_body_geometry)
            return
        img_bgr = ensure_bgr(img_bgr)
        self._photo = np_to_photoimage(img_bgr, self.max_side)
        self.img_lbl.configure(image=self._photo, text="")
        self.after_idle(self._cache_front_body_geometry)


class CVCourseApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.state = AppState()
        self.title(self.t("app_title"))
        self.geometry("1200x780")
        self._bgr: np.ndarray | None = None
        self._draw_canvas: tk.Canvas | None = None
        self._cap: cv2.VideoCapture | None = None
        self._video_engine = VideoEngine()
        self._cards: dict[str, FlipCard] = {}
        self._after_id: str | None = None
        self._active_specs: list[AlgorithmSpec] = []
        self._log_buffer: list[tuple[str, str, str]] = []
        self._log_filter_level: str = "ALL"
        self._log_filter_display_to_level: dict[str, str] = {}
        self._rec_writer: cv2.VideoWriter | None = None
        self._rec_path: str | None = None
        self._rec_fourcc: str = "mp4v"
        self._rec_pending: bool = False
        self._canvas_sync_after: str | None = None
        self._last_canvas_inner_w: int = 0
        self._scroll_inner_width_cap: int = 640
        self._lang_var = tk.StringVar(value=self.state.language)
        self._toolbar_btn_keys: list[tuple[ttk.Button, str]] = []
        self._video_transport: ttk.Frame | None = None
        self._video_play_btn: ttk.Button | None = None
        self._video_scale: tk.Scale | None = None
        self._video_time_lbl: ttk.Label | None = None
        self._video_pos_var = tk.IntVar(value=0)
        self._video_playing = True
        self._video_total_frames = 0
        self._video_has_seek = False
        self._video_last_frame: np.ndarray | None = None
        self._video_suppress_scale_cb = False
        self._video_scale_dragging = False
        self._build_ui()
        self.bind_all("<MouseWheel>", self._on_main_area_mousewheel, add="+")
        self.bind_all("<Button-4>", self._on_main_area_mousewheel, add="+")
        self.bind_all("<Button-5>", self._on_main_area_mousewheel, add="+")
        self._tick_clock()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def t(self, key: str, **kwargs: object) -> str:
        return t(self.state.language, key, **kwargs)

    def _on_lang_selected(self) -> None:
        self.state.language = self._lang_var.get()
        if self.state.language not in SUPPORTED_LANGS:
            self.state.language = "en"
            self._lang_var.set("en")
        self._apply_language()

    def _apply_language(self) -> None:
        from cv_course.algo_descriptions import reload_algo_description_csv

        reload_algo_description_csv()
        self._lang_var.set(self.state.language)
        self.title(self.t("app_title"))
        ph_font = ("Microsoft YaHei UI", 14) if self.state.language == "zh" else ("Segoe UI", 14)
        self._placeholder.configure(text=self.t("placeholder"), font=ph_font)
        self._log_title_lbl.configure(text=self.t("log_title"))
        self._log_filter_lbl.configure(text=self.t("log_filter"))
        self._configure_log_filter_combo()
        self._build_menubar()
        for btn, key in self._toolbar_btn_keys:
            btn.configure(text=self.t(key))
        for c in self._cards.values():
            c.apply_language()
        if self._video_play_btn is not None:
            self._video_refresh_play_button()
        if self._video_time_lbl is not None and self._cap is not None:
            try:
                self._video_refresh_time_label(int(self._video_pos_var.get()))
            except (tk.TclError, ValueError):
                pass
        self._render_log()

    def _configure_log_filter_combo(self) -> None:
        pairs = [
            (self.t("log_filter_all"), "ALL"),
            (self.t("log_filter_info"), "INFO"),
            (self.t("log_filter_debug"), "DEBUG"),
            (self.t("log_filter_warning"), "WARNING"),
            (self.t("log_filter_error"), "ERROR"),
        ]
        self._log_filter_display_to_level = {d: lv for d, lv in pairs}
        displays = [p[0] for p in pairs]
        self._log_filter_combo.configure(values=displays)
        cur = self._log_filter_level
        rev = {lv: d for d, lv in pairs}
        pick = rev.get(cur, displays[0])
        self._log_filter_combo.set(pick)
        self._log_filter_level = self._log_filter_display_to_level.get(pick, "ALL")

    def _on_log_filter_selected(self, _event=None) -> None:
        disp = self._log_filter_combo.get()
        self._log_filter_level = self._log_filter_display_to_level.get(disp, "ALL")
        self._render_log()

    def _build_menubar(self) -> None:
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        m_op = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.t("menu_operation"), menu=m_op)
        m_op.add_command(label=self.t("op_open_image"), command=self._open_image)
        m_op.add_command(label=self.t("op_open_video"), command=self._open_video)
        m_op.add_command(label=self.t("op_camera"), command=self._open_camera)
        m_op.add_command(label=self.t("op_draw"), command=self._mode_draw)
        m_op.add_separator()
        m_op.add_command(label=self.t("op_rec_start"), command=self._start_recording_dialog)
        m_op.add_command(label=self.t("op_rec_stop"), command=self._stop_recording)
        m_op.add_separator()
        m_op.add_command(label=self.t("op_save"), command=self._save_file)
        m_op.add_separator()
        m_op.add_command(label=self.t("op_exit"), command=self._on_close)

        m_set = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.t("menu_settings"), menu=m_set)
        m_set.add_command(label=self.t("set_image"), command=self._dlg_image_settings)
        m_set.add_command(label=self.t("set_video"), command=self._dlg_video_settings)
        m_set.add_command(label=self.t("set_layout"), command=self._dlg_layout_settings)
        m_set.add_separator()
        m_set.add_command(label=self.t("set_pick_image"), command=self._dlg_pick_image_algos)
        m_set.add_command(label=self.t("set_pick_video"), command=self._dlg_pick_video_algos)
        m_set.add_separator()
        m_lang = tk.Menu(m_set, tearoff=0)
        m_set.add_cascade(label=self.t("menu_language"), menu=m_lang)
        for code in SUPPORTED_LANGS:
            lab = self.t("lang_en" if code == "en" else "lang_zh")
            m_lang.add_radiobutton(label=lab, variable=self._lang_var, value=code, command=self._on_lang_selected)

        m_about = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.t("menu_about"), menu=m_about)
        m_about.add_command(label=self.t("about_contact"), command=self._dlg_contact)
        m_about.add_command(
            label=self.t("about_version"),
            command=lambda: messagebox.showinfo(self.t("about_version"), __version__, parent=self),
        )

    def _dlg_contact(self) -> None:
        messagebox.showinfo(self.t("contact_title"), self.t("contact_body"), parent=self)

    def _build_ui(self) -> None:
        self._build_menubar()

        tb = ttk.Frame(self)
        tb.pack(side="top", fill="x", padx=4, pady=2)
        self._tb = tb
        self._toolbar_btn_keys.clear()
        from cv_course.ui_tk.toolbar_icons import build_toolbar_icons

        icons = build_toolbar_icons(self)
        self._toolbar_icon_refs = list(icons.values())
        for key, cmd, iname in [
            ("tb_open_image", self._open_image, "open_image"),
            ("tb_open_video", self._open_video, "open_video"),
            ("tb_camera", self._open_camera, "camera"),
            ("tb_draw", self._mode_draw, "draw"),
            ("tb_save", self._save_file, "save"),
            ("tb_rec_start", self._start_recording_dialog, "rec_start"),
            ("tb_rec_stop", self._stop_recording, "rec_stop"),
        ]:
            b = ttk.Button(tb, image=icons[iname], text=self.t(key), compound=tk.LEFT, command=cmd)
            b.pack(side="left", padx=2)
            self._toolbar_btn_keys.append((b, key))

        main = ttk.Panedwindow(self, orient=tk.HORIZONTAL)
        main.pack(fill="both", expand=True, padx=4, pady=4)
        self._main_pw = main

        left = ttk.Frame(main)
        main.add(left, weight=8)

        self._log_outer = ttk.Frame(main)
        main.add(self._log_outer, weight=2)

        op_outer = ttk.Frame(left)
        op_outer.pack(fill="both", expand=True)
        self._op_outer = op_outer
        ph_font = ("Microsoft YaHei UI", 14) if self.state.language == "zh" else ("Segoe UI", 14)
        self._placeholder = ttk.Label(
            op_outer,
            text=self.t("placeholder"),
            font=ph_font,
            anchor="center",
        )
        self._placeholder.pack(expand=True)

        # 画布与滚动条放在独立 Frame 内用 grid 排布，避免 pack 顺序导致水平条与画布宽度不一致、难以拖动。
        self._canvas_scroll_outer = ttk.Frame(op_outer)
        self._canvas = tk.Canvas(self._canvas_scroll_outer, highlightthickness=0)
        self._scroll_y = ttk.Scrollbar(self._canvas_scroll_outer, orient="vertical", command=self._canvas.yview)
        self._scroll_x = ttk.Scrollbar(self._canvas_scroll_outer, orient="horizontal", command=self._canvas.xview)
        self._canvas.configure(yscrollcommand=self._scroll_y.set, xscrollcommand=self._scroll_x.set)
        self._card_host = ttk.Frame(self._canvas)
        self._canvas_win = self._canvas.create_window((0, 0), window=self._card_host, anchor="nw")
        self._card_host.bind("<Configure>", lambda _e: self._schedule_canvas_scroll_sync())
        self._canvas.bind("<Configure>", lambda _e: self._schedule_canvas_scroll_sync())
        self._canvas_scroll_outer.grid_columnconfigure(0, weight=1)
        self._canvas_scroll_outer.grid_rowconfigure(0, weight=1)
        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._scroll_y.grid(row=0, column=1, sticky="ns")
        self._scroll_x.grid(row=1, column=0, sticky="ew")

        self._log_title_lbl = ttk.Label(self._log_outer, text=self.t("log_title"), font=("Segoe UI", 10, "bold"))
        self._log_title_lbl.pack(anchor="w")
        fl = ttk.Frame(self._log_outer)
        fl.pack(fill="x")
        self._log_filter_lbl = ttk.Label(fl, text=self.t("log_filter"))
        self._log_filter_lbl.pack(side="left", padx=(0, 4))
        self._log_filter_combo = ttk.Combobox(fl, width=14, state="readonly")
        self._log_filter_combo.pack(side="left")
        self._configure_log_filter_combo()
        self._log_filter_combo.bind("<<ComboboxSelected>>", self._on_log_filter_selected)

        self.log_text = scrolledtext.ScrolledText(self._log_outer, height=24, wrap="word", font=("Consolas", 9))
        self.log_text.pack(fill="both", expand=True, pady=4)
        for tag, color in [("INFO", "#333"), ("DEBUG", "#666"), ("WARNING", "#a60"), ("ERROR", "#c00")]:
            self.log_text.tag_configure(tag, foreground=color)

        self.status = ttk.Label(self, relief=tk.SUNKEN, anchor="w")
        self.status.pack(side="bottom", fill="x")
        self.after_idle(self._set_main_pane_ratio)

    def _set_main_pane_ratio(self, _attempt: int = 0) -> None:
        """Split main vs log pane; retry until Panedwindow has a real width (idle early winfo_width≈1)."""
        try:
            panes = self._main_pw.panes()
            if len(panes) < 2:
                return
            w = max(self._main_pw.winfo_width(), 1)
            if w < 200 and _attempt < 15:
                self.after(50, lambda a=_attempt + 1: self._set_main_pane_ratio(a))
                return
            if w < 200:
                return
            # Leave at least ~220px for log; main area uses canvas width (not whole window).
            pos = max(420, min(int(w * 0.72), w - 220))
            self._main_pw.sashpos(0, pos)
        except tk.TclError:
            pass

    def _schedule_canvas_scroll_sync(self) -> None:
        """防抖：子图每帧改图会触发大量 Configure，避免与 itemconfig 形成嵌套布局死循环。"""
        if self._canvas_sync_after is not None:
            self.after_cancel(self._canvas_sync_after)
        self._canvas_sync_after = self.after_idle(self._do_canvas_scroll_sync)

    def _do_canvas_scroll_sync(self) -> None:
        self._canvas_sync_after = None
        try:
            cw = max(self._canvas.winfo_width(), 1)
            rw = max(self._card_host.winfo_reqwidth(), 1)
            layout_floor = max(1, self._scroll_inner_width_cap)
            # 内容宽度：实测 reqwidth 与布局预估取大。不再用 min(..., max(floor,cw+1))，否则 floor 偏小时 cap 退化成 cw+1，水平滚动条失效。
            content_w = max(rw, layout_floor)
            inner_max = 16384
            inner_w = min(inner_max, max(cw, content_w))
            if inner_w != self._last_canvas_inner_w:
                self._last_canvas_inner_w = inner_w
                self._canvas.itemconfig(self._canvas_win, width=inner_w)
            bbox = self._canvas.bbox("all")
            if bbox:
                self._canvas.configure(scrollregion=bbox)
        except tk.TclError:
            pass

    def _wheel_widget_in_image_grid_scroll_area(self, w: tk.Misc | None) -> bool:
        """滚轮是否发生在子图画布、其内层或垂直滚动条上。"""
        roots: tuple[tk.Misc, ...]
        try:
            roots = (self._canvas, self._scroll_y, self._canvas_scroll_outer, self._card_host)
        except AttributeError:
            return False
        cur: tk.Misc | None = w
        while cur is not None:
            if cur in roots:
                return True
            try:
                cur = cur.master  # type: ignore[assignment]
            except (tk.TclError, AttributeError):
                break
        return False

    def _on_main_area_mousewheel(self, event: tk.Event) -> None:
        """多子图时滚轮驱动画布垂直滚动；卡牌翻到背面时交给卡片自身滚动，避免抢事件。"""
        if self.state.mode == AppMode.NONE:
            return
        try:
            c = self._canvas
            if not c.winfo_ismapped():
                return
        except (tk.TclError, AttributeError):
            return
        w = event.widget
        if not self._wheel_widget_in_image_grid_scroll_area(w):
            return
        cur: tk.Misc | None = w
        while cur is not None:
            if isinstance(cur, FlipCard) and not cur._front:
                return
            try:
                cur = cur.master  # type: ignore[assignment]
            except (tk.TclError, AttributeError):
                break
        step = 0
        if getattr(event, "delta", 0):
            step = int(-1 * (event.delta / 120))
        elif getattr(event, "num", None) == 4:
            step = -3
        elif getattr(event, "num", None) == 5:
            step = 3
        if step:
            try:
                self._canvas.yview_scroll(step, "units")
            except tk.TclError:
                pass

    def _render_log(self) -> None:
        self.log_text.delete("1.0", tk.END)
        filt = self._log_filter_level
        for ts, level, msg in self._log_buffer:
            if filt != "ALL" and level != filt:
                continue
            line = f"[{ts}] [{level}] {msg}\n"
            self.log_text.insert(tk.END, line, (level,))
        self.log_text.see(tk.END)

    def _log(self, level: str, msg: str) -> None:
        ts = time.strftime("%H:%M:%S")
        self._log_buffer.append((ts, level, msg))
        self._render_log()

    def _refresh_status_line(self) -> None:
        tstr = time.strftime("%Y-%m-%d %H:%M:%S")
        dirty = f" | {self.t('status_dirty')}" if self.state.dirty else ""
        mode = mode_display(self.state.language, self.state.mode) if self.state.mode != AppMode.NONE else self.t("status_none")
        try:
            self.status.configure(text=f"{self.t('status_op')}: {mode}  |  {tstr}{dirty}")
        except tk.TclError:
            pass

    def _tick_clock(self) -> None:
        self._refresh_status_line()
        self.after(1000, self._tick_clock)

    def _clear_mode(self) -> None:
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None
        if self._rec_writer is not None:
            try:
                self._rec_writer.release()
            except Exception:
                pass
            self._rec_writer = None
            self._rec_pending = False
            self._log("INFO", self.t("log_rec_closed"))
        if self._canvas_sync_after is not None:
            try:
                self.after_cancel(self._canvas_sync_after)
            except tk.TclError:
                pass
            self._canvas_sync_after = None
        self._hide_video_transport_line()
        self._video_playing = True
        self._video_last_frame = None
        self._video_scale_dragging = False
        self._video_total_frames = 0
        self._video_has_seek = False
        if self._cap:
            self._cap.release()
            self._cap = None
        self._bgr = None
        self._video_engine.reset()
        for w in self._card_host.winfo_children():
            w.destroy()
        self._cards.clear()
        self._active_specs = []
        self._last_canvas_inner_w = 0
        self._scroll_inner_width_cap = 640
        self._draw_canvas = None
        try:
            self._canvas_scroll_outer.pack_forget()
        except tk.TclError:
            pass
        self._placeholder.pack_forget()
        self._placeholder.pack(expand=True)

    def _switch_mode(self, mode: AppMode) -> None:
        self._clear_mode()
        self.state.mode = mode
        self.state.dirty = False
        self._log("INFO", self.t("log_mode", mode=mode_display(self.state.language, mode)))

    def _show_card_grid(self, with_video_transport: bool = False) -> None:
        self._placeholder.pack_forget()
        self._hide_video_transport_line()
        if with_video_transport:
            self._ensure_video_transport_widgets()
            self._video_transport.pack(side=tk.TOP, fill=tk.X, padx=4, pady=(0, 4))
        self._canvas_scroll_outer.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.after_idle(self._set_main_pane_ratio)

    def _filtered_image_specs(self) -> list[AlgorithmSpec]:
        ids = [s.id for s in iter_algorithms("image")]
        en = self.state.image_settings.enabled_algorithm_ids
        if en:
            ids = [i for i in ids if i in en]
        return [s for s in iter_algorithms("image") if s.id in ids]

    def _filtered_video_specs(self) -> list[AlgorithmSpec]:
        ids = [s.id for s in iter_algorithms("video")]
        en = self.state.video_settings.enabled_algorithm_ids
        if en:
            ids = [i for i in ids if i in en]
        return [s for s in iter_algorithms("video") if s.id in ids]

    def _dlg_pick_image_algos(self) -> None:
        r = show_algorithm_picker(self, "image", self.state.image_settings.enabled_algorithm_ids, self.state.language)
        if r.cancelled:
            return
        self.state.image_settings.enabled_algorithm_ids = r.enabled_ids
        self._log("INFO", self.t("log_pick_image"))
        if self.state.mode == AppMode.IMAGE and self._bgr is not None:
            self._layout_cards(self._filtered_image_specs())
            self._refresh_image_cards()

    def _dlg_pick_video_algos(self) -> None:
        r = show_algorithm_picker(self, "video", self.state.video_settings.enabled_algorithm_ids, self.state.language)
        if r.cancelled:
            return
        self.state.video_settings.enabled_algorithm_ids = r.enabled_ids
        self._log("INFO", self.t("log_pick_video"))
        if self.state.mode in (AppMode.VIDEO, AppMode.CAMERA) and self._cap is not None:
            self._layout_cards(self._filtered_video_specs())

    def _start_recording_dialog(self) -> None:
        if self.state.mode not in (AppMode.VIDEO, AppMode.CAMERA) or self._cap is None:
            messagebox.showinfo(self.t("dlg_info"), self.t("rec_need_video"), parent=self)
            return
        if self._rec_writer is not None or self._rec_pending:
            messagebox.showinfo(self.t("dlg_info"), self.t("rec_busy"), parent=self)
            return
        path = filedialog.asksaveasfilename(
            title=self.t("rec_title_save"),
            defaultextension=".mp4",
            filetypes=[
                ("MP4", "*.mp4"),
                ("AVI", "*.avi"),
                (self.t("file_all"), "*.*"),
            ],
        )
        if not path:
            return
        dlg = tk.Toplevel(self)
        dlg.title(self.t("rec_dlg_title"))
        dlg.transient(self)
        fc_var = tk.StringVar(value=self._rec_fourcc or "mp4v")
        ttk.Label(dlg, text=self.t("rec_fourcc_hint")).grid(row=0, column=0, columnspan=2, padx=8, pady=6, sticky="w")
        ttk.Entry(dlg, textvariable=fc_var, width=10).grid(row=1, column=0, padx=8, pady=4, sticky="w")
        ttk.Label(dlg, text=self.t("rec_suffix_hint")).grid(row=1, column=1, padx=4, pady=4, sticky="w")

        def go():
            raw = fc_var.get().strip()
            if len(raw) < 4:
                raw = (raw + "mp4v")[:4]
            self._rec_fourcc = raw[:4]
            self._rec_path = path
            self._rec_pending = True
            self._log("INFO", self.t("log_rec_next_frame", path=path, fc=self._rec_fourcc))
            dlg.destroy()

        def cancel_dlg():
            dlg.destroy()

        dlg.protocol("WM_DELETE_WINDOW", cancel_dlg)
        bf = ttk.Frame(dlg)
        bf.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(bf, text=self.t("btn_cancel"), command=cancel_dlg).pack(side="right", padx=6)
        ttk.Button(bf, text=self.t("btn_start"), command=go).pack(side="right", padx=6)
        dlg.grab_set()
        self.wait_window(dlg)

    def _stop_recording(self) -> None:
        self._rec_pending = False
        if self._rec_writer is not None:
            try:
                self._rec_writer.release()
            except Exception:
                pass
            p = self._rec_path
            self._rec_writer = None
            self._rec_path = None
            self._log("INFO", self.t("log_rec_stopped", path=p or ""))
        else:
            self._log("INFO", self.t("log_rec_idle"))

    def _layout_cards(self, specs: list[AlgorithmSpec]) -> None:
        for w in self._card_host.winfo_children():
            w.destroy()
        self._cards.clear()
        self._active_specs = list(specs)
        lay = self.state.layout
        cols = max(1, lay.per_line)
        for i, sp in enumerate(specs):
            r, c = (i // cols, i % cols) if lay.row_major else (i % cols, i // cols)
            card = FlipCard(self._card_host, sp, lay.card_max_side, self)
            card.grid(row=r, column=c, padx=6, pady=6, sticky="n")
            self._cards[sp.id] = card
        n = len(specs)
        # 水平滚动条依据「列数」估算宽度：行优先时列数=min(每行列数, 卡片数)；列优先时列数=ceil(n/每行列数)。
        if lay.row_major:
            n_columns = min(cols, n) if n else 1
        else:
            n_columns = (n + cols - 1) // cols if n else 1
        cell = lay.card_max_side + 100
        self._scroll_inner_width_cap = max(640, n_columns * cell + 80)
        self._last_canvas_inner_w = 0
        self._card_host.update_idletasks()
        self._do_canvas_scroll_sync()

    def _open_image(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[
                (self.t("file_images"), "*.jpg *.jpeg *.png *.bmp *.tif"),
                (self.t("file_all"), "*.*"),
            ],
        )
        if not path:
            return
        self._switch_mode(AppMode.IMAGE)
        im = cv2.imread(path)
        if im is None:
            messagebox.showerror(self.t("dlg_error"), self.t("err_read_image"), parent=self)
            self._switch_mode(AppMode.NONE)
            return
        self.state.current_path = path
        self._bgr = im
        self._show_card_grid()
        self._layout_cards(self._filtered_image_specs())
        self._refresh_image_cards()
        self._log("INFO", self.t("log_open_image", path=path))

    def _refresh_image_cards(self) -> None:
        if self._bgr is None:
            return
        p = self.state.image_settings
        for sp in iter_algorithms("image"):
            c = self._cards.get(sp.id)
            if not c:
                continue
            try:
                out = apply_image_algorithm(sp.id, self._bgr, p)
                c.set_image(out)
            except Exception as e:
                self._log("ERROR", self.t("log_img_algo_err", aid=sp.id, err=str(e)))
                c.set_image(self._bgr)

    def _open_camera_capture(self, index: int = 0) -> cv2.VideoCapture:
        """Windows 上 CAP_DSHOW 通常比默认 MSMF 更快出首帧；缩小缓冲与分辨率降低首帧处理耗时。"""
        if sys.platform == "win32":
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                try:
                    cap.release()
                except Exception:
                    pass
                cap = cv2.VideoCapture(index)
        else:
            cap = cv2.VideoCapture(index)
        if cap.isOpened():
            try:
                cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            except Exception:
                pass
            try:
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            except Exception:
                pass
            for _ in range(2):
                cap.grab()
        return cap

    def _open_video(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[
                (self.t("file_video"), "*.mp4 *.avi *.mkv *.mov"),
                (self.t("file_all"), "*.*"),
            ],
        )
        if not path:
            return
        self._switch_mode(AppMode.VIDEO)
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            messagebox.showerror(self.t("dlg_error"), self.t("err_open_video"), parent=self)
            self._switch_mode(AppMode.NONE)
            return
        self._cap = cap
        self.state.current_path = path
        self._video_engine = VideoEngine()
        self._show_card_grid(with_video_transport=True)
        self._layout_cards(self._filtered_video_specs())
        self._log("INFO", self.t("log_open_video", path=path))
        self._video_update_transport_after_open()
        self._after_id = self.after(1, self._video_loop)

    def _open_camera(self) -> None:
        self._switch_mode(AppMode.CAMERA)
        cap = self._open_camera_capture(0)
        if not cap.isOpened():
            messagebox.showerror(self.t("dlg_error"), self.t("err_camera"), parent=self)
            self._switch_mode(AppMode.NONE)
            return
        self._cap = cap
        self.state.current_path = None
        self._video_engine = VideoEngine()
        self._show_card_grid(with_video_transport=True)
        self._layout_cards(self._filtered_video_specs())
        self._log("INFO", self.t("log_camera"))
        self._video_update_transport_after_open()
        self._after_id = self.after(1, self._video_loop)

    def _hide_video_transport_line(self) -> None:
        if self._video_transport is not None:
            try:
                self._video_transport.pack_forget()
            except tk.TclError:
                pass

    def _ensure_video_transport_widgets(self) -> None:
        if self._video_transport is not None:
            return
        bar = ttk.Frame(self._op_outer)
        self._video_transport = bar
        self._video_play_btn = ttk.Button(bar, text="", command=self._video_on_play_pause, width=12)
        self._video_play_btn.pack(side=tk.LEFT, padx=(0, 8))
        self._video_time_lbl = ttk.Label(bar, text=" ")
        self._video_time_lbl.pack(side=tk.RIGHT, padx=(8, 0))
        self._video_scale = tk.Scale(
            bar,
            from_=0,
            to=1,
            orient=tk.HORIZONTAL,
            variable=self._video_pos_var,
            showvalue=0,
            resolution=1,
            command=self._video_on_scale_move,
        )
        self._video_scale.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self._video_scale.bind("<ButtonPress-1>", self._video_on_scale_press)
        self._video_scale.bind("<ButtonRelease-1>", self._video_on_scale_release)

    def _video_ticks_ms(self) -> int:
        fps = float(self._cap.get(cv2.CAP_PROP_FPS) or 0.0) if self._cap else 0.0
        if fps < 1 or fps > 120:
            fps = 30.0
        return max(1, int(round(1000.0 / fps)))

    def _video_refresh_play_button(self) -> None:
        if self._video_play_btn is None:
            return
        lab = self.t("video_pause") if self._video_playing else self.t("video_play")
        self._video_play_btn.configure(text=lab)

    def _video_refresh_time_label(self, frame_idx: int) -> None:
        if self._video_time_lbl is None:
            return
        if self.state.mode == AppMode.CAMERA:
            self._video_time_lbl.configure(text=self.t("video_pos_camera"))
            return
        tot = self._video_total_frames
        if self._video_has_seek and tot > 0:
            cur = max(0, min(frame_idx + 1, tot))
            self._video_time_lbl.configure(text=self.t("video_pos_frames", cur=cur, total=tot))
        else:
            self._video_time_lbl.configure(text=self.t("video_pos_unknown"))

    def _video_set_scale_pos_ui(self, idx: int) -> None:
        if not self._video_scale or not self._video_has_seek or self._video_total_frames <= 0:
            return
        up = max(0, min(idx, self._video_total_frames - 1))
        self._video_suppress_scale_cb = True
        try:
            self._video_pos_var.set(up)
        finally:
            self._video_suppress_scale_cb = False
        self._video_refresh_time_label(up)

    def _video_sync_slider_from_capture(self) -> None:
        if not self._video_has_seek or self._video_scale_dragging or self._cap is None:
            return
        raw = int(self._cap.get(cv2.CAP_PROP_POS_FRAMES) or 0)
        fi = max(0, raw - 1)
        if self._video_total_frames > 0:
            fi = min(fi, self._video_total_frames - 1)
        self._video_set_scale_pos_ui(fi)

    def _video_on_scale_press(self, _event=None) -> None:
        self._video_scale_dragging = True

    def _video_on_scale_move(self, _val: str) -> None:
        if self._video_suppress_scale_cb:
            return
        if not self._video_has_seek:
            return
        try:
            i = int(float(_val))
        except (TypeError, ValueError):
            return
        self._video_refresh_time_label(i)

    def _video_on_scale_release(self, _event=None) -> None:
        self._video_scale_dragging = False
        if not self._video_has_seek or self._cap is None:
            return
        if self.state.mode != AppMode.VIDEO:
            return
        pos = int(self._video_pos_var.get())
        pos = max(0, min(pos, max(0, self._video_total_frames - 1)))
        self._cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ok, frame = self._cap.read()
        if ok and frame is not None:
            self._video_process_frame(ensure_bgr(frame), update_last=True)
            self._video_sync_slider_from_capture()
        else:
            self._video_playing = False
            self._video_refresh_play_button()
            if self._video_has_seek and self._video_total_frames > 0:
                self._video_set_scale_pos_ui(self._video_total_frames - 1)

    def _video_on_play_pause(self) -> None:
        if self._cap is None or self.state.mode not in (AppMode.VIDEO, AppMode.CAMERA):
            return
        self._video_playing = not self._video_playing
        self._video_refresh_play_button()
        if self._video_playing:
            if self._after_id:
                try:
                    self.after_cancel(self._after_id)
                except tk.TclError:
                    pass
                self._after_id = None
            self._after_id = self.after(1, self._video_loop)
        else:
            if self._after_id:
                try:
                    self.after_cancel(self._after_id)
                except tk.TclError:
                    pass
                self._after_id = None

    def _video_update_transport_after_open(self) -> None:
        self._video_playing = True
        self._video_last_frame = None
        self._video_scale_dragging = False
        if self.state.mode == AppMode.CAMERA:
            self._video_total_frames = 0
            self._video_has_seek = False
        else:
            tf = int(self._cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            self._video_total_frames = max(0, tf)
            self._video_has_seek = self._video_total_frames > 1
        self._ensure_video_transport_widgets()
        self._video_suppress_scale_cb = True
        try:
            self._video_pos_var.set(0)
            if self._video_scale is not None:
                if self._video_has_seek:
                    self._video_scale.configure(state=tk.NORMAL, to=max(1, self._video_total_frames - 1))
                else:
                    self._video_scale.configure(state=tk.DISABLED, to=1)
        finally:
            self._video_suppress_scale_cb = False
        self._video_refresh_time_label(0)
        self._video_refresh_play_button()

    def _video_process_frame(self, frame: np.ndarray, *, update_last: bool) -> None:
        frame = ensure_bgr(frame)
        if update_last:
            self._video_last_frame = frame.copy()
        if self._rec_pending and self._rec_writer is None and self._rec_path:
            h, w = frame.shape[:2]
            fps = float(self._cap.get(cv2.CAP_PROP_FPS) or 0.0) if self._cap else 0.0
            if fps < 1 or fps > 120:
                fps = 30.0
            fc = (self._rec_fourcc or "mp4v").strip()
            if len(fc) < 4:
                fc = (fc + "mp4v")[:4]
            fc = fc[:4]
            code = cv2.VideoWriter_fourcc(fc[0], fc[1], fc[2], fc[3])
            self._rec_writer = cv2.VideoWriter(self._rec_path, code, fps, (w, h))
            if not self._rec_writer.isOpened():
                self._log("ERROR", self.t("log_vw_fail"))
                try:
                    self._rec_writer.release()
                except Exception:
                    pass
                self._rec_writer = None
            self._rec_pending = False
        if self._rec_writer is not None:
            self._rec_writer.write(frame)
        vp = self.state.video_settings
        for sp in self._active_specs:
            if sp.category != "video":
                continue
            c = self._cards.get(sp.id)
            if not c:
                continue
            try:
                out = apply_video_algorithm(sp.id, frame, vp, self._video_engine)
                c.set_image(out)
            except Exception as e:
                self._log("WARNING", self.t("log_img_algo_err", aid=sp.id, err=str(e)))
                c.set_image(frame)

    def _video_loop(self) -> None:
        self._after_id = None
        if self._cap is None or self.state.mode not in (AppMode.VIDEO, AppMode.CAMERA):
            return
        if not self._video_playing:
            return
        ok, frame = self._cap.read()
        if not ok or frame is None:
            if self.state.mode == AppMode.VIDEO:
                self._video_playing = False
                self._video_refresh_play_button()
                if self._video_has_seek and self._video_total_frames > 0:
                    self._video_set_scale_pos_ui(self._video_total_frames - 1)
                self._log("INFO", self.t("log_video_eof"))
            else:
                self._after_id = self.after(self._video_ticks_ms(), self._video_loop)
            return
        self._video_process_frame(frame, update_last=True)
        self._video_sync_slider_from_capture()
        delay = self._video_ticks_ms()
        self._after_id = self.after(delay, self._video_loop)

    def _mode_draw(self) -> None:
        self._switch_mode(AppMode.DRAW)
        self._show_card_grid()
        from cv_course.ui_tk.toolbar_icons import build_draw_tool_icons

        self._card_host.grid_columnconfigure(0, weight=1)
        self._card_host.grid_rowconfigure(0, weight=1)

        host = ttk.Frame(self._card_host)
        host.grid(row=0, column=0, sticky="nsew")
        host.grid_columnconfigure(0, weight=1)
        host.grid_rowconfigure(1, weight=1)

        tool_var = tk.StringVar(value="pencil")
        color_var = tk.StringVar(value="#000000")
        width_var = tk.IntVar(value=3)

        st: dict[str, object] = {"anchor": None, "preview": None}
        poly_pts: list[tuple[int, int]] = []
        last = {"x": 0, "y": 0}
        btn1 = {"down": False}

        bar = ttk.Frame(host)
        bar.grid(row=0, column=0, sticky="ew", pady=(0, 6))

        icons = build_draw_tool_icons(self)
        self._draw_palette_icon_refs = list(icons.values())

        cv = tk.Canvas(host, bg="white", highlightthickness=0, cursor="crosshair")
        cv.grid(row=1, column=0, sticky="nsew")

        def get_stroke() -> tuple[str, int]:
            try:
                wv = max(1, min(48, int(width_var.get())))
            except (tk.TclError, ValueError):
                wv = 2
            return color_var.get(), wv

        def clear_preview() -> None:
            pid = st.get("preview")
            if pid is not None:
                try:
                    cv.delete(pid)
                except tk.TclError:
                    pass
            st["preview"] = None

        def reset_interaction() -> None:
            st["anchor"] = None
            poly_pts.clear()
            clear_preview()
            btn1["down"] = False

        tool_btns: dict[str, tk.Button] = {}

        def select_tool(name: str) -> None:
            tool_var.set(name)
            for n, b in tool_btns.items():
                b.configure(relief=tk.SUNKEN if n == name else tk.RAISED)
            reset_interaction()

        tool_cfg = (
            ("pencil", "draw_pencil", "draw_tool_pencil"),
            ("line", "draw_line", "draw_tool_line"),
            ("poly", "draw_poly", "draw_tool_poly"),
            ("circle", "draw_circle", "draw_tool_circle"),
        )
        for val, ikey, tipkey in tool_cfg:
            b = tk.Button(
                bar,
                image=icons[ikey],
                width=34,
                height=30,
                relief=tk.SUNKEN if val == "pencil" else tk.RAISED,
                command=lambda v=val: select_tool(v),
            )
            b.pack(side=tk.LEFT, padx=2)
            b.bind("<Enter>", lambda _e, k=tipkey: self.status.configure(text=self.t(k)))
            b.bind("<Leave>", lambda _e: self._refresh_status_line())
            tool_btns[val] = b

        ttk.Separator(bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill="y", padx=8)

        ttk.Label(bar, text=self.t("draw_color")).pack(side=tk.LEFT, padx=(0, 4))
        sw = tk.Canvas(bar, width=36, height=26, highlightthickness=1, highlightbackground="#999")

        def paint_swatch() -> None:
            sw.delete("all")
            c = color_var.get()
            sw.create_rectangle(0, 0, 40, 30, fill=c, outline="")

        sw.pack(side=tk.LEFT, padx=2)

        def on_color_write(*_a: object) -> None:
            paint_swatch()

        color_var.trace_add("write", on_color_write)
        paint_swatch()

        def pick_color() -> None:
            r = colorchooser.askcolor(color_var.get(), parent=self)
            if r and r[1]:
                color_var.set(r[1])

        ttk.Button(bar, text=self.t("draw_pick_color"), command=pick_color).pack(side=tk.LEFT, padx=4)

        ttk.Label(bar, text=self.t("draw_width")).pack(side=tk.LEFT, padx=(12, 4))
        tk.Spinbox(bar, from_=1, to=48, width=5, textvariable=width_var).pack(side=tk.LEFT)

        def on_press(e: tk.Event) -> None:
            btn1["down"] = True
            t = tool_var.get()
            c, w = get_stroke()
            if t == "pencil":
                last["x"], last["y"] = e.x, e.y
            elif t == "line":
                st["anchor"] = (e.x, e.y)
            elif t == "circle":
                st["anchor"] = (e.x, e.y)
            elif t == "poly":
                if not poly_pts:
                    poly_pts.append((e.x, e.y))
                else:
                    x0, y0 = poly_pts[-1]
                    cv.create_line(x0, y0, e.x, e.y, width=w, fill=c, capstyle=tk.ROUND)
                    poly_pts.append((e.x, e.y))
                    self.state.dirty = True
                clear_preview()

        def on_motion(e: tk.Event) -> None:
            t = tool_var.get()
            c, w = get_stroke()
            if t == "pencil" and btn1["down"]:
                x0, y0 = last["x"], last["y"]
                cv.create_line(x0, y0, e.x, e.y, width=w, fill=c, capstyle=tk.ROUND, smooth=True)
                last["x"], last["y"] = e.x, e.y
                self.state.dirty = True
                return
            if t == "line" and st["anchor"]:
                clear_preview()
                x0, y0 = st["anchor"]  # type: ignore[misc]
                st["preview"] = cv.create_line(x0, y0, e.x, e.y, width=w, fill=c, dash=(5, 5))
            elif t == "circle" and st["anchor"]:
                clear_preview()
                x0, y0 = st["anchor"]  # type: ignore[misc]
                st["preview"] = cv.create_rectangle(
                    x0, y0, e.x, e.y, width=max(1, w // 2), outline=c, dash=(5, 5)
                )
            elif t == "poly" and poly_pts:
                clear_preview()
                x0, y0 = poly_pts[-1]
                st["preview"] = cv.create_line(x0, y0, e.x, e.y, width=w, fill=c, dash=(4, 4))

        def on_release(e: tk.Event) -> None:
            btn1["down"] = False
            t = tool_var.get()
            c, w = get_stroke()
            if t == "line" and st["anchor"]:
                x0, y0 = st["anchor"]  # type: ignore[misc]
                clear_preview()
                cv.create_line(x0, y0, e.x, e.y, width=w, fill=c, capstyle=tk.ROUND)
                st["anchor"] = None
                self.state.dirty = True
            elif t == "circle" and st["anchor"]:
                x0, y0 = st["anchor"]  # type: ignore[misc]
                clear_preview()
                cv.create_oval(x0, y0, e.x, e.y, width=w, outline=c, fill="")
                st["anchor"] = None
                self.state.dirty = True

        def on_poly_close(_e: tk.Event) -> None:
            if tool_var.get() != "poly":
                return
            if len(poly_pts) < 3:
                return
            c, w = get_stroke()
            x0, y0 = poly_pts[-1]
            xa, ya = poly_pts[0]
            cv.create_line(x0, y0, xa, ya, width=w, fill=c, capstyle=tk.ROUND)
            poly_pts.clear()
            clear_preview()
            self.state.dirty = True

        cv.bind("<ButtonPress-1>", on_press)
        cv.bind("<ButtonRelease-1>", on_release)
        cv.bind("<B1-Motion>", on_motion)
        cv.bind("<Motion>", on_motion)
        cv.bind("<Button-3>", on_poly_close)

        self._draw_canvas = cv
        self._log("INFO", self.t("log_draw_hint"))

    def _save_file(self) -> None:
        if self.state.mode == AppMode.IMAGE and self._bgr is not None:
            path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[(self.t("file_png"), "*.png"), (self.t("file_jpeg"), "*.jpg")],
            )
            if path:
                cv2.imwrite(path, self._bgr)
                self.state.dirty = False
                self._log("INFO", self.t("log_saved_image", path=path))
        elif self.state.mode == AppMode.DRAW and getattr(self, "_draw_canvas", None) is not None:
            path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[(self.t("file_png"), "*.png")],
            )
            if path:
                self._draw_canvas.postscript(file=path.replace(".png", ".eps"), colormode="color")
                # Tk postscript is eps; for png use grab - simplified message
                try:
                    self._draw_canvas.update()
                    x = self._draw_canvas.winfo_rootx()
                    y = self._draw_canvas.winfo_rooty()
                    from PIL import ImageGrab

                    bbox = (x, y, x + self._draw_canvas.winfo_width(), y + self._draw_canvas.winfo_height())
                    ImageGrab.grab(bbox=bbox).save(path)
                    self.state.dirty = False
                    self._log("INFO", self.t("log_saved_canvas", path=path))
                except Exception as e:
                    self._log("ERROR", self.t("log_save_draw_fail", err=str(e)))
        elif self.state.mode in (AppMode.VIDEO, AppMode.CAMERA):
            self._log("INFO", self.t("log_video_save_hint"))
        else:
            messagebox.showinfo(self.t("dlg_info"), self.t("save_none"), parent=self)

    def _dlg_image_settings(self) -> None:
        top = tk.Toplevel(self)
        top.title(self.t("dlg_image_title"))
        p = self.state.image_settings
        vars_: dict[str, tk.Variable] = {
            "kernel_size": tk.IntVar(value=p.kernel_size),
            "canny_t1": tk.IntVar(value=p.canny_t1),
            "canny_t2": tk.IntVar(value=p.canny_t2),
            "rotate_angle": tk.DoubleVar(value=p.rotate_angle),
            "scale_factor": tk.DoubleVar(value=p.scale_factor),
            "binary_thresh": tk.IntVar(value=p.binary_thresh),
            "adaptive_block": tk.IntVar(value=p.adaptive_block),
            "adaptive_c": tk.IntVar(value=p.adaptive_c),
            "hsv_h_low": tk.IntVar(value=p.hsv_h_low),
            "hsv_h_high": tk.IntVar(value=p.hsv_h_high),
            "morph_kernel": tk.IntVar(value=p.morph_kernel),
            "gaussian_ksize": tk.IntVar(value=p.gaussian_ksize),
        }
        r = 0

        def row(label, key, w="entry"):
            nonlocal r
            ttk.Label(top, text=label).grid(row=r, column=0, sticky="w", padx=6, pady=2)
            if w == "entry":
                ttk.Entry(top, textvariable=vars_[key], width=12).grid(row=r, column=1, sticky="w")
            r += 1

        for lb_key, k in [
            ("lbl_kernel", "kernel_size"),
            ("lbl_canny_lo", "canny_t1"),
            ("lbl_canny_hi", "canny_t2"),
            ("lbl_rotate", "rotate_angle"),
            ("lbl_scale", "scale_factor"),
            ("lbl_bin", "binary_thresh"),
            ("lbl_adapt_block", "adaptive_block"),
            ("lbl_adapt_c", "adaptive_c"),
            ("lbl_hsv_h_lo", "hsv_h_low"),
            ("lbl_hsv_h_hi", "hsv_h_high"),
            ("lbl_morph_k", "morph_kernel"),
            ("lbl_gauss_k", "gaussian_ksize"),
        ]:
            row(self.t(lb_key), k)

        def apply():
            p.kernel_size = int(vars_["kernel_size"].get())
            p.canny_t1 = int(vars_["canny_t1"].get())
            p.canny_t2 = int(vars_["canny_t2"].get())
            p.rotate_angle = float(vars_["rotate_angle"].get())
            p.scale_factor = float(vars_["scale_factor"].get())
            p.binary_thresh = int(vars_["binary_thresh"].get())
            p.adaptive_block = int(vars_["adaptive_block"].get())
            p.adaptive_c = int(vars_["adaptive_c"].get())
            p.hsv_h_low = int(vars_["hsv_h_low"].get())
            p.hsv_h_high = int(vars_["hsv_h_high"].get())
            p.morph_kernel = int(vars_["morph_kernel"].get())
            p.gaussian_ksize = int(vars_["gaussian_ksize"].get())
            if self.state.mode == AppMode.IMAGE:
                self._refresh_image_cards()
            top.destroy()

        ttk.Button(top, text=self.t("btn_ok"), command=apply).grid(row=r, column=0, columnspan=2, pady=8)

    def _dlg_video_settings(self) -> None:
        top = tk.Toplevel(self)
        top.title(self.t("dlg_video_title"))
        v = self.state.video_settings
        hs = tk.DoubleVar(value=v.haar_scale)
        hn = tk.IntVar(value=v.haar_neighbors)
        mh = tk.IntVar(value=v.mog2_history)
        mv = tk.IntVar(value=v.mog2_var_threshold)
        ttk.Label(top, text=self.t("lbl_haar_scale")).grid(row=0, column=0)
        ttk.Entry(top, textvariable=hs).grid(row=0, column=1)
        ttk.Label(top, text=self.t("lbl_haar_neighbors")).grid(row=1, column=0)
        ttk.Entry(top, textvariable=hn).grid(row=1, column=1)
        ttk.Label(top, text=self.t("lbl_mog2_hist")).grid(row=2, column=0)
        ttk.Entry(top, textvariable=mh).grid(row=2, column=1)
        ttk.Label(top, text=self.t("lbl_mog2_var")).grid(row=3, column=0)
        ttk.Entry(top, textvariable=mv).grid(row=3, column=1)
        yw = tk.StringVar(value=v.yolo_weights_path)
        ttk.Label(top, text=self.t("lbl_yolo_weights")).grid(row=4, column=0, sticky="w", padx=4, pady=4)
        ttk.Entry(top, textvariable=yw, width=40).grid(row=4, column=1, sticky="w", padx=4, pady=4)
        ttk.Label(top, text=self.t("lbl_yolo_hint")).grid(row=5, column=1, sticky="w")

        def ok():
            v.haar_scale = float(hs.get())
            v.haar_neighbors = int(hn.get())
            v.mog2_history = int(mh.get())
            v.mog2_var_threshold = int(mv.get())
            new_y = yw.get().strip()
            if new_y != v.yolo_weights_path:
                self._video_engine.yolo_model = None
                self._video_engine.yolo_path_loaded = None
            v.yolo_weights_path = new_y or "yolo11n.pt"
            self._video_engine.mog2 = None
            top.destroy()

        ttk.Button(top, text=self.t("btn_ok"), command=ok).grid(row=6, column=0, columnspan=2, pady=6)

    def _dlg_layout_settings(self) -> None:
        top = tk.Toplevel(self)
        top.title(self.t("dlg_layout_title"))
        lay = self.state.layout
        row_maj = tk.BooleanVar(value=lay.row_major)
        per = tk.IntVar(value=lay.per_line)
        side = tk.IntVar(value=lay.card_max_side)
        ttk.Checkbutton(top, text=self.t("layout_row_major"), variable=row_maj).pack(anchor="w", padx=8)
        ttk.Label(top, text=self.t("layout_per_line")).pack(anchor="w")
        ttk.Entry(top, textvariable=per).pack()
        ttk.Label(top, text=self.t("layout_card_side")).pack(anchor="w")
        ttk.Entry(top, textvariable=side).pack()

        def ok():
            lay.row_major = row_maj.get()
            lay.per_line = max(1, int(per.get()))
            lay.card_max_side = max(80, int(side.get()))
            if self._active_specs:
                self._layout_cards(self._active_specs)
                for c in self._cards.values():
                    c.set_max_side(lay.card_max_side)
                if self.state.mode == AppMode.IMAGE:
                    self._refresh_image_cards()
            top.destroy()

        ttk.Button(top, text=self.t("btn_ok"), command=ok).pack(pady=6)

    def _on_close(self) -> None:
        self._clear_mode()
        self.destroy()


def main() -> None:
    app = CVCourseApp()
    app.mainloop()
