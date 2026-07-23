"""
============================================================
verify_retrieval.py
============================================================
文件路径：src/knowledge/verify_retrieval.py
用途：验证 Dify 知识库检索效果
      对 10 个测试查询调用检索 API，输出 Markdown 表格

依赖安装：
    pip install -r src/requirements.txt

使用方式（在项目根目录执行）：
    # 方式 1：通过环境变量配置
    set DIFY_BASE_URL=http://localhost/v1
    set DIFY_DATASET_ID=你的dataset_id
    set DIFY_KNOWLEDGE_API_KEY=dataset-xxxxxxxx
    python src/knowledge/verify_retrieval.py

    # 方式 2：通过命令行参数
    python src/knowledge/verify_retrieval.py --base_url http://localhost/v1 --dataset_id xxx --api_key dataset-xxx

    # 方式 3：使用配置文件
    python src/knowledge/verify_retrieval.py --config .env

与 PRD 5.1 节对照：
    ✅ 10 个测试查询，覆盖 3 个演示场景 + 7 个变体
    ✅ 包含中英文混排故障码（SP-2003 报警）
    ✅ 标红 score < 0.5 的结果

API 文档参考：
    POST /v1/datasets/{dataset_id}/retrieve
    认证：Authorization: Bearer {knowledge_api_key}
    ⚠️ Dify 1.13.0+ 必须显式传 score_threshold_enabled，否则 500 错误
============================================================
"""

import os
import argparse
import requests
from datetime import datetime
from pathlib import Path

# ============================================================
# 测试查询定义（10 个，覆盖 3 个演示场景 + 7 个变体）
# ============================================================

TEST_QUERIES = [
    # --- 场景 1：知识库命中（FANUC 主轴异响）---
    {
        "id": "Q01",
        "query": "FANUC 0i-MF 系统主轴异响，报警代码 SP-2003",
        "scene": "场景1-精确",
        "expected_hit": True,
        "note": "PRD 场景1原题，应高概率命中 FANUC 手册"
    },
    {
        "id": "Q02",
        "query": "SP-2003 报警怎么处理",  # ⚠️ 中英文混排故障码
        "scene": "场景1-变体",
        "expected_hit": True,
        "note": "中英文混排，测试 Embedding 对故障码的理解"
    },
    {
        "id": "Q03",
        "query": "主轴轴承磨损如何检测",
        "scene": "场景1-变体",
        "expected_hit": "中",
        "note": "语义泛化，未提具体型号，测试召回广度"
    },
    # --- 场景 2：联网兜底（西门子驱动）---
    {
        "id": "Q04",
        "query": "西门子 840D sl 驱动模块过流故障",
        "scene": "场景2-精确",
        "expected_hit": "中",
        "note": "PRD 场景2原题，如手册覆盖应命中，否则走联网"
    },
    {
        "id": "Q05",
        "query": "Siemens 驱动 IGBT 损坏排查步骤",
        "scene": "场景2-变体",
        "expected_hit": "低-中",
        "note": "中英文混排 + 专业术语，测试专业词汇召回"
    },
    # --- 场景 3：多轮追问（换刀故障）---
    {
        "id": "Q06",
        "query": "CNC 加工中心换刀故障",
        "scene": "场景3-精确",
        "expected_hit": True,
        "note": "PRD 场景3原题，应命中故障案例集"
    },
    {
        "id": "Q07",
        "query": "换刀臂卡在中间位置怎么办",
        "scene": "场景3-追问",
        "expected_hit": "中",
        "note": "多轮追问场景，测试上下文相关召回"
    },
    # --- 变体查询（覆盖其他设备类型）---
    {
        "id": "Q08",
        "query": "PLC 通讯故障排查步骤",
        "scene": "变体-泛化",
        "expected_hit": "低-中",
        "note": "测试知识库对未覆盖设备的召回表现"
    },
    {
        "id": "Q09",
        "query": "伺服电机过热保护机制",
        "scene": "变体-泛化",
        "expected_hit": "中",
        "note": "常见故障类型，测试语义理解"
    },
    {
        "id": "Q10",
        "query": "FANUC 系统参数备份与恢复",
        "scene": "变体-边缘",
        "expected_hit": "低-中",
        "note": "边缘场景，测试知识库覆盖边界"
    },
]


