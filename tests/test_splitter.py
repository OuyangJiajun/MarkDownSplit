"""拆分流程测试: 用样例 md 验证输出目录结构、标题提升、图片复制。"""

import os
import shutil
import textwrap

from markdownsplit.parser import parse_markdown
from markdownsplit.splitter import split_tree
from markdownsplit.rewriter import rewrite
from markdownsplit.cli import main


SAMPLE_MD = textwrap.dedent("""\
    # 概述

    这是文档概述。

    ![概览图](images/overview.png)

    ## 背景

    一些背景内容。

    # 架构设计

    架构设计总览段落。

    ![架构图](images/arch.png)

    ## 模块A

    模块A 的说明。

    ### 子模块A1

    子模块A1 细节。

    ### 子模块A2

    子模块A2 细节。

    ## 模块B

    模块B 的说明。

    ## 模块C

    模块C 的说明。

    ### 子模块C1

    子模块C1 细节。

    # 部署

    部署说明。

    ## 线上部署

    线上部署细节。

    ## 测试部署

    测试部署细节。
""")


def _make_png(path):
    """写一个最小合法 PNG 占位文件。"""
    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
        "890000000d49444154789c63000100000005000100"
        "0e9e0a0a0000000049454e44ae426082"
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)


def _setup_workspace(tmp):
    src_dir = os.path.join(tmp, "src")
    os.makedirs(src_dir)
    md_path = os.path.join(src_dir, "sample.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(SAMPLE_MD)
    _make_png(os.path.join(src_dir, "images", "overview.png"))
    _make_png(os.path.join(src_dir, "images", "arch.png"))
    return md_path


def test_split_structure_and_promotion(tmp_path):
    md_path = _setup_workspace(str(tmp_path))
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()
    source_md_dir = os.path.dirname(md_path)
    root = parse_markdown(text)
    # 用很小阈值强制深度拆分
    files = split_tree(root, threshold=3)
    out_root = os.path.join(str(tmp_path), "out")

    paths = []
    for of in files:
        paths.append(rewrite(of, out_root, source_md_dir))

    rel = sorted(os.path.relpath(p, out_root).replace(os.sep, "/") for p in paths)
    # 三个 H1 → 三个目录
    assert "01-概述/概述.md" in rel
    assert "02-架构设计/架构设计.md" in rel or "02-架构设计/00-架构设计.md" in rel
    assert "03-部署/部署.md" in rel
    # 架构设计被拆分,含模块A/B/C
    assert any("02-架构设计/01-模块A.md" == r for r in rel)
    assert any("02-架构设计/02-模块B.md" == r for r in rel)
    assert any("02-架构设计/03-模块C.md" == r for r in rel)
    # 模块A 含子模块,被拆分为目录
    assert any(r.startswith("02-架构设计/01-模块A/") for r in rel)


def test_image_copied_and_path_rewritten(tmp_path):
    md_path = _setup_workspace(str(tmp_path))
    source_md_dir = os.path.dirname(md_path)
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()
    root = parse_markdown(text)
    files = split_tree(root, threshold=3)
    out_root = os.path.join(str(tmp_path), "out")
    for of in files:
        rewrite(of, out_root, source_md_dir)

    # 概述文件应含 assets/overview.png 并复制成功
    overview = os.path.join(out_root, "01-概述", "概述.md")
    content = open(overview, encoding="utf-8").read()
    assert "assets/overview.png" in content
    assert os.path.isfile(os.path.join(out_root, "01-概述", "assets", "overview.png"))
    arch = os.path.join(out_root, "02-架构设计", "00-架构设计.md")
    if not os.path.isfile(arch):
        arch = os.path.join(out_root, "02-架构设计", "架构设计.md")
    content = open(arch, encoding="utf-8").read()
    assert "assets/arch.png" in content
    assert os.path.isfile(os.path.join(os.path.dirname(arch), "assets", "arch.png"))


def test_title_promotion(tmp_path):
    md_path = _setup_workspace(str(tmp_path))
    source_md_dir = os.path.dirname(md_path)
    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()
    root = parse_markdown(text)
    files = split_tree(root, threshold=3)
    out_root = os.path.join(str(tmp_path), "out")
    for of in files:
        rewrite(of, out_root, source_md_dir)

    # 模块A 被拆分,其子模块A1 文件原为 H3,应提升为 H1
    a1_candidates = []
    for of in files:
        if of.filename.startswith("子模块A1"):
            rewrite(of, out_root, source_md_dir)
    for dirpath, _, fns in os.walk(out_root):
        for fn in fns:
            if fn.startswith("子模块A1"):
                a1_candidates.append(os.path.join(dirpath, fn))
    assert a1_candidates, "未找到子模块A1 文件"
    content = open(a1_candidates[0], encoding="utf-8").read()
    # 原为 H3 的「子模块A1」应提升为 H1
    assert content.lstrip().startswith("# 子模块A1")
    assert not content.lstrip().startswith("### 子模块A1")


def test_cli_force(tmp_path):
    md_path = _setup_workspace(str(tmp_path))
    out_root = os.path.join(str(tmp_path), "out")
    rc = main([md_path, "-o", out_root, "--threshold", "3"])
    assert rc == 0
    # 再次不传 --force 应失败
    rc2 = main([md_path, "-o", out_root, "--threshold", "3"])
    assert rc2 == 1
    # 传 --force 应成功
    rc3 = main([md_path, "-o", out_root, "--threshold", "3", "--force"])
    assert rc3 == 0


def test_no_headings(tmp_path):
    src_dir = os.path.join(str(tmp_path), "src")
    os.makedirs(src_dir)
    md_path = os.path.join(src_dir, "n.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("只有正文,没有标题。\n")
    out_root = os.path.join(str(tmp_path), "out")
    rc = main([md_path, "-o", out_root, "--threshold", "3", "--force"])
    assert rc == 0
    # 前置内容写入 00-index.md
    idx = os.path.join(out_root, "00-index.md")
    assert os.path.isfile(idx)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
