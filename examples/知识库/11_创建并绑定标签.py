"""创建标签并绑定到 Dify 知识库。

为了让脚本每次都能稳定运行，这个脚本会：
1. 创建一个临时标签。
2. 把标签绑定到当前知识库。
3. 查看当前知识库绑定的标签。
4. 解绑临时标签。
5. 删除临时标签。

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

# 临时标签名称。用 UUID 保证每次运行都不重复。
TEMP_TAG_NAME = f"demo-tag-{uuid.uuid4()}"


def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }


def create_tag() -> dict:
    url = f"{API_BASE_URL}/datasets/tags"
    data = {
        "name": TEMP_TAG_NAME,
    }

    response = requests.post(url, headers=get_headers(), json=data, timeout=30)
    response.raise_for_status()
    return response.json()


def bind_tag(tag_id: str) -> dict:
    url = f"{API_BASE_URL}/datasets/tags/binding"
    data = {
        "tag_ids": [tag_id],
        "target_id": DATASET_ID,
    }

    response = requests.post(url, headers=get_headers(), json=data, timeout=30)
    response.raise_for_status()

    if not response.text.strip():
        return {"result": "success"}
    return response.json()


def get_dataset_tags() -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/tags"

    response = requests.get(url, headers=get_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def unbind_tag(tag_id: str) -> dict:
    url = f"{API_BASE_URL}/datasets/tags/unbinding"
    data = {
        "tag_ids": [tag_id],
        "target_id": DATASET_ID,
    }

    response = requests.post(url, headers=get_headers(), json=data, timeout=30)
    response.raise_for_status()

    if not response.text.strip():
        return {"result": "success"}
    return response.json()


def delete_tag(tag_id: str) -> dict:
    url = f"{API_BASE_URL}/datasets/tags"
    data = {
        "tag_id": tag_id,
    }

    response = requests.delete(url, headers=get_headers(), json=data, timeout=30)
    response.raise_for_status()

    if not response.text.strip():
        return {"result": "success"}
    return response.json()


def main() -> None:
    print("开始演示 Dify 知识库标签管理...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")

    tag = create_tag()
    tag_id = tag.get("id")

    if not tag_id:
        raise RuntimeError("标签创建失败，没有拿到标签 ID")

    print("\n临时标签创建成功：")
    print(f"标签名称：{tag.get('name')}")
    print(f"标签 ID：{tag_id}")

    bind_result = bind_tag(tag_id)
    print("\n标签绑定成功，接口返回：")
    print(json.dumps(bind_result, ensure_ascii=False, indent=2))

    tags_result = get_dataset_tags()
    print("\n当前知识库标签：")
    for item in tags_result.get("data", []):
        print(f"- {item.get('name')}（{item.get('id')}）")

    unbind_result = unbind_tag(tag_id)
    print("\n临时标签解绑成功，接口返回：")
    print(json.dumps(unbind_result, ensure_ascii=False, indent=2))

    delete_result = delete_tag(tag_id)
    print("\n临时标签删除成功，接口返回：")
    print(json.dumps(delete_result, ensure_ascii=False, indent=2))

    print("\n说明：标签可以用来给知识库分类，方便后续筛选和管理。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
