# Ruyi DOCX

`src/docx` 是独立的 Word 文档自动化包，导入名为 `ruyi_docx`。它不会覆盖第三方 `python-docx` 使用的顶层包名 `docx`。

## 能力

- 使用强类型 Block 创建标题、段落、列表、表格、图片、分页、代码块、提示块、超链接和目录域。
- 支持 A4/横向页面、中文字体、标题层级、页眉、页脚和页码。
- 读取文档结构并提取纯文本。
- 跨 Run 替换正文、嵌套表格、页眉和页脚中的文本。
- 追加段落、删除段落和应用 Word 命名样式。
- 可选使用 `docxtpl` 渲染模板、使用 `docxcompose` 合并文档。
- 可选通过 LibreOffice Headless 渲染 PDF，渲染器不可用时返回明确错误。
- 校验 ZIP 完整性、必要 OOXML 部件和 `python-docx` 可读性。
- 提供路径受限的 MCP 适配器和 [`SKILL.md`](SKILL.md) AI 操作规范。

## 真实案例

[`examples/北科大2026/12_生成零基础Dify入门.py`](../../examples/北科大2026/12_生成零基础Dify入门.py) 使用同一份结构化课程数据生成 Markdown 和 DOCX，避免两种格式长期漂移。生成器还会维护项目文档库的导航、`deep_read_at` 和 `last_reviewed_at` 语义。

```powershell
python "examples\北科大2026\12_生成零基础Dify入门.py"
```

已验证产物包含 58 个段落、7 个表格、目录域和 7 个官方来源超链接。

## 开发验证

从源码仓库根目录运行：

```powershell
$env:PYTHONPATH=(Resolve-Path 'src\docx\src').Path
python -m pytest src/docx/tests -q
ruff format --check src/docx/src src/docx/tests src/docx/examples "examples/北科大2026/12_生成零基础Dify入门.py"
ruff check src/docx/src src/docx/tests src/docx/examples "examples/北科大2026/12_生成零基础Dify入门.py"
```

## 可选能力

核心包只依赖 `python-docx`。模板、合并和 MCP 依赖按需安装：

```powershell
pip install -e ".[templates,mcp,test]"
```

LibreOffice 不是 Python 依赖，需要由运行环境单独提供。未安装时，PDF 渲染会抛出 `RenderError`，不能据此报告视觉排版已经验证。
