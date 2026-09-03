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
- 按需求包导入 Apifox OpenAPI、生成受保护的 pytest 基础层，并回收 Apifox CLI 发布冒烟报告
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
cd <AutoTest-AI项目目录>
powershell -ExecutionPolicy Bypass -File ".\setup-env.ps1"
```

网络访问官方 PyPI 较慢时，不需要修改项目文件，可临时指定镜像：

```powershell
$env:AUTOTEST_PIP_INDEX_URL = "https://pypi.tuna.tsinghua.edu.cn/simple"
powershell -ExecutionPolicy Bypass -File ".\setup-env.ps1"
```

也可以明确指定创建虚拟环境使用的 Python：

```powershell
powershell -ExecutionPolicy Bypass -File ".\setup-env.ps1" -PythonExecutable "C:\Python312\python.exe"
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
powershell -ExecutionPolicy Bypass -File ".\verify-migration.ps1" -RunTests
```

之后日常启动，统一使用平台入口：

```powershell
cd <AutoTest-AI项目目录>
.\platform.cmd
```

浏览器打开 <http://127.0.0.1:8765>。

平台入口还提供环境安装和完整自检：

```powershell
.\platform.cmd setup
.\platform.cmd check
```

需要临时更换监听端口时：

```powershell
.\platform.cmd start -Port 8877
```

启动顺序：

1. `setup-env.ps1` 只使用系统 Python 创建项目 `.venv`，所有依赖安装到项目目录内。
2. `platform.ps1` 是正式统一入口，`platform.cmd` 是免执行策略配置的短命令；旧 `start.ps1` 仅保留兼容并转交给统一入口。
3. `.venv`、运行凭证、CSV账号数据、数据库环境变量和报告均被 Git 忽略，不随仓库迁移。
4. 依赖版本来源统一由 `requirements.txt` 和 `pyproject.toml` 管理；安装镜像通过 `AUTOTEST_PIP_INDEX_URL` 临时注入，不写死到仓库。
5. 安装后会在 `.venv/autotest-environment.json` 记录 Python 版本和依赖清单哈希，便于判断迁移环境是否一致。
6. 迁移完成后运行 `verify-migration.ps1 -RunTests`，同时检查虚拟环境、依赖、关键配置模板、代码导入和平台回归测试。

## 当前平台定位

AutoTest AI 的定位是 AI 自动化质量中枢，不是替代 JMeter、Postman、Newman、pytest、MySQL 或 Redis 的自研执行器。平台负责需求理解、测试设计、脚本生成、外部工具调度、只读证据核查和报告复盘；企业认可的测试工具负责真实执行。

核心业务价值：

- 需求包独立管理：每个需求独立沉淀资料、接口文档、测试点、测试用例、JMeter/Newman资产和报告。
- 多账号场景：支持单账号需求和多角色需求分离，例如财富等级使用 `wealth_user`，工资交易使用 `applicant`、`proxy`、`operator`。
- 配置驱动迁移：环境地址、JMeter目录、Redis/MySQL只读策略、账号文件和报告目录放在 `config/env.test.yaml`，迁移时优先改配置。
- AI 幻觉校验与一次修正：AI 生成测试点、用例和数据断言后，会用真实接口文档、DB元数据、Redis Key规则做静态校验；发现未证实引用时，只生成一次候选修正版，不自动覆盖正式资产。
- 结构化测试用例：把接口字段、运行变量、DB表字段、Redis Key证据自动写入用例前置条件、步骤和预期结果，减少人工梳理映射关系。
- 企业工具编排：接口链路交给 Postman/Newman，性能和复杂链路交给 JMeter，结果回收到报告中心。
- Apifox 协同：接口文档、Mock、单接口调试和发布冒烟留在 Apifox；平台导入 OpenAPI、生成 pytest 基础层、调用 CLI 并回收报告。
- 报告复盘：执行结果结合接口响应、JMeter指标、DB/Redis只读证据做复盘分析，而不是只展示图表。

## 主线工作流

平台按需求包收口一条可迁移流程：

1. 选择或新建需求包，导入需求资料和接口文档。
2. 生成测试点、测试用例和结构化测试用例。
3. 生成当前需求包的 `account_model.yaml`，判断单账号、多角色、多流程槽位和 CSV/运行参数策略。
4. 维护 `resource_manifest.yaml` 并执行资源预检，确认账号文件、数据库表、Redis Key、运行参数和接口变量依赖是否齐全。
5. 按 JMeter Skill 规则生成 Newman、JMeter、pytest 执行资产。
6. 执行 Newman/JMeter，并把原始报告回收到当前需求包。
7. 用接口响应、DB/Redis证据、JMeter/Newman结果生成 AI 复盘。

这条链路的原则是：测试用例决定“测什么”，账号模型决定“用谁测”，JMeter/Newman/pytest 负责“怎么执行”，DB/Redis 元数据负责“证据是否真实存在”，AI 复盘负责“把失败原因讲清楚”。

## 需求资源登记与预检

每个需求包拥有独立的 `resource_manifest.yaml`。它只登记当前需求真正使用的账号来源、CSV/Excel 数据集、数据库表、Redis Key 模式、运行参数和接口变量提取规则，不把某个需求的数据源强加给其他需求。

平台根据账号模型、测试用例、场景计划和正式证据规则生成 `outputs/resource-preflight-check.json`，并把缺口分为：

- `BLOCKED`：缺少后无法执行，或执行结果没有可信身份和依赖变量。
- `WARNING`：接口可以执行，但数据证据或结论不完整。
- `SUGGESTION`：建议补充的测试能力，例如长时间过期流程的时间控制入口。
- `CONFIRMED_IGNORED`：测试已确认当前需求不需要，不再重复提醒。

工作台的“资源与预检”入口可以维护资源登记、重新检查缺口并确认忽略。Redis 只有在需求、用例或证据规则明确涉及缓存语义时才建议登记；明确声明不使用 Redis 的需求不会被强制提醒。

## 需求包四层状态

需求包不再用一个 `READY` 同时表示“文件已生成”和“质量已通过”。平台分别输出：

- `asset_status`：需求资料、测试用例和工具资产是否成形。
- `preflight_status`：账号、CSV、数据库、Redis、运行参数和变量依赖是否可执行。
- `latest_execution_status`：Newman、JMeter、pytest 等真实工具最近一轮执行结论；生成计划和 AI 复盘不算真实执行。
- `quality_status`：综合资产、预检、真实执行和复盘证据形成最终质量结论。

因此“资产 READY、执行 FAILED”会明确显示为质量 `FAILED`，不会再被顶部 READY 掩盖。

## YAML 环境配置

配置文件位于：

- `config/env.test.yaml`：本机测试环境配置。
- `config/env.example.yaml`：迁移示例，不放真实敏感值。

YAML 通过 Python 的 `PyYAML` 库加载，代码里使用 `import yaml` 和 `yaml.safe_load()`。YAML 只保存环境、路径、开关和只读策略，不保存真实密码、ticket、sn、Authorization 或公司密钥。

脚本运行数据由测试用例决定。单账号、单链路需求可以直接走运行参数、本机加密凭证、登录接口或 Redis 只读缓存；多账号、多角色、多流程或多组数据组合时，再使用 CSV 管理账号池、角色、国家币种、流程槽位、金额、循环次数和压测参数。

## JMeter 脚本生成 Skill

JMeter 生成规则位于 `skills/jmeter-script-generation/SKILL.md` 和 `skills/jmeter-script-generation/rules.yaml`。它定义了从测试用例生成 JMX 的最低标准：

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

后续演进到 Agent 时，这个 Skill 会作为工具调用契约，而不是把脚本生成逻辑散落在页面或临时脚本里。每次生成需求包脚本时，平台会把机器可读规则写入 `outputs/jmeter/jmeter-skill-contract.json`，用于说明线程组、请求、CSV、断言、监听器、报告和证据规则的生成依据。

JMeter 不直接猜测账号来源。平台会先根据需求和测试用例生成当前需求包的 `account_model.yaml`，再由 JMeter Skill 决定是否启用单账号、双角色、多流程槽位、CSV、登录接口、Redis 登录态或 MySQL 只读证据。

多账号预检会输出申请人槽位、国家/币种组合、代理匹配情况和凭证来源摘要，用于执行前排查 401、50017、代理白名单缺失和账号复用问题。

## 结构化测试用例输出

平台支持把同一份需求包输出为三类执行资产：

- Postman/Newman 集合：适合轻量接口回归和快速冒烟。
- JMeter 脚本：适合复杂业务流、状态流、并发、持续压测和性能指标采集。
- 结构化测试用例：适合评审、手工测试、缺陷定位和 AI 复盘输入。

## Apifox 企业链路

企业已经维护 Apifox 时，Apifox 是接口定义真相源，平台不重复维护另一份接口文档。工作台先选择需求包，再走两条独立但可汇总的链路。

### OpenAPI 3.0 → pytest 基础层

1. 在 Apifox 完整导出 OpenAPI 3.0 JSON/YAML。
2. 在工作台“Apifox企业链路”导入文件。
3. 平台保存到 `requirements/<package_id>/apifox/openapi.json`，接口变化时自动归档旧版本。
4. 平台按当前需求包用例筛选接口，并生成 `outputs/pytest/generated/test_openapi_contract.py`。
5. 人工业务断言、DB/Redis证据和复杂流程放在 `outputs/pytest/business/`；重新导入时不会覆盖。

生成层只负责 URL、方法、参数、基础状态码和响应类型校验。复杂业务逻辑继续由 pytest 维护，避免把发布冒烟脚本写成难维护的业务自动化平台。

### Apifox CLI → 发布冒烟 → 报告回收

1. 在 Apifox 自动化测试中维护核心发布冒烟套件。
2. 把 CI/CD 页面生成的命令配置到 `requirements/<package_id>/apifox/cli-profile.yaml`。
3. 把 access token 放入 `APIFOX_ACCESS_TOKEN` 环境变量，不写入 YAML、Git 或报告。
4. 需要回收 Apifox 原生 JSON/HTML 时，在 `report_globs` 中填写相对需求包的文件模式。
5. 工作台执行发布冒烟后，原始输出、匹配到的原生报告和 `summary.json` 归档到当前需求包 `reports/apifox-smoke-*`。
6. 结果进入同一 `run_id` 的报告中心、统一场景报告和 AI 复盘。

职责边界：Apifox CLI 做版本发布前快速冒烟；pytest 做全量回归和深度数据证据；JMeter 做复杂状态流、并发和性能。平台仍保留反向生成 OpenAPI/Postman/cURL 交换包的兼容能力，仅用于企业没有完整 Apifox 资产时补建基线，不作为主流程。

结构化测试用例不会覆盖原始用例，会写入当前需求包自己的 `outputs/structured-test-cases.json` 和 `outputs/structured-test-cases.md`。生成时会读取当前需求包的测试用例、正式 `evidence_rules.yaml` 和候选 `evidence_rules.candidates.yaml`，把接口字段、 `${变量}`、数据库只读校验、Redis 证据校验补进前置条件、操作步骤和预期结果。

每条结构化用例会额外给出质量分级和脚本生成就绪状态：

- `READY`：接口、变量和证据条件满足当前脚本生成要求。
- `NEEDS_EVIDENCE`：写操作或状态变更用例缺少 DB/Redis 证据规则。
- `NEEDS_EVIDENCE_REVIEW`：仅命中候选证据规则，需要采纳后再作为正式校验。
- `NEEDS_DATA`：依赖运行数据但当前信息不足。
- `MANUAL_ONLY`：涉及人工处理、后台运营、定时过期或长时间等待。

脚本生成就绪状态只表示这条用例是否具备生成脚本的条件，不等于已经完成自动化执行。推荐工具会标明用例适合 `newman`、`jmeter`、`pytest` 还是 `manual`，异常来源会标明是需求异常、接口契约异常、状态机异常还是数据约束异常。

结构化用例还会生成覆盖率看板和缺口清单：

- 覆盖率看板：汇总用例总数、脚本生成就绪数量、待证据确认数量、人工验证数量和对应比例。
- 缺口清单：按候选证据待采纳、缺少正式证据规则、缺少运行数据、人工验证或长等待分组。
- 下一步动作：每条用例给出建议动作，例如进入脚本生成、采纳候选证据、补充证据规则、补齐运行数据或纳入人工测试清单。
- 用例到 JMeter 映射：输出 `case-jmeter-mapping.json`，记录测试用例ID、线程组、请求采样器、变量、断言和 DB/Redis 证据规则。
- Redis 可选证据：登录态、缓存、限流、处理中互斥等场景只给推荐，不强制绑定不存在或未确认的 Key。
- 生成前数据准备检查：输出 `data-preflight-check.json`，静态检查账号模型、CSV账号池、代理国家币种匹配和执行前只读SQL检查模板。
- Excel 导出：输出 `structured-test-cases.xlsx`，用于评审、手工测试和面试展示；不额外依赖 openpyxl。

这个能力的业务价值是：测试人员不用手工从接口文档、数据库表结构、Redis Key 之间反复找映射，平台会先生成可审阅的证据规则，再把已确认或候选证据注入测试用例。AI 输出会进入“生成 -> 元数据校验 -> 一次候选修正 -> 人工确认”流程，不做无限自动修正，也不直接覆盖正式资产。

## 需求包执行链路

当前工作台按需求包组织执行资产，目录位于 `requirements/<package_id>`。例如：

- `requirements/wealth-level`：财富等级专项需求。
- `requirements/salary-trade`：工资代理快速结算需求。

每个需求包内部固定分为 `docs`、`data`、`skills`、`outputs/newman`、`outputs/jmeter`、`outputs/pytest`、`reports`。页面上的执行中心会先选择“当前执行需求包”，再对该需求包生成脚本、打开 JMeter 和回收报告。

后端接口约定：

- `GET /api/projects/{project_id}/requirement-packages`：读取需求包目录和资产状态。
- `POST /api/projects/{project_id}/requirement-packages`：新建独立需求包并生成可迁移目录。
- `GET/POST /api/projects/{project_id}/requirement-packages/{package_id}/resource-manifest`：读取或维护当前需求包资源登记。
- `GET/POST /api/projects/{project_id}/requirement-packages/{package_id}/resource-preflight`：按当前用例和场景重新执行资源预检。
- `POST /api/projects/{project_id}/requirement-packages/{package_id}/execution-plan`：生成场景级执行计划，把 Newman、JMeter、pytest 和人工复核按业务场景归拢。
- `POST /api/projects/{project_id}/requirement-packages/{package_id}/tool-assets`：按需求包生成 Newman、JMeter、pytest 资产。
- `POST /api/projects/{project_id}/requirement-packages/{package_id}/newman/run`：运行当前需求包的 Newman 轻量接口回归。
- `POST /api/projects/{project_id}/requirement-packages/{package_id}/pytest/run`：运行当前需求包的 pytest 深度证据复核，发起接口请求并输出 HTTP、JMeter/Newman、DB/Redis 证据 JSON。
- `POST /api/projects/{project_id}/requirement-packages/{package_id}/ai-review`：汇总当前需求包报告、外部工具结果和数据证据，生成 AI 复盘报告。
- `POST /api/projects/{project_id}/requirement-packages/{package_id}/scenario-report`：生成统一场景报告，把 Newman、JMeter、pytest、数据准备和维护点按同一批业务场景汇总。
- `GET /api/projects/{project_id}/requirement-packages/{package_id}/report-index`：生成或读取需求包报告索引，区分运行批次、最新报告、历史报告和保留策略。
- `GET /api/projects/{project_id}/requirement-packages/{package_id}/schema-audit`：校验需求包 YAML/JSON 资产是否符合当前 Schema。
- `POST /api/projects/{project_id}/requirement-packages/{package_id}/schema-upgrade`：对旧版资产做兼容升级；写入前会备份原文件，只补版本信息和类型标记，不重写业务内容。
- `POST /api/projects/{project_id}/jmeter/open-gui`：传入 `package_id` 或 `script_key` 后打开对应 JMeter 脚本。
- `POST /api/projects/{project_id}/structured-test-cases`：按当前需求包生成结构化测试用例增强版。

这个设计的目的不是把所有需求塞到一个执行中心里，也不是简单把用例按工具拆开。平台会先生成“场景级执行计划”：一个业务场景下面再挂 Newman 预检、JMeter 主流程、pytest 数据证据和人工复核动作。这样人工维护时仍然按需求和场景看问题，而不是在多个工具报告之间来回找线索。

同一份需求和接口资产可以生成不同工具脚本：Newman 跑轻量接口回归，JMeter 跑复杂流程和性能，pytest 做深度校验和复盘。新增需求时应新增或识别独立需求包，避免覆盖已有需求的 JMX、CSV 或报告。

### 一键运行当前需求包

执行中心提供“一键运行当前需求包”。它会创建或复用当前 `run_id`，并按下面顺序收口一次执行：

1. 重新执行资源预检和 Schema 校验。
2. 复用当前需求包已经存在的结构化用例、场景计划和工具资产，不默认覆盖人工维护内容。
3. 真实运行 Newman 接口冒烟和 pytest 深度证据复核。
4. 生成 Newman 接口问题分析、JMeter 安全压测预案、统一场景报告和 AI 执行复盘。
5. 刷新当前需求包报告索引，所有结果只进入同一个需求包和运行批次。

JMeter 持续压测不会被一键执行静默启动。测试人员必须在压测预案中明确选择阶梯，平台才会执行对应 JMX，并回收原始 JTL、JMeter HTML 和性能分析。这样可以减少普通回归操作，同时保留对并发数、持续时间和真实负载的人工控制。

后端入口：`POST /api/projects/{project_id}/requirement-packages/{package_id}/pipeline/run`。

可选参数包括 `run_id`、`run_newman`、`run_pytest`、`create_load_plan`、`jmeter_stage`，以及显式重新生成资产的开关。默认策略是复用正式资产，只补缺失文件。

统一场景报告归档在 `requirements/<package_id>/reports/scenario-report-*`。它不是新的执行工具，而是把已经存在的执行计划、数据准备、Newman、JMeter 和 pytest 结果按场景合并，回答“这个业务流程有没有跑、失败在哪、下一步维护哪个文件”。报告中心会把它显示为“场景总报告”。

AI 复盘不是替代测试判断，而是把原始执行结果变成可读结论：识别鉴权、参数契约、业务断言、数据证据、环境网络和服务异常，并给出下一步应由测试、产品、后端、DBA 或环境负责人确认的方向。

## 报告批次与保留策略

需求包报告按运行批次保存到 `requirements/<package_id>/reports/<tool>-<timestamp>`。平台会生成 `requirements/<package_id>/reports/report-index.json`，把报告分成：

- 最新报告：每种 `report_type` 只认最近一份，用于需求包状态和统一场景报告。
- 历史归档：保留每次 Newman、JMeter、pytest、AI 复盘、场景报告的批次。
- 保留建议：默认每种报告保留最近 5 份，14 天后标记为归档候选，默认不自动删除。

保留策略配置在 `config/env.example.yaml` 的 `reports` 段。迁移到新机器时可以复制为 `config/env.test.yaml` 后按环境调整。

## Schema 校验与升级

需求包正式资产包含 `manifest.json`、`resource_manifest.yaml`、`account_model.yaml`、`outputs/structured-test-cases.json`、`outputs/case-jmeter-mapping.json` 和 `outputs/execution-plan.json`。平台会用 Schema 审计检查必填字段、基础类型和版本号。

当前资产版本为 `1.1`。旧版 `1.0` 资产仍可读取；执行 `schema-upgrade` 时会先把原文件复制到 `requirements/<package_id>/outputs/schema-upgrade-backups/<timestamp>/`，再只补 `schema_version`、`schema_kind` 和迁移标记，不覆盖用例、证据规则、账号模型或脚本内容。

## pytest 深度证据复核

pytest 在这套体系里负责执行后的深度校验。它会读取当前需求包的 `evidence_rules.yaml`，主动发起接口请求，并可通过运行变量读取 JMeter JTL、Newman JSON、MySQL 和 Redis 证据。输出报告归档在 `requirements/<package_id>/reports/pytest-evidence-*`。

这层的定位不是替代 JMeter 状态机，也不是只看 HTTP 状态码，而是回答“接口跑完之后，业务数据是否真的符合预期”：订单是否落库、状态是否正确、日志是否可追溯、Redis 缓存是否匹配。默认只允许只读 SQL，业务写入仍由接口请求产生。

pytest 复盘层按通用规则运行，不绑定某个业务需求。它会从接口响应 JSON 中自动提取常见业务标识字段，并把这些变量补给后续请求和证据规则。遇到新项目的新字段时，可以在 `requirements/<package_id>/runtime_aliases.yaml` 增加别名映射，模板见 `data/templates/runtime-aliases.example.yaml`，不需要改 pytest 主逻辑。

`runtime_aliases.yaml` 也可以保存当前需求包确认过的非敏感公共请求参数，例如 `appVersion`、`appCode`、设备类型和语言。账号 `uid/ticket` 仍从运行时输入或角色 CSV 读取，不能写进该 YAML。运行器按接口路径切换申请人/代理身份，避免工资交易继承财富等级的账号或版本参数。

pytest 证据复盘规则已沉淀为 `skills/pytest-evidence-review/SKILL.md`。生成当前需求包工具资产时，平台会同步输出 `outputs/pytest/pytest-evidence-skill-contract.json`，用于说明本次 pytest 应该消费哪些需求包资产、如何处理运行变量、如何读取 DB/Redis 证据，以及报告必须如何归档。

pytest 报告会优先读取 `manifest.json` 里声明的 `orchestration.primary_plan`，默认是 `outputs/execution-plan.json`，并按业务场景汇总 HTTP、JMeter/Newman 和 DB/Redis 证据结果；没有正式编排文件时，才退回结构化用例里的 `scenario_type`。这样复杂需求不会变成一坨接口结果，而是能按“创建-取消”“创建-拒绝”“完整成交”等场景复核；未来如果出现更高级的编排文件，也只需要让需求包 manifest 指向新文件。

场景驱动执行时，pytest 会按编排文件里的场景顺序组织用例：先跑当前场景接口并提取运行变量，再立即执行该场景的 DB/Redis 证据规则，最后进入下一个场景。这样多账号、多订单、多流程需求不会只拿最后一个 `orderNo` 做统一校验。

每个场景执行前会恢复基础运行上下文，再注入该场景自己的变量；场景内产生的订单号、流水号、状态值只服务当前场景。证据规则优先使用编排文件里绑定的 rule id，适合工资交易这种多申请人、多订单、多状态流转需求，也能迁移到后续更复杂的业务。

## 执行结果回灌复盘

每个需求包可以生成独立 AI 复盘报告，输入包括：

- 当前需求包的 Newman/JMeter/pytest 执行摘要。
- 平台最近保存的接口执行记录。
- 结构化测试用例、质量分级、脚本生成就绪状态和缺口清单。
- 用例到 JMeter 映射表。
- 数据准备检查、执行前只读 SQL 模板、DB/Redis 证据执行报告。

复盘报告会输出 `summary.json` 和 `review.md`，归档在 `requirements/<package_id>/reports/ai-review-*`。复盘只给结论、根因分类和修改建议，不自动修改脚本或业务数据。根因分类包括鉴权、请求契约、业务断言、测试数据、数据证据、性能、环境和服务异常。

当存在 pytest 场景证据报告时，AI 复盘会读取其中的 `scenarios`：按场景统计 HTTP 失败、DB/Redis 证据失败和阻断项，并把失败场景转成可读 finding。这样复盘结论能定位到具体业务流程，而不是只说总失败数。

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
cd <AutoTest-AI项目目录>
git status --short --ignored
git add README.md app.py quality_hub_backend/api/fastapi_app.py config/env.example.yaml tests/test_package_status_model.py
git commit -m "chore: initialize portable quality hub baseline"
```

提交前重点确认这些文件仍然被忽略：`database.env`、`data/*.bin`、`data/salary-trade-applicants.csv`、`data/salary-trade-accounts.csv`、`data/salary-trade-proxies.csv`、`reports/`、`work/`。这些属于本机运行态，不应该进入仓库。

发布或迁移前按 `docs/release-checklist.md` 完成验收。该清单区分平台本身、需求包资产、真实测试环境和敏感运行数据，避免把“平台可运行”和“某次业务测试通过”混成一个结论。

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
