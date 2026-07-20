from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_SRC = PROJECT_ROOT / "src" / "docx" / "src"
sys.path.insert(0, str(PACKAGE_SRC))

from ruyi_docx import (  # noqa: E402
    Callout,
    CalloutKind,
    CodeBlock,
    DocumentMetadata,
    DocumentSpec,
    Heading,
    Hyperlink,
    ListBlock,
    Paragraph,
    TableBlock,
    TableOfContents,
    WordDocumentService,
)


@dataclass(frozen=True, slots=True)
class LessonSection:
    title: str
    paragraphs: tuple[str, ...] = ()
    bullets: tuple[str, ...] = ()
    code: tuple[tuple[str, str], ...] = ()
    callouts: tuple[tuple[str, str, CalloutKind], ...] = ()
    table: tuple[tuple[str, ...], ...] | None = None


DOC_TITLE = "零基础 Dify 入门"
DEEP_READ_AT = "2026-07-18T11:55:32+08:00"

SECTIONS = (
    LessonSection(
        "1. 先建立正确的 Dify 心智模型",
        paragraphs=(
            "Dify 是一个开源 AI 应用开发平台。它把模型、提示词、知识库、工具、代码、条件分支和运行日志组织成可重复、可观察的应用。",
            "学习 Dify 不应从“如何让模型回答一句话”开始，而应从“如何把数据、流程和模型组合成可维护应用”开始。",
        ),
        bullets=(
            "编排：用 Workflow、Chatflow 和 Agent 组织模型与工具。",
            "知识：导入自己的资料，让应用通过 RAG 获取上下文。",
            "发布：通过 Web App、嵌入页面或 API 提供服务。",
            "监控：查看运行日志、反馈、引用和失败路径。",
            "集成：连接模型供应商、数据源、插件和外部服务。",
        ),
    ),
    LessonSection(
        "2. 第一次启动和访问",
        paragraphs=(
            "本项目使用 docker 目录中的 Compose 配置启动 Dify。第一次运行前先确认 Docker Desktop 已启动，并在 docker 目录检查 Compose 配置。",
        ),
        code=(
            (
                "powershell",
                "cd docker\ndocker compose config --quiet\ndocker compose up -d\ndocker compose ps",
            ),
            ("powershell", "curl.exe -I --max-time 20 http://127.0.0.1/"),
        ),
        callouts=(
            (
                "安全边界",
                "不要把 .env、key.txt、Token、密码或供应商凭据写进课程文档、Git 提交或知识库。",
                CalloutKind.WARNING,
            ),
        ),
    ),
    LessonSection(
        "3. 应用类型怎么选",
        paragraphs=(
            "Workflow 从输入运行到输出一次，适合报告生成、批处理和数据加工；Chatflow 保留对话层，每条消息都会触发流程；Agent 由模型自主决定下一步并调用工具。",
            "已经确定的步骤优先使用 Workflow 或 Chatflow；只有路径确实难以预先定义时才选择 Agent。",
        ),
        table=(
            ("类型", "交互方式", "适用场景"),
            ("Chatbot", "简单对话", "FAQ、轻量问答"),
            ("Chatflow", "对话 + 可视化流程", "带知识检索的客服和助手"),
            ("Workflow", "一次运行", "报告、批处理、自动化"),
            ("Agent", "模型自主决策", "工具调用和开放式任务"),
        ),
    ),
    LessonSection(
        "4. 知识库与 RAG 是入门主线",
        paragraphs=(
            "Dify Knowledge 保存自己的资料，并在回答问题时提供额外上下文。RAG 可以拆成 Retrieval、Augmented、Generation 三步：先检索，再把片段加入上下文，最后让 LLM 基于上下文生成回答。",
            "一份文档进入知识库后，会经历解析、清洗、分段、Embedding、索引和检索。上传接口返回成功，只代表异步任务创建；状态达到 completed 后才适合稳定检索。",
        ),
        bullets=(
            "Dataset：知识库本身，保存配置、检索设置和文档关系。",
            "Document：上传的文件或文本资料。",
            "Segment：文档切分后的检索单元。",
            "Embedding：把文本转换成向量表示。",
            "Retrieval：根据问题找出相关 Segment。",
            "LLM：使用检索上下文生成最终回答。",
        ),
        callouts=(
            (
                "先看证据再看答案",
                "知识库问答出现错误时，先检查命中的分段和引用，再判断是切分、Embedding、检索参数还是提示词问题。",
                CalloutKind.INFO,
            ),
        ),
    ),
    LessonSection(
        "5. 分段、索引和检索调参",
        paragraphs=(
            "General 模式让所有分段共享规则；Parent-child 模式用小的子分段精确匹配，再返回更大的父分段。分隔符、最大长度和 overlap 直接影响召回质量。",
            "High-Quality 使用 Embedding，支持向量、全文和混合检索；Economical 使用关键词倒排索引，成本更低但语义召回能力较弱。",
        ),
        bullets=(
            "Top K 太小会漏召回，太大会引入噪声。",
            "Score Threshold 太高可能无结果，太低会带来无关片段。",
            "Hybrid Search 适合自然语言与编号、接口路径混合的资料。",
            "Rerank 可以改善候选排序，但会增加延迟和模型成本。",
            "Metadata Filter 可以按产品、部门、年份和资料类型缩小范围。",
        ),
        code=(
            (
                "python",
                'QUESTION = "Dify 知识库共有多少个接口？"\nTOP_K = 8\nSEARCH_METHOD = "semantic_search"',
            ),
        ),
    ),
    LessonSection(
        "6. 用 API 完成第一个知识库练习",
        paragraphs=(
            "知识库 Service API Key 在 Knowledge 页面右上角的 Service API 中创建。知识库 Key 可以访问创建者可见的知识库，必须按密码级别保护。",
        ),
        code=(
            (
                "powershell",
                'python "examples\\北科大2026\\01_验证连接.py"\npython "examples\\北科大2026\\02_查看知识库.py"\npython "examples\\北科大2026\\03_上传文档.py"',
            ),
            (
                "http",
                "GET  /v1/datasets\nPOST /v1/datasets/{dataset_id}/document/create-by-file\nPOST /v1/datasets/{dataset_id}/retrieve",
            ),
        ),
        callouts=(
            (
                "本地密钥规则",
                "示例脚本可以从项目根目录 key.txt 读取 Key，但只能输出知识库名称、ID、文档状态等非敏感结果。",
                CalloutKind.WARNING,
            ),
        ),
    ),
    LessonSection(
        "7. 创建第一个 Chatflow",
        paragraphs=(
            "最小的知识库问答流程是 User Input → Knowledge Retrieval → LLM → Answer。先在检索节点确认知识库和 Top K，再把检索结果变量接入 LLM，最后打开引用和归因。",
        ),
        bullets=(
            "没有召回时要有明确兜底，不要让模型凭空猜答案。",
            "用准确问题、同义问题、跨语言问题和无答案问题组成测试集。",
            "检查最终回答是否真的引用了检索片段。",
            "多知识库场景优先考虑 Metadata Filter 和 Rerank。",
        ),
    ),
    LessonSection(
        "8. 常见故障排查",
        table=(
            ("现象", "优先检查", "处理方向"),
            (
                "文档上传成功但不可检索",
                "索引状态、Worker 日志",
                "等待 completed，检查 Embedding",
            ),
            ("Embedding 403", "供应商模型权限和模型名", "确认 text-embedding 模型可用"),
            ("SSL EOF/连接中断", "容器出网和供应商接口", "重试、检查代理或更换供应商"),
            ("检索结果不相关", "分段、Top K、阈值、Rerank", "先看命中分段再调参"),
            ("API 401", "Key 来源和 Authorization", "重新创建或检查 Key，不输出 Key"),
        ),
    ),
    LessonSection(
        "9. 四周学习路线",
        table=(
            ("周次", "主题", "产出"),
            ("第 1 周", "环境、模型、应用类型", "可访问的 Dify 和一个 Chatbot"),
            ("第 2 周", "知识库与 RAG", "多格式资料库和检索测试集"),
            ("第 3 周", "Workflow/Chatflow", "知识检索到 LLM 的完整流程"),
            ("第 4 周", "Agent、API、评估", "脚本、监控和参数调优记录"),
        ),
        paragraphs=(
            "每周都要保留可复核产物：脚本、文档、索引状态、检索证据和失败记录。这样 AI 下次可以先读项目文档库，不必重新扫描整个源码。",
        ),
    ),
)

