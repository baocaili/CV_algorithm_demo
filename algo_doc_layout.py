"""Normalize algorithm teaching markdown from ``algo_descriptions.csv`` for UI (Tk + Streamlit).

Collapses legacy section headings (原理教材级 / 离散实现 / 工程串联 / 举例 等) into the
structure requested for display: 原理 | 功能与应用 | 用法.
"""

from __future__ import annotations

import re
from typing import Dict

_H2 = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)


def sanitize_doc_title(title: str) -> str:
    """Remove internal id suffixes like ``（内部标识 `img_original`）`` or ``(`id`)``."""
    t = (title or "").strip()
    if not t:
        return t
    t = re.sub(r"（\s*内部标识\s*`[^`]+`\s*）", "", t)
    t = re.sub(r"\s*\(`[^`]+`\)", "", t)
    return t.strip()


def _norm_key(k: str) -> str:
    return re.sub(r"\s+", "", (k or "").strip()).lower()


def _split_h2_sections(md: str) -> Dict[str, str]:
    text = (md or "").replace("\r\n", "\n")
    if not text.strip():
        return {}
    matches = list(_H2.finditer(text))
    if not matches:
        return {"__body__": text.strip()}
    out: Dict[str, str] = {}
    if matches[0].start() > 0:
        pre = text[: matches[0].start()].strip()
        if pre:
            out["__preamble__"] = pre
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        out[title] = text[start:end].strip()
    return out


def _merge_zh_principle(sec: Dict[str, str]) -> str:
    parts: list[str] = []

    def grab(pred) -> None:
        for k, v in sec.items():
            if k.startswith("__"):
                continue
            if pred(k) and (v or "").strip():
                parts.append(v.strip())
                return

    grab(lambda k: "原理" in k and "教材" in k)
    grab(lambda k: "离散实现与数学扩展" in k)
    grab(lambda k: "与算法" in k and "关联" in k and "要点" in k)
    return "\n\n".join(parts).strip()


def _merge_en_principle(sec: Dict[str, str]) -> str:
    parts: list[str] = []
    preds = (
        lambda k: _norm_key(k) == "principle",
        lambda k: "math&implementationnotes" in _norm_key(k),
    )
    for pred in preds:
        for k, v in sec.items():
            if k.startswith("__"):
                continue
            if pred(k) and (v or "").strip():
                parts.append(v.strip())
                break
    return "\n\n".join(parts).strip()


def _merge_zh_function(sec: Dict[str, str]) -> str:
    parts: list[str] = []

    def grab(pred) -> None:
        for k, v in sec.items():
            if k.startswith("__"):
                continue
            if pred(k) and (v or "").strip():
                parts.append(v.strip())
                return

    grab(lambda k: k.startswith("算法功能") or _norm_key(k).startswith("算法功能"))
    grab(lambda k: k.startswith("工程串联") or _norm_key(k).startswith("工程串联"))
    return "\n\n".join(parts).strip()


def _merge_en_function(sec: Dict[str, str]) -> str:
    for k, v in sec.items():
        if k.startswith("__"):
            continue
        nk = _norm_key(k)
        if "function" in nk and "pipeline" in nk and (v or "").strip():
            return v.strip()
    if "__body__" in sec:
        return sec["__body__"].strip()
    return ""


def _usage_body(usage: str) -> str:
    sec = _split_h2_sections(usage)
    if len(sec) == 1 and "__body__" in sec:
        b = sec["__body__"]
        b = re.sub(r"^#{1,6}\s*(用法|Usage)[^\n]*\n+", "", b, count=1, flags=re.MULTILINE)
        return b.strip()
    for k, v in sec.items():
        if k.startswith("__"):
            continue
        nk = _norm_key(k)
        if nk.startswith("用法") or nk.startswith("usage"):
            return (v or "").strip()
    return (usage or "").strip()


def normalize_algo_doc_for_display(
    lang: str,
    principle: str,
    function_desc: str,
    example: str,
    usage_py: str,
    extension: str,
) -> tuple[str, str, str]:
    """Return markdown blocks: (原理段, 功能与应用段, 用法段)；举例列忽略；extension 并入原理。"""
    _ = example  # 举例列不展示
    lang_n = "zh" if (lang or "").lower().startswith("zh") else "en"
    h_pr = "原理" if lang_n == "zh" else "Principle"
    h_fn = "功能与应用" if lang_n == "zh" else "Function & application"
    h_us = "用法" if lang_n == "zh" else "Usage"

    p_sec = _split_h2_sections(principle)
    if lang_n == "zh":
        p_body = _merge_zh_principle(p_sec)
    else:
        p_body = _merge_en_principle(p_sec)
    if not p_body and (principle or "").strip():
        if "__body__" in p_sec and len([k for k in p_sec if not k.startswith("__")]) <= 1:
            p_body = (p_sec.get("__body__") or principle).strip()
        elif not any(not k.startswith("__") for k in p_sec):
            p_body = principle.strip()

    ext = (extension or "").strip()
    if ext:
        p_body = (p_body + "\n\n" + ext).strip() if p_body else ext

    f_sec = _split_h2_sections(function_desc)
    if lang_n == "zh":
        f_body = _merge_zh_function(f_sec)
    else:
        f_body = _merge_en_function(f_sec)
    if not f_body and (function_desc or "").strip():
        if "__body__" in f_sec:
            f_body = f_sec["__body__"].strip()

    u_body = _usage_body(usage_py or "")
    u_md = f"# {h_us}\n\n{u_body}" if u_body else ""

    p_md = f"# {h_pr}\n\n{p_body}" if p_body else ""
    f_md = f"# {h_fn}\n\n{f_body}" if f_body else ""
    return p_md, f_md, u_md
