# markdownSplit

`markdownSplit` is a small command-line tool for splitting a large Markdown document into a structured directory tree based on heading hierarchy.

## Features

- Parse Markdown heading structure into nested sections
- Split large sections recursively using a configurable line threshold
- Preserve document preamble as `index.md`
- Promote headings so each generated file starts at a sensible level
- Copy local images into per-file `assets/` folders and rewrite references
- Skip fenced code blocks when detecting headings or rewriting images

## Installation

This project is designed to run directly from the source tree.

```bash
python -m markdownsplit --help
```

If you want to install it into your environment, use your preferred packaging workflow for this repository.

## Usage

Run the CLI with an input Markdown file and an output directory:

```bash
python -m markdownsplit input.md -o output
```

Useful options:

- `-o, --output` — output directory
- `--threshold` — split sections larger than this many lines; default is `500`
- `--force` — replace the output directory if it already exists

Example:

```bash
python -m markdownsplit docs/guide.md -o build/guide --threshold 300 --force
```

## Output structure

Given a document like this:

```markdown
Intro text

# Guide
Some intro text

## Setup
Setup details

## Usage
Usage details
```

The tool generates a structure similar to:

```text
output/
├─ index.md
└─ Guide/
   ├─ Guide.md
   ├─ Setup.md
   └─ Usage.md
```

If a generated file contains local image references, the referenced image files are copied into an `assets/` directory next to that file.

## Notes

- Heading names are sanitized to create valid file and directory names.
- Duplicate sibling headings are disambiguated with numeric suffixes.
- Only local relative image paths are copied; remote URLs are left unchanged.
- Fenced code blocks are ignored when detecting headings and rewriting images.

## Project layout

- `markdownsplit/cli.py` — command-line entry point
- `markdownsplit/parser.py` — Markdown heading tree parser
- `markdownsplit/splitter.py` — output file layout planner
- `markdownsplit/rewriter.py` — heading promotion and image copying
- `markdownsplit/utils.py` — shared helpers

## License

No license file is currently included.
