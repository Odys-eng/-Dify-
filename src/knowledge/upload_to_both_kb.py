"""
upload_to_both_kb.py
把知识库文件同时上传到两个 Dify 知识库：
  - 通用分段库 (text_model)
  - 父子索引库 (hierarchical_model)

运行前设置环境变量（不要把 key 写进代码）：
  Windows PowerShell:  $env:DIFY_KB_KEY="dataset-xxxx"
  Git Bash:            export DIFY_KB_KEY="dataset-xxxx"

用法：
  python src/knowledge/upload_to_both_kb.py            # 保留已有 5 个 PDF，仅追加 92 个 .md
  python src/knowledge/upload_to_both_kb.py --clear    # 清空全部旧文档（含 PDF）后上传
  python src/knowledge/upload_to_both_kb.py --dry-run  # 只列出将要做什么
"""

import os
import sys
import json
import time
import requests
import urllib3

from pathlib import Path

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================
DIFY_BASE_URL = os.environ.get("DIFY_BASE_URL", "https://localhost/v1")
DATASET_API_KEY = os.environ.get("DIFY_KB_KEY", "")
if not DATASET_API_KEY:
    raise SystemExit("请先设置环境变量 DIFY_KB_KEY（形如 dataset-xxxx）")

# 两个目标知识库
KB_GENERAL = "62874d02-ed9d-4d31-b087-6b4ea50d0bc2"       # 通用分段
KB_HIERARCHICAL = "cdfa2492-f2ab-4eaf-a3e2-b159365f030d"  # 父子索引

PROJECT_ROOT = Path(__file__).parent.parent.parent
# 只上传 md 知识文档；5 个 PDF 已在库中，保留不动
SOURCE_DIRS = [
    PROJECT_ROOT / "制造业设备维修知识库",
]
SUPPORTED_EXTENSIONS = {".md"}
EXCLUDE_NAMES = {"README.md"}
UPLOAD_DELAY = 0.6

DRY_RUN = "--dry-run" in sys.argv
# 默认不清空（保留已有的 5 个 PDF）；如需清空全部旧文档加 --clear
DO_CLEAR = "--clear" in sys.argv

MIME_MAP = {
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".csv": "text/csv",
}
# ============================================================


def headers():
    return {"Authorization": f"Bearer {DATASET_API_KEY}"}


def req(method, path, **kw):
    kw.setdefault("timeout", 60)
    kw.setdefault("verify", False)
    return requests.request(method, f"{DIFY_BASE_URL}{path}", headers=headers(), **kw)


def list_documents(dataset_id):
    """列出知识库里所有文档 (id, name)。"""
    docs, page = [], 1
    while True:
        r = req("GET", f"/datasets/{dataset_id}/documents?page={page}&limit=100")
        r.raise_for_status()
        data = r.json()
        docs.extend((d["id"], d["name"]) for d in data.get("data", []))
        if not data.get("has_more"):
            break
        page += 1
    return docs


def clear_dataset(dataset_id, label, md_only=False):
    """删除知识库里旧文档。md_only=True 时只删 .md，保留 PDF。"""
    docs = list_documents(dataset_id)
    to_del = [(i, n) for i, n in docs if (not md_only or n.lower().endswith(".md"))]
    kept = len(docs) - len(to_del)
    print(f"  [{label}] 现有 {len(docs)} 个，待删 {len(to_del)} 个 md，保留 {kept} 个")
    for doc_id, name in to_del:
        if DRY_RUN:
            print(f"    [DRY] 将删除：{name}")
            continue
        r = req("DELETE", f"/datasets/{dataset_id}/documents/{doc_id}")
        status = "✓" if r.status_code in (200, 204) else f"✗ {r.status_code}"
        print(f"    删除 {name} ... {status}")
        time.sleep(0.3)


