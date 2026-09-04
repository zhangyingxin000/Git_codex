# Engineering Architecture

本文说明当前工程化拆分的边界，以及新增功能应该放在哪里。目标不是一次性重写旧平台，而是在保持现有功能可运行的前提下，把高频变化部分逐步迁出 `app.py` 和 `static/app.js`。

## 后端边界

FastAPI 应用入口位于 `quality_hub_backend/api/fastapi_app.py`，并由 `create_app()` 创建。新代码按以下边界放置：

| 目录 | 职责 | 不应承担的职责 |
| --- | --- | --- |
| `api/routes/` | HTTP 路由、请求参数、状态码和响应入口 | 业务编排、文件处理、外部工具执行 |
| `handlers/` | 把一个请求转换为可执行任务，组织服务调用 | 直接维护 HTTP 路由或持久化细节 |
| `services/` | 可复用业务能力、任务队列、覆盖分析 | 页面响应和前端展示 |
| `config/` | 环境变量、YAML 配置和运行路径 | 执行业务流程 |
| `startup/` | 应用启动、关闭和资源生命周期 | 需求包业务规则 |
| `schemas/` | API 输入输出模型 | 数据访问和工具执行 |

`app.py` 仍是兼容层，已有功能暂时通过 `legacy` 调用继续工作。新增公共能力应优先进入上述模块；后续迁移旧路由时，以一个完整业务域为单位移动，并保留原接口路径和响应结构。

## 后台任务

`quality_hub_backend/services/task_queue.py` 提供本地最小任务队列：

1. API 通过 `POST /api/tasks` 提交任务。
2. 任务先写入 `data/task_queue.db`，状态为 `PENDING`。
3. `ThreadPoolExecutor` 执行任务，状态变为 `RUNNING`。
4. 成功后保存有限大小的结果并标记 `PASSED`；失败保存错误摘要并标记 `FAILED`。
5. 平台异常退出后，遗留的 `RUNNING` 任务在下次启动时标记为 `INTERRUPTED`，不会伪装成成功。

当前支持 `demo_salary_trade`、`requirement_pipeline`、`requirement_pytest` 和 `requirement_newman`。需求包流水线默认禁止外部写操作，Newman 默认只执行只读请求。新增任务类型应在 `handlers/task_handlers.py` 注册，不在路由中直接写长时间执行逻辑。

这套实现适合单机演示和日常本地运行。未来需要多机器 Worker、任务重试、取消、优先级和监控时，可以保持 API 与任务状态模型不变，把执行层替换为 Celery 或 RQ。

## 前端模块

前端暂不引入构建工具，避免给迁移和启动增加 Node 构建步骤。`static/index.html` 直接加载以下源码模块，浏览器调试时看到的就是原始文件，因此当前不需要 source map：

| 目录 | 职责 |
| --- | --- |
| `static/js/services/api.js` | HTTP 请求和统一错误处理 |
| `static/js/services/tasks.js` | 后台任务查询、提交和刷新 |
| `static/js/components/notifications.js` | 通知与用户反馈 |
| `static/js/components/task-panel.js` | 后台任务面板渲染 |
| `static/js/routers/workspace.js` | 工作台页面切换和导航 |

`static/app.js` 仍保留旧页面编排和兼容入口。新增前端功能应先判断属于 service、component 还是 router，再由 `app.js` 调用。等核心页面完成分域迁移后，再决定是否引入 Rollup/Vite；届时必须输出 source map，并保持 `platform.cmd` 一键启动体验。

## 路由覆盖矩阵

运行以下命令可重新生成路由清单：

```powershell
.\.venv\Scripts\python.exe .\scripts\generate_route_coverage.py
```

结果写入：

- `docs/route-test-coverage.json`：供平台、脚本和后续 CI 使用。
- `docs/route-test-coverage.md`：供人工审查。

覆盖状态含义：

- `COVERED`：存在可识别的测试证据或明确的处理器级验证。
- `UNMAPPED`：尚未找到测试映射，需要补测试或确认优先级。
- `INTEGRATION_REQUIRED`：依赖 JMeter、Newman、MySQL、Redis 或真实外部环境，不应伪装成普通单元测试已覆盖。

矩阵优先保证 P0 路由没有未解释的缺口。路由数量增加后，应同步重新生成矩阵；P0 出现 `UNMAPPED` 时视为回归门禁失败。

## 维护原则

1. 路由只做协议转换，长流程进入 handler 或 service。
2. 后台任务先持久化再执行，页面刷新和平台重启不能丢失最终状态。
3. 不同需求包保持独立资产、账号模型、执行批次和报告目录。
4. 外部写操作默认关闭，演示和自动后台执行不得绕过安全开关。
5. 旧代码按业务域渐进迁移，不做一次性大改，也不覆盖用户维护的正式需求资产。
