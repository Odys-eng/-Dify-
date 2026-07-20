"""设置相似度阈值，过滤相关性较弱的检索结果。

这个脚本会用同一个问题做两次语义检索：
1. 不启用相似度阈值。
2. 启用较高的相似度阈值。

使用方法：
1. 确认下面的 API_BASE_URL、API_KEY、DATASET_ID 正确。
2. 可以修改 QUESTION 和 SCORE_THRESHOLD。
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

# 最低相似度分数。分数低于这个值的结果会被过滤掉。
SCORE_THRESHOLD = 0.7


def retrieve(score_threshold_enabled: bool) -> dict:
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
            "top_k": 5,
            "score_threshold_enabled": score_threshold_enabled,
            "score_threshold": SCORE_THRESHOLD,
        },
    }

    response = requests.post(url, headers=headers, json=data, timeout=90)
    if not response.ok:
        raise RuntimeError(f"接口请求失败：{response.status_code}\n{response.text}")
    return response.json()


def print_records(title: str, result: dict) -> None:
    records = result.get("records", [])

    print(f"\n{title}")
    print(f"命中结果数量：{len(records)}")

    if not records:
        print("没有检索到满足条件的分段。")
        return

    for index, record in enumerate(records, start=1):
        segment = record.get("segment", {})
        content = segment.get("content", "")
        preview = content[:120].replace("\n", " ")

        print(f"\n第 {index} 个结果")
        print(f"分数：{record.get('score')}")
        print(f"文档名称：{segment.get('document', {}).get('name')}")
        print(f"内容预览：{preview}")


def main() -> None:
    print("开始演示相似度阈值过滤...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")
    print(f"问题：{QUESTION}")
    print(f"相似度阈值：{SCORE_THRESHOLD}")

    result_without_threshold = retrieve(score_threshold_enabled=False)
    print_records("不启用相似度阈值：", result_without_threshold)

    result_with_threshold = retrieve(score_threshold_enabled=True)
    print_records("启用相似度阈值后：", result_with_threshold)

    print("\n说明：相似度阈值可以过滤掉分数较低、相关性较弱的检索结果。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
