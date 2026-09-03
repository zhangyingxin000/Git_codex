# Apifox 协同导入说明

需求包：财富等级
生成时间：2026-09-03T16:20:53+08:00

## 导入顺序
1. 在Apifox中导入 `openapi.json`，建立接口文档基线。
2. 通过Postman导入入口导入 `postman-collection.json`，复用请求和断言。
3. 同一入口导入 `postman-environment.json`；测试域名填写 `baseUrl`，Apifox生成的Mock域名填写 `mockBaseUrl`。
4. `environment.example.json` 是便于人工维护和平台迁移的可读配置副本。
5. 单接口排错时导入或复制 `curl/` 下对应用例的cURL。
6. 使用 `case-api-mapping.json` 反查平台用例、Apifox请求和JMeter线程组。
7. ticket、密码、sn、cookie等敏感值只在Apifox本地环境维护，本包不会导出。

## 自动化能力
- 请求会按照 `execution-plan.json` 的业务场景分组；未进入场景计划的接口按用例类型归档。
- 每个请求包含HTTP状态断言，成功用例在响应存在 `code` 时校验业务成功码。
- 响应中的 `orderNo`、`orderId` 和 `access_token` 会自动写入环境变量，供后续步骤使用。
- `apifox-automation-manifest.json` 记录场景、用例数量和自动化能力，便于平台与人工复核。

## 平台边界
- 平台负责生成接口资产、测试用例、执行脚本、运行参数模板和报告归档。
- Apifox负责接口文档、Mock、单接口调试、人工维护和团队协作。
- Newman、JMeter、pytest 负责自动执行与报告产出。
- MySQL/Redis 只读，用于证据核对，不写真实业务数据。

## 本次资产
- 接口数量：1
- 测试用例：2
- cURL文件：2
