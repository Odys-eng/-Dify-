"""用 Python 上传文档到 Dify 知识库。

使用方法：
1. 修改下面的 API_BASE_URL、API_KEY、DATASET_ID、FILE_PATH。
2. 右键运行这个 Python 文件。
"""

import json
from pathlib import Path

import requests


# 本地 Docker 启动的 Dify API 地址。如果你的端口不同，改这里。
API_BASE_URL = "http://localhost:12010/v1"

# 知识库 API Key。
API_KEY = "请填写知识库APIKey"

# 目标知识库 ID。请改成你自己的知识库 ID。
DATASET_ID = "425d72e8-e1b4-4048-aa5d-fd591bd6ac1d"

# 本次演示要上传的文件。
FILE_PATH = Path(r"D:\知识库\零基础AI编程\002_Dify知识库API接口整理.md")


def upload_document() -> dict:
    if DATASET_ID == "请填写你的知识库ID":
        raise RuntimeError("请先把 DATASET_ID 改成你的知识库 ID")

    if not FILE_PATH.exists():
        raise FileNotFoundError(f"文件不存在：{FILE_PATH}")

    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/document/create-by-file"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }

    # data 用来告诉 Dify：用自动规则处理这个中文文档。
    config = {
        "indexing_technique": "high_quality",
        "doc_form": "text_model",
        "doc_language": "Chinese",
        "process_rule": {
            "mode": "automatic",
        },
    }

    with FILE_PATH.open("rb") as file:
        response = requests.post(
            url,
            headers=headers,
            files={"file": (FILE_PATH.name, file)},
            data={"data": json.dumps(config, ensure_ascii=False)},
            timeout=120,
        )

    response.raise_for_status()
    return response.json()


def main() -> None:
    print("开始上传文档到 Dify 知识库...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"上传文件：{FILE_PATH}")

    result = upload_document()

    print("\n上传成功，接口返回：")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    batch = result.get("batch")
    if batch:
        print(f"\n索引任务 batch：{batch}")
        print("提示：上传成功不代表马上可以检索，Dify 还需要解析、切分和索引文档。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