def process_rule_for(doc_form):
    """按知识库类型返回文档处理参数。"""
    if doc_form == "hierarchical_model":
        # 父子索引：父块按段落、子块细分
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
                    "segmentation": {"separator": "\n\n", "max_tokens": 1024},
                    "parent_mode": "paragraph",
                    "subchunk_segmentation": {"separator": "\n", "max_tokens": 256},
                },
            },
        }
    # 通用分段
    return {
        "indexing_technique": "high_quality",
        "doc_form": "text_model",
        "process_rule": {"mode": "automatic"},
    }


def collect_files():
    files = []
    for folder in SOURCE_DIRS:
        if not folder.exists():
            print(f"  ⚠️  文件夹不存在，跳过：{folder}")
            continue
        for path in sorted(folder.rglob("*")):
            if (
                path.is_file()
                and path.suffix.lower() in SUPPORTED_EXTENSIONS
                and path.name not in EXCLUDE_NAMES
            ):
                files.append(path)
    return files


def unique_name(file_path):
    """用父文件夹名作前缀，避免不同类别下同名 md 被 Dify 去重覆盖。
    例：01_机床与数控设备/04_常见故障.md -> 01_机床与数控设备__04_常见故障.md"""
    parent = file_path.parent.name
    return f"{parent}__{file_path.name}"


def upload_file(dataset_id, file_path, doc_form):
    url = f"/datasets/{dataset_id}/document/create-by-file"
    doc_data = process_rule_for(doc_form)
    mime = MIME_MAP.get(file_path.suffix.lower(), "application/octet-stream")
    with open(file_path, "rb") as f:
        r = req(
            "POST",
            url,
            files={"file": (unique_name(file_path), f, mime)},
            data={"data": json.dumps(doc_data, ensure_ascii=False)},
        )
    if r.status_code in (200, 201):
        return True, r.json().get("document", {}).get("id", "?")
    return False, r.text[:150]


def upload_to_kb(dataset_id, label, doc_form, files):
    print(f"\n{'='*60}\n  上传到 [{label}]（{doc_form}）\n{'='*60}")
    ok_n, fails = 0, []
    total = len(files)
    for i, fp in enumerate(files, 1):
        rel = fp.relative_to(PROJECT_ROOT)
        print(f"[{i:3d}/{total}] {rel} ... ", end="", flush=True)
        if DRY_RUN:
            print("[DRY]")
            continue
        try:
            ok, res = upload_file(dataset_id, fp, doc_form)
            if ok:
                print(f"✓ {res}")
                ok_n += 1
            else:
                print(f"✗ {res}")
                fails.append((str(rel), res))
        except Exception as e:
            print(f"✗ {type(e).__name__}: {str(e)[:80]}")
            fails.append((str(rel), str(e)))
        if i < total:
            time.sleep(UPLOAD_DELAY)
    print(f"\n  [{label}] 完成：{ok_n}/{total} 成功，{len(fails)} 失败")
    for name, why in fails:
        print(f"    ✗ {name}  →  {why}")
    return ok_n, fails


def main():
    print("=" * 60)
    print("  Dify 双知识库批量上传")
    print(f"  DRY_RUN={DRY_RUN}  DO_CLEAR={DO_CLEAR}")
    print("=" * 60)

    files = collect_files()
    print(f"\n共收集 {len(files)} 个文件\n")
    if not files:
        print("没有文件可上传")
        return

    targets = [
        (KB_GENERAL, "通用分段库", "text_model"),
        (KB_HIERARCHICAL, "父子索引库", "hierarchical_model"),
    ]

    if DO_CLEAR:
        print("--- 清空全部旧文档（含 PDF）---")
        for ds_id, label, _ in targets:
            clear_dataset(ds_id, label, md_only=False)
    else:
        print("--- 清空旧 .md（保留 5 个 PDF），再重传 ---")
        for ds_id, label, _ in targets:
            clear_dataset(ds_id, label, md_only=True)

    for ds_id, label, doc_form in targets:
        upload_to_kb(ds_id, label, doc_form, files)

    print("\n" + "=" * 60)
    print("  全部提交完成，Dify 后台正在向量化处理（约需几分钟）")
    print("=" * 60)


if __name__ == "__main__":
    main()
