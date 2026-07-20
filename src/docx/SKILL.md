---
name: ruyi-docx
description: Create, read, format, modify, validate, merge, and render Microsoft Word DOCX documents through the local ruyi_docx package.
---

# Ruyi DOCX

Use this skill for deterministic Word document work. Prefer the typed Python service for repeatable pipelines and the MCP adapter for interactive AI use.

## Safety

- Never overwrite an input document unless the user explicitly requests it.
- Keep all MCP paths relative to its configured allowed root.
- Treat external DOCX files as untrusted ZIP packages; validate before editing.
- Do not execute macros or embedded objects.
- Render and inspect important documents before reporting that layout is correct.

## Workflow

1. Validate and read an existing document before editing it.
2. Create a new output path for modifications.
3. Use typed blocks for headings, paragraphs, lists, tables, images, and page breaks.
4. Validate the result after creation or editing.
5. When LibreOffice is available, render to PDF and visually inspect representative pages.

## Python API

```python
from pathlib import Path

from ruyi_docx import DocumentMetadata, DocumentSpec, Heading, Paragraph
from ruyi_docx.service import WordDocumentService

service = WordDocumentService()
service.create(
    DocumentSpec(
        blocks=(Heading("Report", 1), Paragraph("Content")),
        metadata=DocumentMetadata(title="Report"),
    ),
    Path("report.docx"),
)
```

## MCP

Run the server with an explicit filesystem boundary:

```powershell
python -m ruyi_docx.mcp_server --root D:\documents
```

Available tools: create document, read document, replace text, append paragraphs, validate document, and render PDF.

