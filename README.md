# AutoTest AI 智能测试工作台

这是一个可以迁移部署的 AI 自动化测试平台。后端使用 FastAPI 体系运行，迁移到新电脑或新环境时需要先安装项目依赖。

## 已实现

- 项目与测试环境管理
- 需求文档、测试规则、OpenAPI/Swagger JSON/YAML 导入
- 本地规则引擎自动归纳测试点和测试用例
- OpenAI 兼容模型深度生成（可选）
- 接口用例批量执行、状态码与响应内容断言
- 执行证据、失败分类和基础质量看板
- SQLite 持久化
- OpenAPI接口资产目录、参数/请求体元数据和风险分级
- 默认安全执行：POST/PUT/PATCH/DELETE及高风险业务接口自动拦截
- 数据库Schema导入以及接口到数据表的候选映射
- AI业务流程归纳：按模块生成 setup/action/verify 有序步骤
- 流程串行执行、失败停止/继续策略和流程级报告
- 接口/用例搜索筛选、详情查看和完整测试资产导出
- 需求与接口文档关联、接口版本基线和增量变更分析
- 自动识别新增/修改/删除/未变接口，只生成受影响测试资产
- 接口自动化套件、批量执行和套件级统计
- 并发性能基准计划、RPS、平均响应和P95统计
- 必填缺失、类型边界、无效认证、重复请求等异常场景
- 0-100危险系数、资金/删除/资产/回调/认证风险警告
- 流程运行时上下文：自动提取token、sn、ticket、userId、roomId、orderId等字段
- 将上一步响应变量自动注入后续Path、Query、Header和JSON Body
- 被动安全扫描：安全响应头、CORS、危险接口认证声明和环境可用性
- Playwright Web UI计划与可编辑脚本生成
- 内置定时调度器：套件、流程、安全扫描和性能任务
- 单用户最高权限人工控制台，无角色或审批限制
- 手工新增/编辑API、自定义任意分钟间隔的定时任务
- 需求文本自动拆解为业务规则、验收标准、优先级和风险
- 需求→接口→用例→流程→数据库的双语追踪关系
- 每条需求从全量接口中推荐最多50个候选，显示置信度和匹配理由
- 人工勾选/取消候选接口并生成需求级多接口业务流程
- 一键AI流水线：需求、接口、用例、流程、性能、异常、安全、UI、调度和卡点报告
- 公开需求链接抓取，以及TXT/MD/DOCX/PDF/PNG/JPG/WebP直接上传
- DOCX/PDF内嵌图片提取；视觉模型分析页面、流程、状态、控件和图片文字
- 未配置视觉模型时保存原图并明确标记待分析，不伪造图像结论
- 可见 Edge 网页采集器：复用本机登录状态，等待动态内容、自动滚动长页面，并采集文字、标题、表格、链接、图片元数据和整页截图
- 多通道需求采集：同步收集主页面、iframe、页面加载的 JSON/文本数据源和原型资源清单，并生成 DOM/图片/接口/截图数量完整性报告；视觉截图仅作为 Canvas 与图文标注的补充
- Redis 数据中心：支持仅 Host/Port、DB 与可选 TLS 连接，使用 SCAN 限量检索并读取 String/Hash/List/Set/ZSet、TTL 和快照摘要
- Redis 连接器在代码层仅暴露只读命令，不提供 SET、DEL、FLUSH、CONFIG、SHUTDOWN 等修改或管理入口

## 连续迭代方式

每次迭代先导入需求文档，再导入对应OpenAPI并选择关联需求。平台会与现有接口基线比较，记录版本和影响范围；历史用例不会被覆盖或删除。

对于需要登录或由 JavaScript 动态渲染的需求链接，勾选“使用网页登录采集器”。首次运行会打开可见 Edge，可手动登录；登录状态保存在本机 `data/browser-profile`，后续可复用。采集完成后，页面文字与表格进入需求分析，整页截图进入视觉分析。

## 启动

首次迁移到一台新电脑时，先初始化项目 Python 环境：

```powershell
cd C:\Users\DELL\Documents\Codex\2026-08-19\new-chat\outputs\AutoTest-AI
powershell -ExecutionPolicy Bypass -File ".\setup-env.ps1"
```

如果你希望一个依赖一个依赖地确认，也可以在项目目录按下面命令安装：

```powershell
.\.venv\Scripts\python.exe -m pip install fastapi
.\.venv\Scripts\python.exe -m pip install "uvicorn[standard]"
.\.venv\Scripts\python.exe -m pip install pydantic
.\.venv\Scripts\python.exe -m pip install PyYAML
```

