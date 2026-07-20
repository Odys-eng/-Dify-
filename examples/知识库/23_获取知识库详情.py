"""获取 Dify 知识库详情。

这个脚本会读取指定知识库的基础信息和检索配置。

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


def get_dataset_detail() -> dict:
    url = f"{API_BASE_URL}/datasets/{DATASET_ID}"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


def main() -> None:
    print("开始获取 Dify 知识库详情...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"知识库 ID：{DATASET_ID}")

    dataset = get_dataset_detail()
    retrieval_model = dataset.get("retrieval_model_dict", {})

    print("\n基础信息：")
    print(f"名称：{dataset.get('name')}")
    print(f"描述：{dataset.get('description')}")
    print(f"权限：{dataset.get('permission')}")
    print(f"文档数量：{dataset.get('document_count')}")
    print(f"总字数：{dataset.get('word_count')}")

    print("\n索引与模型：")
    print(f"索引模式：{dataset.get('indexing_technique')}")
    print(f"嵌入模型：{dataset.get('embedding_model')}")
    print(f"模型供应商：{dataset.get('embedding_model_provider')}")

    print("\n检索配置：")
    print(f"检索方式：{retrieval_model.get('search_method')}")
    print(f"top_k：{retrieval_model.get('top_k')}")
    print(f"启用重排序：{retrieval_model.get('reranking_enable')}")
    print(f"启用相似度阈值：{retrieval_model.get('score_threshold_enabled')}")
    print(f"相似度阈值：{retrieval_model.get('score_threshold')}")

    print("\n标签与元数据：")
    print(f"标签：{dataset.get('tags')}")
    print(f"自定义元数据：{dataset.get('doc_metadata')}")
    print(f"启用内置元数据：{dataset.get('built_in_field_enabled')}")

    print("\n原始接口返回：")
    print(json.dumps(dataset, ensure_ascii=False, indent=2)[:2000])
    print("\n说明：获取知识库详情常用于检查知识库配置是否符合预期。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