SOURCES = (
    ("Dify 官方文档索引", "https://docs.dify.ai/llms.txt"),
    ("Knowledge", "https://docs.dify.ai/en/cloud/use-dify/knowledge/readme"),
    (
        "索引与检索设置",
        "https://docs.dify.ai/en/cloud/use-dify/knowledge/create-knowledge/setting-indexing-methods",
    ),
    (
        "Workflow 与 Chatflow",
        "https://docs.dify.ai/en/cloud/use-dify/build/workflow-chatflow",
    ),
    ("Agent", "https://docs.dify.ai/en/cloud/use-dify/build/agent"),
    ("API 入门", "https://docs.dify.ai/en/api-reference/guides/get-started"),
    ("知识库 API", "https://docs.dify.ai/en/api-reference/guides/knowledge"),
)


def build_blocks() -> tuple[object, ...]:
    blocks: list[object] = [
        Heading(DOC_TITLE, level=1),
        Paragraph(
            "给第一次接触 Dify 的学习者：从启动、模型、知识库到第一个 Chatflow。",
            alignment="center",
        ),
        Callout(
            "老师的话",
            "先把一次完整链路跑通，再逐个调参。能解释证据来源，比能让模型说出漂亮答案更重要。",
            CalloutKind.SUCCESS,
        ),
        TableOfContents(),
    ]
    for section in SECTIONS:
        blocks.append(Heading(section.title, level=1))
        blocks.extend(Paragraph(text) for text in section.paragraphs)
        if section.bullets:
            blocks.append(ListBlock(section.bullets))
        if section.code:
            blocks.extend(CodeBlock(code, language) for language, code in section.code)
        if section.callouts:
            blocks.extend(
                Callout(title, text, kind) for title, text, kind in section.callouts
            )
        if section.table:
            blocks.append(TableBlock(section.table, column_widths_cm=(3.3, 6.0, 7.0)))
    blocks.extend(
        (
            Heading("官方来源", level=1),
            *(Hyperlink(label, url) for label, url in SOURCES),
        )
    )
    return tuple(blocks)


