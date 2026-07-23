# 复用分析发现

> 本文件只记录目录、配置结构和迁移证据，不记录真实密钥。

## 待分析

- 当前项目：`D:\Windows-OS\code\Summer_study\agent\homework`
- 教学旧版：`D:\Windows-OS\code\Summer_study\agent\RuyiDify-v0.1.0`

## 初步结构

- 教学旧版是完整 Dify 源码仓库，顶层包含 `api/`、`web/`、`docker/`、`dify-agent/`、`packages/` 等。
- 当前项目更像业务交付与部署资料集合，顶层包含 `deploy/`、`data/`、`dify/`、`src/`、知识库资料和大型归档 `DifiProject.rar`。
- 两边目录形态不同，不适合源码级直接覆盖；优先评估环境变量、Compose、工作流 DSL、知识库源文件、自定义扩展代码。
- 旧项目存在 `key.txt`，分析时不读取其内容，避免暴露密钥。

## README 证据

- 当前项目声明对齐 Dify `1.16.0`，业务是制造业设备维修问答，核心资产包括 `src/workflow/chatflow-dsl.yml`、系统提示词、知识库处理/验证脚本、测试脚本、部署覆盖配置与知识库 PDF。
- 旧 RuyiDify README 表明它以完整上游 Dify 为底座，Ruyi 自有增量主要是 `examples/` 教学脚本、`src/docx/` 文档工具和项目文档；这些与 Dify 运行时版本耦合较低。
- 当前 README 在终端中出现乱码，属于读取编码/终端显示问题；后续明确使用 UTF-8 读取，不据此判断文件损坏。

## 资产盘点

- 当前项目有 12 个设备领域的结构化 Markdown 知识库、清单 CSV、评测问题、导入报告。这些内容资产与 Dify 版本基本解耦，是最高价值、最容易复用的一组。
- 当前项目已有 `src/knowledge/upload_to_dify.py`、检索验证和场景测试脚本，说明知识库可通过 API 重建，不必迁移旧数据库卷。
- 当前项目的 Chatflow DSL、系统提示词和节点参数文档是应用逻辑的主要载体；DSL 需在 1.16.0 做导入兼容验证，提示词可直接复用。
- 旧项目的 `examples/知识库/` 有 32 个 Dataset API 教学脚本，可作为新上传/维护脚本的参考；但接口字段和认证方式要与 1.16.0 核对。
- 旧项目 `src/docx/` 是独立 Python 包，和 Dify 核心版本低耦合；只有需要生成/加工 DOCX 时才值得迁入当前项目。

## 配置与工作流细节

- 当前 DSL 自身标记 `version: 0.3.0`，包含知识库 ID、Tavily Key、系统提示词三个占位符，导入后仍需绑定新实例资源；知识库 ID 和凭据无法跨实例直接复用。
- DSL 图中 `Start -> HTTP Request` 是并行直连，因此 Tavily 实际会在每次请求执行，并非注释所称“仅知识库未命中时执行”。这是工作流逻辑问题，不是新旧版本兼容问题。
- 当前导入报告显示 92 个知识资产均已完成索引；`dataset_id` 属于实例内部 ID，只能用于当前实例，重建实例后会变化。
- 旧教程的 Dataset API 仍使用 `/v1/datasets/{id}/document/create-by-file` 与 `/retrieve`，和当前上传/验证思路一致，可复用请求流程，但必须参数化 URL、API Key、Dataset ID 和模型标识。
- 当前 Compose override 假定服务名为 `api`、`worker`、`web`、`weaviate`、`db_postgres`、`redis`；能否复用取决于 1.16.0 官方 Compose 的实际服务名，不能直接套到其他 Dify 版本。

## 版本与持久化数据

- 当前项目内嵌的官方 Dify 仓库明确为 `1.16.0-5-g5ea884f799`。
- 旧 RuyiDify 仓库只有自建基线提交 `93e07bfd`，没有可识别的 Dify tag，不能仅凭目录名 `v0.1.0` 判断其底层 Dify 版本；需继续从镜像/源码标识确认。
- 已从旧版 `api/pyproject.toml` 与 Compose 镜像标签确认其底层是 Dify `1.15.0`；当前是 `1.16.0`，实际只跨一个小版本，并非无法迁移的巨大版本跨度。
- 旧项目 `docker/volumes/` 下已有 `db`、`redis`、`weaviate`、`app`、`plugin_daemon` 等运行数据，说明很多旧配置只存在数据库/卷中，并未成为可移植文件。
- 不应把这些卷目录直接复制到 1.16.0：数据库 schema、插件运行环境、向量索引格式均可能跨版本不兼容。可迁移路径应优先使用 DSL/API/源文档导出；若必须保留全部控制台配置，则应走数据库备份加逐版本升级验证。
- 对 1.15.0 -> 1.16.0，可以在完整备份后让官方 1.16.0 对旧数据库执行迁移，从而整体保留应用、账号、模型配置元数据等；但这属于“升级旧实例”，不能把两个已独立运行的数据库自动合并。
- 新旧两边都存在各自独立、且有不同写入时间的 `db/app/plugin_daemon/weaviate` 数据卷；这证实当前并不是“新实例为空”，而是两个已有状态的实例。选择旧库整体升级会覆盖/放弃当前实例状态，不能无损合并。
- 旧仓库没有发现用户应用的 DSL 导出文件，命中的 YAML 都是 CLI/API 测试夹具；因此旧应用/工作流若要并入当前实例，需要先启动旧实例并从控制台导出 DSL，或通过数据库/API 提取。

