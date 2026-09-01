# 工资代理快速结算 - 结构化测试用例

- 生成时间：2026-09-01T16:33:23+08:00
- 用例数：170
- 带DB校验：143
- 带Redis校验：0
- 质量分级：{"READY": 38, "NEEDS_EVIDENCE": 8, "NEEDS_EVIDENCE_REVIEW": 110, "MANUAL_ONLY": 14}
- 自动化覆盖：{"AUTO_READY": 38, "SCRIPTABLE_EVIDENCE_PENDING": 118, "MANUAL_ONLY": 14}

## 返回工资快速结算创建入口开关：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /union/getAnchorApplyRecord
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / newman
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /union/getAnchorApplyRecord
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /union/getAnchorApplyRecord

### 预期结果
- 根据接口资料样例验证核心成功路径

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。

## 返回工资快速结算创建入口开关：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /union/getAnchorApplyRecord
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /union/getAnchorApplyRecord
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /union/getAnchorApplyRecord

### 预期结果
- 根据接口资料样例验证核心成功路径

### 分级原因
- 写操作/状态变更用例缺少DB或Redis证据规则。

## 进入入口时查询可结算额度：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /userserv/salary/trade/quota
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：data_constraint_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /userserv/salary/trade/quota
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/quota
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_quota_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：data_constraint_exception。

## 按国家和币种选择代理用户：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /userserv/salary/trade/agents
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：data_constraint_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /userserv/salary/trade/agents
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agents
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agents_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：data_constraint_exception。

## 提交收款信息并创建待代理处理订单：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/order/create
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：applicant_uid, order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/order/create
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/create
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status, uid 符合规则 salary_trade_order_created。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_create_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：applicant_uid, order_no, proxy_uid。

## 查看本人快速结算订单列表：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /userserv/salary/trade/order/page
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / newman
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /userserv/salary/trade/order/page
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/order/page
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 order_no 符合规则 salary_trade_get_userserv_salary_trade_order_page_anchor_salary_trade_order。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 查看本人订单详情：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /userserv/salary/trade/order/detail
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / newman
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /userserv/salary/trade/order/detail
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/order/detail
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 order_no 符合规则 salary_trade_get_userserv_salary_trade_order_detail_anchor_salary_trade_order。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 取消待代理处理订单：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/order/cancel
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/order/cancel
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/cancel
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 cancel_reason, status 符合规则 salary_trade_cancelled。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_cancel_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：order_no, proxy_uid。

## 确认已收到代理转账：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/order/confirm
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/order/confirm
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/confirm
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 confirmed_time, finished_time, status 符合规则 salary_trade_finished。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_confirm_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：order_no, proxy_uid。
- 异常来源：state_machine_exception。

## 待确认收款时提交投诉：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/order/appeal
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：applicant_uid, order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/order/appeal
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/appeal
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no, uid 符合规则 salary_trade_appeal_evidence_created。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 evidence_type, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_appeal_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：applicant_uid, order_no。
- 异常来源：state_machine_exception。

## 补充上传本人订单凭证：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/evidence/upload
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/evidence/upload
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/evidence/upload
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no 符合规则 salary_trade_post_userserv_salary_trade_evidence_upload_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 查看本人订单凭证：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /userserv/salary/trade/evidence/list
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / newman
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /userserv/salary/trade/evidence/list
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/evidence/list
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no 符合规则 salary_trade_get_userserv_salary_trade_evidence_list_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 查看本人订单流转记录：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /userserv/salary/trade/logs
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / newman
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /userserv/salary/trade/logs
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/logs
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_logs_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 查看自己的交易公告编辑页信息：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /userserv/salary/trade/agent/notice
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / newman
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /userserv/salary/trade/agent/notice
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agent/notice
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agent_notice_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 保存自己的交易公告：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/agent/notice/save
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/agent/notice/save
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/notice/save
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_notice_save_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 查看可处理或已承接的订单列表：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /userserv/salary/trade/agent/order/page
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / newman
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /userserv/salary/trade/agent/order/page
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agent/order/page
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agent_order_page_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 查看代理侧订单详情：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /userserv/salary/trade/agent/order/detail
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / newman
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /userserv/salary/trade/agent/order/detail
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agent/order/detail
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agent_order_detail_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 接受待代理处理订单：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/agent/order/accept
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/agent/order/accept
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/accept
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_accept_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 拒绝待代理处理订单：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/agent/order/reject
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/agent/order/reject
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/reject
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_reject_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 标记已完成线下转账：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/agent/order/paid
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/agent/order/paid
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/paid
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_paid_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：state_machine_exception。

## 待确认收款时提交投诉：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/agent/order/appeal
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/agent/order/appeal
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/appeal
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_appeal_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：state_machine_exception。

## 补充上传付款或投诉凭证：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/agent/evidence/upload
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/agent/evidence/upload
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/evidence/upload
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 agent_uid, evidence_type 符合规则 salary_trade_post_userserv_salary_trade_agent_evidence_upload_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：state_machine_exception。

## 返回工资快速结算创建入口开关：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /union/getAnchorApplyRecord
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / newman
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /union/getAnchorApplyRecord
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /union/getAnchorApplyRecord

### 预期结果
- 根据接口资料样例验证核心成功路径

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。

