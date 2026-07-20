---
title: Dify 知识库接口文档
updated: 2026-07-15
maintainer: ruyi
status: stable
source: https://docs.dify.ai/zh/api-reference/guides/knowledge
source_last_modified: 2026-07-09
---

# Dify 知识库接口文档

> 【官方文档确认】本文依据 Dify 官方“知识库 API”概览及各端点详情页整理，核对日期为 **2026-07-15**。官方概览页面标注最后修改于 **2026-07-09**。中文页面由 AI 自动翻译，出现歧义时应以其链接的英文原版和当前部署版本为准。

## 1. 总体统计

Dify 官方当前列出 **46 个知识库相关 API**，可分为 **7 类**。

| 类别 | 接口数 | 主要职责 |
|---|---:|---|
| 知识库 | 6 | Dataset 生命周期、配置和检索测试 |
| 文档 | 12 | 文档创建、索引状态、查询、更新、下载和删除 |
| 分段与子分段 | 9 | Segment 与父子模式 Child Chunk 管理 |
| 元数据 | 7 | 自定义/内置字段及文档元数据赋值 |
| 标签 | 7 | 工作空间标签及知识库绑定关系 |
| 模型 | 1 | 查询可用于嵌入和重排序的模型 |
| 知识流水线 | 4 | 文件上传、数据源节点和完整流水线执行 |
| **合计** | **46** |  |

## 2. 统一调用约定

### 2.1 基础地址

服务 API 的基础地址以 Dify 控制台“知识库 → 服务 API”面板显示的端点为准。

- Dify Cloud 示例：`https://api.dify.ai/v1`
- 自托管环境：使用当前部署对应的服务 API 地址

本文所有接口路径均省略基础地址，只保留 `/datasets...` 等相对路径。

### 2.2 身份认证

请求头使用：

```http
Authorization: Bearer <API_KEY>
```

安全要求：

- API Key 只能保存在服务端。
- 不得写入浏览器代码、客户端应用、公开仓库或本文档。
- 单个知识库 API Key 可以访问创建该密钥的账户下所有可见知识库。
- 可在单个知识库左下角的“访问 API”中关闭该知识库的 API 访问。

### 2.3 异步索引

文档创建和内容更新可能触发异步索引：

1. 创建或更新文档。
2. 保存接口返回的 `batch`。
3. 使用索引状态接口轮询。
4. 等待状态变为 `completed` 或 `error`。

可能经过的中间状态包括：

```text
waiting → parsing → cleaning → splitting → indexing → completed/error
```

### 2.4 删除操作

知识库、文档和分段删除通常不可逆。调用 `DELETE` 接口前应：

- 二次确认目标 ID。
- 确认没有误用生产环境。
- 保存必要的备份和审计信息。
- 避免把空响应或超时误判为删除失败后盲目重试。

## 3. 知识库接口（6 个）

用于管理知识库本身的生命周期、配置和检索。

