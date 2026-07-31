"""把 Markdown 文本解析为标题块树。

树结构:
  Block(level=0, title="", preamble=<文档前置内容>, children=[H1 块, ...])
    └─ Block(level=1, title="概述", preamble=<H1 下的直接内容>, children=[H2 块, ...])
        └─ ...

每个 Block 的 preamble 存放「该标题之下、其子标题之前」的内容行(不含标题行本身)。
代码块(``` 或 ~~~)内的 # 行不会被误判为标题。
"""

from .utils import is_heading


class Block:
    """一个标题块。level=0 表示虚拟根节点(文档本身)。"""

    def __init__(self, level: int, title: str):
        self.level = level
        self.title = title
        self.preamble = []          # list[str]: 直接归属本块的内容行
        self.children = []          # list[Block]: 子标题块

    def total_lines(self) -> int:
        """本块及其所有后代的总行数(含标题行,根节点除外)。"""
        n = len(self.preamble) + (1 if self.level > 0 else 0)
        for c in self.children:
            n += c.total_lines()
        return n

    def own_lines(self) -> list:
        """仅本块直接内容(preamble + 重建的标题行),不含子块。"""
        lines = []
        if self.level > 0:
            lines.append("#" * self.level + " " + self.title)
        lines.extend(self.preamble)
        return lines

    def deepest_level(self) -> int:
        """本块子树中出现的最深标题级别(本块自身级别也计入)。"""
        d = self.level
        for c in self.children:
            d = max(d, c.deepest_level())
        return d


def parse_markdown(text: str) -> Block:
    """把 md 文本解析为 Block 树。返回虚拟根节点(level=0)。"""
    root = Block(0, "")
    stack = [root]
    in_fence = False
    fence_marker = ""

    for line in text.splitlines():
        stripped = line.lstrip()
        # 代码围栏检测: ``` 或 ~~~ (允许缩进,忽略语言标识)
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                fence = "```" if stripped.startswith("```") else "~~~"
                # 一行内闭合的情况(如 ```code```)暂不处理,按开闭处理
                in_fence = True
                fence_marker = fence
                stack[-1].preamble.append(line)
                continue
        else:
            stack[-1].preamble.append(line)
            if stripped.startswith(fence_marker):
                in_fence = False
                fence_marker = ""
            continue

        # 围栏外: 识别标题
        h = is_heading(line)
        if h is None:
            stack[-1].preamble.append(line)
            continue

        level, title = h
        # 弹出栈顶所有 level >= 当前 的块,找到当前块的父节点
        while len(stack) > 1 and stack[-1].level >= level:
            stack.pop()
        parent = stack[-1]
        node = Block(level, title)
        parent.children.append(node)
        stack.append(node)

    return root
