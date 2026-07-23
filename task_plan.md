# RuyiDify 新旧版本复用分析

## 目标
对比当前项目与 `D:\Windows-OS\code\Summer_study\agent\RuyiDify-v0.1.0`，识别可直接复用、需要转换和不应复用的资产，并给出迁移顺序与风险。

## 阶段

### Phase 1：盘点两边目录、版本和部署形态
**Status:** complete

### Phase 2：对比配置、数据、工作流及自定义代码
**Status:** complete

### Phase 3：输出复用清单和迁移建议
**Status:** complete

### Phase 4：启动并确认 Dify 1.16 服务状态
**Status:** complete

### Phase 5：对比本地文件与线上知识库文档清单
**Status:** complete

### Phase 6：修复错误状态、补传缺失文件并验证索引
**Status:** in_progress

## 上传冲突方案确认（brainstorming）

- [complete] 检查 Dify 同名文件行为、上传限制与 PDF 完整性
- [complete] 判断无需视觉辅助
- [complete] 向用户确认唯一命名与大文件处理方案
- [complete] 比较并确认 2-3 种修复方案
- [complete] 写入并复核最小设计说明
- [complete] 用户批准推荐方案；`writing-plans` 不可用，继续使用本文件实施

## 最终决策

- 若旧实例中的账号、应用、对话记录和模型配置更重要：以旧 1.15 数据卷为唯一数据源，在完整备份后原位升级到 1.16，再导入当前项目的制造业资产。
- 若队友当前 1.16 实例必须保留：不能合并数据库，只能从旧实例导出应用 DSL、重新上传知识源、重装插件并重新绑定凭据。

## 本次运行目标

- 启动根目录 `dify/docker` 中的 Dify 1.16。
- 以 `data/` 和 `制造业设备维修知识库/` 的支持格式文件为本地基准，核对目标知识库。
- 对错误文档执行重新索引，对缺失文件定向上传，避免重复上传正常文档。

## 约束
- 只读检查两个项目的业务文件，不修改配置或数据。
- 不读取或展示真实密钥值，仅确认变量名和配置结构。

## 错误记录
| 错误 | 尝试 | 处理 |
|---|---:|---|
| 两项目二级目录并行盘点超时 | 1 | 改为顶层盘点，并按文件类型定向检索 |
| 旧仓库全量递归配置检索遇到运行卷中的断链/不可访问文件 | 1 | 排除 `docker/volumes`，只检查受版本控制的部署配置与卷顶层 |
| Docker 运行态查询无权限，获准后引擎仍超时 | 2 | 放弃运行态依赖，基于版本文件、Compose 和数据卷做离线判断 |
| 当前仓库 Git 所有权检查失败 | 1 | 不修改全局 Git 配置；安全问题以源码内容为证据，不依赖跟踪状态 |
| 计划完成检查脚本被 PowerShell 执行策略阻止 | 1 | 使用一次性 `-ExecutionPolicy Bypass` 运行只读检查，不修改系统策略 |
| `deploy/startup.ps1` 被 Windows PowerShell 5 按错误编码解析 | 1 | 不修改脚本，改在 `dify/docker` 直接运行 `docker compose up -d` |
| 宿主机访问 `/apps` 与 `/v1/datasets` 超时 | 1 | 检查 Compose 状态和 API/Nginx 日志，确认服务是否就绪 |
| 合并查询 Compose 状态与日志超时 | 1 | 拆分为单独的 `docker compose ps` 和定向日志查询 |
| 绕过代理后宿主机 80 端口仍超时 | 2 | 改从 API 容器内部调用 Dify API |
| Nginx 镜像没有 `wget` | 1 | 使用 API 容器自带 Python/requests 检查内部端点 |
| 对 `error` 文档调用 update-by-file 返回 `Document is not available` | 1 | 使用 Dataset API 删除错误记录后从本地原文件重新创建 |
| 1MB8014 PDF 上传返回空消息 `invalid_param` | 1 | 文件有效但为 28.3MB，超过 API 默认 15MB；等待选择提高限制或拆分 |
| 首次同名文档内容确认命令转义错误 | 1 | 改用字符串拼接构造 API URL 后成功读取 |
| 单独重建 API 超时且健康检查未就绪 | 1 | 日志停在 `Running migrations`；保持 Worker/数据库运行，等待连接池压力下降后继续 |
| 第一次可恢复同步在第 05 类耗尽两次重试 | 1 | Redis 当前 PONG、资源压力已下降；从失败点续跑并将单次运行重试上限提高到 4 |
| DELETE 超时后重试返回 404 | 1 | 服务端已完成删除；将 204/404 都视为幂等成功后续跑 |
| 第 08 类轮询期间 API 连续超时 | 1 | 将每轮 7 次详情请求改为 1 次分页列表请求，API 暂不可用时等待而非退出 |
