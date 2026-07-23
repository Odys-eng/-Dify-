# Dify 平台制造业维修问答平台实施指南

> **适用版本**：Dify 社区版 1.16.0
> **当前状态**：Docker 已启动（14 容器），Web UI 可访问（http://localhost）
> **前置条件**：`.env` 已配置 DeepSeek + Tavily API Key

---

## 与 Dify 旧版的关键差异

| 旧概念（0.x） | 新版实现（1.16.0） |
|-------------|------------------|
| 模型供应商内置 | 插件化，需从 marketplace 安装或预装 |
| 自定义工具 | HTTP Request 节点（画布直接配置） |
| OpenAI-API-compatible 接 DeepSeek | DeepSeek 原生插件 `langgenius/deepseek` |
| 内置 BGE Embedding | Docker 自部署 TEI 服务 |

---

## 一、前置确认

| # | 检查项 | 命令/方法 |
|---|--------|----------|
| 1 | 容器运行 | `cd dify/docker && docker compose ps` — 14 个 Up |
| 2 | Web UI | 浏览器 http://localhost |
| 3 | DeepSeek Key | `grep DEEPSEEK_API_KEY dify/docker/.env` |
| 4 | Tavily Key | `grep TAVILY_API_KEY dify/docker/.env` |

---

## 二、步骤 1：部署 TEI Embedding 服务

Dify 1.16.0 不自带 Embedding 模型。必须自部署 TEI（Text Embeddings Inference）服务。

### 2.1 启动 TEI

在 PowerShell 执行：

```powershell
docker pull ghcr.io/huggingface/text-embeddings-inference:cpu-1.4

docker run -d --name tei-bge `
  -p 9090:80 `
  ghcr.io/huggingface/text-embeddings-inference:cpu-1.4 `
  --model-id BAAI/bge-large-zh-v1.5
```

> ⚠️ 必须用 `cpu-1.4` 版本，最新 1.7 有 bge 模型 bug。

### 2.2 验证 TEI

```powershell
curl http://localhost:9090/embed -X POST -H "Content-Type: application/json" -d '{"inputs":"测试"}'
```

返回 `[[0.0123, -0.0456, ...]]` 即成功。Dify 1.16.0 调的是 OpenAI 兼容的 `/v1/embeddings` 接口。

### 2.3 在 Dify 中配置 TEI Embedding

1. Dify → 设置 → 模型供应商 → 搜索 **「Text Embeddings Inference」** → 安装
2. 点击「添加模型」：
   - **模型名**：`bge-large-zh-v1.5`
   - **类型**：Text Embedding
   - **服务器 URL**：`http://host.docker.internal:9090`
   - **API Key**：留空
3. 点击「测试连接」 → 返回向量维度 1024 → **✅ 成功**

---

## 三、步骤 2：安装 DeepSeek 模型插件

Dify 1.16.0 中 DeepSeek 是独立插件（`langgenius/deepseek:0.0.19`，已预装在 plugin_daemon 内）。

### 操作

1. Dify → 设置 → 模型供应商 → 找到 **「DeepSeek」** 卡片
2. 如果显示「未安装」 → 点击 **「安装」**（约 10 秒）
3. 安装后 → 点击「添加模型」：
   - **API Key**：从 `.env` 复制 `DEEPSEEK_API_KEY` 的值
   - **模型名**：`deepseek-v4-flash`
   - **类型**：LLM（聊天）
4. 保存 → 测试 `你好` → **✅ 通过**

> ⚠️ 不用 OpenAI-API-compatible，不用改 API 端点。

---

## 四、步骤 3：创建知识库

### 4.1 准备 PDF

| 文档 | 存放路径 | 状态 |
|------|---------|------|
| Siemens 操作手册 | `data/pdfs/SINUMERIK_840Dsl_828D_通用操作手册.pdf` | ✅ 已下载 |
| FANUC 维修手册 | 百度网盘（提取码 `3f8g`） | ❌ 待下载 |
| CNC 故障案例集 | `data/CNC故障案例集.md` | ✅ 已自编 |

### 4.2 创建

1. 顶部导航 → **「知识库」** → 右上角 **「创建知识库」**
2. 名称：`制造业设备维修手册库`
3. 数据源：**「导入已有文本」** → 上传 PDF 文件

### 4.3 分段配置

| 配置 | 值 |
|------|-----|
| 分段方式 | 通用 |
| 分段长度 | 500 |
| 重叠 | 50 |

### 4.4 索引策略

| 配置 | 值 |
|------|-----|
| 索引方式 | 高质量索引 |
| Embedding 模型 | 选择步骤 2.3 配置的 `bge-large-zh-v1.5` |
| 检索方式 | 混合检索 |

### 4.5 检索参数

