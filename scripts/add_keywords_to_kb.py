"""
批量给知识库 md 文档的元数据块添加「关键词」行。
提取 ## 核心知识 里的故障词，插入到 - 更新日期：那行之后。

用法：
    python scripts/add_keywords_to_kb.py [--dry-run]
"""
import re
import sys
from pathlib import Path

KB_DIR = Path(__file__).parent.parent / "制造业设备维修知识库"
DRY_RUN = "--dry-run" in sys.argv


def extract_keywords(content: str) -> str | None:
    """从 ## 核心知识 或 ## 主要部件 节提取关键词（每行 `- 短语：` 的短语部分）。"""
    # 匹配核心知识 / 可能原因 / 检查项 / 主要工作 等不同标题
    section_patterns = [
        r"##\s*核心知识\n(.*?)(?=\n##|\Z)",
        r"##\s*主要部件与功能\n(.*?)(?=\n##|\Z)",
        r"##\s*关键操作步骤\n(.*?)(?=\n##|\Z)",
        r"##\s*日常点检项目\n(.*?)(?=\n##|\Z)",
        r"##\s*适用范围\n(.*?)(?=\n##|\Z)",
    ]
    section_text = ""
    for pat in section_patterns:
        m = re.search(pat, content, re.DOTALL)
        if m:
            section_text = m.group(1)
            break

    if not section_text:
        return None

    # 提取 `- 短语：` 或 `- 短语` 的短语部分（冒号前），最多 6 个
    phrases = []
    for line in section_text.splitlines():
        line = line.strip()
        if not line.startswith("- "):
            continue
        item = line[2:].strip()
        # 取冒号前的部分（故障名 / 部件名）
        phrase = re.split(r"[：:（(]", item)[0].strip()
        if phrase and len(phrase) <= 20:  # 过滤过长的句子
            phrases.append(phrase)
        if len(phrases) >= 6:
            break

    return "、".join(phrases) if phrases else None


def process_file(md_path: Path) -> bool:
    """为文件添加关键词行，已有则跳过。返回 True 表示有修改。"""
    content = md_path.read_text(encoding="utf-8")

    # 已经有关键词行则跳过
    if "- 关键词：" in content:
        return False

    keywords = extract_keywords(content)
    if not keywords:
        print(f"  [SKIP] 未找到关键词节：{md_path.name}")
        return False

    # 在 `- 更新日期：` 行后面插入关键词行
    new_content = re.sub(
        r"(- 更新日期：.*)",
        r"\1\n- 关键词：" + keywords,
        content,
        count=1,
    )

    if new_content == content:
        # 没有更新日期行，改为在最后一个 `- ` 元数据行后插入
        new_content = re.sub(
            r"(- 复核状态：.*)",
            r"\1\n- 关键词：" + keywords,
            content,
            count=1,
        )

    if new_content == content:
        print(f"  [SKIP] 找不到插入位置：{md_path.name}")
        return False

    if DRY_RUN:
        print(f"  [DRY] {md_path.parent.name}/{md_path.name}  →  关键词：{keywords}")
    else:
        md_path.write_text(new_content, encoding="utf-8")
        print(f"  [OK]  {md_path.parent.name}/{md_path.name}  →  关键词：{keywords}")

    return True


def main():
    md_files = sorted(KB_DIR.rglob("*.md"))
    print(f"共找到 {len(md_files)} 个文件，DRY_RUN={DRY_RUN}\n")

    modified = 0
    for f in md_files:
        if process_file(f):
            modified += 1

    print(f"\n完成：修改了 {modified} 个文件（共 {len(md_files)} 个）")


if __name__ == "__main__":
    main()
