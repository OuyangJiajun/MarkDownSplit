"""Turn a parsed Markdown heading tree into an output file layout.

Output names use the original heading text directly. Duplicate headings at the
same level are disambiguated with stable numeric suffixes so sibling documents
and directories do not overwrite one another.
"""

from __future__ import annotations

import os

from .parser import Block
from .utils import sanitize_filename


class OutputFile:
    """One planned Markdown file, relative to the selected output root."""

    def __init__(self, dir_segments: list[str], filename: str, lines: list[str]):
        self.dir_segments = list(dir_segments)
        self.filename = filename
        self.lines = lines

    @property
    def relpath(self) -> str:
        return os.path.join(*self.dir_segments, self.filename) if self.dir_segments else self.filename


def _should_split(block: Block, threshold: int) -> bool:
    return bool(block.children) and block.total_lines() > threshold


def _whole_block_lines(block: Block) -> list[str]:
    """Render a block and all descendants into one Markdown document."""
    lines = block.own_lines()
    for child in block.children:
        lines.extend(_whole_block_lines(child))
    return lines


def _unique_name(base: str, used: set[str]) -> str:
    candidate = base or "untitled"
    index = 2
    while candidate in used:
        candidate = f"{base}_{index}"
        index += 1
    used.add(candidate)
    return candidate


def _emit_subblock(block: Block, base_dir: list[str], threshold: int, out: list[OutputFile], used_names: set[str]) -> None:
    """Emit a non-H1 block, recursively creating directories when needed."""
    safe = _unique_name(sanitize_filename(block.title), used_names)
    if _should_split(block, threshold):
        sub_dir = base_dir + [safe]
        if block.preamble:
            out.append(OutputFile(sub_dir, f"{safe}.md", block.own_lines()))
        child_names: set[str] = set()
        for child in block.children:
            _emit_subblock(child, sub_dir, threshold, out, child_names)
    else:
        out.append(OutputFile(base_dir, f"{safe}.md", _whole_block_lines(block)))


def split_tree(root: Block, threshold: int) -> list[OutputFile]:
    """Plan output files for a parsed document without numeric prefixes."""
    out: list[OutputFile] = []
    if root.preamble:
        preamble = root.preamble[:]
        while preamble and not preamble[-1].strip():
            preamble.pop()
        if preamble:
            out.append(OutputFile([], "index.md", preamble))

    root_names: set[str] = set()
    for h1 in root.children:
        safe = _unique_name(sanitize_filename(h1.title), root_names)
        h1_dir = [safe]
        if _should_split(h1, threshold):
            if h1.preamble:
                out.append(OutputFile(h1_dir, f"{safe}.md", h1.own_lines()))
            child_names: set[str] = set()
            for child in h1.children:
                _emit_subblock(child, h1_dir, threshold, out, child_names)
        else:
            out.append(OutputFile(h1_dir, f"{safe}.md", _whole_block_lines(h1)))
    return out
