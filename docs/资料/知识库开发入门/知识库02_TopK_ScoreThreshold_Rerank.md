# 知识库 02：Top K、Score Threshold 与 Rerank

更新时间：2026-07-09

## PPT 可用标题

三个参数决定知识库检索结果能不能进入模型

## 一句话讲清楚

Top K 决定最多返回多少条结果，Score Threshold 决定低于多少分的结果被丢弃，Rerank 决定候选结果按什么顺序进入上下文。

## 参数解释

### Top K

Top K 是重排后最多返回的结果数量。

讲课时可以这样说：

- Top K 太小，容易漏掉关键资料。
- Top K 太大，容易把无关资料也塞进上下文。
- 开启 Rerank 模型时，Top K 可能受到模型最大输入容量影响。

### Score Threshold

Score Threshold 是返回结果的最低相似度分数。

讲课时可以这样说：

- 阈值高：结果更严格，但可能没有召回。
- 阈值低：结果更多，但噪音也更多。
- 做企业知识库时，不要只追求“有答案”，还要防止错误上下文进入模型。

### Rerank

Rerank 是对候选检索结果重新打分和排序。

讲课时可以这样说：

- Embedding 召回负责先找一批可能相关的内容。
- Rerank 负责进一步判断哪些内容更贴近用户问题。
- 多知识库、多来源资料混合检索时，Rerank 更重要。

## PPT 对比表

| 参数 | 控制什么 | 设置太低 | 设置太高 |
| --- | --- | --- | --- |
| Top K | 返回结果数量 | 漏掉证据 | 引入噪音 |
| Score Threshold | 最低相似度 | 无关内容进入上下文 | 找不到内容 |
| Rerank | 结果排序质量 | 相关内容可能排后面 | 依赖模型能力和成本 |

## 课堂演示建议

1. 同一个知识库，同一个问题，分别设置 Top K 为 1、3、8。
2. 对比召回片段数量和答案变化。
3. 再打开 Score Threshold，观察无结果或低相关结果被过滤的情况。
4. 最后开启 Rerank，对比排序变化。

## 可直接放 PPT 的金句

知识库调参不是让 AI 更会编，而是控制哪些证据有资格进入模型上下文。

## 常见误区

- 误区一：Top K 越大越好。
- 误区二：阈值越高越专业。
- 误区三：只要开了 Rerank，答案就一定更准。
- 误区四：回答不准就直接换大模型。

## 资料来源

- Knowledge Retrieval 节点：https://docs.dify.ai/en/cloud/use-dify/nodes/knowledge-retrieval
- Integrate Knowledge within Apps：https://docs.dify.ai/en/cloud/use-dify/knowledge/integrate-knowledge-within-application

