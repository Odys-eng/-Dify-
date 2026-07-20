"""删除 Dify 知识库中的文档。

为了避免误删课程资料，这个脚本会：
1. 先上传一篇临时演示文档。
2. 再删除这篇临时演示文档。

使用方法：
1. 确认下面的 API_BASE_URL、API_KEY、DATASET_ID 正确。
2. 右键运行这个 Python 文件。
"""

import json
from pathlib import Path

import requests


# 本地 Docker 启动的 Dify API 地址。如果你的端口不同，改这里。
API_BASE_URL = "http://localhost:12010/v1"

# 知识库 API Key。
API_KEY = "请填写知识库APIKey"

# 目标知识库 ID。
DATASET_ID = "425d72e8-e1b4-4048-aa5d-fd591bd6ac1d"

# 临时演示文件。脚本会自动创建它，然后上传、删除。
DEMO_FILE = Path(__file__).with_name("临时删除演示文档.txt")


def create_demo_file() -> None:
    DEMO_FILE.write_text(
        "这是一篇临时删除演示文档，用来演示 Dify 知识库删除文档接口。",
        encoding="utf-8",
    )


def upload_demo_document() -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/document/create-by-file"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }
    config = {
        "indexing_technique": "high_quality",
        "doc_form": "text_model",
        "doc_language": "Chinese",
        "process_rule": {
            "mode": "automatic",
        },
    }

    with DEMO_FILE.open("rb") as file:
        response = requests.post(
            url,
            headers=headers,
            files={"file": (DEMO_FILE.name, file)},
            data={"data": json.dumps(config, ensure_ascii=False)},
            timeout=120,
        )

    response.raise_for_status()
    return response.json()


def delete_document(document_id: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{document_id}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }

    response = requests.delete(url, headers=headers, timeout=30)
    response.raise_for_status()
    if not response.text.strip():
        return {"result": "success"}
    return response.json()


def main() -> None:
    print("开始演示删除 Dify 知识库文档...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")

    create_demo_file()
    print(f"\n已创建临时文件：{DEMO_FILE}")

    upload_result = upload_demo_document()
    document = upload_result.get("document", {})
    document_id = document.get("id")
    document_name = document.get("name")

    print("\n临时文档上传成功：")
    print(f"文档名称：{document_name}")
    print(f"文档 ID：{document_id}")

    if not document_id:
        raise RuntimeError("上传成功，但没有拿到 document_id，无法继续删除")

    delete_result = delete_document(document_id)

    print("\n临时文档删除成功，接口返回：")
    print(json.dumps(delete_result, ensure_ascii=False, indent=2))
    print("\n说明：删除后，这篇文档不会继续参与知识库检索和回答。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
    finally:
        if DEMO_FILE.exists():
            DEMO_FILE.unlink()
