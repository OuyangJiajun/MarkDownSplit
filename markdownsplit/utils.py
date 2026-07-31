"""通用工具: 文件名清理、路径判别、标题识别、行数统计。"""

import os
import re

# 标题行正则: 形如 "# 标题" 到 "###### 标题"。允许末尾的空白。
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
# 图片引用: ![alt](path)  与  <img ... src="path" ...>
MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HTML_IMAGE_RE = re.compile(r"<img\s[^>]*?src\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)

# 文件名中需要清理的非法字符(Windows / Unix 通用)
ILLEGAL_FILENAME_CHARS = re.compile(r'[\\/:*?\"<>|]')


def is_heading(line: str):
    """判断一行是否为 ATX 标题。返回 (级别int, 标题文本) 或 None。

    跳过代码块内的标题行由调用方负责(这里不做上下文判断)。
    """
    m = HEADING_RE.match(line)
    if not m:
        return None
    level = len(m.group(1))
    text = m.group(2).strip()
    # 去掉末尾的 # 闭合(如 "## 标题 ##")
    text = re.sub(r"\s+#+$", "", text).strip()
    if not text:
        return None
    return level, text


def sanitize_filename(name: str, max_len: int = 80) -> str:
    """把标题文本转为合法的文件/目录名。"""
    name = name.strip()
    name = ILLEGAL_FILENAME_CHARS.sub("_", name)
    name = re.sub(r"\s+", " ", name).strip()
    if not name:
        name = "untitled"
    if len(name) > max_len:
        name = name[:max_len].rstrip()
    return name


def is_relative_path(path: str) -> bool:
    """判断是否为相对路径(需要复制/重写的对象)。"""
    if not path:
        return False
    # 带协议的(http://, https://, ftp:// 等)视为外部
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://", path):
        return False
    # 绝对路径: Windows 盘符或 Unix /
    if re.match(r"^[A-Za-z]:[\\/]", path) or path.startswith("/"):
        return False
    # 数据 URI
    if path.startswith("data:"):
        return False
    return True


def count_lines(lines) -> int:
    """统计行数。lines 为 list[str] 或任何可迭代对象。"""
    return sum(1 for _ in lines)


def ensure_dir(path: str) -> None:
    """确保目录存在。"""
    os.makedirs(path, exist_ok=True)