## 返回工资快速结算创建入口开关：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /union/getAnchorApplyRecord
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /union/getAnchorApplyRecord
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /union/getAnchorApplyRecord

### 预期结果
- 根据接口资料样例验证核心成功路径

### 分级原因
- 写操作/状态变更用例缺少DB或Redis证据规则。

## 进入入口时查询可结算额度：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /userserv/salary/trade/quota
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：data_constraint_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /userserv/salary/trade/quota
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/quota
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_quota_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：data_constraint_exception。

## 按国家和币种选择代理用户：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /userserv/salary/trade/agents
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：data_constraint_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /userserv/salary/trade/agents
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agents
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agents_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：data_constraint_exception。

## 提交收款信息并创建待代理处理订单：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/order/create
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：applicant_uid, order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/order/create
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/create
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status, uid 符合规则 salary_trade_order_created。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_create_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：applicant_uid, order_no, proxy_uid。

## 查看本人快速结算订单列表：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /userserv/salary/trade/order/page
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / newman
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /userserv/salary/trade/order/page
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/order/page
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 order_no 符合规则 salary_trade_get_userserv_salary_trade_order_page_anchor_salary_trade_order。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 查看本人订单详情：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /userserv/salary/trade/order/detail
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / newman
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /userserv/salary/trade/order/detail
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/order/detail
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 order_no 符合规则 salary_trade_get_userserv_salary_trade_order_detail_anchor_salary_trade_order。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 取消待代理处理订单：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/order/cancel
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/order/cancel
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/cancel
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 cancel_reason, status 符合规则 salary_trade_cancelled。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_cancel_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：order_no, proxy_uid。

## 确认已收到代理转账：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/order/confirm
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/order/confirm
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/confirm
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 confirmed_time, finished_time, status 符合规则 salary_trade_finished。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_confirm_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：order_no, proxy_uid。
- 异常来源：state_machine_exception。

## 待确认收款时提交投诉：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/order/appeal
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：applicant_uid, order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/order/appeal
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/appeal
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no, uid 符合规则 salary_trade_appeal_evidence_created。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 evidence_type, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_appeal_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：applicant_uid, order_no。
- 异常来源：state_machine_exception。

## 补充上传本人订单凭证：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/evidence/upload
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/evidence/upload
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/evidence/upload
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no 符合规则 salary_trade_post_userserv_salary_trade_evidence_upload_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 查看本人订单凭证：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /userserv/salary/trade/evidence/list
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / newman
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /userserv/salary/trade/evidence/list
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/evidence/list
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no 符合规则 salary_trade_get_userserv_salary_trade_evidence_list_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 查看本人订单流转记录：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /userserv/salary/trade/logs
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / newman
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /userserv/salary/trade/logs
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/logs
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_logs_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 查看自己的交易公告编辑页信息：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /userserv/salary/trade/agent/notice
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / newman
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /userserv/salary/trade/agent/notice
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agent/notice
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agent_notice_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 保存自己的交易公告：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/agent/notice/save
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/agent/notice/save
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/notice/save
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_notice_save_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 查看可处理或已承接的订单列表：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /userserv/salary/trade/agent/order/page
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / newman
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /userserv/salary/trade/agent/order/page
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agent/order/page
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agent_order_page_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 查看代理侧订单详情：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /userserv/salary/trade/agent/order/detail
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / newman
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 GET /userserv/salary/trade/agent/order/detail
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agent/order/detail
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agent_order_detail_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 接受待代理处理订单：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/agent/order/accept
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/agent/order/accept
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/accept
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_accept_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 拒绝待代理处理订单：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/agent/order/reject
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/agent/order/reject
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/reject
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_reject_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 标记已完成线下转账：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/agent/order/paid
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/agent/order/paid
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/paid
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_paid_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：state_machine_exception。

## 待确认收款时提交投诉：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/agent/order/appeal
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/agent/order/appeal
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/appeal
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_appeal_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：state_machine_exception。

## 补充上传付款或投诉凭证：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：POST /userserv/salary/trade/agent/evidence/upload
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备功能场景数据
2. 发送 POST /userserv/salary/trade/agent/evidence/upload
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/evidence/upload
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 根据接口资料样例验证核心成功路径
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 agent_uid, evidence_type 符合规则 salary_trade_post_userserv_salary_trade_agent_evidence_upload_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：state_machine_exception。

## 返回工资快速结算创建入口开关：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /union/getAnchorApplyRecord
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / newman
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /union/getAnchorApplyRecord
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /union/getAnchorApplyRecord

### 预期结果
- 验证必填字段校验：

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 异常来源：api_contract_exception。

## 返回工资快速结算创建入口开关：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /union/getAnchorApplyRecord
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / newman
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /union/getAnchorApplyRecord
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /union/getAnchorApplyRecord

### 预期结果
- 验证长度、数值、类型和空值边界

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 异常来源：api_contract_exception。

## 返回工资快速结算创建入口开关：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /union/getAnchorApplyRecord
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /union/getAnchorApplyRecord
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /union/getAnchorApplyRecord

### 预期结果
- 验证必填字段校验：

### 分级原因
- 写操作/状态变更用例缺少DB或Redis证据规则。
- 异常来源：api_contract_exception。

## 返回工资快速结算创建入口开关：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /union/getAnchorApplyRecord
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /union/getAnchorApplyRecord
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /union/getAnchorApplyRecord

