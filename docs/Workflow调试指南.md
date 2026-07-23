# Workflow 调试指南

> **文件路径**：`docs/Workflow调试指南.md`
> **用途**：Dify Workflow 各节点常见报错及解决方案 + 日志查看方法
> **适用场景**：Workflow 配置完成后，调试阶段排查问题

---

## 一、各节点常见报错及解决方案

### 1.1 知识库检索节点（Knowledge Retrieval）

| 报错信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `Dataset not found` | 知识库 ID 错误或未选择 | 在节点配置中重新选择知识库 |
| `result` 为空（所有查询都未命中） | score_threshold 过高 | 降低 `score_threshold`（0.5 → 0.3）测试 |
| `result` 为空（特定查询未命中） | 知识库内容未覆盖 | 补充相关文档，或检查切片质量 |
| `Embedding model not available` | bge-large-zh-v1.5 未安装 | 在「设置 → 模型供应商」中启用 BGE |
| 检索结果不相关 | 切片过大或 Rerank 未开启 | 1. 减小 `chunk_size`（500→300）<br>2. 确认 `reranking_enable=true` |
| `Timeout` | 知识库数据量过大 | 等待向量化完成，或减少文档数量 |

**调试命令**：
```bash
# 用 verify_retrieval.py 单独测试知识库检索
python src/knowledge/verify_retrieval.py --dataset_id xxx --api_key dataset-xxx
```

---

### 1.2 条件分支节点（if-else）

| 报错信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| 走错分支（命中却走了联网） | `variable_selector` 配置错误 | 确认指向 `["knowledge_retrieval", "result"]` |
| 走错分支（未命中却走了 LLM） | `comparison_operator` 错误 | 确认使用 `not empty`（不是 `empty`） |
| `Invalid condition` | 条件表达式语法错误 | 检查 `case_id`、`logical_operator` 是否正确 |
| 两个分支都执行 | 边连接错误 | 确认 `sourceHandle` 为 `true` / `false` |

**条件配置验证**：

```
正确配置：
  variable_selector: ["knowledge_retrieval", "result"]
  comparison_operator: not empty
  → result 有内容时走 true 分支（命中）
  → result 为空时走 false 分支（未命中）

错误配置（常见）：
  comparison_operator: empty
  → 逻辑反了，有内容时反而走联网搜索
```

---

### 1.3 LLM 节点

| 报错信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `Model not found: deepseek-chat` | ⚠️ 用了停用的模型名 | 改为 `deepseek-v4-flash`（2026-07-24 停用） |
| `Model not found: deepseek-v4-flash` | Dify 版本过旧或未配置供应商 | 1. 升级 Dify<br>2. 用「OpenAI-API-compatible」方式接入 |
| `HTTP 401 Unauthorized` | API Key 错误 | 在「设置 → 模型供应商 → DeepSeek」重新填入 Key |
| `HTTP 429 Rate limit` | DeepSeek 调用频率超限 | 等待 60 秒后重试，或检查账户额度 |
| 输出格式不符合预期 | System Prompt 未生效 | 1. 检查 LLM 节点的 `prompt_template`<br>2. 确认 system 角色的文本已粘贴 |
| 输出缺少引用来源 | Prompt 中引用规则未强调 | 在 System Prompt 中强化「每个结论必须标注引用」 |
| 输出包含编造信息 | LLM 幻觉 | 1. 降低 `temperature`（0.3 → 0.1）<br>2. 在 Prompt 中强调「不编造」 |
| 响应超时（>30s） | 思考模式耗时过长 | 降低 `reasoning_effort`（high → 默认） |
| `thinking mode not supported` | 模型不支持思考模式 | 确认用 `deepseek-v4-flash`（V3 不支持思考模式） |

**LLM 输出验证清单**：

```
□ 答案包含「故障可能原因」部分？
□ 答案包含「排查步骤」部分？
□ 答案包含「引用来源」部分？
□ 每个关键结论后都有引用标注？
□ 涉及安全的步骤有 ⚠️ 标识？
□ 没有编造的设备型号或故障代码？
```

---

### 1.4 工具节点（Tavily Search）

| 报错信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `Tool not found` | 工具未配置或名称错误 | 在「工具 → 自定义」中确认工具已创建 |
| `HTTP 401` | Tavily API Key 错误 | 重新获取 Key 并更新工具配置 |
| `HTTP 429` | Tavily 免费额度耗尽 | 升级付费计划或等待下月重置 |
| `Timeout` | 网络慢或 search_depth=advanced | 改用 `search_depth: basic` |
| 返回结果为空 | 查询过窄或专业性强 | 1. 扩大查询范围<br>2. 手动加 `site:fanuc.com` 定向 |
| `tool_parameters` 映射错误 | 变量引用语法错误 | 确认 `query` 值为 `{{#sys.query#}}` |

**工具测试命令**：
```bash
# 直接测试 Tavily API
TAVILY_API_KEY=$(grep "^TAVILY_API_KEY=" dify/docker/.env | cut -d'=' -f2-)
curl -s https://api.tavily.com/search \
  -H "Content-Type: application/json" \
  -d "{\"api_key\":\"$TAVILY_API_KEY\",\"query\":\"CNC repair\",\"max_results\":2}"
```

---

### 1.5 Answer 节点

