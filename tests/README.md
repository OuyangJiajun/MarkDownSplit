# MarkdownSplit 工具

按标题结构拆分大 Markdown 文件。

## 用法

```bash
python -m markdownsplit big.md -o output/ --threshold 500 --force
```

参数:
- `input` 输入 md 文件
- `-o/--output` 输出根目录
- `--threshold` 行数阈值,超过且有子标题才继续向下拆分(默认 500)
- `--force` 输出目录已存在时先清空

## 拆分策略

详见 [plan](../.cursor/plans/markdownsplit_工具_0b88d090.plan.md)。
