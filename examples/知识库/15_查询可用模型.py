"""查询 Dify 当前工作区可用的模型。

知识库常用的模型包括：
- text-embedding：把文本转成向量，用于语义检索。
- rerank：对检索结果重新排序。

使用方法：
1. 确认下面的 API_BASE_URL、API_KEY 正确。
2. 右键运行这个 Python 文件。
"""

import requests


# 本地 Docker 启动的 Dify API 地址。如果你的端口不同，改这里。
API_BASE_URL = "http://localhost:12010/v1"

# 知识库 API Key。
API_KEY = "请填写知识库APIKey"

# 本次演示要查询的模型类型。
MODEL_TYPES = [
    "text-embedding",
    "rerank",
    "llm",
    "moderation",
]


def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {API_KEY}",
    }


def list_models(model_type: str) -> dict:
    url = f"{API_BASE_URL}/workspaces/current/models/model-types/{model_type}"

    response = requests.get(url, headers=get_headers(), timeout=30)
    response.raise_for_status()
    return response.json()


def print_models(model_type: str, result: dict) -> None:
    providers = result.get("data", [])

    print(f"\n模型类型：{model_type}")
    total_models = sum(len(provider.get("models", [])) for provider in providers)
    print(f"供应商数量：{len(providers)}")
    print(f"模型数量：{total_models}")

    if not providers:
        print("当前没有配置这个类型的模型。")
        return

    for provider in providers:
        provider_name = provider.get("provider")
        provider_label = provider.get("label", {}).get("zh_Hans") or provider.get("label", {}).get("en_US")
        provider_status = provider.get("status")

        print(f"\n供应商：{provider_label}（{provider_name}）")
        print(f"供应商状态：{provider_status}")

        for index, model in enumerate(provider.get("models", [])[:5], start=1):
            model_name = model.get("model")
            model_status = model.get("status")
            context_size = model.get("model_properties", {}).get("context_size")

            print(f"{index}. {model_name}")
            print(f"   状态：{model_status}")
            print(f"   上下文长度：{context_size}")

        if len(provider.get("models", [])) > 5:
            print(f"   还有 {len(provider.get('models', [])) - 5} 个模型未展示。")


def main() -> None:
    print("开始查询 Dify 当前工作区可用模型...")
    print(f"API 地址：{API_BASE_URL}")

    for model_type in MODEL_TYPES:
        result = list_models(model_type)
        print_models(model_type, result)

    print("\n说明：text-embedding 用于语义检索，rerank 用于对检索结果重新排序。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