| 配置 | 值 |
|------|-----|
| 检索模式 | 混合检索 |
| Top K | 3 |
| Score 阈值 | 0.5 |
| Rerank | 开启 |

### 4.6 验证

点击「召回测试」，输入 `主轴异响 SP-2003`，应返回相关片段且 Score ≥ 0.5。

---

## 五、步骤 4：导入 Workflow DSL

### 5.1 导入

1. Dify → **「应用」** → 右上角 **「创建应用」** → **「从 DSL 导入」**
2. 上传 `D:\code\DifiProject\workflow\Workflow-DSL配置.yml`
3. 导入成功 → 画布显示 6 个节点

### 5.2 替换占位符

导入后搜索 `REPLACE_`，替换以下 3 个占位符：

| 搜索 | 替换为 |
|------|--------|
| `REPLACE_DATASET_ID` | 步骤四创建的知识库 ID（知识库 URL 中的 UUID） |
| `REPLACE_TAVILY_KEY` | 从 `.env` 复制 `TAVILY_API_KEY` 的值 |
| `REPLACE_SYSTEM_PROMPT` | 下面 System Prompt 的完整内容 |

### 5.3 确认节点绑定

1. 双击「知识库检索」节点 → 选择步骤四创建的知识库
2. 双击「Tavily HTTP 搜索」节点 → 确认 api_key 已替换
3. 双击「智能问答生成」节点 → 确认模型为 `deepseek-v4-flash`

### 5.4 粘贴 System Prompt

LLM 节点 → System 角色框粘贴：

```
你是一位制造业设备维修智能助手，专注于 CNC 数控机床、PLC、工业机器人、伺服系统等设备的故障诊断与维修指导。

# 回答规则

## 1. 内容来源约束
- 严格基于检索到的资料回答，不编造未在资料中出现的信息
- 如果知识库结果非空，优先使用知识库内容；知识库为空时使用联网搜索结果

## 2. 答案结构（必须遵循）
答案必须按以下结构输出：

**故障可能原因：**
1. [原因1]（概率 XX%）
2. [原因2]（概率 XX%）

**排查步骤：**
Step 1: [可执行的排查动作]
Step 2: [可执行的排查动作]
⚠️ Step 3: [涉及安全的操作必须加警告标识]

**引用来源：**
- 📄 [文档名] 第X页（知识库命中时）
- 🔗 [URL]（联网搜索时）

## 3. 多轮对话上下文处理
- 当用户追问时，结合历史对话保持设备型号、故障类型等上下文一致
- 如果用户切换到完全新话题，直接回答新问题

## 4. 兜底话术（无法回答时）
⚠️ 现有资料无法完全解答该问题。建议：1.联系设备厂商技术支持 2.提供更多故障细节

## 5. 安全警告规则
- 涉及高压电操作、机械拆卸、压力系统的步骤，必须加 ⚠️ 警告
```

### 5.5 LLM 模型配置

| 配置 | 值 |
|------|-----|
| 模型 | deepseek-v4-flash |
| 温度 | 0.3 |
| 最大 Token | 2048 |

### 5.6 发布

点击右上角 **「发布」** → **✅ 完成**

---

## 六、验收演示（3 个场景）

| 场景 | 输入 | 预期 |
|------|------|------|
| 1 | `FANUC 0i-MF 主轴异响 SP-2003` | 故障原因 + 排查步骤 + 📄 引用 |
| 2 | `西门子 840D sl 驱动过流` | 故障原因 + 排查步骤 + 🔗 URL 引用 |
| 3 | 第一轮：`CNC 加工中心换刀故障`<br>第二轮：`换刀臂卡在中间位置怎么办` | 第二轮提及「换刀臂」 |

---

## 附录 A：PDF 下载资源

### Siemens（✅ 已下载）
- 路径：`data/pdfs/SINUMERIK_840Dsl_828D_通用操作手册.pdf`（392 页）

### FANUC 0i-MF 维修说明书（❌ 需手动下载）
- 百度网盘：https://pan.baidu.com/s/1qLOrMqopTrQkSyH-pU1q0w
- 提取码：`3f8g`

### CNC 故障案例集（✅ 已自编）
- 路径：`data/CNC故障案例集.md`（6 个案例 + 报警代码表）

---

## 附录 B：常见问题

| 问题 | 解决 |
|------|------|
| 知识库处理失败 | 检查 TEI 服务：`curl http://localhost:9090/health` |
| LLM 节点报 401 | DeepSeek Key 过期，重新获取 |
| Tavily HTTP 请求失败 | 检查 api_key 是否正确 |
| 导入 DSL 报 YAML 解析错误 | 检查占位符 `REPLACE_XXX` 格式 |
| 发布报「无效变量」 | 检查 prompt 中变量引用 = `{{#节点ID.字段#}}` |
| 容器重启后 Web UI 502 | `docker compose restart nginx` |
