"""
============================================================
test_scenarios.py
============================================================
文件路径：src/tests/test_scenarios.py
用途：基于 Dify App API 的自动化验收测试脚本
      验证 3 个演示场景（知识库命中 / 联网兜底 / 多轮追问）

依赖安装：
    pip install -r src/requirements.txt

使用方式（在项目根目录执行）：
    # 方式 1：环境变量
    set DIFY_APP_API_KEY=app-xxxxxxxx
    set DIFY_BASE_URL=http://localhost/v1
    python src/tests/test_scenarios.py

    # 方式 2：命令行参数
    python src/tests/test_scenarios.py --api_key app-xxx --base_url http://localhost/v1

与 PRD 5.1 节对照：
    ✅ 场景 1：知识库命中（FANUC 0i-MF 主轴异响 SP-2003）
    ✅ 场景 2：联网兜底（西门子 840D sl 驱动过流）
    ✅ 场景 3：多轮追问（换刀故障 → 换刀臂卡死）
    ✅ 响应时间 < 15 秒
    ✅ 检查 DeepSeek API 旧 ID 停用日期（2026-07-24）

API 文档参考：
    POST /v1/chat-messages
    认证：Authorization: Bearer {app_api_key}
    多轮对话：首次 conversation_id 为空，后续传入返回的 ID
============================================================
"""

import os
import sys
import time
import argparse
import requests
from datetime import date, datetime
from pathlib import Path

# ============================================================
# 配置
# ============================================================

# DeepSeek 旧 ID 停用日期
DEEPSEEK_DEPRECATION_DATE = date(2026, 7, 24)
DEEPSEEK_WARNING_DAYS = 7  # 提前 7 天警告

# 响应时间阈值（秒）
RESPONSE_TIME_LIMIT = 15

# 测试用户标识
TEST_USER = "qa-test-user"


# ============================================================
# DeepSeek 旧 ID 停用日期检查
# ============================================================

def check_deepseek_deprecation():
    """
    检查当前日期是否接近 DeepSeek 旧 ID 停用日期
    如果在警告期内，输出警告信息
    """
    today = date.today()
    days_until = (DEEPSEEK_DEPRECATION_DATE - today).days

    print("=" * 60)
    print("  DeepSeek API 旧 ID 停用检查")
    print("=" * 60)
    print(f"  当前日期：{today}")
    print(f"  停用日期：{DEEPSEEK_DEPRECATION_DATE}")
    print(f"  剩余天数：{days_until}")

    if days_until <= 0:
        print("\n  ❌ 严重警告：DeepSeek 旧 ID（deepseek-chat / deepseek-reasoner）已停用！")
        print("     必须确认 Dify 中使用的模型为 deepseek-v4-flash")
        print("     测试可能失败，请先检查 Dify 模型供应商配置")
        return False
    elif days_until <= DEEPSEEK_WARNING_DAYS:
        print(f"\n  ⚠️ 警告：DeepSeek 旧 ID 将在 {days_until} 天后停用！")
        print("     请确认 Dify 中使用的模型为 deepseek-v4-flash（不是 deepseek-chat）")
        print("     停用后 deepseek-chat 将返回 404 错误")
    else:
        print(f"\n  ✅ 距停用还有 {days_until} 天，暂无紧急风险")

    print("=" * 60)
    return True


# ============================================================
# Dify Chat API 调用
# ============================================================

