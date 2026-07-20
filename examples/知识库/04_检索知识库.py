"""检索 Dify 知识库，查看命中的相关分段。

使用方法：
1. 确认下面的 API_BASE_URL、API_KEY、DATASET_ID 正确。
2. 可以修改 QUESTION，换成你想问的问题。
3. 右键运行这个 Python 文件。
"""

import json

import requests


# 本地 Docker 启动的 Dify API 地址。如果你的端口不同，改这里。
API_BASE_URL = "http://localhost:12010/v1"

# 知识库 API Key。
API_KEY = "请填写知识库APIKey"

# 目标知识库 ID。
DATASET_ID = "425d72e8-e1b4-4048-aa5d-fd591bd6ac1d"

# 要检索的问题。
QUESTION = "Dify 上传文件到知识库用哪个接口？"


def retrieve_knowledge() -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/retrieve"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "query": QUESTION,
        "retrieval_model": {
            # 本地演示使用关键词检索，不依赖 Embedding 模型配置。
            "search_method": "keyword_search",
            "reranking_enable": False,
            "top_k": 3,
            "score_threshold_enabled": False,
        },
    }

    response = requests.post(url, headers=headers, json=data, timeout=60)
    response.raise_for_status()
    return response.json()


def main() -> None:
    print("开始检索 Dify 知识库...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")
    print(f"问题：{QUESTION}")

    result = retrieve_knowledge()
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
        print(f"文档名称：{segment.get('document', {}).get('name')}")
        print(f"分段 ID：{segment.get('id')}")
        print(f"内容预览：{preview}")

    print("\n说明：检索接口返回的是相关分段，不是大模型最终回答。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
