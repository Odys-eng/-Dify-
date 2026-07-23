"""修正报告3处与项目不符：§4.3 LLM参数、§3 响应需求、§6 性能数据。"""
from pathlib import Path
import docx

SRC = Path(r"C:\Users\32698\Desktop\生产实习报告_带图_最终版.docx")
doc = docx.Document(str(SRC))

REPL = [
    (
        "选用DeepSeek-V4-Pro模型（经SiliconFlow平台调用），开启思考模式（reasoning_effort=high），上下文窗口1M token。",
        "选用DeepSeek-V4-Pro模型（经SiliconFlow平台调用），该模型默认开启深度思考（回答前可见「已深度思考」过程），并依托其长上下文能力承载知识库检索结果；两条分支的temperature参数独立配置（知识库路径0.3、联网路径0.6），max_tokens设为2048。",
    ),
    (
        "响应时间要求单次问答≤15秒（含联网搜索场景），纯知识库命中应≤5秒；",
        "响应时间以「可用」为目标（深度思考模式下以响应时间换取更高推理质量，实测总响应约40秒；若追求≤15秒可关闭深度思考或改用更快模型）；",
    ),
    (
        "流式首字响应时间6.8秒，平均总响应时间约40秒。",
        "平均总响应时间约40秒（注：首字与总响应时间随模型及是否开启深度思考而变化，6.8秒首字为早期DeepSeek-V3无思考模式下的基准；当前V4-Pro深度思考模式首字延迟增加，以换取推理质量）。",
    ),
]

changed = 0
for p in doc.paragraphs:
    for old, new in REPL:
        if old in p.text:
            if p.runs:
                p.runs[0].text = p.text.replace(old, new)
                for r in p.runs[1:]:
                    r.text = ""
            changed += 1
            print(f"[改] {old[:22]}...")
            break

doc.save(str(SRC))
print(f"完成：{changed}/3 处")
