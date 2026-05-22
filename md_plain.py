"""将常见 Markdown 转为适合 Tk ``Text``/``ScrolledText`` 显示的纯文本（去掉标记、保留可读结构）。"""



from __future__ import annotations



import re



# 占位符：避免围栏代码块内的 ``#`` 注释、``**`` 等被当成 Markdown 处理

_PLACEHOLDER_PREFIX = "\uE000MD_CODE_"

_PLACEHOLDER_SUFFIX = "\uE001"





def _strip_markdown_non_fence(s: str) -> str:

    """对不含围栏代码块占位符的文本做 Markdown 剥离（不处理 ```）。"""

    # ATX 标题 ``#`` … ``######``；围栏外处理，代码块内 ``#`` 不受影响

    s = re.sub(r"(?m)^#{1,6}\s+", "", s)



    s = re.sub(r"(?m)^\s{0,3}[-*+]\s+", "• ", s)

    s = re.sub(r"(?m)^(\s*)(\d+)\.\s+", r"\1\2. ", s)

    s = re.sub(r"(?m)^\s*>\s?", "", s)



    for _ in range(6):

        n = re.sub(r"\*\*([^*\n]+)\*\*", r"\1", s)

        n = re.sub(r"__([^_\n]+)__", r"\1", n)

        if n == s:

            break

        s = n



    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", s)

    # 行内代码不跨行，避免把多行正文/代码粘成一行

    s = re.sub(r"`([^`\n]+)`", r"\1", s)

    s = re.sub(r"~~([^~\n]+)~~", r"\1", s)

    s = re.sub(r"(?m)^\s*-{3,}\s*$", "", s)

    return s





def markdown_to_display_plain(text: str) -> str:

    """

    去掉 Markdown 标记，尽量保留层次与代码内容。



    支持：围栏代码 ```、ATX 标题（``#`` … ``######`` 行首）、有序/无序列表、粗体 **/__、行内 `、`、链接 [t](u)、水平线 ---。



    围栏代码块内的文本不再做 Markdown 处理，且标题规则不会误删 ``#`` 开头的 Python 注释。

    """

    if not text:

        return ""

    s = text.replace("\r\n", "\n")

    blocks: list[str] = []



    def _fence_repl(m: re.Match[str]) -> str:

        body = m.group(1).strip("\n")

        idx = len(blocks)

        blocks.append(body)

        return f"\n\n{_PLACEHOLDER_PREFIX}{idx}{_PLACEHOLDER_SUFFIX}\n\n"



    s = re.sub(r"(?ms)^```[^\n]*\n(.*?)```", _fence_repl, s)

    s = _strip_markdown_non_fence(s)

    for i, body in enumerate(blocks):

        ph = f"{_PLACEHOLDER_PREFIX}{i}{_PLACEHOLDER_SUFFIX}"

        s = s.replace(ph, "\n\n" + body + "\n\n")



    s = re.sub(r"\n{3,}", "\n\n", s)

    return s.strip()


