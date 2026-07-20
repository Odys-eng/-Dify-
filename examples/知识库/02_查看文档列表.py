"""查看 Dify 知识库里的文档列表。

使用方法：
1. 确认下面的 API_BASE_URL、API_KEY、DATASET_ID 正确。
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


def get_document_list() -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def main() -> None:
    print("开始查看 Dify 知识库文档列表...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")

    result = get_document_list()
    documents = result.get("data", [])

    print(f"\n文档总数：{result.get('total', len(documents))}")

    if not documents:
        print("这个知识库里还没有文档。")
        return

    for index, document in enumerate(documents, start=1):
        print(f"\n第 {index} 个文档")
        print(f"名称：{document.get('name')}")
        print(f"文档 ID：{document.get('id')}")
        print(f"索引状态：{document.get('indexing_status')}")
        print(f"显示状态：{document.get('display_status')}")
        print(f"字数：{document.get('word_count')}")
        print(f"是否启用：{document.get('enabled')}")

    print("\n原始接口返回：")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
