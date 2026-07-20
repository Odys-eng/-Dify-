"""批量更新 Dify 知识库文档状态。

为了让脚本每次都能稳定运行，这个脚本会：
1. 通过文本创建一篇临时文档。
2. 批量更新这篇文档的状态。
3. 查询确认状态已经生效。
4. 最后删除临时文档，删除后不再做状态更新。

使用方法：
1. 确认下面的 API_BASE_URL、API_KEY、DATASET_ID 正确。
2. 可以修改 ACTION 演示 disable 或 archive。
3. 右键运行这个 Python 文件。
"""

import json
import time
import uuid

import requests


# 本地 Docker 启动的 Dify API 地址。如果你的端口不同，改这里。
API_BASE_URL = "http://localhost:12010/v1"

# 知识库 API Key。
API_KEY = "请填写知识库APIKey"

# 目标知识库 ID。
DATASET_ID = "425d72e8-e1b4-4048-aa5d-fd591bd6ac1d"

# 临时文档名称。用 UUID 保证每次运行都不重复。
DOCUMENT_NAME = f"临时状态演示文档-{str(uuid.uuid4())[:8]}"
DOCUMENT_TEXT = "这是一篇临时文档，用来演示批量禁用和启用文档状态。"

# 本示例只做一次状态更新。连续更新同一篇文档会被后端索引保护锁拦住。
ACTION = "disable"
ACTION_CHECKS = {
    "disable": ("enabled", False),
    "archive": ("archived", True),
}


def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def create_document_by_text() -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/document/create-by-text"
    data = {
        "name": DOCUMENT_NAME,
        "text": DOCUMENT_TEXT,
        "indexing_technique": "high_quality",
        "doc_form": "text_model",
        "doc_language": "Chinese",
        "process_rule": {
            "mode": "automatic",
        },
    }

    response = requests.post(url, headers=get_headers(), json=data, timeout=120)
    response.raise_for_status()
    return response.json()


def get_indexing_status(batch: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{batch}/indexing-status"

    response = requests.get(url, headers=get_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def wait_for_indexing_completed(batch: str) -> None:
    for attempt in range(1, 31):
        status = get_indexing_status(batch)
        items = status.get("data", [])

        if items:
            indexing_status = items[0].get("indexing_status")
            print(f"第 {attempt} 次查询索引状态：{indexing_status}")
            if indexing_status in {"completed", "error"}:
                return
        else:
            print(f"第 {attempt} 次查询索引状态：暂无数据")

        time.sleep(2)

    raise RuntimeError("等待索引完成超时，请稍后重试")


def update_document_status(action: str, document_id: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/status/{action}"
    data = {
        "document_ids": [document_id],
    }

    response = requests.patch(url, headers=get_headers(), json=data, timeout=30)
    if not response.ok:
        raise RuntimeError(f"批量更新文档状态失败：{response.status_code}\n{response.text}")

    if not response.text.strip():
        return {"result": "success"}
    return response.json()


def get_document(document_id: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{document_id}"

    response = requests.get(url, headers=get_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def assert_document_field(document_id: str, field_name: str, expected_value: bool) -> dict:
    # 每次更新后都重新查询，避免只相信接口返回。
    document = get_document(document_id)
    actual_value = document.get(field_name)

    if actual_value is not expected_value:
        raise RuntimeError(f"{field_name} 应该是 {expected_value}，实际是 {actual_value}")

    print(f"查询确认 {field_name} = {actual_value}")
    return document


def delete_document(document_id: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{document_id}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }

    response = requests.delete(url, headers=headers, timeout=30)
    response.raise_for_status()

    if not response.text.strip():
        return {"result": "success"}
    return response.json()


def assert_document_deleted(document_id: str) -> None:
    # 删除是流程终点：这里只确认 404，不再做 enable/disable/archive 等更新。
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{document_id}"

    response = requests.get(url, headers=get_headers(), timeout=30)
    if response.status_code == 404:
        print("查询确认：文档已经删除，后续不再更新它。")
        return

    raise RuntimeError(f"文档删除后仍可查询：{response.status_code}\n{response.text}")


def main() -> None:
    print("开始演示批量更新 Dify 知识库文档状态...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")
    print(f"临时文档名称：{DOCUMENT_NAME}")
    print(f"本次演示动作：{ACTION}")

    if ACTION not in ACTION_CHECKS:
        raise RuntimeError(f"ACTION 只能是：{', '.join(ACTION_CHECKS)}")

    document_id = None

    try:
        create_result = create_document_by_text()
        document = create_result.get("document", {})
        document_id = document.get("id")
        batch = create_result.get("batch")

        if not document_id or not batch:
            raise RuntimeError("临时文档创建成功，但没有拿到 document_id 或 batch")

        print("\n临时文档创建成功：")
        print(f"文档 ID：{document_id}")

        wait_for_indexing_completed(batch)

        check_field, expected_value = ACTION_CHECKS[ACTION]
        update_result = update_document_status(ACTION, document_id)

        print("\n批量更新成功，接口返回：")
        print(json.dumps(update_result, ensure_ascii=False, indent=2))
        assert_document_field(document_id, check_field, expected_value)

        print("\n说明：批量更新文档状态可以一次性启用、禁用或归档多篇文档。")
    finally:
        if document_id:
            delete_result = delete_document(document_id)
            print("\n临时文档已删除，接口返回：")
            print(json.dumps(delete_result, ensure_ascii=False, indent=2))
            assert_document_deleted(document_id)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
