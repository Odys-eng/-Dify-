from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")


PROJECT_ROOT = Path(__file__).resolve().parents[2]
KEY_FILE = PROJECT_ROOT / "key.txt"
API_BASE_URL = os.getenv("DIFY_API_BASE_URL", "http://localhost/v1").rstrip("/")
DATASET_NAME = "零基础AI编程"
QUESTION = (
    "电子书高级 RAG 章节中的 hierarchical indexing、metadata、pre-retrieval、post-retrieval 和 map and reduce 分别如何改进检索？"
)


def load_key() -> str:
    key = KEY_FILE.read_text(encoding="utf-8").strip() if KEY_FILE.is_file() else ""
    if not key:
        raise ValueError(f"知识库 Key 文件不存在或为空: {KEY_FILE}")
    return key


def call(method: str, url: str, key: str, **kwargs: Any) -> dict[str, Any]:
    response = requests.request(method, url, headers={"Authorization": f"Bearer {key}"}, **kwargs)
    if response.status_code != 200:
        try:
            body = response.json()
            message = body.get("message") if isinstance(body, dict) else response.reason
        except requests.JSONDecodeError:
            message = response.reason
        raise RuntimeError(f"HTTP {response.status_code}: {message}")
    body = response.json()
    if not isinstance(body, dict):
        raise RuntimeError("服务端响应不是 JSON 对象")
    return body


def retrieve(key: str, dataset_id: str) -> dict[str, Any]:
    payload = {
        "query": QUESTION,
        "retrieval_model": {
            "search_method": "semantic_search",
            "reranking_enable": False,
            "top_k": 12,
            "score_threshold_enabled": False,
        },
    }
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            return call(
                "POST", f"{API_BASE_URL}/datasets/{dataset_id}/retrieve", key, json=payload, timeout=90
            )
        except (requests.RequestException, RuntimeError) as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(attempt * 10)
    raise RuntimeError(f"连续查询失败: {last_error}")


def main() -> int:
    try:
        key = load_key()
        datasets = call(
            "GET", f"{API_BASE_URL}/datasets", key, params={"page": 1, "limit": 100}, timeout=30
        ).get("data", [])
        matches = [item for item in datasets if isinstance(item, dict) and item.get("name") == DATASET_NAME]
        if len(matches) != 1:
            raise RuntimeError(f"未找到唯一目标知识库: {DATASET_NAME}")
        dataset_id = str(matches[0]["id"])
        result = retrieve(key, dataset_id)
    except (OSError, ValueError, RuntimeError, requests.RequestException, requests.JSONDecodeError) as exc:
        print(f"查询失败: {exc}", file=sys.stderr)
        return 1

    records = result.get("records", []) if isinstance(result.get("records"), list) else []
    ebook_hits = 0
    print("电子书查询成功")
    print(f"知识库: {DATASET_NAME}")
    print(f"问题: {QUESTION}")
    print(f"总命中分段数: {len(records)}")
    for index, record in enumerate(records, start=1):
        segment = record.get("segment", {}) if isinstance(record, dict) else {}
        document = segment.get("document", {}) if isinstance(segment, dict) else {}
        name = str(document.get("name") or "未提供") if isinstance(document, dict) else "未提供"
        content = str(segment.get("content") or "") if isinstance(segment, dict) else ""
        if "电子书第6章" in name:
            ebook_hits += 1
        print(f"证据 {index} | 文档: {name}")
        print(f"  {' '.join(content.split())[:360]}")

    print(f"电子书章节命中数: {ebook_hits}")
    if ebook_hits == 0:
        print("本次结果未命中电子书章节，请改用更具体的问题或增加 Top K", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