| # | 方法 | 路径 | 接口 | 用途 |
|---:|---|---|---|---|
| 1 | `POST` | `/datasets` | [创建空知识库](https://docs.dify.ai/zh/api-reference/knowledge-bases/create-an-empty-knowledge-base) | 创建一个尚未包含文档的知识库。 |
| 2 | `GET` | `/datasets` | [获取知识库列表](https://docs.dify.ai/zh/api-reference/knowledge-bases/list-knowledge-bases) | 分页查询知识库，支持关键词或标签筛选。 |
| 3 | `GET` | `/datasets/{dataset_id}` | [获取知识库详情](https://docs.dify.ai/zh/api-reference/knowledge-bases/get-knowledge-base) | 读取嵌入模型、检索配置和文档统计等详情。 |
| 4 | `PATCH` | `/datasets/{dataset_id}` | [更新知识库](https://docs.dify.ai/zh/api-reference/knowledge-bases/update-knowledge-base) | 按请求字段修改名称、权限、嵌入模型或检索设置。 |
| 5 | `DELETE` | `/datasets/{dataset_id}` | [删除知识库](https://docs.dify.ai/zh/api-reference/knowledge-bases/delete-knowledge-base) | 永久删除知识库及其全部文档。 |
| 6 | `POST` | `/datasets/{dataset_id}/retrieve` | [从知识库检索分段 / 测试检索](https://docs.dify.ai/zh/api-reference/knowledge-bases/retrieve-chunks-from-a-knowledge-base-test-retrieval) | 按查询召回相关分段；生产检索和召回测试共用。 |

## 4. 文档接口（12 个）

用于创建、索引、查询、下载、更新和删除知识库中的文档。

| # | 方法 | 路径 | 接口 | 用途 |
|---:|---|---|---|---|
| 1 | `POST` | `/datasets/{dataset_id}/document/create-by-text` | [从文本创建文档](https://docs.dify.ai/zh/api-reference/documents/create-document-by-text) | 用文本创建文档并返回异步索引 batch ID。 |
| 2 | `POST` | `/datasets/{dataset_id}/document/create-by-file` | [从文件创建文档](https://docs.dify.ai/zh/api-reference/documents/create-document-by-file) | 上传文件创建文档并返回异步索引 batch ID。 |
| 3 | `GET` | `/datasets/{dataset_id}/documents/{batch}/indexing-status` | [获取文档嵌入状态（进度）](https://docs.dify.ai/zh/api-reference/documents/get-document-indexing-status) | 使用 batch ID 轮询解析、切分和索引进度。 |
| 4 | `GET` | `/datasets/{dataset_id}/documents` | [获取知识库的文档列表](https://docs.dify.ai/zh/api-reference/documents/list-documents) | 分页查询文档，支持关键词或索引状态筛选。 |
| 5 | `GET` | `/datasets/{dataset_id}/documents/{document_id}` | [获取文档详情](https://docs.dify.ai/zh/api-reference/documents/get-document) | 读取索引状态、元数据及处理统计信息。 |
| 6 | `GET` | `/datasets/{dataset_id}/documents/{document_id}/download` | [下载文档](https://docs.dify.ai/zh/api-reference/documents/download-document) | 获取原始上传文件的签名下载 URL。 |
| 7 | `POST` | `/datasets/{dataset_id}/documents/download-zip` | [批量下载文档（ZIP）](https://docs.dify.ai/zh/api-reference/documents/download-documents-as-zip) | 将最多 100 个文件上传型文档打包下载。 |
| 8 | `PATCH` | `/datasets/{dataset_id}/documents/{document_id}` | [更新文档](https://docs.dify.ai/zh/api-reference/documents/update-document) | 上传新文件替换内容并重新触发索引。 |
| 9 | `POST` | `/datasets/{dataset_id}/documents/{document_id}/update-by-text` | [用文本更新文档](https://docs.dify.ai/zh/api-reference/documents/update-document-by-text) | 更新文本、名称或处理配置；内容变化会重建索引。 |
| 10 | `POST` | `/datasets/{dataset_id}/documents/{document_id}/update-by-file` | [用文件更新文档](https://docs.dify.ai/zh/api-reference/documents/update-document-by-file) | 已废弃的文件更新别名，应改用“更新文档”。 |
| 11 | `PATCH` | `/datasets/{dataset_id}/documents/status/{action}` | [批量更新文档状态](https://docs.dify.ai/zh/api-reference/documents/update-document-status-in-batch) | 批量启用、禁用、归档或取消归档文档。 |
| 12 | `DELETE` | `/datasets/{dataset_id}/documents/{document_id}` | [删除文档](https://docs.dify.ai/zh/api-reference/documents/delete-document) | 永久删除文档及其全部分段。 |

## 5. 分段与子分段接口（9 个）

用于管理文档分段，以及父子分段模式中的子分段。

| # | 方法 | 路径 | 接口 | 用途 |
|---:|---|---|---|---|
| 1 | `POST` | `/datasets/{dataset_id}/documents/{document_id}/segments` | [向文档添加分段](https://docs.dify.ai/zh/api-reference/chunks/create-chunks) | 手动新增分段；问答模式还需要 `answer`。 |
| 2 | `GET` | `/datasets/{dataset_id}/documents/{document_id}/segments` | [从文档获取分段](https://docs.dify.ai/zh/api-reference/chunks/list-chunks) | 分页查询分段，支持关键词或状态筛选。 |
| 3 | `GET` | `/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}` | [获取文档中的分段详情](https://docs.dify.ai/zh/api-reference/chunks/get-chunk) | 读取单个分段的内容、关键词和索引状态。 |
| 4 | `POST` | `/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}` | [更新文档中的分段](https://docs.dify.ai/zh/api-reference/chunks/update-chunk) | 更新内容、关键词或答案并重新索引该分段。 |
| 5 | `DELETE` | `/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}` | [删除文档中的分段](https://docs.dify.ai/zh/api-reference/chunks/delete-chunk) | 永久删除指定分段。 |
| 6 | `POST` | `/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks` | [创建子分段](https://docs.dify.ai/zh/api-reference/chunks/create-child-chunk) | 在父分段下创建 customized 子分段。 |
| 7 | `GET` | `/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks` | [获取子分段](https://docs.dify.ai/zh/api-reference/chunks/list-child-chunks) | 分页查询某个父分段的子分段。 |
| 8 | `PATCH` | `/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks/{child_chunk_id}` | [更新子分段](https://docs.dify.ai/zh/api-reference/chunks/update-child-chunk) | 修改子分段内容。 |
| 9 | `DELETE` | `/datasets/{dataset_id}/documents/{document_id}/segments/{segment_id}/child_chunks/{child_chunk_id}` | [删除子分段](https://docs.dify.ai/zh/api-reference/chunks/delete-child-chunk) | 永久删除指定子分段。 |

父子模式说明：

- 父子模式对应 `hierarchical_model`。
- 通过 API 创建或更新的子分段，其 `type` 为 `customized`。
- 由索引流程自动生成的子分段，其 `type` 为 `automatic`。

## 6. 元数据接口（7 个）

元数据为文档附加结构化信息，并可在检索时用于过滤。

| # | 方法 | 路径 | 接口 | 用途 |
|---:|---|---|---|---|
| 1 | `POST` | `/datasets/{dataset_id}/metadata` | [创建元数据字段](https://docs.dify.ai/zh/api-reference/metadata/create-metadata-field) | 创建 `string`、`number` 或 `time` 类型的自定义字段。 |
| 2 | `GET` | `/datasets/{dataset_id}/metadata` | [获取元数据字段列表](https://docs.dify.ai/zh/api-reference/metadata/list-metadata-fields) | 查询自定义和内置字段及其使用文档数。 |
| 3 | `PATCH` | `/datasets/{dataset_id}/metadata/{metadata_id}` | [更新元数据字段](https://docs.dify.ai/zh/api-reference/metadata/update-metadata-field) | 重命名自定义元数据字段。 |
| 4 | `DELETE` | `/datasets/{dataset_id}/metadata/{metadata_id}` | [删除元数据字段](https://docs.dify.ai/zh/api-reference/metadata/delete-metadata-field) | 删除字段及所有文档上的对应取值。 |
| 5 | `GET` | `/datasets/{dataset_id}/metadata/built-in` | [获取内置元数据字段](https://docs.dify.ai/zh/api-reference/metadata/get-built-in-metadata-fields) | 查询 `document_name`、`uploader`、`upload_date` 等内置字段。 |
| 6 | `POST` | `/datasets/{dataset_id}/metadata/built-in/{action}` | [更新内置元数据字段](https://docs.dify.ai/zh/api-reference/metadata/update-built-in-metadata-field) | 通过 action 为知识库启用或禁用内置字段。 |
| 7 | `POST` | `/datasets/{dataset_id}/documents/metadata` | [批量更新文档元数据](https://docs.dify.ai/zh/api-reference/metadata/update-document-metadata-in-batch) | 一次为多个文档写入元数据键值对。 |

元数据还可以充当稳定的外部键。例如，把源系统的记录 ID 写入文档元数据，后续同步时即可按该 ID 查找并更新同一文档，避免重复导入。

## 7. 标签接口（7 个）

标签在工作空间层面管理，不依附于某个具体知识库。

| # | 方法 | 路径 | 接口 | 用途 |
|---:|---|---|---|---|
| 1 | `POST` | `/datasets/tags` | [创建知识库标签](https://docs.dify.ai/zh/api-reference/tags/create-knowledge-tag) | 在工作空间中创建知识库标签。 |
| 2 | `GET` | `/datasets/tags` | [获取知识库标签列表](https://docs.dify.ai/zh/api-reference/tags/list-knowledge-tags) | 查询工作空间内的全部知识库标签。 |
| 3 | `PATCH` | `/datasets/tags` | [修改知识库标签](https://docs.dify.ai/zh/api-reference/tags/update-knowledge-tag) | 重命名知识库标签。 |
| 4 | `DELETE` | `/datasets/tags` | [删除知识库标签](https://docs.dify.ai/zh/api-reference/tags/delete-knowledge-tag) | 删除标签并解除全部绑定，不删除知识库。 |
| 5 | `POST` | `/datasets/tags/binding` | [绑定标签到知识库](https://docs.dify.ai/zh/api-reference/tags/create-tag-binding) | 为知识库绑定一个或多个标签。 |
| 6 | `POST` | `/datasets/tags/unbinding` | [解除标签与知识库的绑定](https://docs.dify.ai/zh/api-reference/tags/delete-tag-binding) | 从知识库移除指定标签绑定。 |
| 7 | `GET` | `/datasets/{dataset_id}/tags` | [获取知识库绑定的标签](https://docs.dify.ai/zh/api-reference/tags/get-knowledge-base-tags) | 查询某个知识库当前绑定的标签。 |

## 8. 模型接口（1 个）

| # | 方法 | 路径 | 接口 | 用途 |
|---:|---|---|---|---|
| 1 | `GET` | `/workspaces/current/models/model-types/{model_type}` | [获取可用模型](https://docs.dify.ai/zh/api-reference/models/get-available-models) | 按 `model_type` 查询当前工作空间可用模型。 |

常用的 `model_type`：

- `text-embedding`：查询嵌入模型。
- `rerank`：查询重排序模型。

实际返回结果取决于当前工作空间已经配置的模型供应商和模型。

## 9. 知识流水线接口（4 个）

知识流水线用于从数据源摄取数据，并将其转换为知识库文档。

| # | 方法 | 路径 | 接口 | 用途 |
|---:|---|---|---|---|
| 1 | `POST` | `/datasets/pipeline/file-upload` | [上传流水线文件](https://docs.dify.ai/zh/api-reference/knowledge-pipeline/upload-pipeline-file) | 上传供知识流水线后续处理的文件。 |
| 2 | `GET` | `/datasets/{dataset_id}/pipeline/datasource-plugins` | [获取数据源插件列表](https://docs.dify.ai/zh/api-reference/knowledge-pipeline/list-datasource-plugins) | 查询已发布或草稿流水线的数据源节点。 |
| 3 | `POST` | `/datasets/{dataset_id}/pipeline/datasource/nodes/{node_id}/run` | [执行数据源节点](https://docs.dify.ai/zh/api-reference/knowledge-pipeline/run-datasource-node) | 单独执行数据源节点并流式返回事件。 |
| 4 | `POST` | `/datasets/{dataset_id}/pipeline/run` | [运行流水线](https://docs.dify.ai/zh/api-reference/knowledge-pipeline/run-pipeline) | 以 `streaming` 或 `blocking` 模式运行完整知识流水线。 |

知识流水线可以通过 `is_published` 选择运行已发布版本或当前草稿版本。

## 10. 推荐调用流程

### 10.1 最小文本知识库闭环

```text
POST /datasets
    ↓
POST /datasets/{dataset_id}/document/create-by-text
    ↓ 保存 batch
GET /datasets/{dataset_id}/documents/{batch}/indexing-status
    ↓ completed
POST /datasets/{dataset_id}/retrieve
```

验收重点：

- 知识库没有被重复创建。
- 文档索引状态为 `completed`。
- 测试问题能召回预期内容。
- 返回结果保留文档和分段来源信息。
- API Key 未进入日志、前端或版本库。

### 10.2 最小文件知识库闭环

1. 创建或选择知识库。
2. 调用文件创建接口上传文件。
3. 保存返回的 `batch`。
4. 轮询索引状态，直到 `completed` 或 `error`。
5. 查询文档详情与分段，检查切分和索引结果。
6. 调用检索接口，验证真实问题能否召回正确内容。

### 10.3 增量同步流程

1. 给文档写入源系统 ID 等稳定元数据。
2. 同步前按外部 ID 定位已有文档，避免重复创建。
3. 内容变化时调用文本更新或标准文件更新接口。
4. 等待重新索引完成后执行检索验收。
5. 记录知识库 ID、文档 ID、batch、索引终态和检索证据，但不记录 API Key。

## 11. 重要兼容性说明

- `POST .../update-by-file` 在官方概览中已标记为**废弃别名**，新代码应使用 `PATCH /datasets/{dataset_id}/documents/{document_id}`。
- 标签属于工作空间；删除标签只解除绑定，不删除被标记的知识库。
- 删除自定义元数据字段时，文档会同时失去该字段的已有取值。
- 检索接口既用于生产召回，也用于知识库召回测试。
- 接口清单来自当前官方文档，不代表任意历史 Dify 版本都具有相同路径和参数。
- 自托管 Dify 升级后，或发现接口返回与本文不一致时，应重新核对当前版本、官方端点详情页及本地源码。

## 12. 统计复核

```text
知识库           6
文档            12
分段与子分段     9
元数据           7
标签             7
模型             1
知识流水线       4
-----------------
总计            46
```

## 13. 官方来源

- [Dify 知识库 API 总览](https://docs.dify.ai/zh/api-reference/guides/knowledge)
- 本文每个接口名称均直接链接到对应的官方端点详情页。
