"""
rebuild_parent_kb_fulldoc.py
重建「制造业设备维修-父子索引」库：
  1. 删除库内所有 .md（保留 5 个 PDF）
  2. 用【全文父块模式 parent_mode=full-doc】重传 data/kb_upload_ready 的 92 个文件

只操作父子库 cdfa2492...，不碰通用库。

运行：DIFY_KB_KEY=dataset-xxxx python scripts/rebuild_parent_kb_fulldoc.py
"""
import os
import sys
import json
import time
import requests
import urllib3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

WORKERS = 8  # 并发数

BASE = os.environ.get("DIFY_BASE_URL", "https://localhost/v1")
KEY = os.environ.get("DIFY_KB_KEY", "")
if not KEY:
    raise SystemExit("请设置 DIFY_KB_KEY")

# 目标：父子索引库（按名字 制造业设备维修-父子索引 核对过）
DS_ID = "cdfa2492-f2ab-4eaf-a3e2-b159365f030d"
DS_NAME_EXPECT = "制造业设备维修-父子索引"

ROOT = Path(__file__).parent.parent
UPLOAD_DIR = ROOT / "data" / "kb_upload_ready"
DELAY = 0.6
DRY = "--dry-run" in sys.argv
SKIP_CLEAR = "--skip-clear" in sys.argv


def H():
    return {"Authorization": f"Bearer {KEY}"}


def guard_name():
    """再次核对库名，防止删错库。"""
    r = requests.get(f"{BASE}/datasets/{DS_ID}", headers=H(), timeout=8, verify=False)
    r.raise_for_status()
    name = r.json().get("name", "")
    if name != DS_NAME_EXPECT:
        raise SystemExit(f"库名不符！期望「{DS_NAME_EXPECT}」实际「{name}」，已中止")
    print(f"✓ 已核对目标库：{name}  (id={DS_ID})")


def list_docs():
    docs, page = [], 1
    while True:
        r = requests.get(
            f"{BASE}/datasets/{DS_ID}/documents?page={page}&limit=100",
            headers=H(), timeout=10, verify=False,
        )
        d = r.json()
        docs += d.get("data", [])
        if not d.get("has_more"):
            break
        page += 1
    return docs


def _del_one(doc_id):
    r = requests.delete(
        f"{BASE}/datasets/{DS_ID}/documents/{doc_id}",
        headers=H(), timeout=15, verify=False,
    )
    return r.status_code in (200, 204)


def clear_md():
    docs = list_docs()
    md = [d for d in docs if d["name"].lower().endswith(".md")]
    pdf = [d for d in docs if d["name"].lower().endswith(".pdf")]
    print(f"现有 {len(docs)} 个：md={len(md)} 待删，pdf={len(pdf)} 保留")
    if DRY:
        for d in md[:5]:
            print(f"  [DRY] 删 {d['name']}")
        print(f"  [DRY] ... 共 {len(md)} 个")
        return
    ok = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(_del_one, d["id"]): d for d in md}
        for fu in as_completed(futs):
            if fu.result():
                ok += 1
    print(f"已删除 {ok}/{len(md)} 个 md")


def fulldoc_rule():
    """父子索引 + 全文父块模式。"""
    return {
        "indexing_technique": "high_quality",
        "doc_form": "hierarchical_model",
        "process_rule": {
            "mode": "hierarchical",
            "rules": {
                "pre_processing_rules": [
                    {"id": "remove_extra_spaces", "enabled": True},
                    {"id": "remove_urls_emails", "enabled": False},
                ],
                # 父级切分：API 强制要求此字段；max_tokens 设大保证整篇=一个父块
                "segmentation": {
                    "separator": "\n\n\n\n",
                    "max_tokens": 4000,
                },
                # 全文父块：整篇文档作为一个父块
                "parent_mode": "full-doc",
                # 子块分隔：按行切句
                "subchunk_segmentation": {
                    "separator": "\n",
                    "max_tokens": 256,
                    "chunk_overlap": 0,
                },
            },
        },
    }


def _upload_one(fp, rule):
    try:
        with open(fp, "rb") as f:
            r = requests.post(
                f"{BASE}/datasets/{DS_ID}/document/create-by-file",
                headers=H(),
                files={"file": (fp.name, f, "text/markdown")},
                data={"data": json.dumps(rule, ensure_ascii=False)},
                timeout=90, verify=False,
            )
        if r.status_code in (200, 201):
            return (fp.name, True, "")
        return (fp.name, False, r.text[:150])
    except Exception as e:
        return (fp.name, False, f"{type(e).__name__}: {str(e)[:80]}")


def upload_all():
    files = sorted(UPLOAD_DIR.glob("*.md"))
    total = len(files)
    print(f"\n重传 {total} 个文件（全文父块模式，{WORKERS} 并发）")
    if DRY:
        print(f"  [DRY] 将上传 {total} 个")
        return
    rule = fulldoc_rule()
    ok, fails, done = 0, [], 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(_upload_one, fp, rule) for fp in files]
        for fu in as_completed(futs):
            name, good, why = fu.result()
            done += 1
            if good:
                ok += 1
            else:
                fails.append((name, why))
            if done % 10 == 0 or done == total:
                print(f"  进度 {done}/{total}（成功 {ok}，失败 {len(fails)}）")
    print(f"\n完成：{ok}/{total} 成功，{len(fails)} 失败")
    for n, w in fails:
        print(f"  ✗ {n} → {w}")


def main():
    print("=" * 60)
    print(f"  重建父子库（全文父块模式）DRY={DRY}")
    print("=" * 60)
    guard_name()
    if SKIP_CLEAR:
        print("\n--- 跳过删除（--skip-clear）---")
    else:
        print("\n--- 1. 清除旧 md（保留 PDF）---")
        clear_md()
    print("\n--- 2. 全文父块模式重传 ---")
    upload_all()
    print("\n" + "=" * 60)
    print("  完成，Dify 后台向量化中（几分钟）")


if __name__ == "__main__":
    main()
