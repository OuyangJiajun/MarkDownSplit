from __future__ import annotations

import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlsplit

HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*$")
IMAGE_RE = re.compile(r"(!\[[^]]*\]\()([^\)]+)(\))")
INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


@dataclass
class Section:
    level: int
    title: str
    lines: list[str] = field(default_factory=list)
    children: list["Section"] = field(default_factory=list)

    @property
    def line_count(self) -> int:
        return len(self.lines) + sum(child.line_count for child in self.children)


def parse_markdown(lines: list[str]) -> tuple[list[str], list[Section]]:
    root: list[Section] = []
    preamble: list[str] = []
    stack: list[Section] = []
    for line in lines:
        match = HEADING_RE.match(line)
        if not match:
            (stack[-1].lines if stack else preamble).append(line)
            continue
        section = Section(len(match.group(1)), match.group(2).strip())
        while stack and stack[-1].level >= section.level:
            stack.pop()
        if stack:
            stack[-1].children.append(section)
        else:
            root.append(section)
        stack.append(section)
    return preamble, root


def safe_name(title: str, fallback: str = "untitled") -> str:
    name = INVALID_FILENAME.sub("_", title).strip(" .") or fallback
    return name[:100]


def promote_headings(lines: list[str]) -> list[str]:
    levels = [len(match.group(1)) for line in lines if (match := HEADING_RE.match(line))]
    if not levels:
        return lines
    shift = min(levels) - 1
    return [
        ("#" * max(1, len(match.group(1)) - shift) + line[len(match.group(1)):])
        if (match := HEADING_RE.match(line)) else line
        for line in lines
    ]


def _render(section: Section, inherited: list[str] | None = None) -> list[str]:
    content = list(inherited or []) + [f'{"#" * section.level} {section.title}\n'] + section.lines
    for child in section.children:
        content.extend(_render(child))
    return content


def _relative_image_path(raw: str) -> Path | None:
    target = raw.strip().split()[0].strip("<>")
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or Path(target).is_absolute() or target.startswith("#"):
        return None
    return Path(unquote(parsed.path))


def rewrite_images(lines: list[str], source_dir: Path, output_dir: Path) -> list[str]:
    assets = output_dir / "assets"
    rewritten: list[str] = []
    for line in lines:
        def replace(match: re.Match[str]) -> str:
            original = match.group(2)
            image_path = _relative_image_path(original)
            if image_path is None:
                return match.group(0)
            source = (source_dir / image_path).resolve()
            if not source.is_file():
                return match.group(0)
            assets.mkdir(parents=True, exist_ok=True)
            destination = assets / source.name
            if not destination.exists():
                shutil.copy2(source, destination)
            return f"{match.group(1)}{Path('assets', source.name).as_posix()}{match.group(3)}"
        rewritten.append(IMAGE_RE.sub(replace, line))
    return rewritten


def split_markdown(input_path: Path, output_dir: Path, threshold: int = 500) -> list[Path]:
    lines = input_path.read_text(encoding="utf-8").splitlines(keepends=True)
    preamble, sections = parse_markdown(lines)
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    def emit(section: Section, directory: Path, inherited: list[str] | None = None) -> None:
        children = section.children
        if section.line_count > threshold and children:
            directory.mkdir(parents=True, exist_ok=True)
            own = promote_headings(_render(section, inherited)[: len((inherited or [])) + 1 + len(section.lines)])
            if own[1:] and any(line.strip() for line in own[1:]):
                target = directory / f"{safe_name(section.title)}.md"
                target.write_text("".join(rewrite_images(own, input_path.parent, directory)), encoding="utf-8")
                written.append(target)
            for index, child in enumerate(children, 1):
                emit(child, directory, None)
            return
        target_dir = directory
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{safe_name(section.title)}.md"
        content = promote_headings(_render(section, inherited))
        target.write_text("".join(rewrite_images(content, input_path.parent, target_dir)), encoding="utf-8")
        written.append(target)

    for section in sections:
        emit(section, output_dir / safe_name(section.title))
    if preamble:
        target = output_dir / "index.md"
        target.write_text("".join(rewrite_images(preamble, input_path.parent, output_dir)), encoding="utf-8")
        written.insert(0, target)
    return written
