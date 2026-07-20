"""给 Dify 知识库文档写入元数据。

为了让脚本每次都能稳定运行，这个脚本会：
1. 创建一个临时元数据字段。
2. 给 002 文档写入这个元数据字段的值。
3. 查看文档列表，确认元数据已经写入。
4. 删除临时元数据字段，避免留下测试数据。

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

# 临时元数据字段和值。用 UUID 保证每次运行都不重复。
TEMP_METADATA_NAME = f"demo_course_{str(uuid.uuid4()).replace('-', '_')[:8]}"
TEMP_METADATA_VALUE = "零基础AI编程"


def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def create_metadata_field() -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/metadata"
    data = {
        "name": TEMP_METADATA_NAME,
        "type": "string",
    }

    response = requests.post(url, headers=get_headers(), json=data, timeout=30)
    response.raise_for_status()
    return response.json()


def write_document_metadata(metadata_id: str, metadata_name: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/metadata"
    data = {
        "operation_data": [
            {
                "document_id": DOCUMENT_ID,
                "metadata_list": [
                    {
                        "id": metadata_id,
                        "name": metadata_name,
                        "value": TEMP_METADATA_VALUE,
                    }
                ],
            }
        ]
    }

    response = requests.post(url, headers=get_headers(), json=data, timeout=30)
    response.raise_for_status()
    return response.json()


def get_document_metadata() -> list:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents"

    response = requests.get(url, headers=get_headers(), timeout=30)
    response.raise_for_status()

    for document in response.json().get("data", []):
        if document.get("id") == DOCUMENT_ID:
            return document.get("doc_metadata", [])

    raise RuntimeError("没有在文档列表中找到目标文档")


def delete_metadata_field(metadata_id: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/metadata/{metadata_id}"

    response = requests.delete(url, headers=get_headers(), timeout=30)
    response.raise_for_status()

    if not response.text.strip():
        return {"result": "success"}
    return response.json()


def main() -> None:
    print("开始演示给 Dify 知识库文档写入元数据...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")
    print(f"文档 ID：{DOCUMENT_ID}")

    field = create_metadata_field()
    metadata_id = field.get("id")
    metadata_name = field.get("name")

    if not metadata_id or not metadata_name:
        raise RuntimeError("元数据字段创建失败，没有拿到字段 ID 或名称")

    print("\n临时元数据字段创建成功：")
    print(f"字段名称：{metadata_name}")
    print(f"字段 ID：{metadata_id}")

    write_result = write_document_metadata(metadata_id, metadata_name)
    print("\n文档元数据写入成功，接口返回：")
    print(json.dumps(write_result, ensure_ascii=False, indent=2))

    metadata_list = get_document_metadata()
    matched = [
        item
        for item in metadata_list
        if item.get("id") == metadata_id and item.get("value") == TEMP_METADATA_VALUE
    ]

    if not matched:
        raise RuntimeError("没有在文档列表中确认到刚写入的元数据")

    print("\n已从文档列表中确认元数据：")
    print(json.dumps(matched[0], ensure_ascii=False, indent=2))

    delete_result = delete_metadata_field(metadata_id)
    print("\n临时元数据字段已删除，接口返回：")
    print(json.dumps(delete_result, ensure_ascii=False, indent=2))

    print("\n说明：文档元数据可以记录课程阶段、资料来源、适用对象等结构化信息。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
