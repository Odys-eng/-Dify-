"""让 Dify 应用根据知识库中的资料回答问题。

这个案例与前面的“检索知识库”不同：
1. 知识库检索接口只返回相关分段。
2. 应用聊天接口会先检索知识库，再让大模型生成最终回答。

运行前需要在 Dify 控制台完成一次应用配置：
1. 创建一个“聊天助手”应用。
2. 在应用的上下文中添加案例使用的知识库。
3. 提示词填写：请优先根据上下文中的知识回答；资料不足时明确说明不知道。
4. 发布应用，并在“访问 API”页面创建应用 API Key。
5. 把下面的 APP_API_KEY 改成刚创建的 app- 开头的密钥。

注意：这里使用的是“应用 API Key”，不是前面案例中的“知识库 API Key”。
"""

import json

import requests


# 本地 Docker 启动的 Dify API 地址。如果你的端口不同，改这里。
API_BASE_URL = "http://localhost:12010/v1"

# 应用 API Key，必须是 app- 开头的密钥。
APP_API_KEY = "请填写应用APIKey"

# 要向知识库应用提出的问题。
QUESTION = "Dify 上传文件到知识库用哪个接口？"

# 用来区分不同终端用户。教学演示使用固定值即可。
USER_ID = "case-29-student"


def get_headers() -> dict:
    return {
        "Authorization": f"Bearer {APP_API_KEY}",
        "Content-Type": "application/json",
    }


def validate_config() -> None:
    if not APP_API_KEY.startswith("app-"):
        raise RuntimeError(
            "请先把 APP_API_KEY 改成 Dify 应用的 API Key。"
            "注意：应用密钥以 app- 开头，不能使用 dataset- 开头的知识库密钥。"
        )


def ask_ai() -> dict:
    url = f"{API_BASE_URL}/chat-messages"
    data = {
        # 当前应用没有额外表单变量，所以 inputs 传空对象。
        "inputs": {},
        "query": QUESTION,
        # blocking 会等待模型生成完成后，一次性返回完整结果，便于初学者理解。
        "response_mode": "blocking",
        # 空字符串表示开始一次新会话。
        "conversation_id": "",
        "user": USER_ID,
    }

    response = requests.post(url, headers=get_headers(), json=data, timeout=180)
    if not response.ok:
        raise RuntimeError(f"调用应用失败：{response.status_code}\n{response.text}")
    return response.json()


def print_retriever_resources(result: dict) -> None:
    metadata = result.get("metadata", {})
    resources = metadata.get("retriever_resources", [])

    print(f"\n本次回答引用了 {len(resources)} 个知识库分段：")
    if not resources:
        print("没有返回知识库引用。请检查应用是否已经接入并发布知识库配置。")
        return

    for index, resource in enumerate(resources, start=1):
        content = resource.get("content", "").replace("\n", " ")
        print(f"\n引用 {index}")
        print(f"文档名称：{resource.get('document_name', '未知文档')}")
        print(f"相关度：{resource.get('score', '未返回')}")
        print(f"内容预览：{content[:200]}")


def main() -> None:
    validate_config()

    print("开始让 AI 根据知识库回答问题...")
    print(f"API 地址：{API_BASE_URL}")
    print(f"问题：{QUESTION}")

    result = ask_ai()
    answer = result.get("answer", "")

    print("\nAI 回答：")
    print(answer or "接口没有返回回答内容。")

    print_retriever_resources(result)

    print("\n会话信息：")
    print(f"会话 ID：{result.get('conversation_id')}")
    print(f"消息 ID：{result.get('message_id')}")

    usage = result.get("metadata", {}).get("usage", {})
    if usage:
        print("\n模型用量：")
        print(json.dumps(usage, ensure_ascii=False, indent=2))

    print("\n说明：这次返回的不再只是检索分段，而是大模型结合资料生成的最终回答。")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("\n运行失败：")
        print(error)
