from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
KEY_FILE = PROJECT_ROOT / "key.txt"
API_BASE_URL = os.getenv("DIFY_API_BASE_URL", "http://localhost/v1").rstrip("/")


def load_api_key() -> str:
    if not KEY_FILE.is_file():
        raise FileNotFoundError(f"知识库 Key 文件不存在: {KEY_FILE}")

    api_key = KEY_FILE.read_text(encoding="utf-8").strip()
    if not api_key:
        raise ValueError(f"知识库 Key 文件为空: {KEY_FILE}")
    return api_key


def get_error_message(response: requests.Response) -> str:
    try:
        body: Any = response.json()
    except requests.JSONDecodeError:
        return response.reason or "未知错误"

    if isinstance(body, dict):
        for field in ("message", "error", "code"):
            value = body.get(field)
            if value:
                return str(value)
    return "服务端返回了未识别的错误响应"


def fetch_datasets(api_key: str) -> list[dict[str, Any]]:
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
            raise RuntimeError(f"HTTP {response.status_code}: {get_error_message(response)}")

        body = response.json()
        page_data = body.get("data") if isinstance(body, dict) else None
        if not isinstance(page_data, list):
            raise RuntimeError("响应中缺少知识库列表")

        datasets.extend(item for item in page_data if isinstance(item, dict))
        if not body.get("has_more"):
            return datasets
        page += 1


def format_timestamp(value: object) -> str:
    if not isinstance(value, (int, float)):
        return "未提供"
    return datetime.fromtimestamp(value).astimezone().isoformat(timespec="seconds")


def format_names(items: object, *, include_type: bool = False) -> str:
    if not isinstance(items, list) or not items:
        return "无"

    values: list[str] = []
    for item in items:
        if not isinstance(item, dict) or not item.get("name"):
            continue
        value = str(item["name"])
        if include_type and item.get("type"):
            value = f"{value} ({item['type']})"
        values.append(value)
    return ", ".join(values) if values else "无"


def print_dataset(index: int, dataset: dict[str, Any]) -> None:
    retrieval = dataset.get("retrieval_model_dict")
    retrieval = retrieval if isinstance(retrieval, dict) else {}
    reranking = retrieval.get("reranking_model")
    reranking = reranking if isinstance(reranking, dict) else {}
    summary = dataset.get("summary_index_setting")
    summary = summary if isinstance(summary, dict) else {}

    print(f"\n[{index}] {dataset.get('name') or '未命名知识库'}")
    print(f"  ID: {dataset.get('id') or '未提供'}")
    print(f"  描述: {dataset.get('description') or '无'}")
    print(f"  提供方式: {dataset.get('provider') or '未提供'}")
    print(f"  权限: {dataset.get('permission') or '未提供'}")
    print(f"  数据源类型: {dataset.get('data_source_type') or '未提供'}")
    print(f"  索引方式: {dataset.get('indexing_technique') or '未提供'}")
    print(f"  文档形式: {dataset.get('doc_form') or '未提供'}")
    print(f"  分段结构: {dataset.get('chunk_structure') or '未提供'}")
    print(f"  Embedding 模型: {dataset.get('embedding_model') or '未配置'}")
    print(f"  Embedding 供应商: {dataset.get('embedding_model_provider') or '未配置'}")
    print(f"  Embedding 可用: {dataset.get('embedding_available')}")
    print(f"  检索方式: {retrieval.get('search_method') or '未提供'}")
    print(f"  Top K: {retrieval.get('top_k', '未提供')}")
    print(f"  Score 阈值启用: {retrieval.get('score_threshold_enabled')}")
    print(f"  Score 阈值: {retrieval.get('score_threshold')}")
    print(f"  Rerank 启用: {retrieval.get('reranking_enable')}")
    print(f"  Rerank 模式: {retrieval.get('reranking_mode') or '未提供'}")
    print(f"  Rerank 模型: {reranking.get('reranking_model_name') or '未配置'}")
    print(f"  Rerank 供应商: {reranking.get('reranking_provider_name') or '未配置'}")
    print(f"  文档数量: {dataset.get('document_count', 0)}")
    print(f"  可用文档数量: {dataset.get('total_available_documents', 0)}")
    print(f"  总文档数量: {dataset.get('total_documents', 0)}")
    print(f"  词数: {dataset.get('word_count', 0)}")
    print(f"  关联应用数量: {dataset.get('app_count', 0)}")
    print(f"  标签: {format_names(dataset.get('tags'))}")
    print(f"  文档元数据: {format_names(dataset.get('doc_metadata'), include_type=True)}")
    print(f"  内置元数据启用: {dataset.get('built_in_field_enabled')}")
    print(f"  摘要索引启用: {summary.get('enable')}")
    print(f"  Service API 启用: {dataset.get('enable_api')}")
    print(f"  已发布: {dataset.get('is_published')}")
    print(f"  多模态: {dataset.get('is_multimodal')}")
    print(f"  创建者: {dataset.get('author_name') or dataset.get('created_by') or '未提供'}")
    print(f"  创建时间: {format_timestamp(dataset.get('created_at'))}")
    print(f"  更新时间: {format_timestamp(dataset.get('updated_at'))}")


def main() -> int:
    try:
        api_key = load_api_key()
        datasets = fetch_datasets(api_key)
    except (FileNotFoundError, ValueError) as exc:
        print(f"配置错误: {exc}", file=sys.stderr)
        return 2
    except requests.RequestException as exc:
        print(f"连接失败: {exc.__class__.__name__}", file=sys.stderr)
        return 3
    except (RuntimeError, requests.JSONDecodeError) as exc:
        print(f"查询失败: {exc}", file=sys.stderr)
        return 4

    print(f"知识库总数: {len(datasets)}")
    if not datasets:
        print("当前工作区没有可见知识库。")
        return 0

    for index, dataset in enumerate(datasets, start=1):
        print_dataset(index, dataset)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
