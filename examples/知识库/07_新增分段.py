"""向 Dify 知识库文档中新增一个分段。

使用方法：
1. 确认下面的 API_BASE_URL、API_KEY、DATASET_ID、DOCUMENT_ID 正确。
2. 可以修改 SEGMENT_CONTENT，换成你想补充的知识内容。
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

# 目标文档 ID。这里默认给 002_Dify知识库API接口整理.md 新增分段。
DOCUMENT_ID = "0d6bb003-904b-4b92-9bd8-63ea25d7f4a3"

# 要新增到文档里的知识内容。
SEGMENT_CONTENT = "这是通过 API 手动新增的演示分段，用来说明 Dify 支持在已有文档中补充新的知识内容。"


def add_segment() -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{DOCUMENT_ID}/segments"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "segments": [
            {
                "content": SEGMENT_CONTENT,
                "keywords": ["API", "新增分段", "知识库"],
            }
        ]
    }

    response = requests.post(url, headers=headers, json=data, timeout=30)
    response.raise_for_status()
    return response.json()


def main() -> None:
    print("开始向 Dify 知识库文档中新增分段...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")
    print(f"文档 ID：{DOCUMENT_ID}")
    print(f"新增内容：{SEGMENT_CONTENT}")

    result = add_segment()

    print("\n新增成功，接口返回：")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("\n说明：再次运行这个脚本，会再次新增一条相同内容的分段。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
