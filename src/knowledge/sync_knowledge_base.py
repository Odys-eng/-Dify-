"""
知识库自动同步脚本
将指定目录下的新 PDF/MD/CSV 文件自动上传到 Dify 知识库。

用法：
    DIFY_KB_KEY=dataset-xxx python sync_knowledge_base.py \
        --watch-dir /path/to/new-manuals \
        --base-url https://localhost/v1 \
        --dataset-id <你的知识库ID>

    # 持续监听模式（每 60 秒扫描一次）：
    python sync_knowledge_base.py --watch-dir ./new-manuals --interval 60
"""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import requests

SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt", ".csv", ".docx"}
TERMINAL_STATUSES = {"completed", "error", "paused"}


class DifyKBClient:
    def __init__(self, base_url: str, dataset_id: str, api_key: str) -> None:
        self.dataset_url = f"{base_url.rstrip('/')}/datasets/{dataset_id}"
        self.session = requests.Session()
        self.session.trust_env = False
        self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        # 走 Nginx https://localhost/v1 时为自签证书，跳过校验（仅本地部署场景）
        if base_url.lower().startswith("https"):
            self.session.verify = False
            requests.packages.urllib3.disable_warnings(
                requests.packages.urllib3.exceptions.InsecureRequestWarning
            )

    def list_documents(self) -> dict[str, dict]:
        """返回 {文档名: 文档信息} 字典"""
        docs: dict[str, dict] = {}
        page = 1
        while True:
            r = self.session.get(
                f"{self.dataset_url}/documents",
                params={"page": page, "limit": 100},
                timeout=60,
            )
            r.raise_for_status()
            data = r.json()
            for doc in data.get("data", []):
                docs[doc["name"]] = doc
            if not data.get("has_more"):
                break
            page += 1
        return docs

    def upload(self, path: Path, name: str) -> str:
        """上传文件，返回 document_id"""
        mime = {
            ".pdf": "application/pdf",
            ".md": "text/markdown",
            ".txt": "text/plain",
            ".csv": "text/csv",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }.get(path.suffix.lower(), "application/octet-stream")
        config = {"indexing_technique": "high_quality", "process_rule": {"mode": "automatic"}}
        with path.open("rb") as f:
            r = self.session.post(
                f"{self.dataset_url}/document/create-by-file",
                files={"file": (name, f, mime)},
                data={"data": json.dumps(config, ensure_ascii=False)},
                timeout=300,
            )
        if r.status_code != 200:
            raise RuntimeError(f"Upload failed for {name}: {r.status_code} {r.text[:300]}")
        return r.json()["document"]["id"]

    def wait_for_indexing(self, doc_id: str, timeout: int = 3600) -> str:
        """等待文档索引完成，返回最终状态"""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            docs = self.list_documents()
            for doc in docs.values():
                if doc["id"] == doc_id:
                    status = doc.get("indexing_status", "unknown")
                    if status in TERMINAL_STATUSES:
                        return status
                    break
            time.sleep(15)
        return "timeout"


def scan_directory(watch_dir: Path) -> list[Path]:
    """扫描目录，返回支持格式的文件列表"""
    files = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(watch_dir.rglob(f"*{ext}"))
    return sorted(files)


def sync(client: DifyKBClient, watch_dir: Path, dry_run: bool = False) -> tuple[int, int, int]:
    """同步目录到知识库。返回 (新增, 跳过, 失败) 计数"""
    local_files = scan_directory(watch_dir)
    if not local_files:
        print(f"[sync] 目录 {watch_dir} 中没有支持的文件")
        return 0, 0, 0

    print(f"[sync] 本地文件 {len(local_files)} 个，正在获取线上文档列表...")
    remote_docs = client.list_documents()
    print(f"[sync] 线上文档 {len(remote_docs)} 个")

    added = skipped = failed = 0
    for path in local_files:
        name = path.name
        if name in remote_docs:
            status = remote_docs[name].get("indexing_status", "unknown")
            if status == "completed":
                print(f"  [skip] {name} (已完成)")
                skipped += 1
                continue
            elif status == "error":
                print(f"  [retry] {name} (之前失败，重新上传)")
            else:
                print(f"  [skip] {name} (状态: {status})")
                skipped += 1
                continue

        if dry_run:
            print(f"  [dry-run] 会上传: {name}")
            added += 1
            continue

        try:
            print(f"  [upload] {name} ({path.stat().st_size // 1024}KB)...")
            doc_id = client.upload(path, name)
            print(f"  [waiting] {name} 索引中...")
            final_status = client.wait_for_indexing(doc_id)
            if final_status == "completed":
                print(f"  [done] {name} ✅")
                added += 1
            else:
                print(f"  [failed] {name}: {final_status}")
                failed += 1
        except Exception as e:
            print(f"  [error] {name}: {e}")
            failed += 1

    return added, skipped, failed


def main() -> None:
    parser = argparse.ArgumentParser(description="同步目录到 Dify 知识库")
    parser.add_argument("--watch-dir", type=Path, required=True, help="要同步的目录")
    parser.add_argument("--base-url", default="https://localhost/v1")
    parser.add_argument("--dataset-id", required=True, help="你的知识库 ID")
    parser.add_argument("--interval", type=int, default=0, help="持续监听间隔秒数，0=单次运行")
    parser.add_argument("--dry-run", action="store_true", help="只显示要上传的文件，不实际上传")
    args = parser.parse_args()

    api_key = os.environ.get("DIFY_KB_KEY")
    if not api_key:
        raise SystemExit("请设置 DIFY_KB_KEY 环境变量")

    client = DifyKBClient(args.base_url, args.dataset_id, api_key)

    while True:
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始同步 {args.watch_dir}")
        added, skipped, failed = sync(client, args.watch_dir, dry_run=args.dry_run)
        print(f"结果：新增 {added}，跳过 {skipped}，失败 {failed}")

        if args.interval <= 0:
            break
        print(f"下次扫描在 {args.interval}s 后...")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