def build_markdown(reviewed_at: str) -> str:
    lines = [
        "---",
        f"title: {DOC_TITLE}",
        "status: verified",
        f"deep_read_at: {DEEP_READ_AT}",
        f"last_reviewed_at: {reviewed_at}",
        "review_after: 2026-08-17",
        "source_revision: unavailable-no-git-history",
        "evidence: docs-confirmed + code-confirmed + runtime-verified",
        "source_paths: [docker, api/controllers/service_api/dataset, api/core/rag, examples/北科大2026]",
        "supersedes: []",
        "---",
        "",
        f"# {DOC_TITLE}",
        "",
        "> 给第一次接触 Dify 的学习者：从启动、模型、知识库到第一个 Chatflow。",
        ">",
        "> 老师的话：先把一次完整链路跑通，再逐个调参。能解释证据来源，比能让模型说出漂亮答案更重要。",
        "",
        "## 目录",
        "",
        "打开 DOCX 后更新目录域即可生成页码。Markdown 使用下面的章节标题直接导航。",
        "",
    ]
    for section in SECTIONS:
        lines.extend([f"## {section.title}", ""])
        lines.extend(section.paragraphs)
        if section.paragraphs:
            lines.append("")
        if section.bullets:
            lines.extend(f"- {item}" for item in section.bullets)
            lines.append("")
        for language, code in section.code:
            lines.extend([f"```{language}", code, "```", ""])
        for title, text, _kind in section.callouts:
            lines.extend([f"> **{title}**：{text}", ""])
        if section.table:
            lines.append("| " + " | ".join(section.table[0]) + " |")
            lines.append("| " + " | ".join("---" for _ in section.table[0]) + " |")
            lines.extend("| " + " | ".join(row) + " |" for row in section.table[1:])
            lines.append("")
    lines.extend(["## 官方来源", ""])
    lines.extend(f"- [{label}]({url})" for label, url in SOURCES)
    lines.extend(["", "资料核对日期：2026-07-18。", ""])
    return "\n".join(lines)


