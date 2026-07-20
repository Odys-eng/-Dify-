# Dify 知识库资料索引

更新时间：2026-07-09

## 官方资料

### 1. Knowledge 概览

来源：https://docs.dify.ai/en/cloud/use-dify/knowledge/readme

要点：

- Dify 的 Knowledge 是可接入 AI 应用的自有数据集合。
- 核心机制是 RAG：先检索相关知识，再把检索结果和用户问题一起交给大模型生成回答。
- 可以创建多个知识库，按领域、场景或数据源拆分，再按应用需要选择性接入。

适合用于：

- 课程里解释“为什么需要知识库”。
- 写 RAG 入门章节。
- 设计 RuyiDify 的企业资料问答案例。

### 2. Knowledge Retrieval 节点

来源：https://docs.dify.ai/en/cloud/use-dify/nodes/knowledge-retrieval

要点：

- Knowledge Retrieval 节点用于在工作流或 Chatflow 中检索知识库内容。
- 常见链路是：用户输入 -> 知识检索 -> LLM 节点结合上下文生成 -> Answer 节点返回。
- 节点配置重点包括查询内容、检索哪些知识库、检索结果如何处理。
- 多个知识库可以同时检索，再通过节点级检索设置进行合并、重排或过滤。
- 支持 Top K、Score Threshold、Rerank Model、Weighted Score、元数据过滤等控制项。

适合用于：

- 讲 Dify 工作流里的 RAG 节点配置。
- 做“知识库检索质量调参”演示。
- 拆解 Top K、阈值、重排模型对答案质量的影响。

### 3. Manage Knowledge via API

来源：https://docs.dify.ai/en/cloud/use-dify/knowledge/manage-knowledge/maintain-dataset-via-api

要点：

- Dify 提供 Knowledge Base API，可用程序管理知识库、文档和 chunks。
- 适合做数据同步、CI/CD 或外部系统自动导入。
- API 访问在创建知识库后默认可用。
- 单个 Knowledge Base API key 可访问同账号下可见的知识库，必须服务端保存，不要暴露到前端或公开仓库。

适合用于：

- RuyiDify 二开里的“批量导入资料”功能设计。
- 企业知识库自动同步脚本。
- 课程里讲“从手工上传到自动化知识工程”。

### 4. External Knowledge API

来源：https://docs.dify.ai/en/cloud/use-dify/knowledge/external-knowledge-api

要点：

- 当团队已有自己的 RAG 系统或第三方知识服务时，可以通过外部知识库 API 接入 Dify。
- Dify 会向配置的 endpoint 自动追加 `/retrieval`，用 `POST` 请求检索。
- 请求中包含 `knowledge_id`、`query`、`retrieval_setting`，可选 `metadata_condition`。
- 鉴权方式是 Bearer token，Dify 只传递 key，实际校验逻辑由外部服务实现。

适合用于：

- 接入已有向量库、LlamaIndex、LangChain、企业搜索系统。
- 设计 RuyiDify 的“外部知识服务适配器”。
- 给学员讲 Dify 内置知识库与外部知识库的边界。

### 5. Connect to External Knowledge Base

来源：https://docs.dify.ai/en/cloud/use-dify/knowledge/connect-external-knowledge-base

要点：

- 连接外部知识库分三步：构建可查询 API、在 Dify 注册 API endpoint、创建外部知识源。
- Dify 对外部知识库只有检索访问权，不能修改或管理外部内容。
- 注册 API 时填写名称、API Endpoint、API Key。
- 创建外部知识库时要填写 External Knowledge ID，它会作为 `knowledge_id` 传给外部服务。
- 常见问题包括响应格式不符合规范，例如 `metadata` 不能是 `null`，每条记录必须有 `content` 和 `score`。

适合用于：

- 做外部知识库接入演示。
- 写企业系统集成方案。
- 给外部 RAG 服务定义最小可用接口。

### 6. Knowledge Pipeline

来源：https://dify.ai/blog/introducing-knowledge-pipeline

要点：

- Knowledge Pipeline 面向企业非结构化数据处理，把 PDF、PPT、Excel、图片、HTML 等资料转成高质量上下文。
- 官方强调企业 RAG 的瓶颈不只是模型，而是把复杂资料转成可靠上下文的工程过程。
- 这类流程需要设计、调试和可观测性，不是简单上传文件。

适合用于：

- 课程里讲“企业 RAG 不等于上传文档”。
- 设计 RuyiDify 的资料处理流水线。
- 写知识工程、上下文工程相关博客。

### 7. Multimodal Knowledge Base

来源：https://dify.ai/blog/multimodal-retrieval-is-now-available-in-the-knowledge-base

要点：

- Dify 知识库已支持多模态检索，文本和图片可以进入统一语义空间。
- 支持 Image-to-Text、Text-to-Image、Image-to-Image 检索。
- Markdown 中引用的 JPG、PNG、GIF 图片可被抽取并向量化，单图上限 2MB。
- 多模态 RAG 的链路依然是 Chunking、Indexing、Retrieval、Reranking、Generation。
- 对包含产品照片、架构图、截图、培训手册的企业资料尤其有价值。

适合用于：

- 讲图文知识库、截图问答、产品资料问答。
- RuyiDify 课程中加入“多模态知识库”高级章节。
- 对比传统文本 RAG 和多模态 RAG。

## 建议课程结构

1. 知识库是什么：从私有数据到 RAG。
2. 快速创建知识库：上传文档、切分、索引、测试检索。
3. 在 Chatflow 中使用 Knowledge Retrieval 节点。
4. 检索质量调参：Top K、Score Threshold、Rerank、元数据过滤。
5. Knowledge Base API：自动化导入与同步。
6. 外部知识库：接入已有 RAG 系统。
7. Knowledge Pipeline：企业资料处理工程化。
8. 多模态知识库：让图片、截图、图表也能被检索。

