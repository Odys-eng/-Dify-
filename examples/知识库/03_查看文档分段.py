"""查看 Dify 知识库中某篇文档的分段列表。

使用方法：
1. 确认下面的 API_BASE_URL、API_KEY、DATASET_ID、DOCUMENT_ID 正确。
2. 右键运行这个 Python 文件。
"""

import requests


# 本地 Docker 启动的 Dify API 地址。如果你的端口不同，改这里。
API_BASE_URL = "http://localhost:12010/v1"

# 知识库 API Key。
API_KEY = "请填写知识库APIKey"

# 目标知识库 ID。
DATASET_ID = "425d72e8-e1b4-4048-aa5d-fd591bd6ac1d"

# 目标文档 ID。这里默认查看 002_Dify知识库API接口整理.md。
DOCUMENT_ID = "0d6bb003-904b-4b92-9bd8-63ea25d7f4a3"


def get_segments() -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{DOCUMENT_ID}/segments"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def main() -> None:
    print("开始查看文档分段列表...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")
    print(f"文档 ID：{DOCUMENT_ID}")

    result = get_segments()
    segments = result.get("data", [])

    print(f"\n分段总数：{result.get('total', len(segments))}")
    print(f"本次返回：{len(segments)} 个")
    print(f"是否还有下一页：{result.get('has_more')}")

    if not segments:
        print("这篇文档还没有分段，可能还没有完成索引。")
        return

    for index, segment in enumerate(segments, start=1):
        content = segment.get("content", "")
        preview = content[:120].replace("\n", " ")

        print(f"\n第 {index} 个分段")
        print(f"分段 ID：{segment.get('id')}")
        print(f"状态：{segment.get('status')}")
        print(f"是否启用：{segment.get('enabled')}")
        print(f"字数：{segment.get('word_count')}")
        print(f"Token 数：{segment.get('tokens')}")
        print(f"内容预览：{preview}")

    print("\n说明：知识库检索时，Dify 主要就是在这些分段里查找相关内容。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