def send_message(
    base_url: str,
    api_key: str,
    query: str,
    conversation_id: str = "",
    timeout: int = 30
) -> dict:
    """
    调用 Dify Chat API 发送消息

    参数：
        base_url: Dify API 基础 URL
        api_key: App API Key
        query: 用户消息
        conversation_id: 会话 ID（首次为空）
        timeout: 超时时间

    返回：
        {
            "status_code": int,
            "response_time": float,
            "answer": str,
            "conversation_id": str,
            "retriever_resources": list,
            "error": str (如有)
        }
    """
    url = f"{base_url}/chat-messages"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": {},
        "query": query,
        "response_mode": "blocking",
        "conversation_id": conversation_id,
        "user": TEST_USER
    }

    start_time = time.time()

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        elapsed = time.time() - start_time

        if response.status_code == 200:
            data = response.json()
            return {
                "status_code": 200,
                "response_time": round(elapsed, 2),
                "answer": data.get("answer", ""),
                "conversation_id": data.get("conversation_id", ""),
                "retriever_resources": data.get("retriever_resources", []),
                "message_id": data.get("message_id", ""),
                "error": None
            }
        else:
            return {
                "status_code": response.status_code,
                "response_time": round(elapsed, 2),
                "answer": "",
                "conversation_id": "",
                "retriever_resources": [],
                "error": f"HTTP {response.status_code}: {response.text[:200]}"
            }
    except requests.exceptions.Timeout:
        return {
            "status_code": 0,
            "response_time": round(time.time() - start_time, 2),
            "answer": "",
            "conversation_id": "",
            "retriever_resources": [],
            "error": f"请求超时（{timeout}秒）"
        }
    except requests.exceptions.RequestException as e:
        return {
            "status_code": 0,
            "response_time": round(time.time() - start_time, 2),
            "answer": "",
            "conversation_id": "",
            "retriever_resources": [],
            "error": str(e)
        }


# ============================================================
# 测试场景定义
# ============================================================

def test_scenario_1(base_url: str, api_key: str) -> dict:
    """
    场景 1：知识库命中
    输入：FANUC 0i-MF 系统主轴异响，报警代码 SP-2003
    预期：走知识库分支，返回排查步骤 + 手册引用
    """
    print("\n[场景 1] 知识库命中测试")
    print("  查询：FANUC 0i-MF 系统主轴异响，报警代码 SP-2003")

    result = send_message(
        base_url=base_url,
        api_key=api_key,
        query="FANUC 0i-MF 系统主轴异响，报警代码 SP-2003"
    )

    checks = {
        "HTTP 状态码 = 200": result["status_code"] == 200,
        "响应时间 < 15 秒": result["response_time"] < RESPONSE_TIME_LIMIT,
        "答案包含「故障可能原因」": "故障可能原因" in result["answer"] or "可能原因" in result["answer"],
        "答案包含「排查步骤」": "排查步骤" in result["answer"] or "Step" in result["answer"],
        "答案包含引用来源": len(result["retriever_resources"]) > 0 or "来源" in result["answer"] or "📄" in result["answer"],
    }

    return {
        "scenario": "场景1-知识库命中",
        "query": "FANUC 0i-MF 系统主轴异响，报警代码 SP-2003",
        "result": result,
        "checks": checks,
        "passed": all(checks.values())
    }


def test_scenario_2(base_url: str, api_key: str) -> dict:
    """
    场景 2：联网兜底
    输入：西门子 840D sl 驱动模块过流故障怎么处理
    预期：走联网搜索分支，返回搜索结果 + URL 引用
    """
    print("\n[场景 2] 联网兜底测试")
    print("  查询：西门子 840D sl 驱动模块过流故障怎么处理")

    result = send_message(
        base_url=base_url,
        api_key=api_key,
        query="西门子 840D sl 驱动模块过流故障怎么处理"
    )

    checks = {
        "HTTP 状态码 = 200": result["status_code"] == 200,
        "响应时间 < 15 秒": result["response_time"] < RESPONSE_TIME_LIMIT,
        "答案包含「故障可能原因」": "故障可能原因" in result["answer"] or "可能原因" in result["answer"],
        "答案包含「排查步骤」": "排查步骤" in result["answer"] or "Step" in result["answer"],
        "答案包含 URL 引用": "http" in result["answer"] or "🔗" in result["answer"] or len(result["retriever_resources"]) > 0,
    }

    return {
        "scenario": "场景2-联网兜底",
        "query": "西门子 840D sl 驱动模块过流故障怎么处理",
        "result": result,
        "checks": checks,
        "passed": all(checks.values())
    }


