from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[1]
KEY_FILE = PROJECT_ROOT / "key.txt"
API_BASE_URL = os.getenv("DIFY_API_BASE_URL", "http://localhost/v1").rstrip("/")
DATASET_NAME = "零基础AI编程"
FILES = [
    ROOT / "练习3资料" / "Dify学习资料汇编.md",
    ROOT / "练习3资料" / "Dify学习资料汇编.pdf",
    ROOT / "练习3资料" / "电子书章节" / "电子书第6章_高级RAG技术_节选.pdf",
]


def load_key() -> str:
    key = KEY_FILE.read_text(encoding="utf-8").strip() if KEY_FILE.is_file() else ""
    if not key:
        raise ValueError(f"知识库 Key 文件不存在或为空: {KEY_FILE}")
    return key


def error_message(response: requests.Response) -> str:
    try:
        body: Any = response.json()
    except requests.JSONDecodeError:
        return response.reason or "未知错误"
    if isinstance(body, dict):
        return str(body.get("message") or body.get("error") or body.get("code") or "未知错误")
    return "未知错误"


def request_json(method: str, url: str, key: str, **kwargs: Any) -> dict[str, Any]:
    headers = dict(kwargs.pop("headers", {}))
    headers["Authorization"] = f"Bearer {key}"
    response = requests.request(method, url, headers=headers, **kwargs)
    if response.status_code not in (200, 201):
        raise RuntimeError(f"HTTP {response.status_code}: {error_message(response)}")
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


def list_documents(key: str, dataset_id: str) -> list[dict[str, Any]]:
    body = request_json(
        "GET",
        f"{API_BASE_URL}/datasets/{dataset_id}/documents",
        key,
        params={"page": 1, "limit": 100},
        timeout=30,
    )
    return [item for item in body.get("data", []) if isinstance(item, dict)]


def delete_document(key: str, dataset_id: str, document_id: str) -> None:
    response = requests.delete(
        f"{API_BASE_URL}/datasets/{dataset_id}/documents/{document_id}",
        headers={"Authorization": f"Bearer {key}"},
        timeout=30,
    )
    if response.status_code not in (200, 204):
        raise RuntimeError(f"删除失败记录失败: HTTP {response.status_code}: {error_message(response)}")


def upload(key: str, dataset_id: str, path: Path) -> tuple[str, str]:
    config = {
        "indexing_technique": "high_quality",
        "doc_form": "text_model",
        "doc_language": "Chinese",
        "process_rule": {"mode": "automatic"},
    }
    with path.open("rb") as file:
        body = request_json(
            "POST",
            f"{API_BASE_URL}/datasets/{dataset_id}/document/create-by-file",
            key,
            files={"file": (path.name, file)},
            data={"data": json.dumps(config, ensure_ascii=False)},
            timeout=120,
        )
    document = body.get("document") if isinstance(body.get("document"), dict) else {}
    return str(document.get("id") or ""), str(body.get("batch") or "")


def wait_for_index(key: str, dataset_id: str, batch: str) -> tuple[str, str]:
    last_error = ""
    for _ in range(48):
        body = request_json(
            "GET", f"{API_BASE_URL}/datasets/{dataset_id}/documents/{batch}/indexing-status", key, timeout=30
        )
        items = [item for item in body.get("data", []) if isinstance(item, dict)]
        statuses = {str(item.get("indexing_status")) for item in items}
        errors = [str(item.get("error")) for item in items if item.get("error")]
        last_error = errors[0] if errors else last_error
        if statuses == {"completed"}:
            return "completed", ""
        if "error" in statuses:
            return "error", last_error
        time.sleep(5)
    return "timeout", last_error


def ensure_uploaded(key: str, dataset_id: str, path: Path) -> tuple[str, str]:
    if not path.is_file():
        raise FileNotFoundError(f"待上传文件不存在: {path}")
    existing = [item for item in list_documents(key, dataset_id) if item.get("name") == path.name]
    completed = [item for item in existing if item.get("indexing_status") == "completed"]
    if completed:
        return str(completed[0]["id"]), "already_completed"
    for item in existing:
        delete_document(key, dataset_id, str(item["id"]))

    document_id = ""
    last_error = ""
    for attempt in range(1, 4):
        document_id, batch = upload(key, dataset_id, path)
        if not document_id or not batch:
            raise RuntimeError(f"上传 {path.name} 后未返回文档 ID 或 batch")
        status, last_error = wait_for_index(key, dataset_id, batch)
        print(f"  第 {attempt} 次索引状态: {status}")
        if status == "completed":
            return document_id, status
        delete_document(key, dataset_id, document_id)
        if attempt < 3:
            time.sleep(attempt * 15)
    raise RuntimeError(f"{path.name} 连续索引失败: {last_error or '索引超时'}")


def main() -> int:
    try:
        key = load_key()
        dataset = find_dataset(key)
        dataset_id = str(dataset["id"])
        print(f"目标知识库: {DATASET_NAME}")
        print(f"知识库 ID: {dataset_id}")
        for path in FILES:
            print(f"上传: {path.name}")
            document_id, status = ensure_uploaded(key, dataset_id, path)
            print(f"  文档 ID: {document_id}")
            print(f"  最终状态: {status}")
    except (OSError, ValueError, RuntimeError, requests.RequestException, requests.JSONDecodeError) as exc:
        print(f"批量上传失败: {exc}", file=sys.stderr)
        return 1
    print("练习3脚本上传完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
