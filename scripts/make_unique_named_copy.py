"""
make_unique_named_copy.py
把 制造业设备维修知识库/ 下的 92 个 md 复制到一个扁平目录，
文件名加「文件夹前缀」保证唯一，方便一次性拖进 Dify 不被去重覆盖。

输出目录：data/kb_upload_ready/
用法：python scripts/make_unique_named_copy.py
"""
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "制造业设备维修知识库"
DST = ROOT / "data" / "kb_upload_ready"
EXCLUDE = {"README.md"}


def main():
    if DST.exists():
        shutil.rmtree(DST)
    DST.mkdir(parents=True)

    n = 0
    for md in sorted(SRC.rglob("*.md")):
        if md.name in EXCLUDE:
            continue
        # 前缀 = 父文件夹名，例：01_机床与数控设备__04_常见故障与可能原因.md
        new_name = f"{md.parent.name}__{md.name}"
        shutil.copy2(md, DST / new_name)
        n += 1

    print(f"完成：{n} 个文件已复制到")
    print(f"  {DST}")
    print("\n示例文件名：")
    for f in sorted(DST.glob("*.md"))[:5]:
        print(f"  {f.name}")


if __name__ == "__main__":
    main()
