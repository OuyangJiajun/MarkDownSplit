# MarkdownSplit

将一个大型 Markdown 文档按标题层级拆分为可独立阅读的小文档，并把本地图片复制到对应输出目录。

## 使用方式

项目只依赖 Python 标准库。运行：

```powershell
python -m markdownsplit .\tests\test.md -o .\output --threshold 300
```

若输出目录已存在，显式传入 `--force` 后会先删除原目录再重新生成：

```powershell
python -m markdownsplit .\tests\test.md -o .\output --threshold 300 --force
```

参数说明：

- `input`：要拆分的 Markdown 文件。
- `-o` / `--output`：生成目录。
- `--threshold`：一个标题块总行数超过此值且还包含子标题时，继续向下拆分；默认 `500`。
- `--force`：覆盖已有输出目录。

## 拆分规则

1. 文档首先解析为标题树（H1–H6）。代码围栏中的 `#` 不视为标题。
2. 每个 H1 对应一个以标题命名的目录，例如 `基础/`；文件和目录均不添加顺序前缀。
3. 一个标题块同时具有子标题且总行数超过 `threshold` 时，建立子目录并递归处理；否则整个块写入一个 Markdown 文件。这样短小章节不会被过度切碎。
4. 被拆出的文件会将其最浅标题提升为 H1，并同步调整更深层标题，保证单独打开仍有正确层级。
5. 第一个 H1 之前的正文会写入输出根目录的 `index.md`。

例如，较大的“架构设计”章节可能生成：

```text
output/
├─ 概览/
│  └─ 概览.md
└─ 架构设计/
   ├─ 架构设计.md
   ├─ 模块A/
   │  ├─ 模块A.md
   │  ├─ 子模块A1.md
   │  └─ 子模块A2.md
   └─ 模块B.md
```

`架构设计.md` 仅在该标题下、子标题前确实有正文时生成。

## 图片与资源

工具会识别 Markdown 图片 `![说明](relative/path.png)` 和 HTML 图片 `<img src="relative/path.png">`。

- 相对于原 Markdown 的本地图片会复制到输出文件同级的 `assets/`；引用改写成 `assets/文件名.png`。
- 外部 URL、绝对路径、数据 URI 和锚点不会被改写。
- 同一输出目录中遇到同名但内容不同的图片时，后来的文件会自动命名为 `name_1.png`、`name_2.png`，不会覆盖先前资源。
- 代码围栏内的图片语法保持原样。

仓库中的 `tests/test.md` 和 `tests/test_assets/` 是一份较大的真实测试样例，可直接用于上述命令。

## 开发与测试

```powershell
python -m pytest -q
```

现有测试覆盖标题提升、递归拆分、图片复制与 CLI 覆盖行为。
