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
FILE_PATH = Path(__file__).resolve().parent / "练习3资料" / "Dify学习资料汇编.docx"
API_BASE_URL = os.getenv("DIFY_API_BASE_URL", "http://localhost/v1").rstrip("/")
DATASET_NAME = "零基础AI编程"
MAX_ATTEMPTS = 3


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


def find_document(key: str, dataset_id: str) -> dict[str, Any]:
    body = request_json(
        "GET",
        f"{API_BASE_URL}/datasets/{dataset_id}/documents",
        key,
        params={"page": 1, "limit": 100, "keyword": FILE_PATH.name},
        timeout=30,
    )
    matches = [item for item in body.get("data", []) if isinstance(item, dict) and item.get("name") == FILE_PATH.name]
    if len(matches) != 1:
        raise RuntimeError(f"未找到唯一目标文档: {FILE_PATH.name}")
    return matches[0]


def delete_document(key: str, dataset_id: str, document_id: str) -> None:
    response = requests.delete(
        f"{API_BASE_URL}/datasets/{dataset_id}/documents/{document_id}",
        headers={"Authorization": f"Bearer {key}"},
        timeout=30,
    )
    if response.status_code not in (200, 204):
        raise RuntimeError(f"删除失败文档失败: HTTP {response.status_code}: {error_message(response)}")


def create_document(key: str, dataset_id: str) -> dict[str, Any]:
    config = {
        "name": FILE_PATH.name,
        "doc_form": "text_model",
        "doc_language": "Chinese",
        "process_rule": {"mode": "automatic"},
    }
    with FILE_PATH.open("rb") as file:
        return request_json(
            "POST",
            f"{API_BASE_URL}/datasets/{dataset_id}/document/create-by-file",
            key,
            files={"file": (FILE_PATH.name, file, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"data": json.dumps(config, ensure_ascii=False)},
            timeout=120,
        )


def wait_for_index(key: str, dataset_id: str, batch: str) -> tuple[str, str]:
    last_error = ""
    for _ in range(36):
        body = request_json(
            "GET", f"{API_BASE_URL}/datasets/{dataset_id}/documents/{batch}/indexing-status", key, timeout=30
        )
        items = [item for item in body.get("data", []) if isinstance(item, dict)]
        statuses = {str(item.get("indexing_status")) for item in items}
        errors = [str(item.get("error") or "") for item in items if item.get("error")]
        last_error = errors[0] if errors else last_error
        if statuses == {"completed"}:
            return "completed", ""
        if "error" in statuses:
            return "error", last_error
        time.sleep(5)
    return "timeout", last_error


def verify_retrieval(key: str, dataset_id: str) -> int:
    last_error: RuntimeError | None = None
    for attempt in range(1, 4):
        try:
            body = request_json(
                "POST",
                f"{API_BASE_URL}/datasets/{dataset_id}/retrieve",
                key,
                json={
                    "query": "Dify 知识库中的 RAG 过程包含哪些步骤？",
                    "retrieval_model": {
                        "search_method": "semantic_search",
                        "reranking_enable": False,
                        "top_k": 5,
                        "score_threshold_enabled": False,
                    },
                },
                timeout=60,
            )
            records = body.get("records", [])
            return len(records) if isinstance(records, list) else 0
        except RuntimeError as exc:
            last_error = exc
            if attempt < 3:
                time.sleep(attempt * 10)
    if last_error:
        raise last_error
    return 0


def main() -> int:
    try:
        if not FILE_PATH.is_file():
            raise FileNotFoundError(f"本地 DOCX 不存在: {FILE_PATH}")
        key = load_key()
        dataset = find_dataset(key)
        dataset_id = str(dataset["id"])
        document = find_document(key, dataset_id)
        document_id = str(document["id"])
        print(f"目标文档 ID: {document_id}")
        print(f"当前索引状态: {document.get('indexing_status')}")

        if document.get("indexing_status") == "completed":
            hits = verify_retrieval(key, dataset_id)
            print("文档已经完成索引，无需修复")
            print(f"语义检索命中数: {hits}")
            return 0

        for attempt in range(1, MAX_ATTEMPTS + 1):
            print(f"第 {attempt} 次重新创建并索引")
            delete_document(key, dataset_id, document_id)
            result = create_document(key, dataset_id)
            updated = result.get("document") if isinstance(result.get("document"), dict) else {}
            document_id = str(updated.get("id") or document_id)
            batch = str(result.get("batch") or "")
            if not batch:
                raise RuntimeError("更新接口未返回 batch")
            status, error = wait_for_index(key, dataset_id, batch)
            print(f"批次 ID: {batch}")
            print(f"索引状态: {status}")
            if status == "completed":
                hits = verify_retrieval(key, dataset_id)
                print("DOCX 索引修复成功")
                print(f"语义检索命中数: {hits}")
                return 0 if hits > 0 else 2
            if error:
                print(f"本次错误: {error}")
            if attempt < MAX_ATTEMPTS:
                delay = attempt * 15
                print(f"等待 {delay} 秒后重试")
                time.sleep(delay)
    except (OSError, ValueError, RuntimeError, requests.RequestException, requests.JSONDecodeError) as exc:
        print(f"修复失败: {exc}", file=sys.stderr)
        return 1

    print("连续重新索引仍未完成，请检查模型供应商网络连通性", file=sys.stderr)
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
