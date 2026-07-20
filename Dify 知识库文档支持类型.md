---
title: Dify 知识库文档支持类型
updated: 2026-07-18
scope: RuyiDify v0.1.0 / Dify 1.15.0
status: verified-from-code
---

# Dify 知识库文档支持类型

## 1. 结论

在本项目的默认 `dify` ETL 配置下，Dify 知识库支持 **13 种文件扩展名**，分别是：

`txt`、`markdown`、`md`、`mdx`、`pdf`、`html`、`htm`、`xlsx`、`xls`、`docx`、`csv`、`vtt`、`properties`。

这 13 种扩展名可归纳为 **8 类内容格式**：纯文本/配置、Markdown、PDF、HTML、Excel、Word、CSV 和 WebVTT 字幕。

日常最主流、最值得优先掌握的类型是：

- PDF：报告、制度、论文和说明书。
- DOCX：Word 文档、方案和合同。
- XLSX/XLS：Excel 表格和结构化业务数据。
- CSV：轻量表格和数据导出文件。
- TXT：纯文本资料。
- Markdown（MD/MDX/MARKDOWN）：技术文档、接口文档和项目说明。
- HTML/HTM：网页或导出的网页正文。

`VTT` 和 `PROPERTIES` 属于较专门的文本格式，分别常用于字幕/转写文本和配置或国际化资源。

## 2. 默认模式完整清单

| 类别 | 扩展名 | 常见内容 | 当前默认模式 |
|---|---|---|---|
| 纯文本 | `.txt` | 笔记、日志、转写文本 | 支持 |
| 配置文本 | `.properties` | Java 配置、国际化资源 | 支持 |
| Markdown | `.markdown`、`.md`、`.mdx` | 技术文档、知识文章 | 支持 |
| PDF | `.pdf` | 报告、论文、说明书 | 支持 |
| HTML | `.html`、`.htm` | 网页正文、离线网页 | 支持 |
| Excel | `.xlsx`、`.xls` | 工作簿、业务表格 | 支持 |
| Word | `.docx` | Office 文档 | 支持 |
| CSV | `.csv` | 逗号分隔表格 | 支持 |
| WebVTT | `.vtt` | 字幕、音视频转写 | 支持 |

计数规则是按服务端允许的文件扩展名计数，因此 Markdown 和 HTML 的别名会分别计入。若按内容格式族合并别名，则是 8 类。

## 3. Unstructured 可选模式

当部署把 `ETL_TYPE` 改为 `Unstructured` 时，基础允许列表变为 **19 种扩展名**：

`txt`、`markdown`、`md`、`mdx`、`pdf`、`html`、`htm`、`xlsx`、`xls`、`vtt`、`properties`、`doc`、`docx`、`csv`、`eml`、`msg`、`pptx`、`xml`、`epub`。

相较默认模式，新增或开放的典型格式包括：

- `.doc`：旧版 Word 文档。
- `.eml`、`.msg`：电子邮件文件。
- `.pptx`：PowerPoint 演示文稿。
- `.xml`：XML 数据文档。
- `.epub`：电子书。

当 `Unstructured` 模式同时配置了 `UNSTRUCTURED_API_URL` 时，还会额外允许 `.ppt`，此时总数为 **20 种扩展名**。

这部分是可选部署能力，不应与本项目默认支持数量混为一谈。

## 4. 上传和解析流程

1. 前端调用支持类型接口获取 `allowed_extensions`，再生成文件选择器允许列表。
2. 上传时，后端 `FileService` 使用 `DOCUMENT_EXTENSIONS` 再次校验扩展名；前端校验不能绕过服务端限制。
3. 文件保存后，知识库异步任务按照扩展名选择提取器。
4. 提取出的文本经过清洗、分段、Embedding 和向量索引后才能参与语义检索。

主要提取器映射包括：

| 文件类型 | 主要提取器 |
|---|---|
| PDF | `PdfExtractor` |
| DOCX | `WordExtractor` |
| XLS/XLSX | `ExcelExtractor` |
| Markdown | `MarkdownExtractor` |
| HTML | `HtmlExtractor` |
| CSV | `CSVExtractor` |
| 其他默认文本格式 | `TextExtractor` |
| 邮件、PPT/PPTX、XML、EPUB | 对应的 Unstructured 提取器 |

## 5. 使用注意事项

- “扩展名被允许”不代表任何文件都能得到高质量解析；扫描 PDF 可能需要 OCR，复杂表格和演示文稿也可能丢失版式信息。
- 同一格式的解析质量受文件结构、编码、图片比例和部署的 ETL 模式影响。
- 知识库上传接口的处理是异步的，上传成功后仍需等待索引状态成为 `completed`。
- 运行时真实清单应以前端调用的 `/files/support-type` 返回结果为准，因为它直接来自当前后端的 `DOCUMENT_EXTENSIONS`。
- API 文档中的“PDF、TXT、DOCX 等常见格式”只是示例，不是完整清单。

## 6. 代码依据

- `api/constants/__init__.py`：默认与 Unstructured 两套扩展名集合，以及 `DOCUMENT_EXTENSIONS` 的生成规则。
- `api/services/file_service.py`：知识库上传的服务端扩展名校验。
- `api/core/rag/extractor/extract_processor.py`：扩展名到具体提取器的映射。
- `api/controllers/console/files.py`：`/files/support-type` 返回当前允许扩展名。
- `web/app/components/datasets/create/file-uploader/hooks/use-file-upload.ts`：前端动态读取后端允许列表。
- `api/configs/feature/__init__.py`：`ETL_TYPE` 默认值为 `dify`。
- `docker/envs/core-services/shared.env.example`：Docker 示例默认 `ETL_TYPE=dify`。

## 7. 可直接用于知识库问答的答案

问：Dify 支持多少种文档类型，主流类型有哪些？

答：按本项目默认 `dify` ETL 的服务端扩展名清单统计，Dify 知识库支持 **13 种文件扩展名**，可归纳为 **8 类内容格式**。主流类型包括 PDF、DOCX、XLSX/XLS、CSV、TXT、Markdown（MD/MDX/MARKDOWN）和 HTML/HTM；另外还支持 VTT 与 PROPERTIES。可选的 Unstructured 模式支持 19 种，配置 Unstructured API 后可达到 20 种。

