"""将 Markdown 转为完整 HTML 文档字符串，供 TkinterWeb ``HtmlFrame.load_html`` 使用。"""

from __future__ import annotations

import re

# 与卡片背面 ``_body`` 背景协调；内容用拼接避免 ``str.format`` 与代码块中的 ``{``/``}`` 冲突。
_HTML_HEAD = """<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<style>
html, body { margin: 0; padding: 0; background: #eef1f6; color: #1a1a1a; }
body { font-family: "Segoe UI", "Microsoft YaHei UI", sans-serif; font-size: 11px; line-height: 1.35; padding: 6px 8px 10px; }
pre, code { font-family: Consolas, "Cascadia Mono", monospace; font-size: 10px; }
pre { background: #e2e6ef; padding: 6px 8px; border-radius: 4px; white-space: pre-wrap; overflow-x: auto; margin: 0.35em 0; word-break: break-word; }
code { background: #e2e6ef; padding: 0 3px; border-radius: 2px; white-space: pre-wrap; }
h1, h2, h3, h4 { font-size: 12px; margin: 0.5em 0 0.25em; }
p { margin: 0.3em 0; }
ul, ol { margin: 0.25em 0 0.25em 1.1em; padding: 0; }
li { margin: 0.1em 0; }
table { border-collapse: collapse; font-size: 10px; }
th, td { border: 1px solid #c5c9d6; padding: 2px 5px; }
</style></head><body>
<div class="md">"""

_HTML_TAIL = "</div></body></html>"

# CSV 中 ``usage_py`` / 拓展常为「## 标题」后直接跟裸 Python；标准 Markdown 会当成段落把换行压成空格。
_HEADING_CODE_LEADS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^(#\s*(?:用法|Usage)[^\n]*\n)(.*)\Z", re.DOTALL),
    re.compile(r"^(#{1,6}\s*(?:用法|Usage)[^\n]*\n)(.*)\Z", re.DOTALL),
    re.compile(r"^(#{2,6}\s*(?:教学要点|Teaching notes|课后拓展|拓展练习)[^\n]*\n)(.*)\Z", re.DOTALL),
)
_PLAIN_CODE_START = re.compile(r"^(?:import |from [\w.]+\s+import\s)", re.MULTILINE)
_PRE_CODE_BLOCK = re.compile(r"<pre>\s*<code(?:\s[^>]*)?>(.*?)</code>\s*</pre>", re.DOTALL | re.IGNORECASE)


def _normalize_doc_cell(raw: str) -> str:
    s = (raw or "").replace("\r\n", "\n").lstrip("\ufeff \t")
    while s.startswith("\n"):
        s = s[1:]
    return s


def fence_algo_doc_cell(cell: str) -> str:
    """若单元格在「用法/教学要点」等标题后是未围栏的代码，则自动包上 `` ```python `` 围栏。"""
    s = _normalize_doc_cell(cell)
    for rx in _HEADING_CODE_LEADS:
        m = rx.match(s)
        if not m:
            continue
        head, rest = m.group(1), m.group(2)
        if not rest.strip() or "```" in rest:
            return s
        return head + "```python\n" + rest.rstrip("\n") + "\n```\n"
    if "```" in s or not s.strip():
        return s
    if _PLAIN_CODE_START.match(s.lstrip("\n")):
        return "```python\n" + s.rstrip("\n") + "\n```\n"
    return s


def _flatten_pre_code_blocks(html: str) -> str:
    """Tkhtml/TkinterWeb 对 ``<pre><code>`` 嵌套有时会把换行吃掉，展平为单层 ``<pre>``。"""
    return _PRE_CODE_BLOCK.sub(lambda m: "<pre>" + m.group(1) + "</pre>", html)


def markdown_to_html_document(md_source: str) -> str:
    """把 Markdown 转为带内联样式的 HTML 文档（UTF-8）。"""
    import markdown
    from markdown.extensions.fenced_code import FencedCodeExtension
    from markdown.extensions.nl2br import Nl2BrExtension
    from markdown.extensions.sane_lists import SaneListExtension
    from markdown.extensions.tables import TableExtension

    body = markdown.markdown(
        md_source,
        extensions=[FencedCodeExtension(), TableExtension(), Nl2BrExtension(), SaneListExtension()],
        output_format="html",
    )
    body = _flatten_pre_code_blocks(body)
    return _HTML_HEAD + body + _HTML_TAIL


# 兼容旧名
def fence_usage_py_markdown(cell: str) -> str:
    return fence_algo_doc_cell(cell)
