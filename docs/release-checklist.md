# AutoTest AI 发布与迁移验收清单

## 1. 平台运行

- [ ] 执行 `platform.cmd check`，依赖、导入、回归测试和迁移检查全部通过。
- [ ] 执行 `platform.cmd` 后，`http://127.0.0.1:8765` 可以打开。
- [ ] FastAPI OpenAPI 中包含需求包、运行批次、一键执行、Newman、JMeter、pytest、报告和 Schema 接口。
- [ ] FastAPI OpenAPI 中包含 Apifox OpenAPI 导入和 Apifox CLI 发布冒烟接口。
- [ ] 页面可以选择需求包，执行中心和报告中心显示同一个需求包。

## 2. 需求包隔离

- [ ] 每个需求位于 `requirements/<package_id>`，资料、数据、脚本、运行批次和报告不与其他需求混用。
- [ ] `manifest.json`、`account_model.yaml`、`resource_manifest.yaml` 和 `outputs/execution-plan.json` 指向当前需求包。
- [ ] 报告索引只接受带当前需求包 `run_id` 的报告，不回退展示旧全局报告。
- [ ] 一键执行默认复用正式资产，不覆盖人工维护的账号模型、证据规则和场景计划。

## 3. 执行与报告

- [ ] Newman 保留原始 JSON，并生成逐接口异常、错误分类、建议负责人和复核动作。
- [ ] pytest 按场景顺序执行，输出 HTTP、DB/Redis 证据和阻断原因 JSON。
- [ ] JMeter 运行保留原始 JTL 和原生 HTML；性能分析必须引用同一批次原始数据。
- [ ] JMeter 长压测必须人工选择阶梯，不由普通一键回归静默启动。
- [ ] 统一场景报告按场景归拢 Newman、JMeter、pytest、数据准备和维护点。
- [ ] Apifox OpenAPI 只导入当前 `package_id`，相同版本不误报变化，变更版本可追溯。
- [ ] pytest `generated` 目录可以重新生成，`business` 目录中的人工逻辑不会被覆盖。
- [ ] Apifox CLI 使用需求包自己的 `cli-profile.yaml`，真实 access token 只从环境变量读取。
- [ ] Apifox CLI 原始日志、摘要、失败分类进入当前 `run_id`，并出现在报告中心、统一场景报告和 AI 复盘。
- [ ] Apifox CLI 命令、日志和 JSON 报告不包含真实 JWT、ticket、token、密码或 Cookie。
- [ ] AI 复盘只做分析和建议，不自动修改脚本、业务库或正式证据规则。

## 4. 数据与安全

- [ ] ticket、token、密码、数据库密码和真实账号 CSV 未提交到 Git。
- [ ] 数据库与 Redis 只登记当前需求需要的数据源，不默认强制所有需求连接。
- [ ] 数据证据默认只读，业务数据变化由被测接口产生。
- [ ] 真实执行域名限制为测试环境，写接口执行前由测试人员确认。

## 5. 迁移

- [ ] 新机器执行 `setup-env.ps1` 创建项目独立 `.venv`。
- [ ] 复制 `config/env.example.yaml` 和数据源模板后，只在本机填写环境值。
- [ ] JMeter、Node/Newman、数据库驱动路径来自 YAML 或环境变量，不依赖旧机器绝对路径。
- [ ] 执行 `verify-migration.ps1 -RunTests` 后再导入本机账号数据和运行凭证。

## 发布结论

平台发布结论和业务测试结论必须分开记录：

- 平台验收通过：说明生成、执行、回收、分析和报告链路可以工作。
- 需求包测试通过：说明某个 `package_id + run_id` 的真实 Newman/JMeter/pytest 与数据证据均达到预期。
- `READY_WITH_WARNINGS`：平台可运行，但仍存在人工用例、未执行工具、候选证据或测试环境限制。
