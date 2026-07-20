from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
KEY_FILE = PROJECT_ROOT / "key.txt"
DOCUMENT_FILE = PROJECT_ROOT / "Dify 知识库接口文档.md"
API_BASE_URL = os.getenv("DIFY_API_BASE_URL", "http://localhost/v1").rstrip("/")
TARGET_DATASET_NAME = "零基础AI编程"


def load_api_key() -> str:
    if not KEY_FILE.is_file():
        raise FileNotFoundError(f"知识库 Key 文件不存在: {KEY_FILE}")
    api_key = KEY_FILE.read_text(encoding="utf-8").strip()
    if not api_key:
        raise ValueError(f"知识库 Key 文件为空: {KEY_FILE}")
    return api_key


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
    datasets: list[dict[str, Any]] = []
    page = 1
    while True:
        response = requests.get(
            f"{API_BASE_URL}/datasets",
            headers={"Authorization": f"Bearer {api_key}"},
            params={"page": page, "limit": 100},
            timeout=30,
        )
        if response.status_code != 200:
            raise RuntimeError(f"查询知识库失败: HTTP {response.status_code}: {error_message(response)}")
        body = response.json()
        page_data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(page_data, list):
            raise RuntimeError("查询知识库失败: 响应中缺少 data 列表")
        datasets.extend(item for item in page_data if isinstance(item, dict))
        if not body.get("has_more"):
            return datasets
        page += 1


def upload_document(api_key: str, dataset_id: str) -> dict[str, Any]:
    if not DOCUMENT_FILE.is_file():
        raise FileNotFoundError(f"上传文档不存在: {DOCUMENT_FILE}")

    config = {
        "indexing_technique": "high_quality",
        "doc_form": "text_model",
        "doc_language": "Chinese",
        "process_rule": {"mode": "automatic"},
    }
    with DOCUMENT_FILE.open("rb") as file:
        response = requests.post(
            f"{API_BASE_URL}/datasets/{dataset_id}/document/create-by-file",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": (DOCUMENT_FILE.name, file, "text/markdown")},
            data={"data": json.dumps(config, ensure_ascii=False)},
            timeout=120,
        )
    if response.status_code not in (200, 201):
        raise RuntimeError(f"上传失败: HTTP {response.status_code}: {error_message(response)}")
    body = response.json()
    return body if isinstance(body, dict) else {}


def create_dataset(api_key: str) -> dict[str, Any]:
    payload = {
        "name": TARGET_DATASET_NAME,
        "description": "零基础 AI 编程知识库",
        "permission": "only_me",
        "provider": "vendor",
        "indexing_technique": "high_quality",
        "embedding_model": "BAAI/bge-m3",
        "embedding_model_provider": "langgenius/siliconflow/siliconflow",
    }
    response = requests.post(
        f"{API_BASE_URL}/datasets",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if response.status_code not in (200, 201):
        raise RuntimeError(f"创建知识库失败: HTTP {response.status_code}: {error_message(response)}")
    body = response.json()
    if not isinstance(body, dict) or not body.get("id"):
        raise RuntimeError("创建知识库失败: 响应中缺少知识库 ID")
    return body


def main() -> int:
    try:
        api_key = load_api_key()
        datasets = list_datasets(api_key)
        matches = [item for item in datasets if item.get("name") == TARGET_DATASET_NAME]
        if len(matches) > 1:
            print(f"存在多个同名知识库，已停止以避免误上传: {TARGET_DATASET_NAME}", file=sys.stderr)
            return 4
        if matches:
            dataset = matches[0]
            created = False
        else:
            dataset = create_dataset(api_key)
            created = True
        result = upload_document(api_key, str(dataset["id"]))
    except (FileNotFoundError, ValueError) as exc:
        print(f"配置错误: {exc}", file=sys.stderr)
        return 2
    except requests.RequestException as exc:
        print(f"连接失败: {exc.__class__.__name__}", file=sys.stderr)
        return 3
    except (RuntimeError, requests.JSONDecodeError) as exc:
        print(f"上传失败: {exc}", file=sys.stderr)
        return 5

    document = result.get("document") if isinstance(result.get("document"), dict) else {}
    print("知识库已创建" if created else "知识库已存在")
    print("上传成功")
    print(f"目标知识库: {TARGET_DATASET_NAME}")
    print(f"知识库 ID: {dataset['id']}")
    print(f"文档名称: {document.get('name') or DOCUMENT_FILE.name}")
    print(f"文档 ID: {document.get('id') or '未返回'}")
    print(f"批次 ID: {result.get('batch') or '未返回'}")
    print("后续状态: 文档需要等待解析、切分和索引完成后才可检索")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