### 预期结果
- 验证长度、数值、类型和空值边界

### 分级原因
- 写操作/状态变更用例缺少DB或Redis证据规则。
- 异常来源：api_contract_exception。

## 返回工资快速结算创建入口开关：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /union/getAnchorApplyRecord
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /union/getAnchorApplyRecord
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /union/getAnchorApplyRecord

### 预期结果
- 验证重复操作不会破坏数据一致性

### 分级原因
- 写操作/状态变更用例缺少DB或Redis证据规则。

## 进入入口时查询可结算额度：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/quota
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, data_constraint_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /userserv/salary/trade/quota
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/quota
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_quota_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, data_constraint_exception。

## 进入入口时查询可结算额度：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/quota
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, data_constraint_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /userserv/salary/trade/quota
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/quota
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_quota_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, data_constraint_exception。

## 按国家和币种选择代理用户：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/agents
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, data_constraint_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /userserv/salary/trade/agents
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agents
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agents_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, data_constraint_exception。

## 按国家和币种选择代理用户：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/agents
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, data_constraint_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /userserv/salary/trade/agents
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agents
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agents_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, data_constraint_exception。

## 提交收款信息并创建待代理处理订单：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/create
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：applicant_uid, order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/order/create
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/create
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status, uid 符合规则 salary_trade_order_created。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_create_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：applicant_uid, order_no, proxy_uid。
- 异常来源：api_contract_exception。

## 提交收款信息并创建待代理处理订单：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/create
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：applicant_uid, order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/order/create
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/create
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status, uid 符合规则 salary_trade_order_created。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_create_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：applicant_uid, order_no, proxy_uid。
- 异常来源：api_contract_exception。

## 提交收款信息并创建待代理处理订单：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/create
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：applicant_uid, order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/order/create
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/create
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status, uid 符合规则 salary_trade_order_created。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_create_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：applicant_uid, order_no, proxy_uid。

## 查看本人快速结算订单列表：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/order/page
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /userserv/salary/trade/order/page
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/order/page
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 order_no 符合规则 salary_trade_get_userserv_salary_trade_order_page_anchor_salary_trade_order。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看本人快速结算订单列表：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/order/page
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /userserv/salary/trade/order/page
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/order/page
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 order_no 符合规则 salary_trade_get_userserv_salary_trade_order_page_anchor_salary_trade_order。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看本人订单详情：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/order/detail
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /userserv/salary/trade/order/detail
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/order/detail
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 order_no 符合规则 salary_trade_get_userserv_salary_trade_order_detail_anchor_salary_trade_order。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看本人订单详情：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/order/detail
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /userserv/salary/trade/order/detail
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/order/detail
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 order_no 符合规则 salary_trade_get_userserv_salary_trade_order_detail_anchor_salary_trade_order。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 取消待代理处理订单：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/cancel
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/order/cancel
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/cancel
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 cancel_reason, status 符合规则 salary_trade_cancelled。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_cancel_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：order_no, proxy_uid。
- 异常来源：api_contract_exception。

## 取消待代理处理订单：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/cancel
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/order/cancel
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/cancel
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 cancel_reason, status 符合规则 salary_trade_cancelled。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_cancel_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：order_no, proxy_uid。
- 异常来源：api_contract_exception。

## 取消待代理处理订单：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/cancel
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/order/cancel
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/cancel
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 cancel_reason, status 符合规则 salary_trade_cancelled。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_cancel_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：order_no, proxy_uid。

## 确认已收到代理转账：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/confirm
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/order/confirm
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/confirm
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 confirmed_time, finished_time, status 符合规则 salary_trade_finished。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_confirm_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：order_no, proxy_uid。
- 异常来源：api_contract_exception, state_machine_exception。

## 确认已收到代理转账：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/confirm
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/order/confirm
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/confirm
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 confirmed_time, finished_time, status 符合规则 salary_trade_finished。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_confirm_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：order_no, proxy_uid。
- 异常来源：api_contract_exception, state_machine_exception。

## 确认已收到代理转账：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/confirm
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/order/confirm
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/confirm
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 confirmed_time, finished_time, status 符合规则 salary_trade_finished。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_confirm_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：order_no, proxy_uid。
- 异常来源：state_machine_exception。

## 待确认收款时提交投诉：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/appeal
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：applicant_uid, order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/order/appeal
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/appeal
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no, uid 符合规则 salary_trade_appeal_evidence_created。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 evidence_type, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_appeal_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：applicant_uid, order_no。
- 异常来源：api_contract_exception, state_machine_exception。

## 待确认收款时提交投诉：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/appeal
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：applicant_uid, order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/order/appeal
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/appeal
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no, uid 符合规则 salary_trade_appeal_evidence_created。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 evidence_type, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_appeal_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：applicant_uid, order_no。
- 异常来源：api_contract_exception, state_machine_exception。

## 待确认收款时提交投诉：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/appeal
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：applicant_uid, order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/order/appeal
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/appeal
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no, uid 符合规则 salary_trade_appeal_evidence_created。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 evidence_type, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_appeal_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：applicant_uid, order_no。
- 异常来源：state_machine_exception。

