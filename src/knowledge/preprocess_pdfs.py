"""
============================================================
preprocess_pdfs.py
============================================================
文件路径：src/knowledge/preprocess_pdfs.py
用途：批量处理 PDF 文档，提取元数据（文档名、章节标题、页码）
      输出 JSON 元数据文件，供 Dify 上传时标注

依赖安装：
    pip install -r src/requirements.txt

使用方式（在项目根目录执行）：
    python src/knowledge/preprocess_pdfs.py --input_dir data/pdfs --output_dir data/metadata

与 PRD 4.2 节对照：
    ✅ 提取文档名、章节标题、页码
    ✅ 输出 JSON 元数据文件

注意：
    - 仅支持文字版 PDF（非扫描件）
    - 章节标题从 PDF 书签/大纲（outline）提取
    - 如 PDF 无书签，仅输出基本信息
============================================================
"""

import json
import argparse
from pathlib import Path
from datetime import datetime

try:
    import PyPDF2
except ImportError:
    print("=" * 60)
    print("错误：未安装 pypdf2")
    print("安装命令（在隔离 venv 中执行）：")
    print("  pip install pypdf2")
    print("=" * 60)
    raise


def extract_pdf_metadata(pdf_path: str) -> dict:
    """
    提取单个 PDF 的元数据

    参数：
        pdf_path: PDF 文件路径

    返回：
        包含元数据的字典
    """
    pdf_path = Path(pdf_path)
    metadata = {
        "file_name": pdf_path.name,
        "file_path": str(pdf_path),
        "file_size_mb": round(pdf_path.stat().st_size / (1024 * 1024), 2),
        "processed_at": datetime.now().isoformat(),
        "total_pages": 0,
        "chapters": [],
        "doc_info": {},
        "warnings": []
    }

    try:
        with open(pdf_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)

            # 1. 基本信息
            metadata["total_pages"] = len(reader.pages)

            # 2. 文档信息（标题、作者等）
            if reader.metadata:
                doc_info = {}
                if reader.metadata.title:
                    doc_info["title"] = str(reader.metadata.title)
                if reader.metadata.author:
                    doc_info["author"] = str(reader.metadata.author)
                if reader.metadata.subject:
                    doc_info["subject"] = str(reader.metadata.subject)
                if reader.metadata.creator:
                    doc_info["creator"] = str(reader.metadata.creator)
                metadata["doc_info"] = doc_info

            # 3. 提取章节标题（从 PDF 大纲/书签）
            chapters = extract_chapters_from_outline(reader)
            if chapters:
                metadata["chapters"] = chapters
            else:
                metadata["warnings"].append(
                    "PDF 无书签/大纲结构，未提取到章节标题。"
                    "建议在 Dify 中使用「通用」分段方式。"
                )

            # 4. 提取首页文本摘要（前 200 字符，供识别文档类型）
            if len(reader.pages) > 0:
                first_page_text = reader.pages[0].extract_text()
                if first_page_text:
                    metadata["first_page_preview"] = first_page_text[:200].replace("\n", " ").strip()
                else:
                    metadata["warnings"].append(
                        "首页无法提取文字，可能是扫描件 PDF。"
                        "请先用 OCR 工具处理。"
                    )

    except Exception as e:
        metadata["errors"] = [f"处理失败：{str(e)}"]

    return metadata


def extract_chapters_from_outline(reader: PyPDF2.PdfReader) -> list:
    """
    从 PDF 大纲（outline/bookmarks）提取章节标题和页码

    参数：
        reader: PyPDF2 PdfReader 对象

    返回：
        章节列表，每项包含 title, page, level
    """
    chapters = []

    def _walk_outline(outline_items, level=1):
        for item in outline_items:
            if isinstance(item, list):
                # 嵌套大纲（子章节）
                _walk_outline(item, level + 1)
            else:
                # 获取标题
                title = item.title if hasattr(item, "title") else str(item)

                # 获取页码（PyPDF2 的页码从 0 开始，+1 转为人类可读）
                try:
                    page_num = reader.get_destination_page_number(item) + 1
                except Exception:
                    page_num = None

                chapters.append({
                    "title": title,
                    "page": page_num,
                    "level": level
                })

    try:
        outline = reader.outline
        if outline:
            _walk_outline(outline)
    except Exception:
        pass

    return chapters


