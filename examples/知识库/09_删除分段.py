"""删除 Dify 知识库文档中的某个分段。

为了让脚本每次都能稳定运行，这个脚本会：
1. 先新增一条临时演示分段。
2. 再从分段列表中查找这条临时分段。
3. 最后删除找到的临时分段。

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
TEMP_SEGMENT_CONTENT = f"这是用于删除接口演示的临时分段，编号：{uuid.uuid4()}"


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
                "content": TEMP_SEGMENT_CONTENT,
                "keywords": ["临时分段", "删除演示"],
            }
        ]
    }

    response = requests.post(url, headers=get_headers(), json=data, timeout=30)
    response.raise_for_status()
    return response.json()


def find_segment_by_content(content: str) -> dict | None:
    page = 1

    while True:
        url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{DOCUMENT_ID}/segments"
        response = requests.get(
            url,
            headers=get_headers(),
            params={"page": page, "limit": 100},
            timeout=30,
        )
        response.raise_for_status()

        result = response.json()
        for segment in result.get("data", []):
            if segment.get("content") == content:
                return segment

        if not result.get("has_more"):
            return None

        page += 1


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
    print("开始演示删除 Dify 知识库文档分段...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")
    print(f"文档 ID：{DOCUMENT_ID}")

    add_result = add_temp_segment()
    created_segment = add_result.get("data", [{}])[0]
    created_segment_id = created_segment.get("id")

    print("\n临时分段新增成功：")
    print(f"分段 ID：{created_segment_id}")
    print(f"分段内容：{TEMP_SEGMENT_CONTENT}")

    found_segment = find_segment_by_content(TEMP_SEGMENT_CONTENT)
    if not found_segment:
        raise RuntimeError("没有在分段列表中找到刚刚新增的临时分段")

    segment_id = found_segment["id"]
    print("\n已从分段列表中找到临时分段：")
    print(f"分段 ID：{segment_id}")

    delete_result = delete_segment(segment_id)

    print("\n临时分段删除成功，接口返回：")
    print(json.dumps(delete_result, ensure_ascii=False, indent=2))
    print("\n说明：删除后，这个分段不会继续参与知识库检索。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
