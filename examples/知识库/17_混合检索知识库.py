"""使用混合检索查询 Dify 知识库。

混合检索 = 关键词检索 + 语义检索。
它既看关键词是否匹配，也看问题和内容在含义上是否相近。

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


def retrieve_by_hybrid_search() -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/retrieve"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "query": QUESTION,
        "retrieval_model": {
            "search_method": "hybrid_search",
            "reranking_enable": False,
            "top_k": 3,
            "score_threshold_enabled": False,
            "weights": {
                "keyword_setting": {
                    "keyword_weight": 0.3,
                },
                "vector_setting": {
                    "vector_weight": 0.7,
                    "embedding_model_name": "BAAI/bge-m3",
                    "embedding_provider_name": "langgenius/siliconflow/siliconflow",
                },
            },
        },
    }

    response = requests.post(url, headers=headers, json=data, timeout=90)
    if not response.ok:
        raise RuntimeError(f"接口请求失败：{response.status_code}\n{response.text}")
    return response.json()


def main() -> None:
    print("开始使用混合检索查询 Dify 知识库...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")
    print(f"问题：{QUESTION}")
    print("关键词权重：0.3")
    print("语义向量权重：0.7")

    result = retrieve_by_hybrid_search()
    records = result.get("records", [])

    print(f"\n命中结果数量：{len(records)}")

    if not records:
        print("没有检索到相关分段。")
        return

    for index, record in enumerate(records, start=1):
        segment = record.get("segment", {})
        content = segment.get("content", "")
        preview = content[:200].replace("\n", " ")

        print(f"\n第 {index} 个命中分段")
        print(f"分数：{record.get('score')}")
        print(f"文档名称：{segment.get('document', {}).get('name')}")
        print(f"分段 ID：{segment.get('id')}")
        print(f"内容预览：{preview}")

    print("\n说明：混合检索会同时利用关键词匹配和语义相似度。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
