# Engineering Architecture

本文说明当前工程化拆分的边界，以及新增功能应该放在哪里。目标不是一次性重写旧平台，而是在保持现有功能可运行的前提下，把高频变化部分逐步迁出 `app.py` 和 `static/app.js`。

## 技术栈

| 层次 | 技术 | 在平台中的职责 |
| --- | --- | --- |
| 运行环境 | Python 3.12+、项目 `.venv` | 隔离平台依赖，保证迁移后可重复安装和运行 |
| Web API | FastAPI、Uvicorn | 提供项目、需求包、执行、证据、报告和后台任务 API |
| 数据模型 | Pydantic | 校验 API 请求参数和配置结构，减少错误数据进入执行层 |
| 平台数据 | SQLite、SQLAlchemy、Alembic | 保存项目、接口、用例、映射、执行记录和后台任务状态 |
| 配置 | PyYAML、环境变量 | 管理多环境地址、工具路径、开关、报告策略和非敏感数据源配置 |
| HTTP 调用 | httpx | 平台预检、接口请求和外部服务访问 |
| MySQL 证据 | PyMySQL | 查询测试环境业务表和元数据；平台默认只读 |
| Redis 证据 | redis-py | 按需求读取登录态、缓存值、TTL 和元数据；不默认强制接入 |
| 接口执行 | Postman Collection、Newman、Apifox CLI | 接口冒烟、轻量回归和发布前卡点 |
| 流程与性能 | Apache JMeter、Java、JMeter Skill、`jmeter-mcp-server` | Skill按用例、OpenAPI和Profile生成受约束JMX，静态门禁校验后由MCP仅负责非GUI执行并回收JTL/HTML |
| 深度验证 | pytest | 场景驱动执行、业务断言、DB/Redis 证据和复盘输入 |
| 报告 | JTL、JMeter HTML、Newman JSON、pytest JSON、可选 Allure | 保留原始结果，并生成统一场景报告和 AI 分析 |
| 前端 | 原生 HTML、CSS、JavaScript | 无构建启动，负责工作台导航、状态展示和执行入口 |

`requirements.txt` 与 `pyproject.toml` 当前声明相同的 Python 运行依赖。JMeter、Java、Node.js、Newman、Apifox CLI 和 Allure 属于外部工具，不安装进 Python 虚拟环境，由工具链预检识别。

## 总体结构

平台采用“控制面 + 外部执行器 + 证据源 + 报告归档”的结构：

```text
浏览器工作台
  -> FastAPI routes
  -> handler / service
  -> 需求包资产与平台 SQLite
  -> adapter 调用 Newman / JMeter MCP / pytest / Apifox CLI
  -> MySQL / Redis 只读证据
  -> 原始报告
  -> 统一场景报告与 AI 复盘
```

平台不是重新实现 Newman、JMeter 或 pytest。平台负责决定测什么、准备什么数据、用哪个工具、如何关联结果；JMeter 路径统一由 `jmeter-mcp-server` 生成或导入 JMX 并触发非GUI执行，Apache JMeter 负责真实发压和原生 HTML。

## 模块关联

| 模块 | 上游 | 下游 | 主要输出 |
| --- | --- | --- | --- |
| `api/fastapi_app.py` | 浏览器、CLI、外部调用方 | `api/routes`、兼容层 | FastAPI 应用、异常处理、静态页面 |
| `api/routes/` | FastAPI | handlers、services、`app.py` 兼容函数 | HTTP 响应，不承载长业务逻辑 |
| `handlers/` | API 路由、后台队列 | services、兼容层执行函数 | 单次任务编排和安全默认值 |
| `services/` | handlers、routes | repositories、adapters、需求包文件 | 用例生成、回归选择、诊断、报告索引、任务状态 |
| `adapters/` | services、handlers | JMeter、Newman、pytest 等进程 | 标准化工具命令、退出码和原始结果 |
| `repositories/` | services | SQLite | 平台读模型和持久化访问 |
| `config/` | 启动入口、services | YAML、环境变量 | 统一运行配置和路径解析 |
| `schemas/` | routes | Pydantic | 请求和响应的数据边界 |
| `startup/` | Uvicorn/FastAPI | 任务队列、生命周期资源 | 启动和关闭资源 |
| `security/`、`storage_policy.py` | routes、services | 外部地址和本地文件操作 | 写操作、目标地址和存储边界控制 |
| `demo/` | `platform.cmd demo`、后台任务 | 合成 SQLite 和回放数据 | 不连接测试服的可复现演示结果 |
| `app.py` | 新 FastAPI 模块 | 旧数据库函数、生成器和执行器 | 兼容现有功能；仍在渐进拆分 |

