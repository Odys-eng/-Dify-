from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
KEY_FILE = PROJECT_ROOT / "key.txt"
API_BASE_URL = os.getenv("DIFY_API_BASE_URL", "http://localhost/v1").rstrip("/")
DATASET_NAME = "零基础AI编程"
QUESTION = "按默认 dify ETL 配置，Dify 知识库支持多少种文档扩展名？主流文档类型有哪些？"


def load_key() -> str:
    key = KEY_FILE.read_text(encoding="utf-8").strip() if KEY_FILE.is_file() else ""
    if not key:
        raise ValueError(f"知识库 Key 文件不存在或为空: {KEY_FILE}")
    return key


def call(method: str, url: str, key: str, **kwargs: Any) -> dict[str, Any]:
    response = requests.request(method, url, headers={"Authorization": f"Bearer {key}"}, **kwargs)
    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code}: {response.reason}")
    body = response.json()
    if not isinstance(body, dict):
        raise RuntimeError("服务端响应不是 JSON 对象")
    return body


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
        result = call(
            "POST",
            f"{API_BASE_URL}/datasets/{dataset_id}/retrieve",
            key,
            json={
                "query": QUESTION,
                "retrieval_model": {
                    "search_method": "semantic_search",
                    "reranking_enable": False,
                    "top_k": 8,
                    "score_threshold_enabled": False,
                },
            },
            timeout=60,
        )
    except (OSError, ValueError, RuntimeError, requests.RequestException, requests.JSONDecodeError) as exc:
        print(f"查询失败: {exc}", file=sys.stderr)
        return 1

    records = result.get("records", [])
    contents: list[str] = []
    print("知识库查询成功")
    print(f"问题: {QUESTION}")
    print(f"命中分段数: {len(records)}")
    for index, record in enumerate(records, start=1):
        segment = record.get("segment", {}) if isinstance(record, dict) else {}
        content = str(segment.get("content") or "") if isinstance(segment, dict) else ""
        contents.append(content)
        print(f"证据 {index}: {' '.join(content.split())[:260]}")

    combined = "\n".join(contents).replace("**", "")
    count_match = re.search(r"默认[^。\n]{0,80}?支持\s*(\d+)\s*种文件扩展名", combined)
    mainstream_match = re.search(r"主流类型包括\s*([^；。\n]+)", combined)
    if not count_match:
        print("未检索到明确数量，请确认文档索引状态", file=sys.stderr)
        return 2
    print(f"答案：默认配置支持 {count_match.group(1)} 种文件扩展名。")
    if mainstream_match:
        print(f"主流类型：{mainstream_match.group(1)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
