# AutoTest AI 质量中枢工程化蓝图

## 平台定位

AutoTest AI 不是自研测试执行器，而是 AI 驱动的质量中枢。

平台负责需求理解、测试资产生成、任务编排、企业工具调度、证据归档和质量报告归纳。真正的接口测试、性能测试、数据校验和 UI 自动化，应由企业认可的工具执行，并保留原始结果。

## 推荐技术栈

### 前端

- React + TypeScript
- Vite
- TanStack Query
- Zustand
- React Router
- ECharts
- Playwright 端到端测试

### 后端

- FastAPI
- Pydantic
- SQLAlchemy
- Alembic
- Celery / Dramatiq / APScheduler
- SQLite 开发环境，MySQL/PostgreSQL 企业部署

### 测试工具适配器

- 接口测试：Newman、pytest、REST Assured
- 性能测试：JMeter、k6、Locust
- UI 自动化：Playwright、Selenium/Appium
- 数据校验：MySQL 只读查询、Redis 只读命令
- CI/CD：Jenkins、GitLab CI、GitHub Actions

## 目标架构

```text
需求输入层
  文档 / 链接 / 图片 / 原型 / 描述 / OpenAPI

AI 测试设计层
  需求拆解 / 测试点 / 用例 / 风险 / 覆盖矩阵

编排层
  多接口链路 / 参数传递 / 环境变量 / 凭证脱敏 / 任务状态机

企业工具执行层
  Newman / pytest / JMeter / Playwright / MySQL / Redis

证据归档层
  JSON / JTL / HTML Report / JUnit XML / 截图 / 日志 / 数据快照

质量报告层
  接口报告 / 性能报告 / 数据一致性 / 缺陷风险 / 面试项目资产
```

## 后端分层

```text
app/
  api/            HTTP API 路由
  domain/         领域模型与业务状态
  services/       用例生成、链路编排、报告归纳
  adapters/       Newman、JMeter、MySQL、Redis 等外部工具适配器
  repositories/   数据访问层
  schemas/        Pydantic 请求响应模型
  workers/        异步任务与调度
  security/       凭证、脱敏、只读策略、审计
```

## 前端分层

```text
src/
  app/            路由、布局、全局 Provider
  features/       需求、用例、执行、数据校验、报告等业务模块
  entities/       Project、Requirement、TestCase、Report 等实体
  shared/         UI 组件、请求客户端、工具函数
  widgets/        质量中枢总览、闭环看板、报告工作区
```

## 企业认可点

- AI 不直接代替测试结论，AI 负责设计和归纳
- 执行结果来自 Newman、pytest、JMeter、MySQL、Redis 等标准工具
- 所有报告保留原始文件和执行命令
- 测试环境、工具版本、执行参数、开始结束时间可追溯
- 凭证脱敏，数据库和 Redis 默认只读
- 可导出测试资产和报告包，支持面试和项目复盘

## V1 完整闭环

1. 导入需求链接、图片或描述
2. AI 生成测试点和测试用例
3. AI 根据 OpenAPI 生成接口集合
4. AI 编排多接口业务链路
5. 调用 Newman 或 pytest 执行接口测试
6. 连接 MySQL / Redis 做只读数据校验
7. 自动生成 JMeter 压测计划并执行
8. 归档原始报告和 AI 总结报告
9. 输出质量看板和面试项目说明