调用原则：`route -> handler/service -> repository/adapter`。下层模块不反向依赖页面；外部工具命令不应直接写在路由里；需求包业务规则不应进入启动模块。

## 需求包数据流

每个需求都以 `requirements/<package_id>/` 为维护边界：

```text
需求文档 / OpenAPI / 抓包
  -> 需求测试用例 + 接口测试用例
  -> account_model.yaml + resource_manifest.yaml
  -> execution-plan.json + evidence_rules.yaml
  -> Newman / JMeter / pytest 工具资产
  -> run-context 独立运行批次
  -> 原始执行报告 + DB/Redis 证据
  -> 统一场景报告
  -> AI 复盘结论
```

关键关联关系：

1. 测试用例决定“测什么”，接口用例和业务流程用例分开维护。
2. `account_model.yaml` 决定单账号、多账号、角色和账号互斥要求。
3. `resource_manifest.yaml` 登记 CSV、MySQL、Redis、运行变量等真实来源。
4. `execution-plan.json` 组织场景顺序，并把场景分配给 Newman、JMeter、pytest 或人工复核。
5. `evidence_rules.yaml` 定义接口执行后如何查询 DB/Redis 和判断业务结果。
6. `run-context` 把同一轮工具结果绑定到一个批次，避免历史报告和当前执行混合。
7. 统一场景报告按用例 ID、场景 ID、订单号等变量关联原始结果，不替代原始报告。

## 工作台职责与收紧方案

当前工作台功能完整，但存在明显入口冗余：同一个需求包可以从质量总览、需求包卡片、执行中心、高级工具链多处生成资产或启动工具；历史执行状态与当前运行批次也会同时出现。功能没有丢失，但人工会难以判断“现在应该点哪个”。

目标只保留四个主工作区：

| 页面 | 只负责什么 | 不再放什么 |
| --- | --- | --- |
| 质量总览 | 项目健康度、当前需求包、阻断项和唯一下一步 | 不直接执行 Newman/JMeter/pytest，不重复展示全部维护按钮 |
| 需求资产 | 需求包、文档、接口、测试用例、账号模型、资源登记和场景计划 | 不展示历史报告和性能执行按钮 |
| 执行中心 | 选择当前需求包、创建运行批次、数据预检、启动工具、查看实时任务 | 不展示完整资产维护表，不混入 demo/其他需求包任务 |
| 报告中心 | 按需求包、运行批次、报告类型查看原始报告和 AI 结论 | 不再提供生成脚本或修改资源入口 |

高级能力保留在折叠区域：工具路径、YAML、JMeter Skill、Apifox 交换、原始参数和人工报告回收。普通主流程不需要反复看到这些配置。

建议按以下顺序继续收紧：

1. 总览页只保留一个“继续下一步”按钮，跳转到对应资产或执行步骤。
2. 执行中心将十多个工具按钮收成“准备、执行、复盘”三个阶段；具体工具由场景计划决定。
3. 当前批次状态与历史最近状态分开标注，禁止用旧报告冒充本轮已执行。
4. 需求包目录只展示正式需求包；手工接口和未归档资料放入“待整理”区域。
5. 报告中心默认按需求包和批次折叠，只展开最新一轮，原始 JSON/JTL/HTML 放在二级详情。
6. 高级工具链只保留一处入口，不在多个页面重复出现。

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

当前已迁移的路由域：

- `api/routes/system.py`：健康检查、存储策略、环境配置和路由覆盖。
- `api/routes/tasks.py`：后台任务提交、查询和任务类型。
- `api/routes/projects.py`：项目基础信息、工作台、诊断、需求包目录、账号模型和资源预检。
- `api/routes/requirement_execution.py`：需求包场景计划、运行批次和 Newman/JMeter/pytest 执行。
- `api/routes/requirement_reports.py`：需求包报告索引、统一场景报告、Schema 审计和 AI 分析。

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
| `static/js/services/requirement-packages.js` | 需求包、运行批次、工具执行和报告请求 |
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