def update_library_indexes(
    library_root: Path, relative_md: str, reviewed_at: str
) -> None:
    manifest = library_root / "manifest.yaml"
    text = manifest.read_text(encoding="utf-8")
    text = text.replace(
        next(
            line
            for line in text.splitlines()
            if line.startswith("latest_reviewed_at: ")
        ),
        f"latest_reviewed_at: {reviewed_at}",
    )
    if "  zero_based_dify: " not in text:
        text = text.replace(
            "  examples: 06-learning-resources/knowledge-base-examples.md\n",
            "  examples: 06-learning-resources/knowledge-base-examples.md\n  zero_based_dify: "
            + relative_md
            + "\n",
        )
    manifest.write_text(text, encoding="utf-8")

    navigation = library_root / "00-navigation" / "index.md"
    nav_text = navigation.read_text(encoding="utf-8")
    row = f"| 零基础 Dify 入门 | `{relative_md}` | `06-learning-resources/knowledge-base-examples.md` |\n"
    if relative_md not in nav_text:
        marker = "| 应该先学什么 | `04-development/learning-path.md` | `06-learning-resources/knowledge-base-examples.md` |\n"
        nav_text = nav_text.replace(marker, marker + row)
        navigation.write_text(nav_text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--library-root",
        type=Path,
        default=Path(__file__).resolve().parents[3] / "RuyiDifity-memery",
    )
    args = parser.parse_args()
    library_root = args.library_root.resolve()
    output_dir = library_root / "06-learning-resources"
    output_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = output_dir / f"{DOC_TITLE}.md"
    docx_path = output_dir / f"{DOC_TITLE}.docx"
    reviewed_at = datetime.now().astimezone().isoformat(timespec="seconds")
    markdown_path.write_text(build_markdown(reviewed_at), encoding="utf-8")
    spec = DocumentSpec(
        blocks=build_blocks(),
        metadata=DocumentMetadata(
            title=DOC_TITLE,
            subject="Dify 从启动、模型、知识库到 Chatflow 的入门课程",
            author="RuyiDify 教学资料",
            keywords=("Dify", "RAG", "Knowledge", "Chatflow", "Workflow"),
        ),
        header_text="RuyiDify | 零基础 Dify 入门",
        footer_text="Dify 入门课程",
    )
    service = WordDocumentService()
    service.create(spec, docx_path)
    report = service.validate(docx_path)
    if not report.valid:
        raise RuntimeError("生成的 DOCX 未通过校验: " + "; ".join(report.errors))
    update_library_indexes(
        library_root, f"06-learning-resources/{DOC_TITLE}.md", reviewed_at
    )
    print(f"Markdown={markdown_path}")
    print(f"DOCX={docx_path}")
    print(
        f"Validation={report.valid}, paragraphs={report.paragraph_count}, tables={report.table_count}"
    )


if __name__ == "__main__":
    main()
