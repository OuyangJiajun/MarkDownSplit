"""命令行入口: markdownsplit <input.md> -o <output_dir> [--threshold N] [--force]"""

import argparse
import os
import sys
import shutil

from .parser import parse_markdown
from .splitter import split_tree
from .rewriter import rewrite


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="markdownsplit",
        description="把大 Markdown 文件按标题结构拆分到目录树中的多个小文件。",
    )
    ap.add_argument("input", help="输入 Markdown 文件路径")
    ap.add_argument("-o", "--output", required=True, help="输出根目录路径")
    ap.add_argument("--threshold", type=int, default=500,
                    help="行数阈值,超过且有子标题才继续向下拆分(默认 500)")
    ap.add_argument("--force", action="store_true",
                    help="输出目录已存在时先清空再写入")
    args = ap.parse_args(argv)

    src = os.path.abspath(args.input)
    out_root = os.path.abspath(args.output)

    if not os.path.isfile(src):
        print(f"错误: 输入文件不存在: {src}", file=sys.stderr)
        return 1

    if os.path.exists(out_root):
        if not args.force:
            print(f"错误: 输出目录已存在: {out_root}\n使用 --force 覆盖。", file=sys.stderr)
            return 1
        shutil.rmtree(out_root)

    with open(src, "r", encoding="utf-8") as f:
        text = f.read()
    source_md_dir = os.path.dirname(src)

    root = parse_markdown(text)
    files = split_tree(root, args.threshold)

    if not files:
        print("警告: 未生成任何拆分文件(文档可能没有任何标题)。", file=sys.stderr)
        return 0

    written = []
    for of in files:
        path = rewrite(of, out_root, source_md_dir)
        written.append(path)

    print(f"完成: 共拆分 {len(written)} 个文件到 {out_root}")
    for p in written:
        print(f"  - {os.path.relpath(p, out_root)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
