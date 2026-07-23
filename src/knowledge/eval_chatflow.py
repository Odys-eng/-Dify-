"""
制造业设备维修智能问答平台 - 形式化评测脚本
用法：
    DIFY_APP_KEY=app-xxx python eval_chatflow.py \
        --base-url http://127.0.0.1:5001/v1 \
        --questions ../../data/eval_questions.csv \
        --output ../../data/eval_results.json

评分维度：
    1. 路径命中（kb/tavily/kb_or_tavily）是否符合预期
    2. 关键词覆盖率（expected_keywords 命中数/总数）
    3. 是否包含结构化格式（故障诊断类）
    4. 响应时间
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
from pathlib import Path

import requests


def strip_think_tags(text: str) -> str:
    """移除 DeepSeek thinking 模式产生的 <think>...</think> 标签内容"""
    import re
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def call_chat(session: requests.Session, base_url: str,
              query: str, conversation_id: str = "") -> tuple[str, float, str]:
    """调用 chat-messages 接口，返回 (answer, elapsed_s, conversation_id)"""
    t0 = time.monotonic()
    r = session.post(
        f"{base_url}/chat-messages",
        json={
            "inputs": {},
            "query": query,
            "response_mode": "blocking",
            "conversation_id": conversation_id,
            "user": "eval-script",
        },
        headers={"Content-Type": "application/json"},
        timeout=180,
    )
    elapsed = time.monotonic() - t0
    if r.status_code != 200:
        raise RuntimeError(f"API error {r.status_code}: {r.text[:300]}")
    data = r.json()
    # 剥离 DeepSeek thinking 标签，只保留最终回答
    answer = strip_think_tags(data.get("answer", ""))
    conv_id = data.get("conversation_id", "")
    return answer, elapsed, conv_id


def score_answer(answer: str, row: dict) -> dict:
    """对一条回答打分，返回评分字典"""
    answer_lower = answer.lower()

    # 1. 关键词覆盖率
    keywords = [k.strip() for k in row["expected_keywords"].split(",") if k.strip()]
    hits = [k for k in keywords if k.lower() in answer_lower]
    kw_score = len(hits) / len(keywords) if keywords else 1.0

    # 2. 是否包含结构化故障诊断格式（仅故障诊断类检查）
    is_fault_q = row.get("expected_path", "") == "kb" and "故障诊断" in row.get("notes", "")
    has_structure = False
    if is_fault_q:
        has_structure = (
            ("故障可能原因" in answer or "可能原因" in answer) and
            ("step" in answer_lower or "排查步骤" in answer or "步骤" in answer)
        )

    # 3. 非空回答
    non_empty = len(answer.strip()) > 50

    # 4. 包含引用来源
    has_citation = "来源" in answer or "引用" in answer or "📄" in answer or "🔗" in answer

    # 5. 兜底话术检测（模糊问题）
    has_fallback = "无法" in answer or "建议" in answer or "补充" in answer

    return {
        "kw_coverage": round(kw_score, 2),
        "kw_hits": hits,
        "has_structure": has_structure if is_fault_q else None,
        "has_citation": has_citation,
        "non_empty": non_empty,
        "has_fallback": has_fallback if row.get("expected_path") == "kb_or_tavily" else None,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="https://localhost/v1")
    parser.add_argument("--questions", type=Path,
                        default=Path(__file__).parent.parent.parent / "data" / "eval_questions.csv")
    parser.add_argument("--output", type=Path,
                        default=Path(__file__).parent.parent.parent / "data" / "eval_results.json")
    parser.add_argument("--delay", type=float, default=3.0,
                        help="每题间隔秒数，避免频率限制")
    args = parser.parse_args()

    api_key = os.environ.get("DIFY_APP_KEY")
    if not api_key:
        raise RuntimeError("请设置 DIFY_APP_KEY 环境变量")

    session = requests.Session()
    session.trust_env = False
    session.headers["Authorization"] = f"Bearer {api_key}"
    # 走 Nginx https://localhost/v1 时为自签证书，跳过校验（仅本地部署场景）
    if args.base_url.lower().startswith("https"):
        session.verify = False
        requests.packages.urllib3.disable_warnings(
            requests.packages.urllib3.exceptions.InsecureRequestWarning
        )

    # 读取题目
    with open(args.questions, encoding="utf-8") as f:
        questions = list(csv.DictReader(f))

    print(f"共 {len(questions)} 道题，开始评测...\n")

    results = []
    multi_turn_conv_id = ""  # 用于多轮对话题目

    for i, row in enumerate(questions):
        qid = row["id"]
        q = row["question"]
        is_multi_turn_2 = "第2轮" in row.get("notes", "")

        print(f"[{qid}] {q[:50]}...", end="", flush=True)

        # 多轮对话第2轮复用前一轮 conversation_id
        conv_id = multi_turn_conv_id if is_multi_turn_2 else ""

        try:
            answer, elapsed, new_conv_id = call_chat(session, args.base_url, q, conv_id)

            # 保存多轮对话 conversation_id
            if "第1轮" in row.get("notes", ""):
                multi_turn_conv_id = new_conv_id

            scores = score_answer(answer, row)
            status = "OK"
        except Exception as e:
            answer = f"ERROR: {e}"
            elapsed = 0.0
            scores = {}
            status = "ERROR"

        result = {
            "id": qid,
            "category": row["category"],
            "question": q,
            "expected_path": row["expected_path"],
            "notes": row["notes"],
            "answer_preview": answer[:300],
            "elapsed_s": round(elapsed, 2),
            "status": status,
            **scores,
        }
        results.append(result)

        # 控制台简报
        kw = scores.get("kw_coverage", 0)
        mark = "OK" if status == "OK" else "FAIL"
        print(f" {elapsed:.1f}s | kw={kw:.0%} | {mark}")

        if i < len(questions) - 1:
            time.sleep(args.delay)

    # 汇总统计
    ok = [r for r in results if r["status"] == "OK"]
    avg_elapsed = sum(r["elapsed_s"] for r in ok) / len(ok) if ok else 0
    avg_kw = sum(r.get("kw_coverage", 0) for r in ok) / len(ok) if ok else 0
    fault_qs = [r for r in ok if r.get("has_structure") is not None]
    struct_rate = sum(1 for r in fault_qs if r.get("has_structure")) / len(fault_qs) if fault_qs else 0
    citation_rate = sum(1 for r in ok if r.get("has_citation")) / len(ok) if ok else 0

    summary = {
        "total": len(results),
        "ok": len(ok),
        "errors": len(results) - len(ok),
        "avg_elapsed_s": round(avg_elapsed, 2),
        "avg_kw_coverage": round(avg_kw, 2),
        "fault_structure_rate": round(struct_rate, 2),
        "citation_rate": round(citation_rate, 2),
    }

    output = {"summary": summary, "results": results}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("\n=== 评测汇总 ===")
    print(f"总题数: {summary['total']}  成功: {summary['ok']}  失败: {summary['errors']}")
    print(f"平均响应时间: {summary['avg_elapsed_s']}s")
    print(f"关键词覆盖率: {summary['avg_kw_coverage']:.0%}")
    print(f"故障诊断结构化率: {summary['fault_structure_rate']:.0%}")
    print(f"引用来源标注率: {summary['citation_rate']:.0%}")
    print(f"\n详细结果已写入: {args.output}")


if __name__ == "__main__":
    main()
