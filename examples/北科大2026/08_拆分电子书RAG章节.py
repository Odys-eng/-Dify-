from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader, PdfWriter


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE = PROJECT_ROOT / "Building AI Agents with LLMs, RAG, and Knowledge Graphs (Salvatore RaieliGabriele Iuculano) (z-library.sk, 1lib.sk, z-lib.sk).pdf"
OUTPUT_DIR = Path(__file__).resolve().parent / "练习3资料" / "电子书章节"

CHAPTERS = [
    (155, 188, "电子书第5章_RAG与减少幻觉.pdf", "Chapter 5 - Extending Your Agent with RAG to Prevent Hallucinations"),
    (189, 232, "电子书第6章_高级RAG技术.pdf", "Chapter 6 - Advanced RAG Techniques for Information Retrieval and Augmentation"),
    (233, 276, "电子书第7章_知识图谱与GraphRAG.pdf", "Chapter 7 - Creating and Connecting a Knowledge Graph to an AI Agent"),
]


def main() -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(f"电子书不存在: {SOURCE}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(SOURCE)
    for first_page, last_page, filename, title in CHAPTERS:
        writer = PdfWriter()
        for page_number in range(first_page, last_page + 1):
            writer.add_page(reader.pages[page_number - 1])
        writer.add_metadata(
            {
                "/Title": title,
                "/Author": "Salvatore Raieli; Gabriele Iuculano",
                "/Subject": "Local study excerpt for Dify knowledge-base retrieval practice",
            }
        )
        output = OUTPUT_DIR / filename
        with output.open("wb") as file:
            writer.write(file)
        print(f"{filename}: pages={len(writer.pages)}, bytes={output.stat().st_size}")

    # Smaller excerpt for providers that intermittently fail on larger batches.
    writer = PdfWriter()
    for page_number in range(189, 201):
        writer.add_page(reader.pages[page_number - 1])
    writer.add_metadata({"/Title": "Chapter 6 - Advanced RAG Techniques (excerpt)"})
    output = OUTPUT_DIR / "电子书第6章_高级RAG技术_节选.pdf"
    with output.open("wb") as file:
        writer.write(file)
    print(f"{output.name}: pages={len(writer.pages)}, bytes={output.stat().st_size}")


if __name__ == "__main__":
    main()
