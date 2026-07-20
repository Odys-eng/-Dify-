"""更新 Dify 知识库配置。

为了让脚本每次都能稳定运行，这个脚本会：
1. 创建一个临时知识库。
2. 更新临时知识库的名称和描述。
3. 查看更新后的结果。
4. 删除临时知识库，避免留下测试数据。

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

# 临时知识库名称。知识库名称最多 40 个字符，所以这里只使用短 ID。
TEMP_DATASET_NAME = f"demo-dataset-{str(uuid.uuid4())[:8]}"
UPDATED_DATASET_NAME = f"updated-demo-{str(uuid.uuid4())[:8]}"


def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def create_dataset() -> dict:
    url = f"{API_BASE_URL}/datasets"
    data = {
        "name": TEMP_DATASET_NAME,
        "description": "更新知识库配置演示：创建时的描述",
        "permission": "only_me",
        "provider": "vendor",
        "indexing_technique": "high_quality",
        "embedding_model": "BAAI/bge-m3",
        "embedding_model_provider": "langgenius/siliconflow/siliconflow",
    }

    response = requests.post(url, headers=get_headers(), json=data, timeout=60)
    response.raise_for_status()
    return response.json()


def update_dataset(dataset_id: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{dataset_id}"
    data = {
        "name": UPDATED_DATASET_NAME,
        "description": "更新知识库配置演示：这是更新后的描述",
        "permission": "only_me",
        "indexing_technique": "high_quality",
        "embedding_model": "BAAI/bge-m3",
        "embedding_model_provider": "langgenius/siliconflow/siliconflow",
    }

    response = requests.patch(url, headers=get_headers(), json=data, timeout=60)
    response.raise_for_status()
    return response.json()


def get_dataset(dataset_id: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{dataset_id}"

    response = requests.get(url, headers=get_headers(), timeout=30)
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
    print("开始演示更新 Dify 知识库配置...")
    print(f"API 地址：{API_BASE_URL}")

    dataset = create_dataset()
    dataset_id = dataset.get("id")

    if not dataset_id:
        raise RuntimeError("知识库创建失败，没有拿到知识库 ID")

    print("\n临时知识库创建成功：")
    print(f"知识库名称：{dataset.get('name')}")
    print(f"知识库 ID：{dataset_id}")
    print(f"描述：{dataset.get('description')}")

    updated_dataset = update_dataset(dataset_id)
    print("\n知识库配置更新成功：")
    print(f"新名称：{updated_dataset.get('name')}")
    print(f"新描述：{updated_dataset.get('description')}")

    checked_dataset = get_dataset(dataset_id)
    print("\n查询确认更新结果：")
    print(f"知识库名称：{checked_dataset.get('name')}")
    print(f"描述：{checked_dataset.get('description')}")
    print(f"索引模式：{checked_dataset.get('indexing_technique')}")
    print(f"嵌入模型：{checked_dataset.get('embedding_model')}")

    delete_result = delete_dataset(dataset_id)

    print("\n临时知识库已删除，接口返回：")
    print(json.dumps(delete_result, ensure_ascii=False, indent=2))
    print("\n说明：更新知识库配置可以修改名称、描述、权限和检索相关设置。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
