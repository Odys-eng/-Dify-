# 知识库 04：外部知识库 API

更新时间：2026-07-09

## PPT 可用标题

外部知识库 API：让 Dify 接入已有 RAG 系统

## 一句话讲清楚

外部知识库 API 适合已经有自研检索系统、向量库或企业搜索服务的团队；Dify 负责发起检索请求，外部服务负责返回可作为上下文的 records。

## 什么时候需要外部知识库

- 企业已经有自己的向量库。
- 客户不希望把资料迁移到 Dify 内置知识库。
- 检索逻辑需要走自研权限系统。
- 资料量大，已经有成熟的搜索服务。
- 需要复用现有 LangChain、LlamaIndex 或内部 RAG 服务。

## Dify 的调用方式

注册外部知识库 API endpoint 后，Dify 会在地址后追加 `/retrieval`，并发送 `POST` 请求。

请求体包含：

- `knowledge_id`：外部知识源 ID。
- `query`：用户搜索问题。
- `retrieval_setting`：检索参数。
- `metadata_condition`：可选的元数据过滤条件。

## 请求示例

```json
{
  "knowledge_id": "ruyidify-course-knowledge",
  "query": "如何创建通用型知识库？",
  "retrieval_setting": {
    "top_k": 3,
    "score_threshold": 0.5
  }
}
```

## 响应结构

外部服务返回 `records` 数组。

每条记录建议包含：

- `content`：检索到的文本片段。
- `score`：相似度分数，通常为 0 到 1。
- `title`：来源文档标题。
- `metadata`：来源信息或业务字段，必须是对象，不要返回 `null`。

## 响应示例

```json
{
  "records": [
    {
      "content": "创建通用型知识库时，先选择创建即用型知识库，再创建空知识库。",
      "score": 0.87,
      "title": "06 Dify 知识库开发入门",
      "metadata": {
        "chapter": "06",
        "page": 11
      }
    }
  ]
}
```

## 讲课重点

- 外部知识库不是更高级的上传方式，而是系统集成方式。
- Dify 不管理外部资料，只消费外部检索结果。
- 鉴权、权限、检索、排序都由外部服务负责。
- `metadata` 不能返回 `null`，否则检索流程可能出错。

## 可直接放 PPT 的金句

外部知识库的价值不是把 Dify 变成搜索引擎，而是让 Dify 成为已有知识系统的应用编排入口。

## 资料来源

- External Knowledge API：https://docs.dify.ai/en/cloud/use-dify/knowledge/external-knowledge-api
- 外部知识库 API 中文文档：https://docs.dify.ai/zh/cloud/use-dify/knowledge/external-knowledge-api