def test_scenario_3(base_url: str, api_key: str) -> dict:
    """
    场景 3：多轮追问
    第一轮：CNC 加工中心换刀故障
    第二轮：如果换刀臂卡在中间位置怎么办
    预期：第二轮基于第一轮上下文回答，涉及「换刀臂」相关内容
    """
    print("\n[场景 3] 多轮追问测试")

    # 第一轮
    print("  第一轮查询：CNC 加工中心换刀故障")
    result_1 = send_message(
        base_url=base_url,
        api_key=api_key,
        query="CNC 加工中心换刀故障"
    )

    if not result_1["conversation_id"]:
        return {
            "scenario": "场景3-多轮追问",
            "query": "CNC 加工中心换刀故障 → 换刀臂卡在中间位置",
            "result": result_1,
            "checks": {"第一轮获取 conversation_id": False},
            "passed": False,
            "error": "第一轮未返回 conversation_id，无法进行多轮测试"
        }

    # 第二轮（使用第一轮的 conversation_id）
    print("  第二轮查询：如果换刀臂卡在中间位置怎么办")
    result_2 = send_message(
        base_url=base_url,
        api_key=api_key,
        query="如果换刀臂卡在中间位置怎么办",
        conversation_id=result_1["conversation_id"]
    )

    # 验证第二轮回答的上下文连贯性
    answer_2 = result_2["answer"]
    context_keywords = ["换刀臂", "刀库", "刀臂", "换刀", "ATC", "机械手"]

    checks = {
        "第一轮 HTTP 200": result_1["status_code"] == 200,
        "第二轮 HTTP 200": result_2["status_code"] == 200,
        "第一轮响应 < 15秒": result_1["response_time"] < RESPONSE_TIME_LIMIT,
        "第二轮响应 < 15秒": result_2["response_time"] < RESPONSE_TIME_LIMIT,
        "第二轮包含「换刀臂」相关内容": any(kw in answer_2 for kw in context_keywords),
        "第二轮上下文连贯（未重新询问设备类型）": "CNC" not in answer_2[:50] or "换刀" in answer_2[:100],
    }

    return {
        "scenario": "场景3-多轮追问",
        "query": "第一轮：CNC 加工中心换刀故障\n第二轮：如果换刀臂卡在中间位置怎么办",
        "result": result_2,
        "result_round1": result_1,
        "checks": checks,
        "passed": all(checks.values())
    }


# ============================================================
# 测试报告生成
# ============================================================

