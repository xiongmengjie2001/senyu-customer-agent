# Dify 配置与端到端验收

## 状态

截至 2026-10-28，**本机 Docker 引擎已恢复正常，现有 Dify 1.17.1 容器已运行**，API 与相关基础依赖健康，登录页 <http://localhost/signin> 可访问。仓库保留 1.18.0 的官方 Docker 配置作为部署参考；现有 1.17.1 实例的 Chatflow 导入兼容性、工具网络和本项目模型端到端调用仍待验证。官方部署参考：[Dify 官方仓库](https://github.com/langgenius/dify/tree/1.18.0/docker)。

## 复用现有 Dify

本机已有实例，当前 HTTP 端口为 80、HTTPS 端口为 443。优先打开 <http://localhost/signin>，在现有实例导入并发布项目 Chatflow，再将应用 API Key 配入本项目。此实例对应 `DIFY_API_URL=http://localhost/v1`。不要为了接入项目而重新运行另一版本的 Compose 覆盖现有实例。

## 在全新环境启动 Dify

```powershell
.\scripts\start-dify.ps1
```

下面的脚本用于全新环境，并非本机现有实例的启动步骤。脚本检查引擎，缺少官方文件才下载固定版本；保留已有配置；HTTP 端口 8080，HTTPS 8443。打开 <http://localhost:8080/install> 初始化本地管理员，不提供预置管理员密码。

## 本地原生后端接入

容器调用本机后端需后端监听 Docker 能访问的地址。在项目 `.env` 设置 `APP_HOST=0.0.0.0` 后重启 `python run.py`；只在可信本机开发网络使用。默认 `127.0.0.1` 模式适用于不接 Dify 的本地演示。

导入 `dify/senyu-chatflow.yml`，在工作流环境变量中配置：

- `BACKEND_URL=http://host.docker.internal:8000`
- `TOOLS_TOKEN` 与项目 `.env` 中的值完全一致，设为 secret。

不需要 Dify 内置 Knowledge。项目选择的是 FAISS，由后端维护发布、版本、状态和负责人；Dify 的 HTTP 知识工具调用同一库，避免两份知识源不同步。

官方 SSRF 代理需要限定内网白名单。启动脚本仅为 `host.docker.internal,senyu` 添加域名白名单；若已有此配置则保留原值，按需合并。不要开启全部私有 IP 的访问。

工作流链路：开始（业务 session_id 与 sys.query）→ Code 安全 JSON 序列化 → HTTP 意图路由 → HTTP FAISS 检索 → Code 组装 → HTTP 受控状态机 → Code 核验 → Answer 返回完整结构化会话。Code 节点负责正确处理引号、换行，禁止 HTTP 错误被解释为业务成功。HTTP 写操作不会创建工单；工单必须经过前端确认与后端一次性凭据核验。

`/api/tools/route` 可按 `ENABLE_LLM` 调用 OpenAI 兼容接口，规则识别优先。模型只返回 JSON 意图枚举，后端检验枚举并拒绝未知输出。Dify 的原生 LLM 节点未使用，模型配置统一注入业务后端环境变量；因此 DSL 不含提供商插件与密钥。

在 Dify 调试 HTTP 节点，确认意图接口返回 `intent`、知识接口返回 `sources`。若 Dify SSRF 代理无法访问主机地址，应通过专用 Docker 网络连接服务，不能关闭全局 SSRF 安全保护。使用容器方式部署后端时，可参考同目录的 `backend-network.override.yaml` 和 compose 网络连接说明；该分支也需实机验收。

发布 Chatflow，复制应用 API Key 到项目 `.env`：

```dotenv
APP_MODE=dify
DIFY_API_URL=http://localhost/v1
# 全新环境使用脚本部署到 8080 时，才改为 http://localhost:8080/v1
DIFY_API_KEY=本地应用密钥
```

重启后打开 UI，顶部应显示「Dify 编排模式」。若未配置或调用失败，明确转人工并在 `/api/admin/audit` 记录 `dify_failure`，不静默回落成假成功。

## 联调验收

```powershell
python eval/verify_dify.py
```

需先启动业务服务并配置 Dify。脚本从 UI 使用的 API 发起：多订单查询、订单选择、确认催单、人工交接，核验 Dify 实际动作记录，并生成 `reports/dify-live.json`。失败会返回非零，不能以本地规则 Eval 替代此项。

对话历史、订单与身份以服务端业务会话为准，Dify conversation_id 只用于编排连续性。消费者不能自行传 user_id；模型输出不能提升操作权限。默认密钥和演示角色凭据仅供本地课程使用。
