from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from markdownsplit.parser import parse_markdown
from markdownsplit.rewriter import rewrite
from markdownsplit.splitter import split_tree


class MarkdownSplitTests(unittest.TestCase):
    def test_parse_markdown_builds_heading_tree_and_ignores_fenced_code_headings(self) -> None:
        text = """Intro line

# Root
body

```python
## not a heading
```

## Child
child body
"""
        root = parse_markdown(text)

        self.assertEqual(root.preamble, ["Intro line", ""])
        self.assertEqual(len(root.children), 1)
        self.assertEqual(root.children[0].title, "Root")
        self.assertEqual(root.children[0].children[0].title, "Child")
        self.assertIn("## not a heading", root.children[0].preamble)

    def test_split_tree_creates_index_and_unique_names_for_duplicate_headings(self) -> None:
        text = """Preamble line

# Chapter
chapter body

## Section
section body

## Section
second section body
"""
        root = parse_markdown(text)
        files = split_tree(root, threshold=2)

        relpaths = [file.relpath.replace("\\", "/") for file in files]
        self.assertIn("index.md", relpaths)
        self.assertIn("Chapter/Chapter.md", relpaths)
        self.assertIn("Chapter/Section.md", relpaths)
        self.assertIn("Chapter/Section_2.md", relpaths)


    def test_rewrite_promotes_headings_and_copies_relative_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_dir = tmp_path / "source"
            output_dir = tmp_path / "output"
            source_dir.mkdir()
            output_dir.mkdir()

            image = source_dir / "pic.png"
            image.write_bytes(b"fake image data")

            class PlannedFile:
                def __init__(self) -> None:
                    self.dir_segments = ["Doc"]
                    self.filename = "Doc.md"
                    self.lines = ["## Child\n", "body\n", "![alt](pic.png)\n"]

            target = rewrite(PlannedFile(), str(output_dir), str(source_dir))

            self.assertTrue(Path(target).is_file())
            content = Path(target).read_text(encoding="utf-8")
            self.assertIn("# Child", content)
            self.assertIn("assets/pic.png", content)
            self.assertTrue((output_dir / "Doc" / "assets" / "pic.png").is_file())


if __name__ == "__main__":
    unittest.main()
