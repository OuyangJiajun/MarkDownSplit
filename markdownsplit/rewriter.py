"""Heading promotion and local image copying for generated Markdown files."""

from __future__ import annotations

import filecmp
import os
import shutil

from .utils import HEADING_RE, HTML_IMAGE_RE, MD_IMAGE_RE, ensure_dir, is_heading, is_relative_path


def _find_min_heading_level(lines: list[str]) -> int:
    """Find the shallowest heading outside fenced code blocks."""
    min_level = 0
    in_fence = False
    marker = ""
    for line in lines:
        stripped = line.lstrip()
        if not in_fence and (stripped.startswith("```") or stripped.startswith("~~~")):
            in_fence = True
            marker = stripped[:3]
            continue
        if in_fence:
            if stripped.startswith(marker):
                in_fence = False
            continue
        heading = is_heading(line)
        if heading and (min_level == 0 or heading[0] < min_level):
            min_level = heading[0]
    return min_level


def _promote_headings(lines: list[str]) -> list[str]:
    """Make the shallowest heading H1, preserving relative heading depth."""
    minimum = _find_min_heading_level(lines)
    if minimum <= 1:
        return lines
    delta = minimum - 1
    result: list[str] = []
    in_fence = False
    marker = ""
    for line in lines:
        stripped = line.lstrip()
        if not in_fence and (stripped.startswith("```") or stripped.startswith("~~~")):
            in_fence = True
            marker = stripped[:3]
            result.append(line)
            continue
        if in_fence:
            result.append(line)
            if stripped.startswith(marker):
                in_fence = False
            continue
        match = HEADING_RE.match(line)
        if match:
            hashes = match.group(1)
            result.append("#" * max(1, len(hashes) - delta) + line[len(hashes):])
        else:
            result.append(line)
    return result


def _asset_name(source: str, assets_dir: str) -> str:
    """Choose a non-conflicting asset name, reusing identical existing files."""
    base = os.path.basename(source)
    stem, suffix = os.path.splitext(base)
    candidate = base
    counter = 1
    while True:
        destination = os.path.join(assets_dir, candidate)
        if not os.path.exists(destination) or filecmp.cmp(source, destination, shallow=False):
            return candidate
        candidate = f"{stem}_{counter}{suffix}"
        counter += 1


def _rewrite_images(lines: list[str], source_md_dir: str, file_dir: str) -> list[str]:
    """Copy relative image files into ``assets`` and rewrite their references."""
    assets_dir = os.path.join(file_dir, "assets")
    copied: dict[str, str] = {}

    def copy_and_rewrite(path: str) -> str | None:
        if not is_relative_path(path):
            return None
        source = os.path.normpath(os.path.join(source_md_dir, path))
        if not os.path.isfile(source):
            return None
        if source not in copied:
            ensure_dir(assets_dir)
            target_name = _asset_name(source, assets_dir)
            destination = os.path.join(assets_dir, target_name)
            if not os.path.exists(destination):
                shutil.copy2(source, destination)
            copied[source] = target_name
        return f"assets/{copied[source]}"

    result: list[str] = []
    in_fence = False
    marker = ""
    for line in lines:
        stripped = line.lstrip()
        if not in_fence and (stripped.startswith("```") or stripped.startswith("~~~")):
            in_fence = True
            marker = stripped[:3]
            result.append(line)
            continue
        if in_fence:
            result.append(line)
            if stripped.startswith(marker):
                in_fence = False
            continue

        def markdown_replacement(match):
            target = copy_and_rewrite(match.group(2))
            # Replacing only the URL also preserves an optional Markdown title.
            return match.group(0) if target is None else match.group(0).replace(match.group(2), target, 1)

        def html_replacement(match):
            target = copy_and_rewrite(match.group(1))
            return match.group(0) if target is None else match.group(0).replace(match.group(1), target, 1)

        result.append(HTML_IMAGE_RE.sub(html_replacement, MD_IMAGE_RE.sub(markdown_replacement, line)))
    return result


def rewrite(output_file, output_root: str, source_md_dir: str) -> str:
    """Write one planned file after promoting headings and copying images."""
    file_dir = os.path.join(output_root, *output_file.dir_segments) if output_file.dir_segments else output_root
    lines = _rewrite_images(_promote_headings(output_file.lines), source_md_dir, file_dir)
    ensure_dir(file_dir)
    target = os.path.join(file_dir, output_file.filename)
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines))
        if lines:
            handle.write("\n")
    return target
