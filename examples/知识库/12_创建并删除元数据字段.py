"""创建并删除 Dify 知识库元数据字段。

为了让脚本每次都能稳定运行，这个脚本会：
1. 创建一个临时元数据字段。
2. 查看当前知识库的元数据字段列表。
3. 删除这个临时元数据字段。
4. 再次查看列表，确认临时字段已经删除。

使用方法：
1. 确认下面的 API_BASE_URL、API_KEY、DATASET_ID 正确。
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

# 临时元数据字段名称。用 UUID 保证每次运行都不重复。
TEMP_METADATA_NAME = f"demo_metadata_{str(uuid.uuid4()).replace('-', '_')[:8]}"


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


def list_metadata_fields() -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/metadata"

    response = requests.get(url, headers=get_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def delete_metadata_field(metadata_id: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/metadata/{metadata_id}"

    response = requests.delete(url, headers=get_headers(), timeout=30)
    response.raise_for_status()

    if not response.text.strip():
        return {"result": "success"}
    return response.json()


def print_metadata_list(title: str, result: dict) -> None:
    fields = result.get("doc_metadata", [])
    print(f"\n{title}")
    print(f"字段数量：{len(fields)}")

    if not fields:
        print("当前没有自定义元数据字段。")
        return

    for field in fields:
        print(f"- {field.get('name')}（{field.get('type')}，ID：{field.get('id')}）")


def main() -> None:
    print("开始演示 Dify 知识库元数据字段管理...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")

    created_field = create_metadata_field()
    metadata_id = created_field.get("id")

    if not metadata_id:
        raise RuntimeError("元数据字段创建失败，没有拿到字段 ID")

    print("\n临时元数据字段创建成功：")
    print(f"字段名称：{created_field.get('name')}")
    print(f"字段类型：{created_field.get('type')}")
    print(f"字段 ID：{metadata_id}")

    after_create = list_metadata_fields()
    print_metadata_list("创建后的元数据字段列表：", after_create)

    delete_result = delete_metadata_field(metadata_id)
    print("\n临时元数据字段删除成功，接口返回：")
    print(json.dumps(delete_result, ensure_ascii=False, indent=2))

    after_delete = list_metadata_fields()
    print_metadata_list("删除后的元数据字段列表：", after_delete)

    print("\n说明：元数据字段可以用来记录文档来源、类型、课程阶段等结构化信息。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
