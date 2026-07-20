# RuyiDify

RuyiDify 是基于开源 Dify 的学习、实践和二次开发项目。仓库保留 Dify 的 Web、API、Worker、Docker Compose、插件与 Agent 能力，并在此基础上增加知识库教学示例和可复用的 DOCX 文档处理工具。

上游 Dify 的产品介绍、安装说明和社区链接继续以 [`README.md`](README.md) 为准。本文件只说明 RuyiDify 自己维护的内容。

## 扩展内容

- `examples/知识库`：知识库、文档、分段、元数据和检索参数的 API 练习。
- `examples/北科大2026`：从连接验证、资料上传到知识库问答的渐进式课程脚本。
- `src/docx`：基于 `python-docx` 的强类型 Word 文档创建、读取、修改和校验工具。
- `docs/博客`：RuyiDify 的公开项目实践文章。

## 项目文档库

RuyiDify 的非上游架构分析、启动方式、知识库链路、验证记录和学习资料维护在独立“项目文档库”中：

```text
../RuyiDifity-memery
```

处理项目任务时，应先阅读项目文档库中的 `AGENTS.md`、`manifest.yaml` 和 `00-navigation/index.md`。只有资料缺失、过期或与运行结果冲突时，才重新深读源码。

## 本地启动

项目当前首选 Docker Compose。准确步骤、组件端口和故障排查以项目文档库的下列文件为准：

- `02-architecture/startup-overview.md`
- `02-architecture/startup-methods.md`
- `02-architecture/component-ports.md`
- `05-configuration/startup-configuration.md`

上游快速启动入口仍见 [`README.md`](README.md)。不要提交 `docker/.env`、`key.txt`、模型供应商凭据或运行数据卷。

## DOCX 真实案例

《零基础 Dify 入门》由下面的脚本从结构化内容同时生成 Markdown 和 DOCX：

```powershell
python "examples\北科大2026\12_生成零基础Dify入门.py"
```

生成器会把产物写入项目文档库，并更新其导航和复核时间。DOCX 能力和开发命令见 [`src/docx/README.md`](src/docx/README.md)。

## 安全边界

- 不提交 `.env`、Key、Token、密码、Cookie 和真实连接串。
- 本地电子书、上传文件、数据库卷和可再生成的课程输出不进入 Git。
- 项目文档库与源码仓库独立提交，避免把审计资料混入上游源码变更。
