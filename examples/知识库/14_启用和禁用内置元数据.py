"""启用和禁用 Dify 知识库内置元数据。

为了让脚本每次都能稳定运行，这个脚本会：
1. 查看 Dify 支持的内置元数据字段。
2. 启用内置元数据。
3. 查看文档列表，确认文档出现内置元数据。
4. 禁用内置元数据，恢复演示前的状态。

使用方法：
1. 确认下面的 API_BASE_URL、API_KEY、DATASET_ID、DOCUMENT_ID 正确。
2. 右键运行这个 Python 文件。
"""

import json

import requests


# 本地 Docker 启动的 Dify API 地址。如果你的端口不同，改这里。
API_BASE_URL = "http://localhost:12010/v1"

# 知识库 API Key。
API_KEY = "请填写知识库APIKey"

# 目标知识库 ID。
DATASET_ID = "425d72e8-e1b4-4048-aa5d-fd591bd6ac1d"

# 目标文档 ID。这里默认是 002_Dify知识库API接口整理.md。
DOCUMENT_ID = "0d6bb003-904b-4b92-9bd8-63ea25d7f4a3"


def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def list_built_in_fields() -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/metadata/built-in"

    response = requests.get(url, headers=get_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def get_metadata_status() -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/metadata"

    response = requests.get(url, headers=get_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def set_built_in_metadata(action: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/metadata/built-in/{action}"

    response = requests.post(url, headers=get_headers(), timeout=30)
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


def main() -> None:
    print("开始演示 Dify 知识库内置元数据...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")
    print(f"文档 ID：{DOCUMENT_ID}")

    built_in_fields = list_built_in_fields()
    print("\nDify 支持的内置元数据字段：")
    for field in built_in_fields.get("fields", []):
        print(f"- {field.get('name')}（{field.get('type')}）")

    before_status = get_metadata_status()
    print("\n启用前状态：")
    print(f"built_in_field_enabled = {before_status.get('built_in_field_enabled')}")

    enable_result = set_built_in_metadata("enable")
    print("\n内置元数据已启用，接口返回：")
    print(json.dumps(enable_result, ensure_ascii=False, indent=2))

    after_enable_status = get_metadata_status()
    print(f"启用后状态：built_in_field_enabled = {after_enable_status.get('built_in_field_enabled')}")

    document_metadata = get_document_metadata()
    print("\n目标文档中的内置元数据：")
    for item in document_metadata:
        if item.get("id") == "built-in":
            print(f"- {item.get('name')} = {item.get('value')}")

    disable_result = set_built_in_metadata("disable")
    print("\n内置元数据已禁用，接口返回：")
    print(json.dumps(disable_result, ensure_ascii=False, indent=2))

    after_disable_status = get_metadata_status()
    print(f"禁用后状态：built_in_field_enabled = {after_disable_status.get('built_in_field_enabled')}")

    print("\n说明：内置元数据由 Dify 自动提供，例如文档名称、上传人、上传时间和来源。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
