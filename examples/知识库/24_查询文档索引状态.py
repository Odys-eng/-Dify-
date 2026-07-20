"""查询 Dify 知识库文档索引状态。

为了让脚本每次都能稳定运行，这个脚本会：
1. 创建一个本地临时文档。
2. 上传临时文档到知识库，并拿到 batch。
3. 轮询查询索引状态，直到 completed 或 error。
4. 删除临时文档，避免留下测试数据。

使用方法：
1. 确认下面的 API_BASE_URL、API_KEY、DATASET_ID 正确。
2. 右键运行这个 Python 文件。
"""

import json
import time
import uuid
from pathlib import Path

import requests


# 本地 Docker 启动的 Dify API 地址。如果你的端口不同，改这里。
API_BASE_URL = "http://localhost:12010/v1"

# 知识库 API Key。
API_KEY = "请填写知识库APIKey"

# 目标知识库 ID。
DATASET_ID = "425d72e8-e1b4-4048-aa5d-fd591bd6ac1d"

# 临时文件路径。
TEMP_FILE = Path(__file__).with_name(f"临时索引状态演示文档-{str(uuid.uuid4())[:8]}.txt")


def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
    }


def create_temp_file() -> None:
    TEMP_FILE.write_text(
        "这是一篇临时索引状态演示文档，用来观察 Dify 上传文档后的处理过程。",
        encoding="utf-8",
    )


def upload_document() -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/document/create-by-file"
    config = {
        "indexing_technique": "high_quality",
        "doc_form": "text_model",
        "doc_language": "Chinese",
        "process_rule": {
            "mode": "automatic",
        },
    }

    with TEMP_FILE.open("rb") as file:
        response = requests.post(
            url,
            headers=get_headers(),
            files={"file": (TEMP_FILE.name, file)},
            data={"data": json.dumps(config, ensure_ascii=False)},
            timeout=120,
        )

    response.raise_for_status()
    return response.json()


def get_indexing_status(batch: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{batch}/indexing-status"

    response = requests.get(url, headers=get_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def wait_for_indexing_completed(batch: str) -> dict:
    latest_status = {}

    for attempt in range(1, 31):
        latest_status = get_indexing_status(batch)
        items = latest_status.get("data", [])

        print(f"\n第 {attempt} 次查询索引状态：")
        if not items:
            print("暂时没有状态数据。")
        else:
            for item in items:
                print(f"文档 ID：{item.get('id')}")
                print(f"索引状态：{item.get('indexing_status')}")
                print(f"处理阶段：{item.get('processing_status')}")

            statuses = {item.get("indexing_status") for item in items}
            if "completed" in statuses or "error" in statuses:
                return latest_status

        time.sleep(2)

    return latest_status


def delete_document(document_id: str) -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}/documents/{document_id}"

    response = requests.delete(url, headers=get_headers(), timeout=30)
    response.raise_for_status()

    if not response.text.strip():
        return {"result": "success"}
    return response.json()


def main() -> None:
    print("开始演示查询 Dify 文档索引状态...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")

    create_temp_file()
    print(f"\n已创建本地临时文件：{TEMP_FILE}")

    upload_result = upload_document()
    document = upload_result.get("document", {})
    document_id = document.get("id")
    batch = upload_result.get("batch")

    if not document_id or not batch:
        raise RuntimeError("上传成功，但没有拿到 document_id 或 batch")

    print("\n临时文档上传成功：")
    print(f"文档 ID：{document_id}")
    print(f"batch：{batch}")

    final_status = wait_for_indexing_completed(batch)

    print("\n最终索引状态：")
    print(json.dumps(final_status, ensure_ascii=False, indent=2))

    delete_result = delete_document(document_id)
    print("\n临时文档已删除，接口返回：")
    print(json.dumps(delete_result, ensure_ascii=False, indent=2))

    print("\n说明：文档上传成功后，还需要等待索引完成，才能稳定参与知识库检索。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
    finally:
        if TEMP_FILE.exists():
            TEMP_FILE.unlink()
