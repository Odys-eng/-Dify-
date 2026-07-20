from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
KEY_FILE = PROJECT_ROOT / "key.txt"
DOCUMENT_FILE = PROJECT_ROOT / "Dify 知识库文档支持类型.md"
API_BASE_URL = os.getenv("DIFY_API_BASE_URL", "http://localhost/v1").rstrip("/")
DATASET_NAME = "零基础AI编程"


def load_key() -> str:
    key = KEY_FILE.read_text(encoding="utf-8").strip() if KEY_FILE.is_file() else ""
    if not key:
        raise ValueError(f"知识库 Key 文件不存在或为空: {KEY_FILE}")
    return key


def request_json(method: str, url: str, key: str, **kwargs: Any) -> dict[str, Any]:
    headers = dict(kwargs.pop("headers", {}))
    headers["Authorization"] = f"Bearer {key}"
    response = requests.request(method, url, headers=headers, **kwargs)
    if response.status_code not in (200, 201):
        try:
            message = response.json().get("message", response.reason)
        except requests.JSONDecodeError:
            message = response.reason
        raise RuntimeError(f"HTTP {response.status_code}: {message}")
    body = response.json()
    if not isinstance(body, dict):
        raise RuntimeError("服务端响应不是 JSON 对象")
    return body


def find_dataset(key: str) -> dict[str, Any]:
    body = request_json(
        "GET", f"{API_BASE_URL}/datasets", key, params={"page": 1, "limit": 100}, timeout=30
    )
    matches = [item for item in body.get("data", []) if isinstance(item, dict) and item.get("name") == DATASET_NAME]
    if len(matches) != 1:
        raise RuntimeError(f"未找到唯一目标知识库: {DATASET_NAME}")
    return matches[0]


def existing_document(key: str, dataset_id: str) -> dict[str, Any] | None:
    body = request_json(
        "GET",
        f"{API_BASE_URL}/datasets/{dataset_id}/documents",
        key,
        params={"page": 1, "limit": 100, "keyword": DOCUMENT_FILE.name},
        timeout=30,
    )
    matches = [item for item in body.get("data", []) if isinstance(item, dict) and item.get("name") == DOCUMENT_FILE.name]
    return matches[0] if len(matches) == 1 else None


def upload(key: str, dataset_id: str) -> dict[str, Any]:
    config = {
        "indexing_technique": "high_quality",
        "doc_form": "text_model",
        "doc_language": "Chinese",
        "process_rule": {"mode": "automatic"},
    }
    with DOCUMENT_FILE.open("rb") as file:
        return request_json(
            "POST",
            f"{API_BASE_URL}/datasets/{dataset_id}/document/create-by-file",
            key,
            files={"file": (DOCUMENT_FILE.name, file, "text/markdown")},
            data={"data": json.dumps(config, ensure_ascii=False)},
            timeout=120,
        )


def wait_for_index(key: str, dataset_id: str, batch: str) -> str:
    for _ in range(24):
        body = request_json(
            "GET", f"{API_BASE_URL}/datasets/{dataset_id}/documents/{batch}/indexing-status", key, timeout=30
        )
        items = body.get("data", [])
        statuses = {item.get("indexing_status") for item in items if isinstance(item, dict)}
        if statuses == {"completed"}:
            return "completed"
        if "error" in statuses:
            return "error"
        time.sleep(5)
    return "timeout"


def main() -> int:
    try:
        key = load_key()
        dataset = find_dataset(key)
        dataset_id = str(dataset["id"])
        current = existing_document(key, dataset_id)
        if current:
            print("目标文档已存在，未重复上传")
            print(f"知识库 ID: {dataset_id}")
            print(f"文档 ID: {current.get('id')}")
            print(f"索引状态: {current.get('indexing_status')}")
            return 0
        result = upload(key, dataset_id)
        document = result.get("document", {})
        batch = str(result.get("batch") or "")
        status = wait_for_index(key, dataset_id, batch) if batch else "未返回批次 ID"
    except (OSError, ValueError, RuntimeError, requests.RequestException, requests.JSONDecodeError) as exc:
        print(f"执行失败: {exc}", file=sys.stderr)
        return 1

    print("文档上传成功")
    print(f"知识库: {DATASET_NAME}")
    print(f"知识库 ID: {dataset_id}")
    print(f"文档 ID: {document.get('id') or '未返回'}")
    print(f"批次 ID: {batch or '未返回'}")
    print(f"索引状态: {status}")
    return 0 if status == "completed" else 2


if __name__ == "__main__":
    raise SystemExit(main())

