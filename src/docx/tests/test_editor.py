from pathlib import Path

from docx import Document

from ruyi_docx import Heading, Paragraph, WordDocumentService


def _source_document(path: Path) -> None:
    document = Document()
    paragraph = document.add_paragraph()
    first = paragraph.add_run("跨 Run ")
    first.bold = True
    paragraph.add_run("查找替换")
    table = document.add_table(rows=1, cols=1)
    table.cell(0, 0).text = "表格旧内容"
    document.sections[0].header.paragraphs[0].text = "旧页眉"
    document.sections[0].footer.paragraphs[0].text = "旧页脚"
    document.add_paragraph("删除我")
    document.add_paragraph("设置为标题")
    document.save(path)


def test_replace_text_across_runs_tables_headers_and_footers(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    output = tmp_path / "replaced.docx"
    _source_document(source)

    result = WordDocumentService().replace(
        source,
        output,
        {
            "跨 Run 查找替换": "替换成功",
            "表格旧内容": "表格新内容",
            "旧页眉": "新页眉",
            "旧页脚": "新页脚",
        },
    )
    document = Document(output)

    assert result.changed_items == 4
    assert document.paragraphs[0].text == "替换成功"
    assert document.paragraphs[0].runs[0].bold is True
    assert document.tables[0].cell(0, 0).text == "表格新内容"
    assert document.sections[0].header.paragraphs[0].text == "新页眉"
    assert document.sections[0].footer.paragraphs[0].text == "新页脚"


def test_replace_text_does_not_loop_when_replacement_contains_needle(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    output = tmp_path / "replaced.docx"
    document = Document()
    document.add_paragraph("A A")
    document.save(source)

    result = WordDocumentService().replace(source, output, {"A": "A+"})

    assert result.changed_items == 2
    assert Document(output).paragraphs[0].text == "A+ A+"


def test_append_delete_and_apply_style(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    appended = tmp_path / "appended.docx"
    deleted = tmp_path / "deleted.docx"
    styled = tmp_path / "styled.docx"
    _source_document(source)
    service = WordDocumentService()

    append_result = service.append(source, appended, (Heading("新增章节", 1), Paragraph("新增正文")))
    delete_result = service.delete_paragraphs(appended, deleted, "删除我")
    style_result = service.apply_style(deleted, styled, "设置为标题", "Heading 2")
    document = Document(styled)

    assert append_result.changed_items == 2
    assert delete_result.changed_items == 1
    assert style_result.changed_items == 1
    assert "新增章节" in [paragraph.text for paragraph in document.paragraphs]
    assert "删除我" not in [paragraph.text for paragraph in document.paragraphs]
    target = next(paragraph for paragraph in document.paragraphs if paragraph.text == "设置为标题")
    assert target.style.name == "Heading 2"