# ============================================================
# Dify 知识库检索 API 调用
# ============================================================

def retrieve_from_dify(
    base_url: str,
    dataset_id: str,
    api_key: str,
    query: str,
    top_k: int = 3,
    score_threshold: float = 0.5
) -> dict:
    """
    调用 Dify 知识库检索 API

    参数：
        base_url: Dify API 基础 URL（如 http://localhost/v1）
        dataset_id: 知识库 ID
        api_key: Knowledge API Key
        query: 检索查询
        top_k: 返回结果数
        score_threshold: 相似度阈值

    返回：
        API 响应 JSON
    """
    url = f"{base_url}/datasets/{dataset_id}/retrieve"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # ⚠️ Dify 1.13.0+ 必须显式传 score_threshold_enabled，否则 500 错误
    payload = {
        "query": query,
        "retrieval_model": {
            "search_method": "semantic_search",
            "reranking_enable": True,
            "reranking_mode": "reranking_model",
            "reranking_model": {
                "reranking_provider_name": "",
                "reranking_model_name": ""
            },
            "top_k": top_k,
            "score_threshold_enabled": True,
            "score_threshold": score_threshold
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError:
        return {"error": f"HTTP {response.status_code}: {response.text}"}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


# ============================================================
# 结果格式化
# ============================================================

def format_results_table(results: list) -> str:
    """
    将检索结果格式化为 Markdown 表格
    score < 0.5 的结果用 ⚠️ 标记
    """
    lines = []
    lines.append("# 知识库检索效果验证报告\n")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    lines.append(f"测试查询数：{len(results)}\n")
    lines.append("Score 阈值：0.5（低于此值标记 ⚠️）\n")

    # 汇总统计
    hit_count = sum(1 for r in results if r.get("top_score", 0) >= 0.5)
    hit_rate = (hit_count / len(results) * 100) if results else 0

    lines.append("\n## 汇总统计\n")
    lines.append("| 指标 | 值 |\n|------|----|\n")
    lines.append(f"| 总查询数 | {len(results)} |\n")
    lines.append(f"| 命中数（score ≥ 0.5） | {hit_count} |\n")
    lines.append(f"| 命中率 | {hit_rate:.1f}% |\n")
    lines.append(f"| 平均最高 Score | {sum(r.get('top_score', 0) for r in results)/len(results):.3f} |\n")

    # 详细结果表
    lines.append("\n## 详细检索结果\n\n")
    lines.append("| 编号 | 场景 | 查询 | Top1 Score | Top1 文档 | Top1 页码 | 命中? | 备注 |\n")
    lines.append("|------|------|------|-----------|----------|----------|-------|------|\n")

    for r in results:
        top_score = r.get("top_score", 0)
        top_doc = r.get("top_doc", "—")
        top_page = r.get("top_page", "—")
        hit = "✅ 命中" if top_score >= 0.5 else "⚠️ 未命中"
        query_short = r["query"][:30] + ("..." if len(r["query"]) > 30 else "")

        lines.append(
            f"| {r['id']} | {r['scene']} | {query_short} | "
            f"{top_score:.3f} | {top_doc} | {top_page} | {hit} | {r['note']} |\n"
        )

    # 未命中查询详情
    missed = [r for r in results if r.get("top_score", 0) < 0.5]
    if missed:
        lines.append("\n## ⚠️ 未命中查询详情（score < 0.5）\n\n")
        for r in missed:
            lines.append(f"### {r['id']}：{r['query']}\n")
            lines.append(f"- 场景：{r['scene']}\n")
            lines.append(f"- 最高 Score：{r.get('top_score', 0):.3f}\n")
            lines.append(f"- 备注：{r['note']}\n")
            if r.get("error"):
                lines.append(f"- 错误：{r['error']}\n")
            lines.append("\n")

    return "".join(lines)


# ============================================================
# 主流程
# ============================================================

def load_config(args) -> tuple:
    """从环境变量或命令行参数加载配置"""
    base_url = args.base_url or os.environ.get("DIFY_BASE_URL", "http://localhost/v1")
    dataset_id = args.dataset_id or os.environ.get("DIFY_DATASET_ID", "")
    api_key = args.api_key or os.environ.get("DIFY_KNOWLEDGE_API_KEY", "")

    # 如果指定了配置文件，从中加载
    if args.config:
        config_path = Path(args.config)
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("DIFY_BASE_URL="):
                        base_url = line.split("=", 1)[1]
                    elif line.startswith("DIFY_DATASET_ID="):
                        dataset_id = line.split("=", 1)[1]
                    elif line.startswith("DIFY_KNOWLEDGE_API_KEY="):
                        api_key = line.split("=", 1)[1]

    if not dataset_id or not api_key:
        print("=" * 60)
        print("错误：缺少必要配置")
        print("请通过以下方式之一提供配置：")
        print("  1. 环境变量：DIFY_BASE_URL, DIFY_DATASET_ID, DIFY_KNOWLEDGE_API_KEY")
        print("  2. 命令行参数：--base_url, --dataset_id, --api_key")
        print("  3. 配置文件：--config .env")
        print("=" * 60)
        return None, None, None

    return base_url, dataset_id, api_key


def main():
    parser = argparse.ArgumentParser(description="Dify 知识库检索效果验证")
    parser.add_argument("--base_url", help="Dify API 基础 URL（默认 http://localhost/v1）")
    parser.add_argument("--dataset_id", help="知识库 ID")
    parser.add_argument("--api_key", help="Knowledge API Key")
    parser.add_argument("--config", help="配置文件路径（.env 格式）")
    parser.add_argument("--output", default="reports/检索验证报告.md", help="报告输出路径")

    args = parser.parse_args()

    base_url, dataset_id, api_key = load_config(args)
    if not all([base_url, dataset_id, api_key]):
        return

    print("=" * 60)
    print("  知识库检索效果验证")
    print("=" * 60)
    print(f"API 地址：{base_url}")
    print(f"知识库 ID：{dataset_id}")
    print(f"API Key：{api_key[:12]}...")
    print(f"测试查询数：{len(TEST_QUERIES)}\n")

    # 执行检索
    results = []
    for q in TEST_QUERIES:
        print(f"[{q['id']}] 检索中：{q['query'][:40]}...")

        response = retrieve_from_dify(
            base_url=base_url,
            dataset_id=dataset_id,
            api_key=api_key,
            query=q["query"],
            top_k=3,
            score_threshold=0.5
        )

        if "error" in response:
            print(f"  ✗ 错误：{response['error']}")
            results.append({
                **q,
                "top_score": 0,
                "top_doc": "—",
                "top_page": "—",
                "error": response["error"]
            })
        else:
            records = response.get("records", [])
            if records:
                top = records[0]
                score = top.get("score", 0)
                # 从 metadata 或 content 中提取文档名和页码
                doc_name = top.get("metadata", {}).get("document_name", "未知文档")
                page_num = top.get("metadata", {}).get("page", "—")

                print(f"  ✓ Score: {score:.3f} | 文档: {doc_name}")

                results.append({
                    **q,
                    "top_score": score,
                    "top_doc": doc_name,
                    "top_page": page_num
                })
            else:
                print("  ⚠ 无命中结果")
                results.append({
                    **q,
                    "top_score": 0,
                    "top_doc": "无命中",
                    "top_page": "—"
                })

    # 生成报告
    report = format_results_table(results)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"\n{'=' * 60}")
    print(f"  验证完成！报告已保存：{output_path}")

    # 打印汇总
    hit_count = sum(1 for r in results if r.get("top_score", 0) >= 0.5)
    print(f"  命中率：{hit_count}/{len(results)} ({hit_count/len(results)*100:.1f}%)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
