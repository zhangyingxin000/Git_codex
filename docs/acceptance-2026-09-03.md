# AutoTest AI 验收记录（2026-09-03）

## 平台结论

平台主链路达到可交付状态：

`需求包 -> run_id -> Newman/JMeter/pytest -> DB/Redis证据 -> 原始报告 -> AI分析 -> 统一场景报告`

- `platform.cmd check` 通过。
- 平台回归测试 `17 passed`。
- Python、前端 JavaScript 和迁移检查通过。
- FastAPI OpenAPI 共识别 104 条路由，一键执行、Newman、pytest 和统一场景报告接口齐全。
- 首页和前端资源返回 HTTP 200。
- 报告按 `package_id + run_id` 隔离，不回退混入旧全局报告。

## 财富等级验收

运行批次：`acceptance-live-wealth-20260903-r5`

- Newman 接口冒烟：PASSED。
- pytest 场景证据：PASSED。
- 缺失 UID 用例真实移除 `uid`；非法 UID 用例真实发送 `uid=not-a-number`。
- JMeter 压测预案：READY，未静默启动持续压测。
- 最终批次状态：`READY_WITH_WARNINGS`。
- 统一场景报告和 AI 复盘已生成；剩余提醒属于待补场景证据，不是工具执行失败。

## 工资交易验收

运行批次：`acceptance-safe-salary-20260903-r3`

- 默认安全模式只执行 GET，不发送 96 个写接口。
- 角色 CSV 已接入运行器，申请人和代理按接口路径切换，不写死单个凭证。
- 30 个去重后的只读请求已执行。
- Newman 发现 10 个事件：9 个认证失败，1 个请求前置参数问题。
- 认证失败已归类为 `authentication`，报告包含接口、HTTP 状态、响应摘要、建议负责人和复核动作。
- 当前 CSV ticket 的 JWT uid 与账号 uid 一致，但服务端仍返回 401；这属于测试环境登录态失效或被后续登录替换，不能由平台绕过。
- 代理订单详情缺少可用订单号时返回 400，属于前置业务变量未准备。

## 安全与迁移

- ticket、密码和数据库密码不写入正式 YAML、脚本或 Git。
- 工资交易公共设备参数位于需求包 `runtime_aliases.yaml`，账号身份仍从角色 CSV/运行时输入读取。
- pytest 每个运行批次使用独立临时目录，避免 Windows 用户所有权冲突。
- 工资交易不强制 Redis；DB 仍作为代理资格与订单、日志、凭证证据来源。

## 后续业务动作

1. 更新工资交易申请人/代理 CSV 中的有效 ticket，再复跑同一安全流水线。
2. 需要验证写流程时显式开启写接口，并使用独立申请人槽位执行 8 条状态流。
3. JMeter 持续压测由人工选择阶梯后启动，回收原始 JTL 和 HTML，再生成性能分析。
