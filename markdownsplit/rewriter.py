"""标题提升与图片复制/路径重写。

标题提升: 扫描文件内出现的最浅标题级别 min_level,把所有标题向上平移
  delta = min_level - 1,使文件从 H1 开始组织(L1 标题或无标题则不动)。

图片处理: 扫描 `![alt](path)` 与 `<img src="path">`,对相对路径图片:
  - 复制到该文件所在目录的 `assets/` 子目录(按需创建)。
  - 同名冲突时加数字后缀。
  - 把引用路径重写为 `assets/<文件名>`。
  - 代码围栏内的图片语法不重写。
"""

import os
import shutil

from .utils import (
    HEADING_RE,
    MD_IMAGE_RE,
    HTML_IMAGE_RE,
    is_heading,
    is_relative_path,
    ensure_dir,
)


def _find_min_heading_level(lines) -> int:
    """返回文件内最浅的标题级别(忽略代码围栏内)。无标题返回 0。"""
    min_level = 0
    in_fence = False
    fence_marker = ""
    for line in lines:
        stripped = line.lstrip()
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = True
                fence_marker = "```" if stripped.startswith("```") else "~~~"
                continue
        else:
            if stripped.startswith(fence_marker):
                in_fence = False
                fence_marker = ""
            continue
        h = is_heading(line)
        if h is not None:
            level = h[0]
            if min_level == 0 or level < min_level:
                min_level = level
    return min_level


def _promote_headings(lines) -> list:
    """把文件内标题向上平移,使最浅标题成为 H1。"""
    min_level = _find_min_heading_level(lines)
    if min_level <= 1:
        return lines
    delta = min_level - 1
    out = []
    in_fence = False
    fence_marker = ""
    for line in lines:
        stripped = line.lstrip()
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = True
                fence_marker = "```" if stripped.startswith("```") else "~~~"
                out.append(line)
                continue
        else:
            out.append(line)
            if stripped.startswith(fence_marker):
                in_fence = False
                fence_marker = ""
            continue
        m = HEADING_RE.match(line)
        if m:
            hashes = m.group(1)
            rest = line[len(hashes):]
            new_level = max(1, len(hashes) - delta)
            out.append("#" * new_level + rest)
        else:
            out.append(line)
    return out


def _rewrite_images(lines, source_md_dir: str, file_dir_abs: str) -> list:
    """复制相对路径图片到 file_dir_abs/assets,并重写引用路径。"""
    assets_dir = os.path.join(file_dir_abs, "assets")
    # basename -> 已使用的目标文件名(检测冲突)
    used_names = {}
    # 源绝对路径 -> 目标文件名(本文件内去重复制)
    copied = {}

    def resolve_and_copy(path: str) -> str:
        """返回重写后的相对路径(相对 file_dir),或 None 表示不处理。"""
        if not is_relative_path(path):
            return None
        src = os.path.normpath(os.path.join(source_md_dir, path))
        if not os.path.isfile(src):
            return None
        if src in copied:
            return os.path.join("assets", copied[src])
        base = os.path.basename(src)
        # 处理同名冲突
        target_name = base
        if target_name in used_names:
            name, ext = os.path.splitext(base)
            i = 1
            while f"{name}_{i}{ext}" in used_names:
                i += 1
            target_name = f"{name}_{i}{ext}"
        ensure_dir(assets_dir)
        shutil.copy2(src, os.path.join(assets_dir, target_name))
        used_names[target_name] = src
        copied[src] = target_name
        return os.path.join("assets", target_name)

    out = []
    in_fence = False
    fence_marker = ""
    for line in lines:
        stripped = line.lstrip()
        if not in_fence:
            if stripped.startswith("```") or stripped.startswith("~~~"):
                in_fence = True
                fence_marker = "```" if stripped.startswith("```") else "~~~"
                out.append(line)
                continue
        else:
            out.append(line)
            if stripped.startswith(fence_marker):
                in_fence = False
                fence_marker = ""
            continue

        def _md_repl(m):
            alt, path = m.group(1), m.group(2)
            new_path = resolve_and_copy(path)
            if new_path is None:
                return m.group(0)
            return f"![{alt}]({new_path})"

        def _html_repl(m):
            path = m.group(1)
            new_path = resolve_and_copy(path)
            if new_path is None:
                return m.group(0)
            return m.group(0).replace(path, new_path, 1)

        new_line = MD_IMAGE_RE.sub(_md_repl, line)
        new_line = HTML_IMAGE_RE.sub(_html_repl, new_line)
        out.append(new_line)
    return out


def rewrite(of, output_root: str, source_md_dir: str) -> str:
    """对一个 OutputFile 做标题提升 + 图片处理,并写入磁盘。返回写入的绝对路径。"""
    lines = _promote_headings(of.lines)
    file_dir_abs = os.path.join(output_root, *of.dir_segments) if of.dir_segments else output_root
    lines = _rewrite_images(lines, source_md_dir, file_dir_abs)
    ensure_dir(file_dir_abs)
    target = os.path.join(file_dir_abs, of.filename)
    with open(target, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        if lines:
            f.write("\n")
    return target
