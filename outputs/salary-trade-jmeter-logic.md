# 工资代理快速结算 JMeter 接口测试逻辑

## 资料依据

- 需求原型：`C:\Users\DELL\Desktop\工资交易`
- 接口文档：`C:\Users\DELL\Desktop\01-工资代理快速结算-App接口文档.md`
- JMeter 脚本：`C:\Users\DELL\Documents\Codex\2026-08-19\new-chat\outputs\AutoTest-AI\outputs\performance-baseline-with-salary-thread.jmx`

## 线程组结构

| 线程组 | 覆盖目标 | 默认状态 |
| --- | --- | --- |
| 登录鉴权前置 | 登录接口提取 `access_token`，同步为业务接口使用的 `ticket` | 启用 |
| 工资交易读接口基准（自动提取订单号） | 入口、额度、代理列表、公告、订单列表、详情、日志、凭证等只读校验 | 启用 |
| 工资交易需求流A：创建后申请人取消（10-50） | 创建订单后由申请人取消，验证待处理到已取消 | 关闭 |
| 工资交易需求流B：创建-接单-付款-确认（10-20-30-40） | 完整成功主流程，验证创建、接单、付款、确认到账 | 关闭 |
| 工资交易需求流C：创建-接单-付款-投诉（30-80） | 申请人在待确认收款状态提交投诉 | 关闭 |
| 工资交易需求流D：创建后代理拒绝（10-60） | 创建订单后代理拒绝，验证已拒绝分支 | 关闭 |
| 工资交易需求流E：公告与凭证维护接口 | 代理公告保存、申请人凭证、代理凭证上传 | 关闭 |
| 工资交易需求流F：代理侧投诉（30-80） | 代理人在待确认收款状态提交投诉 | 关闭 |

## 接口覆盖

已覆盖接口文档中的 21 个 App 接口：

- `/union/getAnchorApplyRecord`
- `/userserv/salary/trade/quota`
- `/userserv/salary/trade/agents`
- `/userserv/salary/trade/order/create`
- `/userserv/salary/trade/order/page`
- `/userserv/salary/trade/order/detail`
- `/userserv/salary/trade/order/cancel`
- `/userserv/salary/trade/order/confirm`
- `/userserv/salary/trade/order/appeal`
- `/userserv/salary/trade/evidence/upload`
- `/userserv/salary/trade/evidence/list`
- `/userserv/salary/trade/logs`
- `/userserv/salary/trade/agent/notice`
- `/userserv/salary/trade/agent/notice/save`
- `/userserv/salary/trade/agent/order/page`
- `/userserv/salary/trade/agent/order/detail`
- `/userserv/salary/trade/agent/order/accept`
- `/userserv/salary/trade/agent/order/reject`
- `/userserv/salary/trade/agent/order/paid`
- `/userserv/salary/trade/agent/order/appeal`
- `/userserv/salary/trade/agent/evidence/upload`

## 核心变量

| 变量 | 含义 | 来源 |
| --- | --- | --- |
| `ticket` | 申请人登录态 | 平台本机凭证或登录鉴权前置 |
| `agent_ticket` | 代理用户登录态 | 平台本机代理凭证或启动参数 `-Jagent_ticket`；严格模式不允许复用申请人 `ticket` |
| `applicant_uid` | 申请人 UID，默认 `1454428` | 启动参数或脚本默认值 |
| `agent_uid` | 代理 UID，默认 `1454924`，读接口会从 `/userserv/salary/trade/agents` 提取可选代理 | 启动参数、接口提取或脚本默认值 |
| `salary_order_no` | 创建订单后返回的订单号 | JSON 提取器 `$.data.orderNo` |
| `salary_order_id` | 兼容详情、日志、凭证接口的订单变量 | 由 `salary_order_no` 同步 |
| `salaryAmount` | 申请结算金额，默认 `100` | 启动参数或脚本默认值 |
| `countryCode` | 国家，默认 `EG` | 启动参数或脚本默认值 |
| `currency` | 币种，默认 `EGP` | 启动参数或脚本默认值 |
| `bankReceiverName` / `swiftCode` / `bankName` / `bankAccount` / `bankReceiverAddress` | 创建订单必填收款资料 | 优先从订单列表第一条订单回填；没有时使用脚本默认值或启动参数 |

## 必填信息回填

- `/userserv/salary/trade/order/page` 返回订单列表后，JMeter 会从第一条订单里提取 `orderNo`、`uid`、`agentUid`、`salaryAmount`、`receiveCurrency`、`countryCode` 和银行收款资料。
- 提取到的字段会写入 JMeter 变量和全局属性，后面的详情、日志、凭证、创建订单链路可以直接复用。
- 文本类字段会做 URL 编码，避免阿拉伯语、空格、特殊字符放进 `x-www-form-urlencoded` 请求体后变形。

## 断言逻辑

- 所有接口先断言 HTTP 状态码为 `200`。
- 所有业务接口再断言响应正文包含 `"code":200`。
- 创建订单断言返回状态 `10`。
- 代理接单断言返回状态 `20`。
- 代理付款断言返回状态 `30`。
- 申请人确认到账断言返回状态 `40`。
- 申请人取消后查询详情断言状态 `50`。
- 代理拒绝后查询详情断言状态 `60`。
- 投诉后查询详情断言状态 `80`。

## 当前执行注意

- 读接口基准可以直接执行。
- A-F 业务流会真实创建或变更订单，默认关闭，需要单独启用。
- 完整跨角色链路必须使用代理用户自己的 `agent_ticket`，否则代理侧接口会因严格身份校验而失败。
- 当前抓包已确认：`1454428` 可结算工资 `7800`，当前进行中订单号 `1454428260827142252363112`，状态 `10`，分配代理 `1454924`。
- 运营处理投诉属于后台/运营端能力，当前 App 接口文档没有给运营处理接口，因此 JMeter App 脚本只覆盖投诉进入 `80`，运营处理闭环需要后续补运营端接口文档。
