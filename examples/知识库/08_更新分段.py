"""更新 Dify 知识库文档中的某个分段。

为了让脚本每次都能稳定运行，这个脚本会：
1. 先新增一条临时演示分段。
2. 再更新这条临时分段的内容和关键词。
3. 最后删除这条临时分段，避免留下测试数据。

使用方法：
1. 确认下面的 API_BASE_URL、API_KEY、DATASET_ID、DOCUMENT_ID 正确。
2. 右键运行这个 Python 文件。
"""

import json
import uuid

import requests


# 本地 Docker 启动的 Dify API 地址。如果你的端口不同，改这里。
API_BASE_URL = "http://localhost:12010/v1"

# 知识库 API Key。
API_KEY = "请填写知识库APIKey"

# 目标知识库 ID。
DATASET_ID = "425d72e8-e1b4-4048-aa5d-fd591bd6ac1d"

# 目标文档 ID。这里默认是 002_Dify知识库API接口整理.md。
DOCUMENT_ID = "0d6bb003-904b-4b92-9bd8-63ea25d7f4a3"

# 临时分段内容。用 UUID 保证每次运行都不重复。
OLD_CONTENT = f"这是用于更新接口演示的临时分段，编号：{uuid.uuid4()}"
NEW_CONTENT = f"这是通过 API 更新后的临时分段，编号：{uuid.uuid4()}"


def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def add_temp_segment() -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{DOCUMENT_ID}/segments"
    data = {
        "segments": [
            {
                "content": OLD_CONTENT,
                "keywords": ["临时分段", "更新演示"],
            }
        ]
    }

    response = requests.post(url, headers=get_headers(), json=data, timeout=30)
    response.raise_for_status()
    return response.json()


def update_segment(segment_id: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{DOCUMENT_ID}/segments/{segment_id}"
    data = {
        "segment": {
            "content": NEW_CONTENT,
            "keywords": ["API", "更新分段", "知识库"],
            "enabled": True,
        }
    }

    response = requests.post(url, headers=get_headers(), json=data, timeout=30)
    response.raise_for_status()
    return response.json()["data"]


def get_segment(segment_id: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{DOCUMENT_ID}/segments/{segment_id}"
    response = requests.get(url, headers=get_headers(), timeout=30)
    response.raise_for_status()
    return response.json()["data"]


def delete_segment(segment_id: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{DOCUMENT_ID}/segments/{segment_id}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }

    response = requests.delete(url, headers=headers, timeout=30)
    response.raise_for_status()

    if not response.text.strip():
        return {"result": "success"}
    return response.json()


def main() -> None:
    print("开始演示更新 Dify 知识库文档分段...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")
    print(f"文档 ID：{DOCUMENT_ID}")

    add_result = add_temp_segment()
    segment = add_result.get("data", [{}])[0]
    segment_id = segment.get("id")

    if not segment_id:
        raise RuntimeError("临时分段创建失败，没有拿到分段 ID")

    print("\n临时分段新增成功：")
    print(f"分段 ID：{segment_id}")
    print(f"原内容：{OLD_CONTENT}")

    updated_segment = update_segment(segment_id)
    checked_segment = get_segment(segment_id)

    print("\n临时分段更新成功：")
    print(f"接口返回内容：{updated_segment.get('content')}")
    print(f"查询确认内容：{checked_segment.get('content')}")
    print(f"查询确认关键词：{checked_segment.get('keywords')}")

    delete_result = delete_segment(segment_id)

    print("\n临时分段已删除，接口返回：")
    print(json.dumps(delete_result, ensure_ascii=False, indent=2))
    print("\n说明：更新分段后，知识库会使用新的分段内容参与检索。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
