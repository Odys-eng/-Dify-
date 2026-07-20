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
QUESTION = "Dify 知识库接口文档中，Dify 知识库总共有多少个接口？请返回文档明确给出的接口总数。"


def load_api_key() -> str:
    if not KEY_FILE.is_file():
        raise FileNotFoundError(f"知识库 Key 文件不存在: {KEY_FILE}")
    key = KEY_FILE.read_text(encoding="utf-8").strip()
    if not key:
        raise ValueError(f"知识库 Key 文件为空: {KEY_FILE}")
    return key


def error_message(response: requests.Response) -> str:
    try:
        body: Any = response.json()
    except requests.JSONDecodeError:
        return response.reason or "未知错误"
    if isinstance(body, dict):
        for field in ("message", "error", "code"):
            if body.get(field):
                return str(body[field])
    return "服务端返回了未识别的错误响应"


def list_datasets(api_key: str) -> list[dict[str, Any]]:
    response = requests.get(
        f"{API_BASE_URL}/datasets",
        headers={"Authorization": f"Bearer {api_key}"},
        params={"page": 1, "limit": 100},
        timeout=30,
    )
    if response.status_code != 200:
        raise RuntimeError(f"查询知识库失败: HTTP {response.status_code}: {error_message(response)}")
    body = response.json()
    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, list):
        raise RuntimeError("查询知识库失败: 响应中缺少 data 列表")
    return [item for item in data if isinstance(item, dict)]


def retrieve(api_key: str, dataset_id: str) -> dict[str, Any]:
    response = requests.post(
        f"{API_BASE_URL}/datasets/{dataset_id}/retrieve",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
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
    if response.status_code != 200:
        raise RuntimeError(f"文档查询失败: HTTP {response.status_code}: {error_message(response)}")
    body = response.json()
    if not isinstance(body, dict):
        raise RuntimeError("文档查询失败: 响应不是 JSON 对象")
    return body


def extract_counts(contents: list[str]) -> list[int]:
    counts: list[int] = []
    for content in contents:
        plain_content = content.replace("**", "")
        pattern = r"(?:共计|总计|一共|共有|总共)?\s*(\d+)\s*个(?:知识库相关\s*API|接口)"
        for match in re.finditer(pattern, plain_content, flags=re.IGNORECASE):
            value = int(match.group(1))
            if value not in counts:
                counts.append(value)
    return counts


def main() -> int:
    try:
        api_key = load_api_key()
        datasets = list_datasets(api_key)
        matches = [item for item in datasets if item.get("name") == DATASET_NAME]
        if len(matches) != 1:
            print(f"未找到唯一目标知识库: {DATASET_NAME}", file=sys.stderr)
            return 4
        dataset = matches[0]
        result = retrieve(api_key, str(dataset["id"]))
    except (FileNotFoundError, ValueError) as exc:
        print(f"配置错误: {exc}", file=sys.stderr)
        return 2
    except requests.RequestException as exc:
        print(f"连接失败: {exc.__class__.__name__}", file=sys.stderr)
        return 3
    except (RuntimeError, requests.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 5

    records = result.get("records") if isinstance(result.get("records"), list) else []
    contents: list[str] = []
    print("文档查询成功")
    print(f"知识库: {DATASET_NAME}")
    print(f"知识库 ID: {dataset['id']}")
    print(f"命中分段数: {len(records)}")
    for index, record in enumerate(records, start=1):
        segment = record.get("segment", {}) if isinstance(record, dict) else {}
        content = str(segment.get("content") or "") if isinstance(segment, dict) else ""
        contents.append(content)
        preview = " ".join(content.split())[:240]
        print(f"证据 {index}: {preview}")

    counts = extract_counts(contents)
    if len(counts) == 1:
        print(f"文档给出的接口总数: {counts[0]}")
    elif counts:
        print(f"文档中检出的接口数量表述: {', '.join(map(str, counts))}")
        print("请结合上方证据人工确认最终统计")
    else:
        print("未在本次命中分段中检出明确的‘X 个接口’表述")
        print("请等待知识库索引完成后重试，或提高检索范围")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
