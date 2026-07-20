"""通过文本更新 Dify 知识库文档。

为了让脚本每次都能稳定运行，这个脚本会：
1. 先通过文本创建一篇临时文档。
2. 再用新的文本内容更新这篇临时文档。
3. 轮询索引状态，直到 completed 或 error。
4. 查询分段，确认内容已经更新。
5. 删除临时文档，避免留下测试数据。

使用方法：
1. 确认下面的 API_BASE_URL、API_KEY、DATASET_ID 正确。
2. 可以修改 OLD_TEXT 和 NEW_TEXT。
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
DOCUMENT_NAME = f"临时文本更新文档-{str(uuid.uuid4())[:8]}"

OLD_TEXT = "这是更新前的文本内容，用来演示通过文本创建文档。"
NEW_TEXT = "这是更新后的文本内容，用来演示通过 API 直接替换已有文档的文字资料。"


def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def create_document_by_text() -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/document/create-by-text"
    data = {
        "name": DOCUMENT_NAME,
        "text": OLD_TEXT,
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


def update_document_by_text(document_id: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{document_id}/update-by-text"
    data = {
        "name": DOCUMENT_NAME,
        "text": NEW_TEXT,
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


def wait_for_indexing_completed(batch: str) -> dict:
    latest_status = {}

    for attempt in range(1, 31):
        latest_status = get_indexing_status(batch)
        items = latest_status.get("data", [])

        print(f"\n第 {attempt} 次查询索引状态：")
        if not items:
            print("暂时没有状态数据。")
        else:
            for item in items:
                print(f"文档 ID：{item.get('id')}")
                print(f"索引状态：{item.get('indexing_status')}")
                print(f"完成分段：{item.get('completed_segments')} / {item.get('total_segments')}")

            statuses = {item.get("indexing_status") for item in items}
            if "completed" in statuses or "error" in statuses:
                return latest_status

        time.sleep(2)

    return latest_status


def list_segments(document_id: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{document_id}/segments"

    response = requests.get(url, headers=get_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


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


def main() -> None:
    print("开始演示通过文本更新 Dify 知识库文档...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")
    print(f"文档名称：{DOCUMENT_NAME}")

    document_id = None

    try:
        create_result = create_document_by_text()
        document = create_result.get("document", {})
        document_id = document.get("id")
        create_batch = create_result.get("batch")

        if not document_id or not create_batch:
            raise RuntimeError("临时文档创建成功，但没有拿到 document_id 或 batch")

        print("\n临时文本型文档创建成功：")
        print(f"文档 ID：{document_id}")
        print(f"原文本：{OLD_TEXT}")

        print("\n等待临时文档第一次索引完成...")
        wait_for_indexing_completed(create_batch)

        update_result = update_document_by_text(document_id)
        batch = update_result.get("batch")

        if not batch:
            raise RuntimeError("文档更新成功，但没有拿到 batch")

        print("\n文档文本更新成功：")
        print(f"新文本：{NEW_TEXT}")
        print(f"batch：{batch}")

        final_status = wait_for_indexing_completed(batch)
        print("\n最终索引状态：")
        print(json.dumps(final_status, ensure_ascii=False, indent=2))

        segments_result = list_segments(document_id)
        segments = segments_result.get("data", [])

        print("\n更新后的分段内容：")
        for segment in segments:
            print(f"- {segment.get('content')}")

        if not any(NEW_TEXT in segment.get("content", "") for segment in segments):
            raise RuntimeError("没有在分段中确认到更新后的文本内容")

        print("\n说明：通过文本更新文档适合直接替换知识库里的文字资料。")
    finally:
        if document_id:
            delete_result = delete_document(document_id)
            print("\n临时文档已删除，接口返回：")
            print(json.dumps(delete_result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