| 报错信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| 输出为空 | LLM 节点未连接 | 确认 LLM → Answer 的边存在 |
| 输出包含 `{{#...#}}` | 变量引用未解析 | 检查 `answer` 字段值为 `{{#llm_generate.text#}}` |
| 引用块不显示 | `retriever_resource` 未开启 | 在 Workflow features 中开启 `retriever_resource.enabled: true` |

---

### 1.6 整体 Workflow

| 报错信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `Workflow execution failed` | 节点连接断裂 | 检查所有 edges，确认 6 条连接完整 |
| `Circular dependency` | 节点形成环 | Workflow 不支持循环，检查是否有反向连接 |
| `Node type not supported` | Dify 版本过旧 | 升级 Dify 社区版到最新 |
| 多轮对话上下文丢失 | Memory 未开启 | Chatflow 模式自动开启 Memory，检查应用类型是否为 `advanced-chat` |

---

## 二、如何查看 Dify 节点执行日志

### 2.1 在 Web UI 中查看

1. 打开 Workflow 应用 → 点击右上角 **「运行」** 或在聊天界面发送消息
2. 执行完成后，点击消息下方的 **「查看详情」** 或 **「Trace」** 按钮
3. 展开工作流执行图，查看每个节点的：
   - **输入**：该节点接收的数据
   - **输出**：该节点产生的数据
   - **耗时**：执行时间
   - **状态**：成功/失败

### 2.2 在 Docker 日志中查看

```bash
# 查看 API 服务日志（实时跟踪）
cd dify/docker
docker compose logs -f api

# 查看 Worker 服务日志（异步任务，如知识库向量化）
docker compose logs -f worker

# 查看最近 100 行日志
docker compose logs --tail 100 api

# 过滤错误日志
docker compose logs api 2>&1 | grep -i "error\|exception\|fail"

# 查看特定时间段的日志
docker compose logs --since "2026-07-19T23:00:00" api
```

### 2.3 关键日志关键词

| 关键词 | 含义 | 所在服务 |
|--------|------|---------|
| `workflow_run` | Workflow 执行记录 | api |
| `node_execution` | 节点执行记录 | api |
| `knowledge_retrieval` | 知识库检索日志 | api |
| `llm_completion` | LLM 调用日志 | api |
| `tool_invocation` | 工具调用日志 | api |
| `embedding` | 向量化日志 | worker |
| `ERROR` | 错误日志 | 全部 |

### 2.4 调试模式

在 Dify Workflow 编辑器中，可以单步调试：

1. 点击任意节点 → 右侧面板显示 **「输入」** 和 **「输出」**
2. 点击 **「运行此节点」** 可单独执行该节点（需提供输入）
3. 使用 **「运行」** 按钮执行整个 Workflow，查看完整执行链路

---

## 三、调试工作流

### 3.1 分步调试法

```
Step 1：单独测试知识库检索
  → 用 verify_retrieval.py 确认知识库返回正确结果
  → 或在 Workflow 编辑器中单独运行 KR 节点

Step 2：验证 if-else 分支
  → 输入一个必定命中的查询（如「FANUC 主轴异响」）
  → 确认走 true 分支
  → 输入一个必定未命中的查询（如「量子计算机维修」）
  → 确认走 false 分支

Step 3：验证 Tavily 工具
  → 在 false 分支中检查 Tool 节点输出
  → 确认返回搜索结果 JSON

Step 4：验证 LLM 输出
  → 检查 LLM 节点的输出是否符合 System Prompt 规定的结构
  → 确认引用标注存在

Step 5：端到端测试
  → 运行 3 个验收场景
  → 确认整体流程无报错
```

### 3.2 常见问题快速排查

| 症状 | 首先检查 | 其次检查 |
|------|---------|---------|
| 无任何响应 | LLM 节点是否配置 | API Key 是否有效 |
| 响应很慢 | Tavily search_depth | reasoning_effort 是否过高 |
| 答案不相关 | 知识库 score_threshold | 切片大小是否合适 |
| 答案有编造 | temperature 是否过高 | System Prompt 是否强调「不编造」 |
| 引用不显示 | retriever_resource 是否开启 | 知识库是否真正命中 |
| 多轮对话失效 | 应用类型是否为 advanced-chat | Memory 是否被禁用 |

---

## 四、性能优化建议

### 4.1 响应时间优化

| 优化项 | 当前值 | 优化建议 | 预期效果 |
|--------|--------|---------|---------|
| Tavily search_depth | basic | 保持 basic | advanced 慢 2-3 倍 |
| reasoning_effort | high | 知识库命中时可用默认 | 减少 LLM 思考时间 |
| top_k | 3 | 保持 3 | 更多结果增加 LLM 处理时间 |
| max_tokens | 2048 | 可降至 1024 | 减少输出时间 |

### 4.2 成本优化

| 优化项 | 当前配置 | 优化建议 |
|--------|---------|---------|
| DeepSeek 调用 | V4-Flash ¥1/百万输入 | 最优（已是最便宜） |
| Tavily 调用 | 免费 1000 次/月 | Demo 阶段够用 |
| 知识库向量化 | 一次性 | 无持续成本 |
| Embedding | bge-large-zh 本地 | 无 API 费用 |

### 4.3 目标性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 知识库命中响应时间 | ≤ 5 秒 | 不触发联网搜索 |
| 联网兜底响应时间 | ≤ 15 秒 | 含 Tavily 搜索 + LLM |
| 多轮追问响应时间 | ≤ 8 秒 | 有上下文，略快于首次 |
| 成功率 | ≥ 95% | 20 次测试允许 1 次失败 |
