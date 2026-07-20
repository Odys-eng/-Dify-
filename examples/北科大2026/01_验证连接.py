from __future__ import annotations

import os
import sys
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


def main() -> int:
    try:
        api_key = load_api_key()
        response = requests.get(
            f"{API_BASE_URL}/datasets",
            headers={"Authorization": f"Bearer {api_key}"},
            params={"page": 1, "limit": 20},
            timeout=30,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"配置错误: {exc}", file=sys.stderr)
        return 2
    except requests.RequestException as exc:
        print(f"连接失败: {exc.__class__.__name__}", file=sys.stderr)
        return 3

    if response.status_code != 200:
        print(f"连接失败: HTTP {response.status_code}", file=sys.stderr)
        print(f"服务端信息: {get_error_message(response)}", file=sys.stderr)
        return 4

    try:
        body = response.json()
    except requests.JSONDecodeError:
        print("连接失败: HTTP 200，但响应不是有效 JSON", file=sys.stderr)
        return 5

    datasets = body.get("data") if isinstance(body, dict) else None
    if not isinstance(datasets, list):
        print("连接失败: 响应中缺少知识库列表", file=sys.stderr)
        return 6

    total = body.get("total", len(datasets))
    print("连接成功")
    print(f"API 地址: {API_BASE_URL}/datasets")
    print(f"HTTP 状态: {response.status_code}")
    print(f"当前页知识库数量: {len(datasets)}")
    print(f"知识库总数: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