## 环境与插件差异

- 旧 `.env` 有 226 个变量，新 `.env` 有 249 个。1.16.0 新增一批 agent backend、Redis keepalive 和 workflow timeout 配置；不能用旧 `.env` 整文件覆盖新版，应以 1.16.0 模板为基准逐项迁移业务值。
- 旧版独有的已安装模型插件包括 Anthropic、OpenAI、通义；新版当前已有 DeepSeek、HuggingFace Hub/TEI、Ollama、SiliconFlow。插件目录不能直接复制，应在新实例按需重新安装旧版独有插件。
- 新旧 `app/storage/.dify_secret_key` 不同，而 `.env` 的 `SECRET_KEY` 均为空。旧数据库中的加密凭据依赖旧 storage 密钥；若整体升级旧实例，必须把旧数据库与旧 `app/storage` 成套保留。
- 新旧 `DB_PASSWORD` 不同。直接把旧数据库卷放进当前 1.16 目录并沿用当前 `.env` 很可能无法连接；整体升级必须同步处理旧数据库凭据。

## 安全与脚本风险

- 当前 `src/knowledge/upload_to_dify.py` 含硬编码的 Dataset API Key。应立即轮换该 Key，并改为从环境变量读取；迁移方案不能复制明文密钥。
- 当前上传脚本自动选择 API 返回的第一个知识库，目标实例有多个知识库时存在误传风险；迁移时应显式指定 Dataset ID 或按名称精确匹配。
- 旧 DOCX 工具是 `ruyi-docx 0.1.0`、要求 Python 3.12，仅依赖 `python-docx` 核心包；可作为独立模块迁移，不应混入 Dify 官方源码目录。

## 最终复用矩阵

| 资产 | 复用级别 | 建议方式 |
|---|---|---|
| 制造业 Markdown/CSV/PDF、评测题 | 直接复用 | 用 1.16 Dataset API 重新建库和上传 |
| System Prompt、节点参数、验收用例 | 直接复用 | 作为文本/测试资产迁入 |
| 旧知识库 API 教学脚本 | 修改后复用 | 参数化 URL、Key、Dataset ID、模型名 |
| `ruyi-docx` 独立包 | 按需直接复用 | 独立安装，不改 Dify 官方源码 |
| 旧应用/Chatflow | 导出后复用 | 从 1.15 控制台导出 DSL，再导入 1.16 并重绑资源 |
| 知识库索引和 Dataset ID | 不直接复用 | 从源文件重建，ID 会变化 |
| 模型供应商与插件 | 清单可复用 | 新版重装插件并重新录入凭据 |
| `.env` | 仅逐项复用 | 以 1.16 模板为底，不整文件覆盖 |
| PostgreSQL/Weaviate/Redis/plugin 卷 | 不用于合并 | 仅在“整体升级旧实例”路线中成套备份和迁移 |
| 账号、工作区、历史记录、旧 API Key | 无法资源级合并 | 只有整体升级旧数据库才能完整保留 |

## 推荐顺序（保留当前 1.16 实例）

1. 立即轮换当前源码中暴露的 Dataset API Key，并把脚本改为环境变量读取。
2. 启动旧 1.15 实例，逐个导出自己的应用/Chatflow DSL，同时记录插件、模型和知识库清单。
3. 在当前 1.16 中重装 Anthropic、OpenAI、通义等确实需要的旧插件，并重新录入凭据。
4. 导入旧 DSL，逐个重绑模型、Dataset、环境变量和工具凭据。
5. 使用源文档/API 重建旧知识库，不复制 Weaviate 索引；用评测问题回归验证。
6. 修正当前 DSL 的 Tavily 无条件执行问题，再运行三类验收场景。

## 备选顺序（以旧实例为主）

1. 停止旧实例并完整备份旧 `docker/.env` 与全部 `docker/volumes`，同时备份当前 1.16 实例。
2. 用一份隔离副本执行 1.15 -> 1.16 升级，必须保留旧 `app/storage/.dify_secret_key` 与数据库凭据。
3. 升级成功后检查数据库迁移、登录、应用运行、模型凭据解密、知识库检索和插件状态。
4. 再把当前根目录的制造业 DSL、知识库源文件和测试资产导入升级后的实例。

## 2026-07-21 知识库修复任务