完整依赖以 `requirements.txt` 为准。迁移时推荐直接执行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\requirements.txt
```

依赖验证：

```powershell
.\.venv\Scripts\python.exe -c "import fastapi, uvicorn, pydantic, yaml; print('OK')"
```

之后日常启动：

```powershell
cd C:\Users\DELL\Documents\Codex\2026-08-19\new-chat\outputs\AutoTest-AI
.\start.ps1
```

浏览器打开 <http://127.0.0.1:8765>。

启动顺序：

1. 优先使用项目内 `.venv\Scripts\python.exe`。
2. 没有 `.venv` 时，尝试系统 Python `3.12`、`3.13`、`3.14`。
3. 依赖缺失时不会再直接报一串 `No module named uvicorn`，而是提示先运行 `setup-env.ps1`。

## 当前平台定位

AutoTest AI 的定位是 AI 自动化质量中枢，不是替代 JMeter、Postman、Newman、pytest、MySQL 或 Redis 的自研执行器。平台负责需求理解、测试设计、脚本生成、外部工具调度、只读证据核查和报告复盘；企业认可的测试工具负责真实执行。

核心业务价值：

- 需求包独立管理：每个需求独立沉淀资料、接口文档、测试点、测试用例、JMeter/Newman资产和报告。
- 多账号场景：支持单账号需求和多角色需求分离，例如财富等级使用 `wealth_user`，工资交易使用 `applicant`、`proxy`、`operator`。
- 配置驱动迁移：环境地址、JMeter目录、Redis/MySQL只读策略、账号文件和报告目录放在 `config/env.test.yaml`，迁移时优先改配置。
- AI 幻觉校验：AI 生成测试点、用例和数据断言时，应被真实接口文档、DB元数据、Redis Key规则约束，避免乱编字段和状态。
- 结构化测试用例：把接口字段、运行变量、DB表字段、Redis Key证据自动写入用例前置条件、步骤和预期结果，减少人工梳理映射关系。
- 企业工具编排：接口链路交给 Postman/Newman，性能和复杂链路交给 JMeter，结果回收到报告中心。
- 报告复盘：执行结果结合接口响应、JMeter指标、DB/Redis只读证据做复盘分析，而不是只展示图表。

## YAML 环境配置

配置文件位于：

- `config/env.test.yaml`：本机测试环境配置。
- `config/env.example.yaml`：迁移示例，不放真实敏感值。

YAML 通过 Python 的 `PyYAML` 库加载，代码里使用 `import yaml` 和 `yaml.safe_load()`。YAML 只保存环境、路径、开关和只读策略，不保存真实密码、ticket、sn、Authorization 或公司密钥。

脚本运行数据由测试用例决定。单账号、单链路需求可以直接走运行参数、本机加密凭证、登录接口或 Redis 只读缓存；多账号、多角色、多流程或多组数据组合时，再使用 CSV 管理账号池、角色、国家币种、流程槽位、金额、循环次数和压测参数。

## JMeter 脚本生成 Skill

JMeter 生成规则位于 `skills/jmeter-script-generation/SKILL.md`。它定义了从测试用例生成 JMX 的最低标准：

- 读取当前需求包 `account_model.yaml`
- 线程组
- 请求参数
- CSV 参数化
- 变量提取
- 断言
- 监听器
- 冒烟、基准压测、阶梯负载、稳定性场景
- 并发数、持续时间和性能指标
- JTL/HTML 报告回收
- 用例到脚本的 manifest 映射

后续演进到 Agent 时，这个 Skill 会作为工具调用契约，而不是把脚本生成逻辑散落在页面或临时脚本里。

JMeter 不直接猜测账号来源。平台会先根据需求和测试用例生成当前需求包的 `account_model.yaml`，再由 JMeter Skill 决定是否启用单账号、双角色、多流程槽位、CSV、登录接口、Redis 登录态或 MySQL 只读证据。

## 结构化测试用例输出

平台支持把同一份需求包输出为三类执行资产：

- Postman/Newman 集合：适合轻量接口回归和快速冒烟。
- JMeter 脚本：适合复杂业务流、状态流、并发、持续压测和性能指标采集。
- 结构化测试用例：适合评审、手工测试、缺陷定位和 AI 复盘输入。

结构化测试用例不会覆盖原始用例，会写入当前需求包自己的 `outputs/structured-test-cases.json` 和 `outputs/structured-test-cases.md`。生成时会读取当前需求包的测试用例、正式 `evidence_rules.yaml` 和候选 `evidence_rules.candidates.yaml`，把接口字段、 `${变量}`、数据库只读校验、Redis 证据校验补进前置条件、操作步骤和预期结果。

这个能力的业务价值是：测试人员不用手工从接口文档、数据库表结构、Redis Key 之间反复找映射，平台会先生成可审阅的证据规则，再把已确认或候选证据注入测试用例。AI 输出仍然需要元数据校验和人工确认，不做无限自动修正。

## 需求包执行链路

当前工作台按需求包组织执行资产，目录位于 `requirements/<package_id>`。例如：

- `requirements/wealth-level`：财富等级专项需求。
- `requirements/salary-trade`：工资代理快速结算需求。

每个需求包内部固定分为 `docs`、`data`、`skills`、`outputs/newman`、`outputs/jmeter`、`outputs/pytest`、`reports`。页面上的执行中心会先选择“当前执行需求包”，再对该需求包生成脚本、打开 JMeter 和回收报告。

后端接口约定：

- `GET /api/projects/{project_id}/requirement-packages`：读取需求包目录和资产状态。
- `POST /api/projects/{project_id}/requirement-packages`：新建独立需求包并生成可迁移目录。
- `POST /api/projects/{project_id}/requirement-packages/{package_id}/tool-assets`：按需求包生成 Newman、JMeter、pytest 资产。
- `POST /api/projects/{project_id}/requirement-packages/{package_id}/newman/run`：运行当前需求包的 Newman 轻量接口回归。
- `POST /api/projects/{project_id}/requirement-packages/{package_id}/ai-review`：汇总当前需求包报告、外部工具结果和数据证据，生成 AI 复盘报告。
- `POST /api/projects/{project_id}/jmeter/open-gui`：传入 `package_id` 或 `script_key` 后打开对应 JMeter 脚本。
- `POST /api/projects/{project_id}/structured-test-cases`：按当前需求包生成结构化测试用例增强版。

这个设计的目的不是把所有需求塞到一个执行中心里，而是让同一份需求和接口资产可以生成不同工具脚本：Newman 跑轻量接口回归，JMeter 跑复杂流程和性能，pytest 做深度校验和复盘。新增需求时应新增或识别独立需求包，避免覆盖已有需求的 JMX、CSV 或报告。

AI 复盘不是替代测试判断，而是把原始执行结果变成可读结论：识别鉴权、参数契约、业务断言、数据证据、环境网络和服务异常，并给出下一步应由测试、产品、后端、DBA 或环境负责人确认的方向。

## 多账号标准化

多账号规则见 `docs/multi-account-standard.md`，生成规则见 `skills/account-model-generation/SKILL.md`。每个需求包会生成自己的 `account_model.yaml`，例如 `requirements/salary-trade/account_model.yaml`。

核心原则：

- 单账号需求不强制 CSV，例如财富等级默认走运行参数、登录接口或 Redis 登录态。
- 双角色需求使用角色化账号，例如申请人、代理人、运营。
- 多流程且账号互斥的需求使用流程槽位，例如工资交易 8 条状态流需要 8 个申请人。
- 代理人可以复用，但必须先由数据库白名单确认国家和币种匹配，再由 CSV、登录接口或 Redis 补齐真实 ticket。
- token/ticket 必须校验 uid 归属，不允许拿 A 用户的 ticket 跑 B 用户接口。
- 未知角色或新业务约束先写入当前需求包 `extensions.pending`，由测试确认后再生效；多次复用后再升级到通用 Skill。

## Git 版本管理

项目可以直接作为 Git 仓库管理，Python、前端、JMeter 脚本和需求包结构都可以进入版本管理。`.gitignore` 已排除运行态和敏感文件，包括 `.venv`、`reports`、`work`、`database.env`、本地数据库、ticket/password CSV、凭证 bin 和备份文件。

首次提交可在本机 PowerShell 执行：

```powershell
cd C:\Users\DELL\Documents\Codex\2026-08-19\new-chat\outputs\AutoTest-AI
git status --short --ignored
git add .
git commit -m "chore: initialize portable quality hub baseline"
```

提交前重点确认这些文件仍然被忽略：`database.env`、`data/*.bin`、`data/salary-trade-applicants.csv`、`data/salary-trade-accounts.csv`、`data/salary-trade-proxies.csv`、`reports/`、`work/`。这些属于本机运行态，不应该进入仓库。

## 数据位置

平台数据保存在 `data/autotest_ai.db`。AI 密钥也保存在本机数据库中，请只在可信开发环境使用。

## 安全边界

- Base URL 应配置为测试环境。
- 接口执行器会实际发送请求；批量执行前检查生成用例的 method、path 和 payload。
- 后续接入业务数据库时，应使用专用最小权限账号，默认只读，并为写操作设置审批与 SQL 审计。

## 外部 MySQL 数据源

`database.env.example` 提供了连接配置模板。正式连接器遵循以下约束：

- 密码不写入源码或平台 SQLite。
- 默认 `readonly`，只允许 `SELECT`、`SHOW`、`DESCRIBE` 和 `EXPLAIN`。
- 写操作需要单独的低权限账号和明确审批。
- 禁止以生产数据库和 root 账号作为自动化执行账号。

接口鉴权信息通过环境变量 `AUTOTEST_HEADER_SN` 或
`AUTOTEST_HEADER_AUTHORIZATION` 注入，不写入用例数据库。

Soulfree测试环境启动脚本已经按授权开放全部HTTP方法和高风险接口，同时通过域名白名单锁定测试服务器：

```powershell
$env:AUTOTEST_ALLOW_MUTATIONS="true"
$env:AUTOTEST_ALLOW_HIGH_RISK="true"
$env:AUTOTEST_ALLOWED_HOSTS="test2westarlive.gzxchate.com"
```

如果请求指向白名单之外的域名，执行器仍会强制拦截，避免误操作生产环境。
