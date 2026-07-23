# 制造业设备维修知识库智能问答平台

> 基于 **RuyiDify（Dify 1.16）+ Pipeline RAG** 构建  
> 新手从零开始，按本文档操作即可完成全部配置。

---

## 目录

1. [平台简介](#1-平台简介)
2. [准备工作（5 分钟）](#2-准备工作)
3. [第一步：启动 Dify 服务](#3-第一步启动-dify-服务)
4. [第二步：配置 API Key](#4-第二步配置-api-key)
5. [第三步：访问平台](#5-第三步访问平台)
6. [日常操作](#6-日常操作)
7. [知识库管理](#7-知识库管理)
8. [数据备份](#8-数据备份)
9. [评测与验证](#9-评测与验证)
10. [项目文件说明](#10-项目文件说明)
11. [常见问题](#11-常见问题)
12. [关键配置速查](#12-关键配置速查)
13. [安全说明](#13-安全说明)

---

## 1. 平台简介

本平台回答制造业设备维修问题，例如：
- 「FANUC 0i-MF 主轴报警 SP-2003 怎么处理？」
- 「西门子 840D sl 驱动过流怎么排查？」
- 「2025 年最新的 ABB 机器人有哪些新功能？」

**工作原理：**

```
用户提问
  │
  ├─ 在知识库中找到答案 ──→ 结构化故障诊断格式输出
  │
  └─ 知识库没有 ──→ 自动联网搜索（Tavily）──→ 基于搜索结果回答
```

**技术栈：**

| 组件 | 说明 |
|------|------|
| Dify 1.16 | AI 应用编排平台（开源，自部署）|
| DeepSeek-V4-Pro | 大语言模型（通过 SiliconFlow 调用）|
| BGE Embedding | 向量化模型，用于知识库检索 |
| Weaviate | 向量数据库 |
| Tavily | 联网搜索 API |

**从零到跑通，你要做的 5 件事（约 30-40 分钟，大部分时间在等下载）：**

| 步骤 | 做什么 | 对应章节 | 大概耗时 |
|------|--------|---------|---------|
| ① 装环境 | 装 Docker Desktop、Git、Python | 第 2 节 | 10 分钟 |
| ② 申请 Key | 注册 SiliconFlow、Tavily，各拿一个 Key | 第 2 节 | 5 分钟 |
| ③ 启动服务 | 跑一条命令 `bash deploy/startup.sh` | 第 3 节 | 5-10 分钟（等镜像下载）|
| ④ 配置平台 | 网页里填模型 Key、建知识库、导入工作流 | 第 4 节 | 10 分钟 |
| ⑤ 开始问答 | 打开对话页提问验证 | 第 5 节 | 2 分钟 |

> 👉 全程照着章节顺序走即可，每一步都有可直接复制的命令。卡住了看 **第 11 节 常见问题**。

---

## 2. 准备工作

### 需要安装的软件

| 软件 | 版本要求 | 下载地址 |
|------|---------|---------|
| Docker Desktop | 最新版 | https://www.docker.com/products/docker-desktop |
| Git | 任意版本 | https://git-scm.com |
| Python | 3.10 以上 | https://www.python.org（用于运行脚本）|

安装完成后，逐条运行下面的命令验证（都能打印版本号才算成功）：

```bash
docker --version
docker compose version
git --version
python --version
```

> 🪟 **Windows 用户注意**：
> - Docker Desktop 需要开启 WSL2（首次安装会引导），并在 BIOS 里开启 CPU 虚拟化。
> - 每次启动电脑后，要先打开 Docker Desktop 应用、等左下角变绿显示 Running，`docker` 命令才可用。
> - 涉及 `bash`/`openssl`/`crontab` 的命令，请在 **Git Bash** 或 **WSL** 里运行（PowerShell 没有这些命令）。

脚本运行前，先安装 Python 依赖：

```bash
pip install -r src/requirements.txt
```

### 需要申请的 API Key（均有免费额度）

#### SiliconFlow（必须）
> 用途：驱动 DeepSeek-V4-Pro 大模型 + BGE 向量化模型

1. 打开 https://siliconflow.cn → 注册账号
2. 进入「API 密钥」→ 点击「新建 API 密钥」
3. 复制密钥，格式为 `sk-xxxxxxxxxxxxxxxx`

#### Tavily（必须）
> 用途：知识库未命中时联网搜索，免费 1000 次/月

1. 打开 https://app.tavily.com → 注册账号
2. 登录后在 Dashboard 复制 API Key
3. 格式为 `tvly-xxxxxxxxxxxxxxxx`

### 系统要求

| 资源 | 最低要求 |
|------|---------|
| 内存 | 8 GB（推荐 16 GB）|
| 磁盘 | 20 GB 可用空间 |
| 网络 | 能访问 SiliconFlow 和 Tavily |

---

## 3. 第一步：启动 Dify 服务

> 🚀 **最省事的方式（推荐新手）**：直接跑一键脚本，它会自动帮你下载 Dify、生成配置、启动服务。
> 见下方 **3.1（一键启动）**。如果想手动一步步来，看 **3.2（手动启动）**。

### 3.1 一键启动（推荐）

一条命令搞定「下载 Dify → 生成配置 → 启动全部服务」：

```bash
# Mac / Linux / Windows(Git Bash 或 WSL)
bash deploy/startup.sh

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File deploy\startup.ps1
```

脚本运行逻辑（无需你操心）：
1. 检查 Docker 是否装好、是否在运行
2. 如果没有 `dify/` 目录，自动 `git clone` 官方 Dify 到 `dify/`
3. 从 `deploy/.env.template` 生成 `dify/docker/.env`
4. **第一次运行会停下来**，提示你去 `dify/docker/.env` 填 `TAVILY_API_KEY`（联网搜索用）
5. 填好后**再跑一次同样的命令**，它就会启动所有容器并做健康检查

> 💡 **只需要填一个 Key**：`TAVILY_API_KEY`（在 https://app.tavily.com 免费获取）。
> SiliconFlow 的模型密钥不在这里填，而是启动后在 Dify 网页控制台里配（见 **4.3 节**）。
> `.env` 不会被 Git 提交，可放心填真实 Key。

看到 `启动完成！访问地址：http://localhost` 就成功了，跳到 **第 4 节**。

### 3.2 手动启动（想了解细节时用）

**① 获取 Dify 目录**（一键脚本会自动做，手动则二选一）：

```bash
# 方式 A：克隆官方 Dify（推荐，和脚本一致）
git clone https://github.com/langgenius/dify.git dify

# 方式 B：如果队友给了你 DifiProject.rar，解压它得到 dify/ 目录
# 7z x DifiProject.rar   或   unrar x DifiProject.rar
```

**② 准备配置文件**：

```bash
# Mac/Linux
cp deploy/.env.template dify/docker/.env
cp deploy/docker-compose.override.yaml dify/docker/docker-compose.override.yaml
# Windows（PowerShell）
copy deploy\.env.template dify\docker\.env
copy deploy\docker-compose.override.yaml dify\docker\docker-compose.override.yaml
```

打开 `dify/docker/.env`，填入 Tavily 密钥：

```bash
TAVILY_API_KEY=tvly-你的Tavily密钥
```

**③ 启动服务**：

```bash
cd dify/docker
docker compose up -d
```

首次启动会下载镜像，**大约需要 5-10 分钟**（取决于网速）。

> ⚠️ 若你要把 `DifiProject.rar` 转发给别人，先确认包内 `dify/docker/.env`、`nginx/conf.d/.htpasswd_plaintext`、`nginx/ssl/dify.key` 中**没有真实密钥/密码**。可运行 `bash deploy/sanitize-for-release.sh` 检查清理（见 [docs/分发前清理清单.md](docs/分发前清理清单.md)）。

### 3.3 （可选）加 HTTPS + 登录保护

以上启动后是 `http://localhost` 直接访问。如果想加上 HTTPS、限流和登录框（Basic Auth），跑一条命令：

```bash
bash deploy/setup-hardening.sh   # Windows 用 Git Bash / WSL
```

它会自动生成自签证书、生成随机 Basic Auth 密码（存到 `.htpasswd_plaintext`）、部署 Nginx 配置并重启。完成后改用 `https://localhost` 访问。不需要这层保护的话，跳过本节即可。

### 3.4 确认服务正常

```bash
docker compose ps
```

所有服务显示 `Up` 或 `healthy` 即为正常：

```
docker-api-1         Up (healthy)
docker-worker-1      Up
docker-nginx-1       Up
docker-web-1         Up
docker-db_postgres-1 Up (healthy)
docker-redis-1       Up (healthy)
docker-weaviate-1    Up
```

---

## 4. 第二步：配置 API Key

> 这一步在 Dify 控制台中完成，告诉 Dify 使用哪个模型。

### 4.1 登录控制台

打开浏览器访问：
- **没做 3.3 加固** → `http://localhost`
- **做了 3.3 加固** → `https://localhost`（浏览器提示「证书不安全」→ 点「高级」→「继续访问」，自签名证书正常现象）

首次访问会进入 **初始化页面**：自行注册管理员邮箱和密码，之后就用这组账号登录控制台。

### 4.2 登录凭据

| 验证层 | 用户名 | 密码位置 |
|--------|--------|---------|
| Dify 账号（必有）| 首次访问时自己注册的邮箱 | 初始化时自行设置 |
| Nginx Basic Auth（仅做了 3.3 加固才有）| `admin` | `dify/docker/nginx/conf.d/.htpasswd_plaintext` 文件中 |

> 📌 若做了 3.3 加固：**务必保存 `.htpasswd_plaintext` 里的密码**，容器重建后该文件会消失，丢了需重新生成。

### 4.3 配置 SiliconFlow 模型供应商

1. 控制台左下角 → 「设置」→「模型供应商」
2. 找到 **SiliconFlow** → 点击「设置」→ 填入 SiliconFlow API Key（`sk-xxxxxxx`）→ 保存
3. 回到「模型供应商」页顶部 → 「系统模型设置」，选好三类默认模型：
   - **系统推理模型**：`deepseek-ai/DeepSeek-V4-Pro`
   - **Embedding 模型**：`BAAI/bge-large-zh-v1.5`
   - **Rerank 模型**（可选）：`Pro/BAAI/bge-reranker-v2-m3`

> ⚠️ **必须先配好 Embedding 模型再建知识库**，否则文档上传后无法完成索引（向量化会失败）。

### 4.4 创建知识库并上传文档

> ⚠️ **关键：分段模式选「父子索引」+ 父块用「全文」**。本项目文档是结构化短文（每篇约 2KB，含核心知识/可能原因/检查步骤等小节）。若用「通用」分段或父块选「段落」，泛泛查询只会命中文档标题元数据、拿不到正文——这是本项目踩过的最大坑。

1. 控制台顶部 → 「知识库」→ 「创建知识库」→ 建一个空知识库
2. 进入知识库 → 「设置」，按下表配置后保存：

   | 设置项 | 选择 |
   |--------|------|
   | 分段模式 | **Parent-Child（父子索引）** |
   | └ 父块模式 | **全文（整篇文档作为父块）** ← 不要选「段落」 |
   | 索引方式 | 高质量 |
   | Embedding 模型 | **BAAI/bge-large-zh-v1.5**（中文模型，别用 en 英文版） |
   | 检索设置 | 混合检索 + Rerank（Pro/BAAI/bge-reranker-v2-m3） |

3. 记录两样东西备用：
   - **知识库 API 密钥**：「API 访问」页点「创建密钥」，形如 `dataset-xxxxxxxx`
   - **知识库 ID**：地址栏 `/datasets/<这段就是ID>/documents`
4. **先生成唯一命名副本**（避免不同类别下同名 md 被 Dify 按文件名去重覆盖）：

```bash
cd homework
python scripts/make_unique_named_copy.py
# 输出到 data/kb_upload_ready/，92 个文件加了「文件夹名__」前缀
```

5. 上传。二选一：

   **方式A：Web UI 手动上传（推荐，能直观选父块模式）**
   知识库 →「添加文件」→ 进 `data/kb_upload_ready/` → 全选 92 个 →
   分段模式选 **Parent-Child**、父块选 **全文** → 确认。再单独把 `data/pdfs/` 的 PDF 传进去。

   **方式B：脚本上传（父子库专用，全文父块模式）**
   ```bash
   # Windows（PowerShell）
   $env:DIFY_KB_KEY="<你的知识库API密钥 dataset-xxxx>"
   python scripts/rebuild_parent_kb_fulldoc.py   # 脚本内 DS_ID 需改成你的知识库ID
   ```

> 💡 脚本走 Nginx 的 `https://localhost/v1`（自签证书，已默认跳过校验）。上传完知识库应显示全部文档 **completed**（本项目 92 个 md + 5 个 PDF = 97 个）。
>
> ✅ **验证**：知识库「召回测试」输入「除尘常见问题」，top1 应命中 `12_除尘环保与公用工程__04_常见故障与可能原因.md`、且返回内容有 2000+ 字符（含完整正文，不只是标题）。

### 4.5 导入 Workflow（问答应用）

1. 控制台顶部 → 「工作室」→ 右上角「创建应用」→「导入 DSL 文件」
2. 选择 `src/workflow/chatflow-dsl.yml`
3. 导入后打开 Workflow 编辑器，做三处配置：
   - **关联知识库**：点「知识库检索」节点 → 选中你在 4.4 创建的父子索引库
   - **启用 Score 阈值**：同一节点 → 打开「Score 阈值」开关 → 设 **0.4**
     （低于 0.4 视为未命中 → 自动走 Tavily 联网兜底。**开关不打开阈值不生效**，是本项目第二个坑）
   - **填 Tavily Key**：点 `tavily_search`（HTTP Request）节点 → Body 里把 `REPLACE_TAVILY_KEY` 替换为真实 Tavily 密钥
4. 点击右上角「发布」

> ✅ **验证分流**：问「除尘常见问题」应走知识库分支；问「汇川 MD520 变频器 E.OC1 故障排查」（库里没有的具体型号）应走 Tavily 联网分支。

---

## 5. 第三步：访问平台

### 5.1 对话界面

发布应用后，在应用页点「访问 WebApp / 发布 → 运行」即可得到对话链接，形如 `https://localhost/chat/<你的AppID>`。

| 地址 | 说明 |
|------|------|
| `https://localhost/chat/<你的AppID>` | 本机访问 |
| `https://<本机局域网IP>/chat/<你的AppID>` | 局域网其他设备（用 `ipconfig`/`ifconfig` 查本机 IP） |

> 访问前需通过 Basic Auth（见 4.2）。`<你的AppID>` 在发布后的分享链接里，每个应用各不相同。

### 5.2 验证平台工作正常

在对话框里输入以下问题，验证两条路径：

**验证知识库路径**（应 6-10 秒出现第一个字）：
```
FANUC 0i-MF 主轴报警 SP-2003 怎么处理？
```

**验证联网路径**（应 10-20 秒出现第一个字）：
```
2025 年发布的 FANUC iHMI 系统有哪些新功能？
```

两条路径都能正常回答，平台配置完成 ✅

---

## 6. 日常操作

### 启动服务

```bash
cd dify/docker
docker compose up -d
```

### 停止服务

```bash
cd dify/docker
docker compose down
```

### 查看服务状态

```bash
cd dify/docker
docker compose ps
```

### 查看日志（排查问题）

```bash
# 查看 API 服务日志
docker logs docker-api-1 --tail 50

# 查看 Nginx 日志
docker logs docker-nginx-1 --tail 50

# 查看 Worker 日志（知识库索引任务）
docker logs docker-worker-1 --tail 50
```

---

## 7. 知识库管理

### 查看当前知识库状态

在容器内直接查（把 `<知识库API密钥>` 和 `<知识库ID>` 换成你的值）：

```bash
docker exec docker-api-1 python3 -c "
import requests
s = requests.Session(); s.trust_env = False
s.headers['Authorization'] = 'Bearer <知识库API密钥>'
r = s.get('http://127.0.0.1:5001/v1/datasets/<知识库ID>/documents',
          params={'limit': 1}, timeout=30)
data = r.json()
print(f'知识库文档数: {data[\"total\"]}')
"
```

### 添加新设备手册

1. 将 PDF 文件放入 `data/new-manuals/` 目录
2. 运行同步脚本：

```bash
cd homework

# Windows（PowerShell）
$env:DIFY_KB_KEY="<你的知识库API密钥>"
python src/knowledge/sync_knowledge_base.py --watch-dir data/new-manuals

# Mac/Linux
DIFY_KB_KEY="<你的知识库API密钥>" \
  python src/knowledge/sync_knowledge_base.py --watch-dir data/new-manuals
```

脚本会自动：跳过已存在文档 → 上传新文件 → 等待索引完成 → 报告结果。

> 详见 [docs/KNOWLEDGE_BASE_GUIDE.md](docs/KNOWLEDGE_BASE_GUIDE.md) — 包含厂商手册下载地址和预处理方法。

### 重建父子索引库（全文父块模式）

若要重建父子索引库（清空旧 md、保留 PDF、全文父块模式重传）：

```bash
cd homework
python scripts/make_unique_named_copy.py          # 1. 先生成唯一命名副本
$env:DIFY_KB_KEY="<你的知识库API密钥>"              # 2. PowerShell 设 key
python scripts/rebuild_parent_kb_fulldoc.py        # 3. 重建（脚本内 DS_ID 改成你的库ID）
```

> 脚本有库名核对保护，只操作名为「制造业设备维修-父子索引」的库，避免误删。

### 修复索引错误文档

```bash
DIFY_KB_KEY="<你的知识库API密钥>" \
  python src/knowledge/repair_dataset.py \
  --base-url https://localhost/v1 \
  --dataset-id <你的知识库ID> \
  --knowledge-root 制造业设备维修知识库 \
  --data-root data
```

---

## 8. 数据备份

> ⚠️ 重要：容器数据存储在 Docker 卷中，`docker compose down -v` 会**永久删除**所有数据。务必定期备份。

### 手动备份

```bash
cd homework
bash src/scripts/backup.sh
```

备份文件保存在 `backups/YYYYMMDD_HHMMSS/`，自动保留最近 7 份。

### 设置自动备份（每天凌晨 2 点）

```bash
# 编辑 crontab
crontab -e

# 添加这一行（修改路径为实际路径）
0 2 * * * cd /path/to/homework && bash src/scripts/backup.sh >> backup.log 2>&1
```

### 从备份恢复

```bash
# 恢复 PostgreSQL
docker exec -i docker-db_postgres-1 pg_restore \
  -U postgres -d dify < backups/YYYYMMDD_HHMMSS/postgres_dify.dump

# 恢复 Weaviate（需先停止服务）
cd dify/docker && docker compose down
tar -xzf backups/YYYYMMDD_HHMMSS/weaviate_data.tar.gz -C volumes/weaviate/
docker compose up -d
```

---

## 9. 评测与验证

运行 20 题自动评测，检验平台回答质量：

```bash
cd homework

# Windows（PowerShell）
$env:DIFY_APP_KEY="<你的Service API密钥 app-xxxx>"
python src/knowledge/eval_chatflow.py `
  --base-url https://localhost/v1 `
  --questions data/eval_questions.csv `
  --output data/eval_results.json

# Mac/Linux
DIFY_APP_KEY="<你的Service API密钥 app-xxxx>" \
  python src/knowledge/eval_chatflow.py \
  --base-url https://localhost/v1 \
  --questions data/eval_questions.csv \
  --output data/eval_results.json
```

**基准结果（2026-07-22）：**

> 说明：下表为 2026-07-22 的历史评测数据，当时为对比提速临时切到 DeepSeek-V3 跑测；平台当前默认模型为 `deepseek-ai/DeepSeek-V4-Pro`，切换模型后建议重新跑一次评测更新本表。

| 指标 | 结果 |
|------|------|
| 总成功率 | 20/20（100%）|
| 关键词覆盖率 | 100% |
| 引用来源标注率 | 100% |
| 流式首字响应 | 6.8s |
| 平均总响应时间 | ~40s |

---

## 10. 项目文件说明

```
homework/
├── README.md                             # 本文件
├── .gitignore                            # 不入库的文件列表
│
├── dify/docker/                          # Dify 部署目录（核心）
│   ├── docker-compose.yaml               # 官方 Compose（不要修改）
│   ├── docker-compose.override.yaml      # 自定义配置（资源限制、日志轮转）
│   ├── .env                              # ⚠️ 环境变量和 API Key（不入库）
│   └── nginx/
│       ├── conf.d/rate_limit.conf        # Nginx：Rate Limiting + Basic Auth + HTTPS
│       ├── conf.d/.htpasswd              # Basic Auth 密码哈希（不入库）
│       ├── conf.d/.htpasswd_plaintext    # ⚠️ Basic Auth 明文密码（不入库，务必备份！）
│       └── ssl/dify.crt + dify.key       # 自签名 TLS 证书（不入库）
│
├── src/
│   ├── workflow/
│   │   ├── chatflow-dsl.yml              # Workflow 完整配置（可导入 Dify 重建）
│   │   └── system-prompt.txt            # LLM 系统提示词
│   ├── knowledge/
│   │   ├── sync_knowledge_base.py       # 新手册自动上传脚本 ← 常用
│   │   ├── repair_dataset.py            # 修复索引错误脚本
│   │   ├── eval_chatflow.py             # 20 题评测脚本
│   │   ├── upload_to_dify.py            # 单文件上传脚本
│   │   └── upload_to_both_kb.py         # 双库并发上传（通用库+父子库）
│   └── scripts/
│       └── backup.sh                    # 数据备份脚本 ← 定期运行
│
├── scripts/
│   ├── add_keywords_to_kb.py            # 批量给文档元数据加关键词
│   ├── make_unique_named_copy.py        # 生成唯一命名副本（防 Dify 同名去重）← 上传前必跑
│   └── rebuild_parent_kb_fulldoc.py     # 全文父块模式重建父子库
│
├── data/
│   ├── eval_questions.csv               # 评测题目（20 题）
│   ├── eval_results.json                # 最新评测结果
│   ├── CNC故障案例集.md                  # 知识库源文件
│   ├── new-manuals/                     # 放新 PDF 手册的目录（上传前暂存）
│   └── pdfs/                            # 已有设备手册 PDF（不入库）
│
├── 制造业设备维修知识库/                  # 13 类设备，92 个 MD 文件（+ data/pdfs 5 个 PDF = 入库 97 个）
│   ├── 00_通用安全与维修方法/
│   ├── 01_机床与数控设备/
│   ├── ... （02-11 各设备大类）
│   └── 12_除尘环保与公用工程/
│
├── deploy/
│   ├── startup.sh / startup.ps1         # 一键启动脚本（自动下载Dify+配置+启动）
│   ├── setup-hardening.sh               # 一键加 HTTPS+限流+Basic Auth
│   ├── sanitize-for-release.sh          # 分发前清理密钥脚本
│   ├── .env.template                    # 环境变量模板
│   ├── docker-compose.override.yaml     # 资源限制+日志轮转
│   └── nginx/rate_limit.conf.template   # Nginx 配置模板
│
└── docs/                               # 详细文档（PRD/架构/调优/应急/验收等 14 篇）
    ├── KNOWLEDGE_BASE_GUIDE.md          # 真实手册获取与上传完整指南
    └── 分发前清理清单.md                 # 交给别人前的脱敏清单
```

---

## 11. 常见问题

**Q：`bash deploy/startup.sh` 跑完好像停了，让我填 .env？**  
A：这是正常的。脚本第一次运行只帮你把 `.env` 建好，然后停下来等你填 `TAVILY_API_KEY`。填好后**再运行一次同样的命令**，它就会真正启动服务。

**Q：为什么我访问没有弹登录框 / 没有 HTTPS？**  
A：因为 HTTPS + Basic Auth 是**可选**的加固层。想要的话运行 `bash deploy/setup-hardening.sh`（见 3.3）。不运行就是普通 `http://localhost` 直接访问，也能正常用。

**Q：浏览器提示「证书不安全」**  
A：正常现象，做了 3.3 加固后用的是自签名证书。点击「高级」→「继续访问 localhost」。

**Q：弹出 Basic Auth 登录框，用户名密码是什么？**  
A：用户名 `admin`，密码在 `dify/docker/nginx/conf.d/.htpasswd_plaintext` 文件里（运行 3.3 加固脚本时自动生成的随机密码）。

**Q：登录 Dify 控制台的账号密码是什么？**  
A：首次启动后访问 `https://localhost` 会进入初始化页面，由你自行注册管理员邮箱和密码。之后用这组自己设置的账号登录即可（不同的人部署就是各自注册的账号）。

**Q：启动后 `docker compose ps` 有容器一直 `starting`**  
A：首次启动需要时间初始化数据库，等待 1-2 分钟后再检查。如果超过 5 分钟还没好，运行 `docker logs docker-api-1 --tail 30` 查看错误。

**Q：对话没有响应 / 报错**  
A：按顺序排查：
1. 检查 SiliconFlow API Key 是否在控制台「模型供应商」中配置（步骤 4.3）
2. 检查 `docker compose ps` 所有服务是否 `Up`
3. 查看 `docker logs docker-api-1 --tail 50` 找具体错误

**Q：知识库文档数量变少了**  
A：运行修复脚本（见第 7 节「修复索引错误文档」）。

**Q：`.htpasswd_plaintext` 文件不见了**  
A：容器重建后该文件会丢失。需要重新生成：
```bash
cd dify/docker
# 设置新密码（替换 新密码）
PASS="新密码"
HASH=$(openssl passwd -apr1 "$PASS")
echo "admin:$HASH" > nginx/conf.d/.htpasswd
echo "admin:$PASS" > nginx/conf.d/.htpasswd_plaintext
docker compose restart nginx
```

---

## 12. 关键配置速查

> 📌 下表中带「你的」字样的值都是**每个部署实例各不相同**的，需在自己的 Dify 控制台里获取，不能照抄。

| 配置项 | 值 / 获取方式 |
|--------|-----|
| 知识库 ID | 知识库页面 URL `/datasets/<这一段>/documents` |
| 知识库 API Key | 知识库 →「API 访问」→ 创建密钥，形如 `dataset-xxxx` |
| Service API Key | 应用 →「访问 API」→ 创建密钥，形如 `app-xxxx` |
| LLM 模型 | `deepseek-ai/DeepSeek-V4-Pro`（via SiliconFlow）|
| Embedding 模型 | `BAAI/bge-large-zh-v1.5`（via SiliconFlow）|
| Rerank 模型 | `Pro/BAAI/bge-reranker-v2-m3`（via SiliconFlow，可选）|
| WebApp 对话地址 | 应用发布后的分享链接 `https://localhost/chat/<AppID>` |
| Dify 控制台 | `https://localhost` |
| Dify 控制台账号 | 首次初始化时自行注册 |
| Basic Auth 用户名 | `admin` |
| Basic Auth 密码位置 | `dify/docker/nginx/conf.d/.htpasswd_plaintext` |

---

## 13. 安全说明

以下文件**不会**被 Git 提交（已在 `.gitignore`），但本地必须妥善保管：

| 文件 | 内容 | 丢失后果 |
|------|------|---------|
| `dify/docker/.env` | SiliconFlow / Tavily API Key | 服务无法调用模型 |
| `dify/docker/nginx/conf.d/.htpasswd_plaintext` | Basic Auth 明文密码 | 无法登录 WebApp |
| `dify/docker/nginx/ssl/dify.key` | TLS 私钥 | HTTPS 失效 |

**其他注意事项：**
- 知识库 API Key 不要硬编码进脚本，始终通过 `DIFY_KB_KEY` 环境变量传入
- 定期运行 `bash src/scripts/backup.sh` 备份数据库
- `data/pdfs/` 下的设备手册 PDF 不入库（体积大，可能含版权内容）

---

## License

MIT