def process_directory(input_dir: str, output_dir: str) -> list:
    """
    批量处理目录下的所有 PDF

    参数：
        input_dir: PDF 输入目录
        output_dir: 元数据 JSON 输出目录

    返回：
        所有处理结果的汇总列表
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"错误：输入目录不存在 - {input_dir}")
        return []

    # 用去重后的集合合并大小写匹配，避免在大小写不敏感的文件系统（Windows/macOS）上重复处理同一文件
    pdf_files = sorted(set(input_path.glob("*.pdf")) | set(input_path.glob("*.PDF")))

    if not pdf_files:
        print(f"警告：目录中未找到 PDF 文件 - {input_dir}")
        return []

    print(f"找到 {len(pdf_files)} 个 PDF 文件，开始处理...\n")

    results = []

    for pdf_file in pdf_files:
        print(f"处理中：{pdf_file.name}")

        # 提取元数据
        metadata = extract_pdf_metadata(str(pdf_file))

        # 输出 JSON 文件
        json_name = pdf_file.stem + "_metadata.json"
        json_path = output_path / json_name

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        # 打印摘要
        print(f"  总页数：{metadata['total_pages']}")
        print(f"  章节数：{len(metadata['chapters'])}")
        if metadata["chapters"]:
            print(f"  首章：{metadata['chapters'][0]['title']}（第 {metadata['chapters'][0]['page']} 页）")
        if metadata.get("warnings"):
            for w in metadata["warnings"]:
                print(f"  ⚠️ {w}")
        print(f"  元数据已保存：{json_path}\n")

        results.append({
            "file": pdf_file.name,
            "metadata_file": str(json_path),
            "total_pages": metadata["total_pages"],
            "chapter_count": len(metadata["chapters"]),
            "has_warnings": bool(metadata.get("warnings"))
        })

    return results


def generate_summary_report(results: list, report_dir: str = "reports"):
    """
    生成汇总报告（Markdown 格式）

    参数：
        results: 处理结果列表
        report_dir: 报告输出目录（默认 reports/）
    """
    report_path = Path(report_dir)
    report_path.mkdir(parents=True, exist_ok=True)
    report_path = report_path / "预处理汇总报告.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# PDF 预处理汇总报告\n\n")
        f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"处理文件数：{len(results)}\n\n")

        f.write("## 文档清单\n\n")
        f.write("| 文件名 | 总页数 | 章节数 | 有警告 | 元数据文件 |\n")
        f.write("|--------|--------|--------|--------|------------|\n")

        for r in results:
            warn = "⚠️ 是" if r["has_warnings"] else "否"
            f.write(
                f"| {r['file']} | {r['total_pages']} | "
                f"{r['chapter_count']} | {warn} | "
                f"`{r['metadata_file']}` |\n"
            )

        f.write("\n## Dify 上传建议\n\n")
        f.write("1. 上传 PDF 时，参考元数据 JSON 中的章节结构\n")
        f.write("2. 如有「无书签」警告，在 Dify 中选择「通用」分段方式\n")
        f.write("3. 如有「扫描件」警告，先用 OCR 工具处理后再上传\n")

    print(f"汇总报告已生成：{report_path}")


def main():
    parser = argparse.ArgumentParser(
        description="批量处理 PDF 文档，提取元数据"
    )
    parser.add_argument(
        "--input_dir",
        default="data/pdfs",
        help="PDF 输入目录（默认：data/pdfs）"
    )
    parser.add_argument(
        "--output_dir",
        default="data/metadata",
        help="元数据 JSON 输出目录（默认：data/metadata）"
    )
    parser.add_argument(
        "--report_dir",
        default="reports",
        help="汇总报告输出目录（默认：reports）"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("  PDF 元数据提取工具")
    print("  用途：为 Dify 知识库上传准备文档元数据")
    print("=" * 60)
    print(f"\n输入目录：{args.input_dir}")
    print(f"输出目录：{args.output_dir}\n")

    results = process_directory(args.input_dir, args.output_dir)

    if results:
        generate_summary_report(results, args.report_dir)
        print(f"\n✓ 处理完成，共 {len(results)} 个文件")
    else:
        print("\n✗ 未处理任何文件")


if __name__ == "__main__":
    main()