- 待启动当前 Dify 1.16 并读取知识库实时状态。
- 本地核对范围：`data/`、`制造业设备维修知识库/`；支持格式以 Dify 上传脚本定义为准。
- `docker compose up -d` 成功返回，API、Worker、Web、Nginx、PostgreSQL、Weaviate 等容器均进入 Running/Healthy 启动流程。
- 启动后宿主机 HTTP 与 Dataset API 暂时超时，需要继续确认 Nginx/API 实际状态。
- `docker compose ps` 显示全部核心容器已运行约 13 小时，API/PostgreSQL 等健康检查通过；此次 `up -d` 实际是确认并保持已有服务。
- API 容器内访问 `/health` 返回 HTTP 200、版本 1.16.0。故障范围收敛为宿主机到容器的 80 端口链路；后续知识库操作改走容器内部 API。
- 目标知识库为 `制造业设备维修`，ID `62874d02-ed9d-4d31-b087-6b4ea50d0bc2`，修复前有 23 个线上文档。
- 本地两个目录共有 102 个支持格式文件：96 个制造业知识库 Markdown/CSV，加上 `data/` 下 1 个 Markdown 和 5 个 PDF。
- 线上 2 个 PDF 处于 `error`：Altivar58 与 SINUMERIK 手册；错误均为 SiliconFlow Embedding 请求发生 SSL `UNEXPECTED_EOF_WHILE_READING`。
- 线上 7 个通用文件名 Markdown 已通过首段条目编号确认属于 `KB-12-*`（除尘环保与公用工程），不是其他设备分类。
- 精确缺失 79 个：`01` 至 `11` 设备分类的 77 个 Markdown、`data/CNC故障案例集.md`、`data/pdfs/1MB8014系列三相异步电动机安装与维护手册.pdf`。
- Dify 1.16 的 update-by-file 不接受当前 `error` 状态文档；服务 API 源码确认错误终态文档可删除并从原文件重新创建，以重新触发解析和索引。
- 两个错误 PDF 已成功删除旧错误记录并从本地原文件重新创建，API 均返回 HTTP 200；首次复查状态为 `parsing`，错误字段已清空。
- Worker 日志显示 SiliconFlow Embedding 调用已恢复成功（插件调用 HTTP 200，Embedding batch 正常完成），原 SSL EOF 故障当前未复现。
- 两份大 PDF 已进入 `splitting/indexing`，各产生约 1000 个 Embedding 批次，完整索引预计耗时较长；不属于卡死。
- 缺失的 `CNC故障案例集.md` 已成功创建为索引探针，当前排队等待 Worker。
- 77 个分类 Markdown 的创建请求均返回 HTTP 200，但 Dify 按文件名去重/替换；12 个分类重复使用 `01_...md` 至 `07_...md`，知识库总数没有增加 77。
- 当前 7 个通用文件名文档已被最后上传的 `KB-11-*`（注塑、冲压与成型设备）替换，原线上 `KB-12-*` 被覆盖；本地源文件仍完整，可用唯一文档名恢复 12 个分类共 84 个文档。
- 最新状态快照：知识库可见 24 个文档，19 completed、3 indexing、2 error。Altivar58 已完成；SINUMERIK 因数据库连接池超时失败；CNC 因 SiliconFlow SSL EOF 失败。
- 1MB8014 PDF 经 `pypdf` 验证为 54 页、未加密、28,299,224 字节。Nginx 限制为 100MB，但 Dify API 默认上传限制为 15MB，因此被拒绝。
- 已将实际 `.env` 与部署模板的 `UPLOAD_FILE_SIZE_LIMIT` 设置为 50MB。单独重建 API 后，容器启动日志暂时停在 `Running migrations`，推测与并发索引造成的数据库连接池压力有关；Worker 和数据库未重启。
- API 进程当前运行 `flask upgrade-db`，CPU 约 97%，数据库约 74%，并非退出或空等；PostgreSQL 有 33 个空闲连接，未达到实例连接上限。先等待迁移检查完成，不强杀进程或重启数据库。
- API 迁移检查已自然完成，健康端点返回 200，容器运行时确认 `UPLOAD_FILE_SIZE_LIMIT=50`。
- 已删除 7 个被覆盖文档和 CNC/SINUMERIK 两个错误文档，9 次删除均返回 204；第 01 类 7 个唯一命名文档均创建成功。
- 新增 `src/knowledge/repair_dataset.py`：可恢复地逐分类同步、等待终态、有限重试，并要求最终严格达到 102 个 completed 文档；脚本不含 API Key。
- 第一次连续同步完成第 01-04 类及第 05 类 6/7 个文档；`05_...周期维护.md` 先后因 I/O 和 Redis 读取超时失败，达到两次重试阈值后安全停止。
- 停止后 Redis 返回 PONG，API/Worker/数据库资源占用已回落，属于瞬时基础设施波动而非持续故障；可从现状幂等续跑。
- 后续续跑已完成第 05、06、07 类，第 08 类已提交；原轮询每批每轮调用 7 次详情 API，索引高峰下导致单 Worker API 超时，现改为每轮一次列表查询并容忍暂时不可用。
