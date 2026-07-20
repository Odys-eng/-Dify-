"""用 API 创建 Dify 知识库。

为了让脚本每次都能稳定运行，这个脚本会：
1. 创建一个临时知识库。
2. 打印创建结果。
3. 删除这个临时知识库，避免留下测试数据。

使用方法：
1. 确认下面的 API_BASE_URL、API_KEY 正确。
2. 右键运行这个 Python 文件。
"""

import json
import uuid

import requests


# 本地 Docker 启动的 Dify API 地址。如果你的端口不同，改这里。
API_BASE_URL = "http://localhost:12010/v1"

# 知识库 API Key。
API_KEY = "请填写知识库APIKey"

# 临时知识库名称。用 UUID 保证每次运行都不重复。
TEMP_DATASET_NAME = f"demo-dataset-{str(uuid.uuid4())[:8]}"


def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def create_dataset() -> dict:
    url = f"{API_BASE_URL}/datasets"
    data = {
        "name": TEMP_DATASET_NAME,
        "description": "API 创建知识库演示",
        "permission": "only_me",
        "provider": "vendor",
        "indexing_technique": "high_quality",
        "embedding_model": "BAAI/bge-m3",
        "embedding_model_provider": "langgenius/siliconflow/siliconflow",
    }

    response = requests.post(url, headers=get_headers(), json=data, timeout=60)
    response.raise_for_status()
    return response.json()


def delete_dataset(dataset_id: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{dataset_id}"

    response = requests.delete(url, headers=get_headers(), timeout=30)
    response.raise_for_status()

    if not response.text.strip():
        return {"result": "success"}
    return response.json()


def main() -> None:
    print("开始演示用 API 创建 Dify 知识库...")
    print(f"API 地址：{API_BASE_URL}")

    dataset = create_dataset()
    dataset_id = dataset.get("id")

    if not dataset_id:
        raise RuntimeError("知识库创建失败，没有拿到知识库 ID")

    print("\n临时知识库创建成功：")
    print(f"知识库名称：{dataset.get('name')}")
    print(f"知识库 ID：{dataset_id}")
    print(f"索引模式：{dataset.get('indexing_technique')}")
    print(f"嵌入模型：{dataset.get('embedding_model')}")
    print(f"模型供应商：{dataset.get('embedding_model_provider')}")

    delete_result = delete_dataset(dataset_id)

    print("\n临时知识库已删除，接口返回：")
    print(json.dumps(delete_result, ensure_ascii=False, indent=2))
    print("\n说明：创建知识库就是新建一个用于存放文档资料的容器。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
