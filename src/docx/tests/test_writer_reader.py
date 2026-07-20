from pathlib import Path

from ruyi_docx import (
    Alignment,
    Callout,
    CodeBlock,
    DocumentMetadata,
    DocumentSpec,
    Heading,
    Hyperlink,
    ListBlock,
    PageBreak,
    Paragraph,
    TableBlock,
    TableOfContents,
    WordDocumentService,
)


def test_create_read_and_validate_document(tmp_path: Path) -> None:
    output = tmp_path / "report.docx"
    service = WordDocumentService()
    spec = DocumentSpec(
        blocks=(
            Heading("项目报告", level=1),
            Paragraph("这是一份中文测试文档。", alignment=Alignment.JUSTIFY),
            ListBlock(("第一项", "第二项")),
            TableBlock((("字段", "内容"), ("状态", "完成")), column_widths_cm=(4.0, 8.0)),
            PageBreak(),
            Heading("结论", level=2),
            Paragraph("能力验证通过。", bold=True),
            CodeBlock("curl http://localhost/v1/datasets", language="bash"),
            Callout("注意", "API Key 只保存在本地安全文件中。"),
            Hyperlink("Dify 官方文档", "https://docs.dify.ai/"),
            TableOfContents(),
        ),
        metadata=DocumentMetadata(title="项目报告", author="RuyiDify", keywords=("DOCX", "测试")),
        header_text="RuyiDify 文档能力",
        footer_text="项目报告",
    )

    result = service.create(spec, output)
    report = service.validate(result)
    snapshot = service.read(result)

    assert result == output.resolve()
    assert report.valid is True
    assert report.paragraph_count >= 10
    assert report.table_count == 2
    assert snapshot.metadata.title == "项目报告"
    assert snapshot.metadata.keywords == ("DOCX", "测试")
    assert snapshot.tables[0].rows[1] == ("状态", "完成")
    assert "能力验证通过" in service.extract_text(result)


def test_invalid_document_reports_error(tmp_path: Path) -> None:
    path = tmp_path / "invalid.docx"
    path.write_text("not a docx", encoding="utf-8")

    report = WordDocumentService().validate(path)

    assert report.valid is False
    assert "ZIP-based DOCX" in report.errors[0]
