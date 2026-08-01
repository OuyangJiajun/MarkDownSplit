"""Command-line entry point for MarkdownSplit."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from .parser import parse_markdown
from .rewriter import rewrite
from .splitter import split_tree


def main(argv: list[str] | None = None) -> int:
    """Split one Markdown file and return a shell-friendly exit status."""
    parser = argparse.ArgumentParser(
        prog="markdownsplit",
        description="Split a large Markdown file into a heading-based directory tree.",
    )
    parser.add_argument("input", type=Path, help="input Markdown file")
    parser.add_argument("-o", "--output", type=Path, required=True, help="output directory")
    parser.add_argument(
        "--threshold",
        type=int,
        default=500,
        help="split blocks larger than this many lines (default: 500)",
    )
    parser.add_argument("--force", action="store_true", help="replace an existing output directory")
    args = parser.parse_args(argv)

    if not args.input.is_file():
        print(f"Error: input file does not exist: {args.input}", file=sys.stderr)
        return 1
    if args.threshold < 1:
        print("Error: --threshold must be positive.", file=sys.stderr)
        return 1
    if args.output.exists():
        if not args.force:
            print(f"Error: output directory already exists: {args.output} (use --force to replace it)", file=sys.stderr)
            return 1
        shutil.rmtree(args.output)

    source = args.input.resolve()
    output = args.output.resolve()
    root = parse_markdown(source.read_text(encoding="utf-8"))
    files = split_tree(root, args.threshold)
    written = [rewrite(file, str(output), str(source.parent)) for file in files]
    print(f"Wrote {len(written)} Markdown files to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