## 补充上传本人订单凭证：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/evidence/upload
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/evidence/upload
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/evidence/upload
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no 符合规则 salary_trade_post_userserv_salary_trade_evidence_upload_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 补充上传本人订单凭证：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/evidence/upload
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/evidence/upload
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/evidence/upload
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no 符合规则 salary_trade_post_userserv_salary_trade_evidence_upload_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 补充上传本人订单凭证：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/evidence/upload
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/evidence/upload
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/evidence/upload
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no 符合规则 salary_trade_post_userserv_salary_trade_evidence_upload_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 查看本人订单凭证：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/evidence/list
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /userserv/salary/trade/evidence/list
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/evidence/list
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no 符合规则 salary_trade_get_userserv_salary_trade_evidence_list_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看本人订单凭证：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/evidence/list
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /userserv/salary/trade/evidence/list
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/evidence/list
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no 符合规则 salary_trade_get_userserv_salary_trade_evidence_list_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看本人订单流转记录：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/logs
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /userserv/salary/trade/logs
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/logs
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_logs_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看本人订单流转记录：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/logs
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /userserv/salary/trade/logs
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/logs
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_logs_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看自己的交易公告编辑页信息：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/agent/notice
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /userserv/salary/trade/agent/notice
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agent/notice
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agent_notice_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看自己的交易公告编辑页信息：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/agent/notice
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /userserv/salary/trade/agent/notice
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agent/notice
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agent_notice_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 保存自己的交易公告：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/notice/save
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/agent/notice/save
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/notice/save
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_notice_save_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 保存自己的交易公告：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/notice/save
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/agent/notice/save
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/notice/save
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_notice_save_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 保存自己的交易公告：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/notice/save
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/agent/notice/save
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/notice/save
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_notice_save_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 查看可处理或已承接的订单列表：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/agent/order/page
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /userserv/salary/trade/agent/order/page
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agent/order/page
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agent_order_page_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看可处理或已承接的订单列表：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/agent/order/page
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /userserv/salary/trade/agent/order/page
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agent/order/page
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agent_order_page_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看代理侧订单详情：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/agent/order/detail
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /userserv/salary/trade/agent/order/detail
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agent/order/detail
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agent_order_detail_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看代理侧订单详情：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/agent/order/detail
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /userserv/salary/trade/agent/order/detail
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agent/order/detail
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agent_order_detail_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 接受待代理处理订单：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/accept
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/agent/order/accept
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/accept
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_accept_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 接受待代理处理订单：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/accept
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/agent/order/accept
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/accept
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_accept_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 接受待代理处理订单：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/accept
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/agent/order/accept
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/accept
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_accept_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 拒绝待代理处理订单：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/reject
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/agent/order/reject
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/reject
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_reject_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 拒绝待代理处理订单：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/reject
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/agent/order/reject
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/reject
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_reject_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 拒绝待代理处理订单：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/reject
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/agent/order/reject
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/reject
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_reject_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 标记已完成线下转账：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/paid
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/agent/order/paid
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/paid
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_paid_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, state_machine_exception。

## 标记已完成线下转账：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/paid
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/agent/order/paid
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/paid
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_paid_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, state_machine_exception。

## 标记已完成线下转账：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/paid
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/agent/order/paid
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/paid
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_paid_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：state_machine_exception。

## 待确认收款时提交投诉：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/appeal
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/agent/order/appeal
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/appeal
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_appeal_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, state_machine_exception。

## 待确认收款时提交投诉：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/appeal
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/agent/order/appeal
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/appeal
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_appeal_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, state_machine_exception。

## 待确认收款时提交投诉：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/appeal
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/agent/order/appeal
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/appeal
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_appeal_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：state_machine_exception。

## 补充上传付款或投诉凭证：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/evidence/upload
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/agent/evidence/upload
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/evidence/upload
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 agent_uid, evidence_type 符合规则 salary_trade_post_userserv_salary_trade_agent_evidence_upload_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, state_machine_exception。

## 补充上传付款或投诉凭证：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/evidence/upload
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/agent/evidence/upload
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/evidence/upload
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 agent_uid, evidence_type 符合规则 salary_trade_post_userserv_salary_trade_agent_evidence_upload_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, state_machine_exception。

## 补充上传付款或投诉凭证：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/evidence/upload
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/agent/evidence/upload
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/evidence/upload
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 agent_uid, evidence_type 符合规则 salary_trade_post_userserv_salary_trade_agent_evidence_upload_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：state_machine_exception。

## 业务规则验证：公共业务规则、状态枚举和状态流转见 [接口文档索引与业务总览](00-工资代理快速结算接口文档索引与业务总览.

- 优先级：P1
- 场景类型：设计用例
- 接口：- 
- 接口字段：-
- 质量分级：MANUAL_ONLY
- 自动化覆盖：MANUAL_ONLY / manual
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 构造满足规则的场景
2. 构造违反规则的场景
3. 对比系统行为