def generate_report(results: list) -> str:
    """生成 Markdown 格式的测试报告"""
    passed = sum(1 for r in results if r["passed"])
    failed = len(results) - passed

    lines = []
    lines.append("# 自动化验收测试报告\n")
    lines.append(f"**生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"**测试场景数**：{len(results)}\n")
    lines.append(f"**通过**：{passed} | **失败**：{failed}\n")
    lines.append(f"**响应时间阈值**：{RESPONSE_TIME_LIMIT} 秒\n\n")

    # 汇总
    lines.append("## 测试汇总\n\n")
    lines.append("| 场景 | 状态 | 响应时间 | 通过项/总项 |\n")
    lines.append("|------|------|---------|------------|\n")
    for r in results:
        status = "✅ 通过" if r["passed"] else "❌ 失败"
        resp_time = r["result"].get("response_time", 0)
        passed_items = sum(1 for v in r["checks"].values() if v)
        total_items = len(r["checks"])
        lines.append(f"| {r['scenario']} | {status} | {resp_time}s | {passed_items}/{total_items} |\n")

    # 详细结果
    lines.append("\n## 详细测试结果\n\n")
    for r in results:
        status = "✅ 通过" if r["passed"] else "❌ 失败"
        lines.append(f"### {r['scenario']} - {status}\n\n")
        lines.append(f"**查询**：{r['query']}\n\n")

        # 检查项
        lines.append("**检查项**：\n\n")
        lines.append("| 检查项 | 结果 |\n|--------|------|\n")
        for check_name, check_result in r["checks"].items():
            mark = "✅" if check_result else "❌"
            lines.append(f"| {check_name} | {mark} |\n")

        # 响应详情
        result = r["result"]
        lines.append(f"\n**响应时间**：{result['response_time']} 秒\n")
        lines.append(f"**HTTP 状态码**：{result['status_code']}\n")

        if result.get("error"):
            lines.append(f"**错误信息**：{result['error']}\n")

        # 答案预览
        answer = result.get("answer", "")
        if answer:
            preview = answer[:300] + ("..." if len(answer) > 300 else "")
            lines.append(f"\n**答案预览**：\n```\n{preview}\n```\n")

        # 引用来源
        resources = result.get("retriever_resources", [])
        if resources:
            lines.append(f"\n**引用来源**（{len(resources)} 条）：\n")
            for i, res in enumerate(resources[:3], 1):
                doc = res.get("document_name", res.get("title", "未知"))
                page = res.get("page", "")
                url = res.get("url", "")
                if url:
                    lines.append(f"  {i}. 🔗 {url}\n")
                else:
                    lines.append(f"  {i}. 📄 {doc} 第{page}页\n")

        lines.append("\n---\n\n")

    # 结论
    lines.append("## 测试结论\n\n")
    if failed == 0:
        lines.append("✅ **所有场景通过，Demo 可进行演示。**\n")
    else:
        lines.append(f"❌ **{failed} 个场景失败，请修复后再演示。**\n")
        lines.append("\n失败场景：\n")
        for r in results:
            if not r["passed"]:
                failed_checks = [k for k, v in r["checks"].items() if not v]
                lines.append(f"- {r['scenario']}：{', '.join(failed_checks)}\n")

    return "".join(lines)


# ============================================================
# 主流程
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Dify Demo 自动化验收测试")
    parser.add_argument("--api_key", help="Dify App API Key")
    parser.add_argument("--base_url", default="http://localhost/v1", help="Dify API 基础 URL")
    parser.add_argument("--output", default="reports/测试报告.md", help="报告输出路径")
    parser.add_argument("--skip_warning", action="store_true", help="跳过 DeepSeek 停用检查")

    args = parser.parse_args()

    # 加载配置
    api_key = args.api_key or os.environ.get("DIFY_APP_API_KEY", "")
    base_url = args.base_url or os.environ.get("DIFY_BASE_URL", "http://localhost/v1")

    if not api_key:
        print("=" * 60)
        print("错误：缺少 DIFY_APP_API_KEY")
        print("请通过以下方式提供：")
        print("  1. 环境变量：DIFY_APP_API_KEY=app-xxxxxxxx")
        print("  2. 命令行参数：--api_key app-xxxxxxxx")
        print("=" * 60)
        sys.exit(1)

    # DeepSeek 停用检查
    if not args.skip_warning:
        check_deepseek_deprecation()

    print(f"\nAPI 地址：{base_url}")
    print(f"API Key：{api_key[:12]}...")
    print(f"响应时间阈值：{RESPONSE_TIME_LIMIT} 秒")
    print(f"\n开始执行 {3} 个测试场景...\n")

    # 执行测试
    results = []

    # 场景 1
    r1 = test_scenario_1(base_url, api_key)
    results.append(r1)
    print(f"  结果：{'✅ 通过' if r1['passed'] else '❌ 失败'} | 响应时间：{r1['result']['response_time']}s")

    # 场景 2
    r2 = test_scenario_2(base_url, api_key)
    results.append(r2)
    print(f"  结果：{'✅ 通过' if r2['passed'] else '❌ 失败'} | 响应时间：{r2['result']['response_time']}s")

    # 场景 3
    r3 = test_scenario_3(base_url, api_key)
    results.append(r3)
    print(f"  结果：{'✅ 通过' if r3['passed'] else '❌ 失败'} | 响应时间：{r3['result']['response_time']}s")

    # 生成报告
    report = generate_report(results)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    # 汇总
    passed = sum(1 for r in results if r["passed"])
    print(f"\n{'=' * 60}")
    print(f"  测试完成：{passed}/{len(results)} 通过")
    print(f"  报告已保存：{output_path}")
    print(f"{'=' * 60}")

    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
