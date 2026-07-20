from pathlib import Path

from ruyi_docx import DocumentMetadata, DocumentSpec, Heading, ListBlock, Paragraph, TableBlock
from ruyi_docx.service import WordDocumentService


def main() -> None:
    output = Path(__file__).resolve().parent / "output" / "ruyi_docx_demo.docx"
    service = WordDocumentService()
    service.create(
        DocumentSpec(
            blocks=(
                Heading("Ruyi DOCX 能力报告", 1),
                Paragraph("该文档由 src/docx 中的确定性文档服务生成。"),
                Heading("已实现能力", 2),
                ListBlock(("专业排版与中文样式", "结构化文档编写", "跨 Run 文本修改", "校验与可选 PDF 渲染")),
                TableBlock((("模块", "状态"), ("Writer", "完成"), ("Editor", "完成"), ("Validator", "完成"))),
            ),
            metadata=DocumentMetadata(title="Ruyi DOCX 能力报告", author="RuyiDify"),
            header_text="Ruyi DOCX",
            footer_text="能力报告",
        ),
        output,
    )
    report = service.validate(output)
    print(f"output={output}")
    print(f"valid={report.valid}, paragraphs={report.paragraph_count}, tables={report.table_count}")


if __name__ == "__main__":
    main()