### 预期结果
- 系统行为与规则一致：公共业务规则、状态枚举和状态流转见 [接口文档索引与业务总览](00-工资代理快速结算接口文档索引与业务总览.

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：state_machine_exception。

## 业务规则验证：即使返回 `true`，申请用户创建订单时仍需通过公会关系、工资额度、代理白名单、国家/币种和工资发放账号余额等校验。

- 优先级：P1
- 场景类型：设计用例
- 接口：- 
- 接口字段：-
- 质量分级：MANUAL_ONLY
- 自动化覆盖：MANUAL_ONLY / manual
- 异常来源：data_constraint_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 构造满足规则的场景
2. 构造违反规则的场景
3. 对比系统行为
4. 执行后按证据规则只读查询数据库。

### 预期结果
- 系统行为与规则一致：即使返回 `true`，申请用户创建订单时仍需通过公会关系、工资额度、代理白名单、国家/币种和工资发放账号余额等校验。
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_case_anchor_salary_trade_agent_whitelist。

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：data_constraint_exception。

## 业务规则验证：不传时服务端使用当前申请用户所属公会查询工资额度 | - 说明：返回可申请工资、进行中冻结工资、最低金额、金币倍数，以及

- 优先级：P1
- 场景类型：设计用例
- 接口：- 
- 接口字段：-
- 质量分级：MANUAL_ONLY
- 自动化覆盖：MANUAL_ONLY / manual
- 异常来源：data_constraint_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 构造满足规则的场景
2. 构造违反规则的场景
3. 对比系统行为

### 预期结果
- 系统行为与规则一致：不传时服务端使用当前申请用户所属公会查询工资额度 | - 说明：返回可申请工资、进行中冻结工资、最低金额、金币倍数，以及服务端按国家汇总的可收款币种。

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：data_constraint_exception。

## 业务规则验证：availableSalary | int64 | 当前可申请工资的整数兼容值，由精确金额截取整数部分得到 | | da

- 优先级：P1
- 场景类型：设计用例
- 接口：- 
- 接口字段：-
- 质量分级：MANUAL_ONLY
- 自动化覆盖：MANUAL_ONLY / manual
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 构造满足规则的场景
2. 构造违反规则的场景
3. 对比系统行为

### 预期结果
- 系统行为与规则一致：availableSalary | int64 | 当前可申请工资的整数兼容值，由精确金额截取整数部分得到 | | data.

### 分级原因
- 缺少可直接执行的接口 method/path。

## 业务规则验证：availableSalaryAmount | float64 | 当前可申请工资的精确金额，单位 USD | | da

- 优先级：P1
- 场景类型：设计用例
- 接口：- 
- 接口字段：-
- 质量分级：MANUAL_ONLY
- 自动化覆盖：MANUAL_ONLY / manual
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 构造满足规则的场景
2. 构造违反规则的场景
3. 对比系统行为

### 预期结果
- 系统行为与规则一致：availableSalaryAmount | float64 | 当前可申请工资的精确金额，单位 USD | | data.

### 分级原因
- 缺少可直接执行的接口 method/path。

## 业务规则验证：processingSalary | float64 | 当前进行中订单冻结的工资金额，单位 USD | | data.

- 优先级：P1
- 场景类型：设计用例
- 接口：- 
- 接口字段：-
- 质量分级：MANUAL_ONLY
- 自动化覆盖：MANUAL_ONLY / manual
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 构造满足规则的场景
2. 构造违反规则的场景
3. 对比系统行为

### 预期结果
- 系统行为与规则一致：processingSalary | float64 | 当前进行中订单冻结的工资金额，单位 USD | | data.

### 分级原因
- 缺少可直接执行的接口 method/path。

## 业务规则验证：minApplyAmount | float64 | 单笔最低申请工资金额，单位 USD，当前为 50 | | data

- 优先级：P1
- 场景类型：设计用例
- 接口：- 
- 接口字段：-
- 质量分级：MANUAL_ONLY
- 自动化覆盖：MANUAL_ONLY / manual
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 构造满足规则的场景
2. 构造违反规则的场景
3. 对比系统行为

### 预期结果
- 系统行为与规则一致：minApplyAmount | float64 | 单笔最低申请工资金额，单位 USD，当前为 50 | | data.

### 分级原因
- 缺少可直接执行的接口 method/path。

## 返回工资快速结算创建入口开关：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /union/getAnchorApplyRecord
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / newman
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /union/getAnchorApplyRecord
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /union/getAnchorApplyRecord

### 预期结果
- 验证必填字段校验：

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 异常来源：api_contract_exception。

## 返回工资快速结算创建入口开关：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /union/getAnchorApplyRecord
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / newman
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /union/getAnchorApplyRecord
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /union/getAnchorApplyRecord

### 预期结果
- 验证长度、数值、类型和空值边界

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 异常来源：api_contract_exception。

## 返回工资快速结算创建入口开关：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /union/getAnchorApplyRecord
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /union/getAnchorApplyRecord
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /union/getAnchorApplyRecord

### 预期结果
- 验证必填字段校验：

### 分级原因
- 写操作/状态变更用例缺少DB或Redis证据规则。
- 异常来源：api_contract_exception。

## 返回工资快速结算创建入口开关：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /union/getAnchorApplyRecord
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /union/getAnchorApplyRecord
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /union/getAnchorApplyRecord

### 预期结果
- 验证长度、数值、类型和空值边界

### 分级原因
- 写操作/状态变更用例缺少DB或Redis证据规则。
- 异常来源：api_contract_exception。

## 返回工资快速结算创建入口开关：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /union/getAnchorApplyRecord
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /union/getAnchorApplyRecord
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /union/getAnchorApplyRecord

### 预期结果
- 验证重复操作不会破坏数据一致性

### 分级原因
- 写操作/状态变更用例缺少DB或Redis证据规则。

## 进入入口时查询可结算额度：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/quota
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, data_constraint_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /userserv/salary/trade/quota
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/quota
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_quota_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, data_constraint_exception。

## 进入入口时查询可结算额度：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/quota
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, data_constraint_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /userserv/salary/trade/quota
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/quota
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_quota_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, data_constraint_exception。

## 按国家和币种选择代理用户：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/agents
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, data_constraint_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /userserv/salary/trade/agents
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agents
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agents_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, data_constraint_exception。

## 按国家和币种选择代理用户：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/agents
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, data_constraint_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /userserv/salary/trade/agents
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agents
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agents_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, data_constraint_exception。

## 提交收款信息并创建待代理处理订单：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/create
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：applicant_uid, order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/order/create
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/create
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status, uid 符合规则 salary_trade_order_created。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_create_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：applicant_uid, order_no, proxy_uid。
- 异常来源：api_contract_exception。

## 提交收款信息并创建待代理处理订单：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/create
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：applicant_uid, order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/order/create
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/create
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status, uid 符合规则 salary_trade_order_created。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_create_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：applicant_uid, order_no, proxy_uid。
- 异常来源：api_contract_exception。

## 提交收款信息并创建待代理处理订单：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/create
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：applicant_uid, order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/order/create
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/create
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status, uid 符合规则 salary_trade_order_created。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_create_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：applicant_uid, order_no, proxy_uid。

## 查看本人快速结算订单列表：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/order/page
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /userserv/salary/trade/order/page
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/order/page
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 order_no 符合规则 salary_trade_get_userserv_salary_trade_order_page_anchor_salary_trade_order。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看本人快速结算订单列表：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/order/page
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /userserv/salary/trade/order/page
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/order/page
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 order_no 符合规则 salary_trade_get_userserv_salary_trade_order_page_anchor_salary_trade_order。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看本人订单详情：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/order/detail
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /userserv/salary/trade/order/detail
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/order/detail
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 order_no 符合规则 salary_trade_get_userserv_salary_trade_order_detail_anchor_salary_trade_order。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看本人订单详情：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/order/detail
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /userserv/salary/trade/order/detail
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/order/detail
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 order_no 符合规则 salary_trade_get_userserv_salary_trade_order_detail_anchor_salary_trade_order。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 取消待代理处理订单：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/cancel
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/order/cancel
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/cancel
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 cancel_reason, status 符合规则 salary_trade_cancelled。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_cancel_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：order_no, proxy_uid。
- 异常来源：api_contract_exception。

## 取消待代理处理订单：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/cancel
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/order/cancel
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/cancel
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 cancel_reason, status 符合规则 salary_trade_cancelled。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_cancel_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：order_no, proxy_uid。
- 异常来源：api_contract_exception。

## 取消待代理处理订单：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/cancel
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/order/cancel
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/cancel
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 cancel_reason, status 符合规则 salary_trade_cancelled。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_cancel_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：order_no, proxy_uid。

## 确认已收到代理转账：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/confirm
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/order/confirm
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/confirm
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 confirmed_time, finished_time, status 符合规则 salary_trade_finished。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_confirm_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：order_no, proxy_uid。
- 异常来源：api_contract_exception, state_machine_exception。

## 确认已收到代理转账：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/confirm
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/order/confirm
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/confirm
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 confirmed_time, finished_time, status 符合规则 salary_trade_finished。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_confirm_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：order_no, proxy_uid。
- 异常来源：api_contract_exception, state_machine_exception。

## 确认已收到代理转账：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/confirm
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/order/confirm
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/confirm
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 confirmed_time, finished_time, status 符合规则 salary_trade_finished。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 agent_uid, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_confirm_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：order_no, proxy_uid。
- 异常来源：state_machine_exception。

## 待确认收款时提交投诉：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/appeal
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：applicant_uid, order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/order/appeal
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/appeal
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no, uid 符合规则 salary_trade_appeal_evidence_created。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 evidence_type, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_appeal_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：applicant_uid, order_no。
- 异常来源：api_contract_exception, state_machine_exception。

## 待确认收款时提交投诉：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/appeal
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：applicant_uid, order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/order/appeal
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/appeal
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no, uid 符合规则 salary_trade_appeal_evidence_created。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 evidence_type, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_appeal_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：applicant_uid, order_no。
- 异常来源：api_contract_exception, state_machine_exception。

## 待确认收款时提交投诉：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/order/appeal
- 接口字段：-
- 质量分级：READY
- 自动化覆盖：AUTO_READY / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：applicant_uid, order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/order/appeal
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/order/appeal
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no, uid 符合规则 salary_trade_appeal_evidence_created。
- DB校验：anchor_salary_trade_order WHERE order_no = ${order_no}，字段 evidence_type, order_no, status 符合规则 salary_trade_post_userserv_salary_trade_order_appeal_anchor_salary_trade_order。

### 分级原因
- 接口、变量和证据条件满足当前自动化生成要求。
- 需要运行时提供变量：applicant_uid, order_no。
- 异常来源：state_machine_exception。

## 补充上传本人订单凭证：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/evidence/upload
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/evidence/upload
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/evidence/upload
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no 符合规则 salary_trade_post_userserv_salary_trade_evidence_upload_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 补充上传本人订单凭证：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/evidence/upload
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/evidence/upload
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/evidence/upload
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no 符合规则 salary_trade_post_userserv_salary_trade_evidence_upload_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 补充上传本人订单凭证：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/evidence/upload
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/evidence/upload
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/evidence/upload
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no 符合规则 salary_trade_post_userserv_salary_trade_evidence_upload_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 查看本人订单凭证：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/evidence/list
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /userserv/salary/trade/evidence/list
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/evidence/list
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no 符合规则 salary_trade_get_userserv_salary_trade_evidence_list_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看本人订单凭证：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/evidence/list
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /userserv/salary/trade/evidence/list
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/evidence/list
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 evidence_type, order_no 符合规则 salary_trade_get_userserv_salary_trade_evidence_list_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看本人订单流转记录：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/logs
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /userserv/salary/trade/logs
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/logs
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_logs_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看本人订单流转记录：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/logs
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /userserv/salary/trade/logs
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/logs
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_logs_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看自己的交易公告编辑页信息：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/agent/notice
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /userserv/salary/trade/agent/notice
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agent/notice
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agent_notice_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看自己的交易公告编辑页信息：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/agent/notice
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /userserv/salary/trade/agent/notice
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agent/notice
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agent_notice_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 保存自己的交易公告：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/notice/save
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/agent/notice/save
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/notice/save
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_notice_save_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 保存自己的交易公告：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/notice/save
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/agent/notice/save
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/notice/save
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_notice_save_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 保存自己的交易公告：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/notice/save
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/agent/notice/save
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/notice/save
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_notice_save_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 查看可处理或已承接的订单列表：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/agent/order/page
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /userserv/salary/trade/agent/order/page
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agent/order/page
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agent_order_page_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看可处理或已承接的订单列表：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/agent/order/page
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /userserv/salary/trade/agent/order/page
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agent/order/page
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agent_order_page_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看代理侧订单详情：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/agent/order/detail
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 GET /userserv/salary/trade/agent/order/detail
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agent/order/detail
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agent_order_detail_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 查看代理侧订单详情：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：GET /userserv/salary/trade/agent/order/detail
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 GET /userserv/salary/trade/agent/order/detail
3. 检查状态码、响应结构和业务结果
4. 调用接口：GET /userserv/salary/trade/agent/order/detail
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_get_userserv_salary_trade_agent_order_detail_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 接受待代理处理订单：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/accept
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/agent/order/accept
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/accept
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_accept_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 接受待代理处理订单：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/accept
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/agent/order/accept
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/accept
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_accept_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 接受待代理处理订单：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/accept
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/agent/order/accept
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/accept
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_accept_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 拒绝待代理处理订单：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/reject
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/agent/order/reject
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/reject
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_reject_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 拒绝待代理处理订单：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/reject
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/agent/order/reject
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/reject
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_reject_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception。

## 拒绝待代理处理订单：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/reject
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/agent/order/reject
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/reject
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_reject_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。

## 标记已完成线下转账：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/paid
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/agent/order/paid
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/paid
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_paid_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, state_machine_exception。

## 标记已完成线下转账：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/paid
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/agent/order/paid
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/paid
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_paid_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, state_machine_exception。

## 标记已完成线下转账：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/paid
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/agent/order/paid
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/paid
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_paid_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：state_machine_exception。

## 待确认收款时提交投诉：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/appeal
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/agent/order/appeal
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/appeal
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_appeal_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, state_machine_exception。

## 待确认收款时提交投诉：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/appeal
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/agent/order/appeal
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/appeal
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_appeal_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, state_machine_exception。

## 待确认收款时提交投诉：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/order/appeal
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：country_code, currency, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/agent/order/appeal
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/order/appeal
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_agent_whitelist WHERE uid = ${proxy_uid}，字段 country_code, status, support_currencies, uid 符合规则 salary_trade_post_userserv_salary_trade_agent_order_appeal_anchor_salary_trade_agent_whitelist。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：state_machine_exception。

## 补充上传付款或投诉凭证：缺失必填参数

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/evidence/upload
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备异常场景数据
2. 发送 POST /userserv/salary/trade/agent/evidence/upload
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/evidence/upload
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证必填字段校验：
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 agent_uid, evidence_type 符合规则 salary_trade_post_userserv_salary_trade_agent_evidence_upload_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, state_machine_exception。

## 补充上传付款或投诉凭证：字段边界与类型错误

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/evidence/upload
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：api_contract_exception, state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备边界场景数据
2. 发送 POST /userserv/salary/trade/agent/evidence/upload
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/evidence/upload
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证长度、数值、类型和空值边界
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 agent_uid, evidence_type 符合规则 salary_trade_post_userserv_salary_trade_agent_evidence_upload_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：api_contract_exception, state_machine_exception。

## 补充上传付款或投诉凭证：重复提交与幂等性

- 优先级：P1
- 场景类型：接口契约
- 接口：POST /userserv/salary/trade/agent/evidence/upload
- 接口字段：-
- 质量分级：NEEDS_EVIDENCE_REVIEW
- 自动化覆盖：SCRIPTABLE_EVIDENCE_PENDING / jmeter
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：order_no, proxy_uid
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 准备可靠性场景数据
2. 发送 POST /userserv/salary/trade/agent/evidence/upload
3. 检查状态码、响应结构和业务结果
4. 调用接口：POST /userserv/salary/trade/agent/evidence/upload
5. 执行后按证据规则只读查询数据库。

### 预期结果
- 验证重复操作不会破坏数据一致性
- DB校验：anchor_salary_trade_evidence WHERE order_no = ${order_no}，字段 agent_uid, evidence_type 符合规则 salary_trade_post_userserv_salary_trade_agent_evidence_upload_anchor_salary_trade_evidence。

### 分级原因
- 仅命中候选证据规则，需要采纳后再作为正式校验。
- 异常来源：state_machine_exception。

## 业务规则验证：公共业务规则、状态枚举和状态流转见 [接口文档索引与业务总览](00-工资代理快速结算接口文档索引与业务总览.

- 优先级：P1
- 场景类型：设计用例
- 接口：- 
- 接口字段：-
- 质量分级：MANUAL_ONLY
- 自动化覆盖：MANUAL_ONLY / manual
- 异常来源：state_machine_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 构造满足规则的场景
2. 构造违反规则的场景
3. 对比系统行为

### 预期结果
- 系统行为与规则一致：公共业务规则、状态枚举和状态流转见 [接口文档索引与业务总览](00-工资代理快速结算接口文档索引与业务总览.

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：state_machine_exception。

## 业务规则验证：即使返回 `true`，申请用户创建订单时仍需通过公会关系、工资额度、代理白名单、国家/币种和工资发放账号余额等校验。

- 优先级：P1
- 场景类型：设计用例
- 接口：- 
- 接口字段：-
- 质量分级：MANUAL_ONLY
- 自动化覆盖：MANUAL_ONLY / manual
- 异常来源：data_constraint_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 构造满足规则的场景
2. 构造违反规则的场景
3. 对比系统行为

### 预期结果
- 系统行为与规则一致：即使返回 `true`，申请用户创建订单时仍需通过公会关系、工资额度、代理白名单、国家/币种和工资发放账号余额等校验。

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：data_constraint_exception。

## 业务规则验证：不传时服务端使用当前申请用户所属公会查询工资额度 | - 说明：返回可申请工资、进行中冻结工资、最低金额、金币倍数，以及

- 优先级：P1
- 场景类型：设计用例
- 接口：- 
- 接口字段：-
- 质量分级：MANUAL_ONLY
- 自动化覆盖：MANUAL_ONLY / manual
- 异常来源：data_constraint_exception

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 构造满足规则的场景
2. 构造违反规则的场景
3. 对比系统行为

### 预期结果
- 系统行为与规则一致：不传时服务端使用当前申请用户所属公会查询工资额度 | - 说明：返回可申请工资、进行中冻结工资、最低金额、金币倍数，以及服务端按国家汇总的可收款币种。

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：data_constraint_exception。

## 业务规则验证：availableSalary | int64 | 当前可申请工资的整数兼容值，由精确金额截取整数部分得到 | | da

- 优先级：P1
- 场景类型：设计用例
- 接口：- 
- 接口字段：-
- 质量分级：MANUAL_ONLY
- 自动化覆盖：MANUAL_ONLY / manual
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 构造满足规则的场景
2. 构造违反规则的场景
3. 对比系统行为

### 预期结果
- 系统行为与规则一致：availableSalary | int64 | 当前可申请工资的整数兼容值，由精确金额截取整数部分得到 | | data.

### 分级原因
- 缺少可直接执行的接口 method/path。

## 业务规则验证：availableSalaryAmount | float64 | 当前可申请工资的精确金额，单位 USD | | da

- 优先级：P1
- 场景类型：设计用例
- 接口：- 
- 接口字段：-
- 质量分级：MANUAL_ONLY
- 自动化覆盖：MANUAL_ONLY / manual
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 构造满足规则的场景
2. 构造违反规则的场景
3. 对比系统行为

### 预期结果
- 系统行为与规则一致：availableSalaryAmount | float64 | 当前可申请工资的精确金额，单位 USD | | data.

### 分级原因
- 缺少可直接执行的接口 method/path。

## 业务规则验证：processingSalary | float64 | 当前进行中订单冻结的工资金额，单位 USD | | data.

- 优先级：P1
- 场景类型：设计用例
- 接口：- 
- 接口字段：-
- 质量分级：MANUAL_ONLY
- 自动化覆盖：MANUAL_ONLY / manual
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 构造满足规则的场景
2. 构造违反规则的场景
3. 对比系统行为

### 预期结果
- 系统行为与规则一致：processingSalary | float64 | 当前进行中订单冻结的工资金额，单位 USD | | data.

### 分级原因
- 缺少可直接执行的接口 method/path。

## 业务规则验证：minApplyAmount | float64 | 单笔最低申请工资金额，单位 USD，当前为 50 | | data

- 优先级：P1
- 场景类型：设计用例
- 接口：- 
- 接口字段：-
- 质量分级：MANUAL_ONLY
- 自动化覆盖：MANUAL_ONLY / manual
- 异常来源：-

### 前置条件
- 需求包：工资代理快速结算
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 数据范围：anchor_salary_trade_agent_whitelist, anchor_salary_trade_order, anchor_salary_trade_order_log, anchor_salary_trade_evidence

### 操作步骤
1. 构造满足规则的场景
2. 构造违反规则的场景
3. 对比系统行为

### 预期结果
- 系统行为与规则一致：minApplyAmount | float64 | 单笔最低申请工资金额，单位 USD，当前为 50 | | data.

### 分级原因
- 缺少可直接执行的接口 method/path。
