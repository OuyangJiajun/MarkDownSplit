"""拆分算法: 把 Block 树转换为输出文件布局。

输出布局规则:
  - 文档根的前置内容(首个 H1 之前) → 输出根目录下的 `00-index.md`。
  - 每个 H1 块 → 输出根目录下的一个目录 `NN-<标题>`。
      * 若该 H1 块「需要拆分」(有子标题且总行数 > 阈值):
          - H1 的前置内容 → 目录内 `00-<标题>.md`(无前置内容则跳过)。
          - 各子块递归处理。
      * 否则(无子标题,或总行数 ≤ 阈值):
          - 整个 H1 块(含子孙)内联写入目录内 `<标题>.md`。
  - 更深层级块(L>=2):
      * 需要拆分(有子标题且总行数 > 阈值) → 子目录 `NN-<标题>` + 前置文件 + 递归。
      * 否则 → 单文件 `NN-<标题>.md`,整块内联。

所有同级文件/目录按出现顺序加 `NN-` 前缀(01、02、...)以保证目录排序与文档顺序一致。
"""

from .parser import Block
from .utils import sanitize_filename


class OutputFile:
    """一个待写出的拆分文件。"""

    def __init__(self, dir_segments, filename: str, lines: list):
        # dir_segments: list[str], 相对输出根的目录段(可为空 list 表示输出根)
        self.dir_segments = list(dir_segments)
        self.filename = filename
        self.lines = lines          # 原始内容行(未经标题提升/图片重写)

    @property
    def relpath(self) -> str:
        import os
        return os.path.join(*self.dir_segments, self.filename) if self.dir_segments else self.filename


def _should_split(block: Block, threshold: int) -> bool:
    """块是否需要拆分为目录: 有子标题且总行数超过阈值。"""
    return bool(block.children) and block.total_lines() > threshold


def _whole_block_lines(block: Block) -> list:
    """把整个块(含子孙)内联展开为行列表,保留原标题层级。"""
    lines = block.own_lines()
    for child in block.children:
        lines.extend(_whole_block_lines(child))
    return lines


def _emit_subblock(block: Block, base_dir, threshold: int, index: int, out: list) -> None:
    """处理 L>=2 的子块: 拆分→目录,否则→单文件。"""
    num = f"{index:02d}"
    safe = sanitize_filename(block.title)
    if _should_split(block, threshold):
        dir_name = f"{num}-{safe}"
        sub_dir = base_dir + [dir_name]
        if block.preamble:
            # 前置文件: 标题行 + 前置内容
            out.append(OutputFile(sub_dir, f"00-{safe}.md", block.own_lines()))
        for j, child in enumerate(block.children, 1):
            _emit_subblock(child, sub_dir, threshold, j, out)
    else:
        out.append(OutputFile(base_dir, f"{num}-{safe}.md", _whole_block_lines(block)))


def split_tree(root: Block, threshold: int) -> list:
    """把根 Block 树拆分为 OutputFile 列表。"""
    out: list = []
    # 文档前置内容(首个 H1 之前)
    if root.preamble:
        # 去除纯空白尾部
        preamble = root.preamble[:]
        while preamble and preamble[-1].strip() == "":
            preamble.pop()
        if preamble:
            out.append(OutputFile([], "00-index.md", preamble))
    # 各 H1 块 → 目录
    for i, h1 in enumerate(root.children, 1):
        num = f"{i:02d}"
        safe = sanitize_filename(h1.title)
        dir_name = f"{num}-{safe}"
        h1_dir = [dir_name]
        if _should_split(h1, threshold):
            if h1.preamble:
                out.append(OutputFile(h1_dir, f"00-{safe}.md", h1.own_lines()))
            for j, child in enumerate(h1.children, 1):
                _emit_subblock(child, h1_dir, threshold, j, out)
        else:
            out.append(OutputFile(h1_dir, f"{safe}.md", _whole_block_lines(h1)))
    return out
