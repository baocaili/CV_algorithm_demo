"""Algorithm teaching copy: load from structured CSV (offline editing, no hardcoded flip-card bodies).

Default: ``cv_course/data/algo_descriptions.csv`` (UTF-8 with optional BOM for Excel).

Override path: environment variable ``CV_COURSE_ALGO_CSV``.

**Columns** (header required): ``algorithm_id``, ``lang`` (``zh`` / ``en``), ``title``,
``principle``, ``function_desc``, ``example``, ``usage_py``, optional ``extension``.

Regenerate the bundled CSV after changing registry / English snippets::

    python -m cv_course.tools.export_algo_descriptions

教学级长文（分类深度段落 + 注册表 + 用法骨架）::

    python -m cv_course.tools.rebuild_algo_csv_detailed
"""

from __future__ import annotations

import csv
import io
import os
from pathlib import Path

from cv_course.algo_doc_layout import sanitize_doc_title

_TABLE: dict[tuple[str, str], dict[str, str]] | None = None


def _default_csv_path() -> Path:
    return Path(__file__).resolve().parent / "data" / "algo_descriptions.csv"


def _normalize_lang(lang: str) -> str:
    s = (lang or "").strip().lower()
    if s.startswith("zh"):
        return "zh"
    if s.startswith("en"):
        return "en"
    return s or "zh"


def _load_table() -> dict[tuple[str, str], dict[str, str]]:
    global _TABLE
    if _TABLE is not None:
        return _TABLE
    path = os.environ.get("CV_COURSE_ALGO_CSV", "").strip()
    p = Path(path) if path else _default_csv_path()
    out: dict[tuple[str, str], dict[str, str]] = {}
    if not p.is_file():
        _TABLE = out
        return out
    try:
        raw = p.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            text = raw.decode("utf-8-sig")
        else:
            text = raw.decode("utf-8")
        text = text.replace("\r\n", "\n").replace("\r", "\n")
    except OSError:
        _TABLE = out
        return out
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        _TABLE = out
        return out
    keymap = {str(f).strip().lower(): str(f) for f in reader.fieldnames}

    def col(row: dict[str, str], logical: str) -> str:
        ak = keymap.get(logical.lower())
        if not ak:
            return ""
        return row.get(ak) or ""

    for row in reader:
        aid = col(row, "algorithm_id").strip()
        if not aid:
            continue
        lang = _normalize_lang(col(row, "lang"))
        if lang not in ("zh", "en"):
            lang = "zh"
        rec = {
            "title": col(row, "title").strip(),
            "principle": col(row, "principle"),
            "function_desc": col(row, "function_desc"),
            "example": col(row, "example"),
            "usage_py": col(row, "usage_py"),
            "extension": col(row, "extension"),
        }
        out[(aid, lang)] = rec
    _TABLE = out
    return out


def reload_algo_description_csv() -> None:
    global _TABLE
    _TABLE = None
    _load_table()


def get_algo_doc_parts(algorithm_id: str, lang: str) -> tuple[str, str, str, str, str]:
    """Return (principle, function_desc, example, usage_py, extension) for flip-card back."""
    table = _load_table()
    row = table.get((str(algorithm_id), _normalize_lang(lang)))
    if row:
        return (
            row.get("principle") or "",
            row.get("function_desc") or "",
            row.get("example") or "",
            row.get("usage_py") or "",
            row.get("extension") or "",
        )
    from cv_course.algorithms.registry import get_algorithm

    s = get_algorithm(str(algorithm_id))
    if s is not None:
        return s.principle, s.function_desc, s.example, s.usage_py, ""
    return "", "", "", "", ""


def get_doc_title(lang: str, spec: object) -> str:
    """Card title: CSV ``title`` if present, else i18n ``algo_title``."""
    aid = str(getattr(spec, "id", ""))
    row = _load_table().get((aid, _normalize_lang(lang)))
    if row:
        t = (row.get("title") or "").strip()
        if t:
            return sanitize_doc_title(t)
    from cv_course.i18n import algo_title

    return sanitize_doc_title(algo_title(lang, spec))
