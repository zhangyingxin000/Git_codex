# 多账号标准化规则

AutoTest AI 按测试用例判断账号模型，不把 CSV 作为所有需求的默认前置。

通用规则由 `skills/account-model-generation/SKILL.md` 维护。每个需求包生成自己的 `account_model.yaml`，脚本生成器、Newman、JMeter 和 pytest 都应该读取这个模型，而不是在各自逻辑里重复猜测账号。

## 账号模型

| 模型 | 适用场景 | 数据载体 | 示例 |
| --- | --- | --- | --- |
| single_account | 单用户、单角色、无账号互斥 | 运行参数、登录前置、Redis登录态 | 财富等级闭环 |
| dual_role | 一个流程里有两个或多个业务角色 | 角色化账号CSV、登录接口、Redis登录态 | 申请人创建订单，代理人接单 |
| multi_flow_slots | 多条流程需要不同账号承载，或同一账号存在处理中互斥 | 流程槽位CSV、账号池、DB白名单、Redis登录态 | 工资交易8条状态流 |

## 身份获取顺序

1. 运行时显式传入 ticket 或 password。
2. 角色 CSV 中填写 ticket、password 或 redis_uid。
3. 登录接口按 shortId 和 password_encrypted 获取 access_token。
4. Redis 只读读取 `user_login_info:{uid}.access_token`。
5. 仍未取得则阻断，不伪造身份认证。

## 新场景扩展

如果未来需求里出现模板未覆盖的新身份或新约束，先进入当前需求包：

```yaml
extensions:
  pending:
    - type: role
      name: risk_reviewer
      reason: 接口字段 reviewerUid 出现在审核步骤中
      suggested_fields: [reviewerUid, ticket]
```

测试确认后再转为 `extensions.confirmed` 或正式角色。只有当多个需求包反复出现同类场景时，才升级 `account-model-generation` Skill。

## 工资交易规则

工资交易是多流程、多角色需求：

- 申请人由流程槽位决定，不能 8 条流程都使用同一个申请人。
- 一个申请人同一时间只能有一个处理中订单，所以 8 条状态流建议准备 8 个申请人。
- 代理人可以复用，但必须满足业务匹配条件。
- 代理候选先从 `anchor_salary_trade_agent_whitelist` 按国家和币种匹配。
- 代理 ticket 来自 CSV、登录接口或 Redis，不来自数据库。
- JWT 解析出的 uid 必须等于当前代理 uid，否则直接阻断，避免拿错人的 ticket 导致 401。

## 财富等级规则

财富等级是单账号闭环：

- 默认不强制 CSV。
- 可通过运行参数、登录接口或 Redis 登录态取得 ticket。
- 只有做多账号登录性能或账号矩阵压测时，才启用账号 CSV。

## 变量命名边界

不同需求包不能共用同一组业务变量：

- 财富等级：`wealth_user_uid`、`wealth_user_ticket`
- 工资交易：`applicant_uid`、`applicant_ticket`、`proxy_uid`、`proxy_ticket`、`salary_order_no`

公共设备参数可以复用，例如 `deviceId`、`model`、`osVersion`、`appVersion`。

## DB 和 Redis 的边界

- DB 用来证明代理资格、订单状态、日志、凭证和金额等业务证据。
- Redis 用来读取缓存证据或历史登录态。
- DB 不保存 ticket，不负责身份认证。
- Redis 取出的 token 必须校验 uid 归属。
