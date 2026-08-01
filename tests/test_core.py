from pathlib import Path

from markdownsplit.core import parse_markdown, promote_headings, split_markdown


def test_parse_and_promote() -> None:
    preamble, sections = parse_markdown(["### Topic\n", "text\n", "#### Detail\n"])
    assert not preamble
    assert sections[0].title == "Topic"
    assert promote_headings(["### Topic\n", "#### Detail\n"]) == ["# Topic\n", "## Detail\n"]


def test_split_and_copy_image(tmp_path: Path) -> None:
    image = tmp_path / "image.png"
    image.write_bytes(b"image")
    source = tmp_path / "source.md"
    source.write_text("# Guide\n\n![image](image.png)\n", encoding="utf-8")
    output = tmp_path / "out"
    written = split_markdown(source, output)
    assert len(written) == 1
    assert (output / "Guide" / "assets" / "image.png").is_file()
    assert "assets/image.png" in written[0].read_text(encoding="utf-8")
