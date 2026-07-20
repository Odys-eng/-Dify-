"""调整知识库检索返回结果数量。

top_k 用来控制最多返回多少个相关分段。
这个脚本会用同一个问题分别演示 top_k = 1、3、5。

使用方法：
1. 确认下面的 API_BASE_URL、API_KEY、DATASET_ID 正确。
2. 可以修改 QUESTION，换成你想问的问题。
3. 右键运行这个 Python 文件。
"""

import requests


# 本地 Docker 启动的 Dify API 地址。如果你的端口不同，改这里。
API_BASE_URL = "http://localhost:12010/v1"

# 知识库 API Key。
API_KEY = "请填写知识库APIKey"

# 目标知识库 ID。
DATASET_ID = "425d72e8-e1b4-4048-aa5d-fd591bd6ac1d"

# 要检索的问题。
QUESTION = "怎么把本地资料导入到 Dify 的知识库？"


def retrieve(top_k: int) -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/retrieve"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "query": QUESTION,
        "retrieval_model": {
            "search_method": "semantic_search",
            "reranking_enable": False,
            "top_k": top_k,
            "score_threshold_enabled": False,
        },
    }

    response = requests.post(url, headers=headers, json=data, timeout=90)
    if not response.ok:
        raise RuntimeError(f"接口请求失败：{response.status_code}\n{response.text}")
    return response.json()


def print_records(top_k: int, result: dict) -> None:
    records = result.get("records", [])

    print(f"\ntop_k = {top_k}")
    print(f"实际返回数量：{len(records)}")

    if not records:
        print("没有检索到相关分段。")
        return

    for index, record in enumerate(records, start=1):
        segment = record.get("segment", {})
        content = segment.get("content", "")
        preview = content[:100].replace("\n", " ")

        print(f"{index}. 分数：{record.get('score')}")
        print(f"   文档：{segment.get('document', {}).get('name')}")
        print(f"   预览：{preview}")


def main() -> None:
    print("开始演示调整检索返回结果数量...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")
    print(f"问题：{QUESTION}")

    for top_k in [1, 3, 5]:
        result = retrieve(top_k)
        print_records(top_k, result)

    print("\n说明：top_k 越大，返回的候选分段越多；top_k 越小，结果越聚焦。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
