"""按子类多选算法展示（Tkinter）。"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Literal

from dataclasses import dataclass

from cv_course.algorithms.subcategories import group_specs_by_subgroup
from cv_course.i18n import SUPPORTED_LANGS, algo_title, subgroup_label, t

Category = Literal["image", "video"]


@dataclass
class AlgorithmPickerResult:
    cancelled: bool = True
    """为 True 时不应修改设置。"""
    enabled_ids: list[str] | None = None
    """确定且勾选全部时为 None（表示展示全部）；否则为选中的 id 列表。"""


def show_algorithm_picker(
    parent: tk.Tk,
    category: Category,
    current_enabled: list[str] | None,
    lang: str,
) -> AlgorithmPickerResult:
    lang = lang if lang in SUPPORTED_LANGS else "en"

    def tr(key: str, **kwargs: object) -> str:
        return t(lang, key, **kwargs)

    grouped = group_specs_by_subgroup(category)
    all_ids: list[str] = []
    for specs in grouped.values():
        for s in specs:
            all_ids.append(s.id)

    initially_on = set(all_ids if current_enabled is None else current_enabled)

    top = tk.Toplevel(parent)
    top.title(tr("picker_title_image" if category == "image" else "picker_title_video"))
    top.transient(parent)
    top.grab_set()
    top.geometry("520x560")

    result = AlgorithmPickerResult(cancelled=True, enabled_ids=None)

    vars_by_id: dict[str, tk.BooleanVar] = {}

    outer = ttk.Frame(top, padding=6)
    outer.pack(fill="both", expand=True)
    canvas = tk.Canvas(outer, highlightthickness=0)
    sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    inner = ttk.Frame(canvas)

    def _scroll_inner(_e=None):
        canvas.configure(scrollregion=canvas.bbox("all"))

    inner.bind("<Configure>", _scroll_inner)
    win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    def _canvas_cfg(e):
        canvas.itemconfig(win_id, width=e.width)

    canvas.bind("<Configure>", _canvas_cfg)

    for sub in sorted(grouped.keys()):
        lf = ttk.LabelFrame(inner, text=subgroup_label(lang, sub))
        lf.pack(fill="x", pady=4, padx=2)
        for spec in grouped[sub]:
            v = tk.BooleanVar(value=spec.id in initially_on)
            vars_by_id[spec.id] = v
            label = f"{algo_title(lang, spec)}  ({spec.id})"
            ttk.Checkbutton(lf, text=label, variable=v).pack(anchor="w", padx=8)

    canvas.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")
    canvas.configure(yscrollcommand=sb.set)

    def _wheel(e):
        canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")

    canvas.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", _wheel))
    canvas.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))

    def select_all(on: bool) -> None:
        for v in vars_by_id.values():
            v.set(on)

    def only_subgroup(sub: str) -> None:
        select_all(False)
        for spec in grouped.get(sub, []):
            vars_by_id[spec.id].set(True)

    btn_row = ttk.Frame(top, padding=(6, 0))
    btn_row.pack(fill="x")
    ttk.Button(btn_row, text=tr("picker_select_all"), command=lambda: select_all(True)).pack(side="left", padx=2)
    ttk.Button(btn_row, text=tr("picker_select_none"), command=lambda: select_all(False)).pack(side="left", padx=2)
    sub_keys = sorted(grouped.keys())
    sub_entries = [(subgroup_label(lang, sk), sk) for sk in sub_keys]
    sub_pick = ttk.Combobox(btn_row, values=[e[0] for e in sub_entries], width=18, state="readonly")
    if sub_entries:
        sub_pick.current(0)

    def only_from_combo() -> None:
        disp = sub_pick.get()
        for _d, sk in sub_entries:
            if subgroup_label(lang, sk) == disp:
                only_subgroup(sk)
                break

    ttk.Button(btn_row, text=tr("picker_only_group"), command=only_from_combo).pack(side="left", padx=6)
    sub_pick.pack(side="left", padx=2)

    def ok():
        chosen = [aid for aid, v in vars_by_id.items() if v.get()]
        if not chosen:
            messagebox.showwarning(tr("dlg_info"), tr("picker_warn_none"), parent=top)
            return
        result.cancelled = False
        result.enabled_ids = None if set(chosen) == set(all_ids) else chosen
        canvas.unbind_all("<MouseWheel>")
        top.destroy()

    def cancel():
        canvas.unbind_all("<MouseWheel>")
        top.destroy()

    bot = ttk.Frame(top, padding=6)
    bot.pack(fill="x")
    ttk.Button(bot, text=tr("picker_cancel"), command=cancel).pack(side="right", padx=4)
    ttk.Button(bot, text=tr("picker_ok"), command=ok).pack(side="right")

    parent.wait_window(top)
    return result
