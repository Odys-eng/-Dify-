"""使用 Rerank 重排序检索 Dify 知识库。

重排序检索会先找出候选分段，再用 Rerank 模型重新判断这些分段和问题的相关程度。

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


def retrieve_with_rerank() -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/retrieve"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "query": QUESTION,
        "retrieval_model": {
            "search_method": "semantic_search",
            "reranking_enable": True,
            "reranking_mode": "reranking_model",
            "reranking_model": {
                "reranking_provider_name": "langgenius/siliconflow/siliconflow",
                "reranking_model_name": "BAAI/bge-reranker-v2-m3",
            },
            "top_k": 3,
            "score_threshold_enabled": False,
        },
    }

    response = requests.post(url, headers=headers, json=data, timeout=120)
    if not response.ok:
        raise RuntimeError(f"接口请求失败：{response.status_code}\n{response.text}")
    return response.json()


def main() -> None:
    print("开始使用 Rerank 重排序检索 Dify 知识库...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")
    print(f"问题：{QUESTION}")
    print("Rerank 模型：BAAI/bge-reranker-v2-m3")

    result = retrieve_with_rerank()
    records = result.get("records", [])

    print(f"\n重排序后结果数量：{len(records)}")

    if not records:
        print("没有检索到相关分段。")
        return

    for index, record in enumerate(records, start=1):
        segment = record.get("segment", {})
        content = segment.get("content", "")
        preview = content[:200].replace("\n", " ")

        print(f"\n第 {index} 个重排序结果")
        print(f"分数：{record.get('score')}")
        print(f"文档名称：{segment.get('document', {}).get('name')}")
        print(f"分段 ID：{segment.get('id')}")
        print(f"内容预览：{preview}")

    print("\n说明：Rerank 会重新判断候选分段和问题的相关程度，把更相关的内容排到前面。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
