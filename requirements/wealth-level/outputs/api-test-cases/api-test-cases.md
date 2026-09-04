# Schema驱动接口测试用例

- 接口数：1
- 用例数：23
- 需要人工确认后执行：2
- 测试维度：功能, 响应契约, 参数校验, 等价类, 边界值, 认证授权, 异常处理, 可靠性, 并发, 安全

| 用例ID | 接口 | 方法 | 路径 | 测试维度 | 设计方法 | 等价类 | 用例标题 | 请求变异 | 预期结果 | 工具 | 自动化状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| API-00001 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 功能 | 等价类划分 | valid | 获取财富等级经验及等级权益：有效等价类正常请求 | {"action": "use_valid_baseline"} | 返回成功状态，响应Schema及核心业务结果正确。 | Newman | READY |
| API-00002 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 响应契约 | 契约校验 | valid | 获取财富等级经验及等级权益：响应状态与Schema契约 | {"action": "validate_response_contract"} | HTTP状态、业务码、必填响应字段、字段类型和枚举均符合OpenAPI契约，不泄露未声明敏感字段。 | Newman | READY |
| API-00003 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 异常处理 | 错误推测 | invalid | 获取财富等级经验及等级权益：使用不支持的HTTP方法 | {"action": "use_unsupported_http_method"} | 返回405或明确的业务拒绝，不执行原接口业务写入。 | Newman | READY |
| API-00004 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 参数校验 | 等价类划分 | invalid | 获取财富等级经验及等级权益：缺失必填字段 query.ticket | {"action": "remove", "field": "query.ticket"} | 接口明确拒绝请求，不产生错误业务数据。 | Newman | READY |
| API-00005 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 参数校验 | 等价类划分 | invalid | 获取财富等级经验及等级权益：query.ticket 非法null | {"action": "replace", "field": "query.ticket", "value": null} | 接口拒绝必填且不可为空字段的null值，不产生500或脏数据。 | Newman | READY |
| API-00006 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 边界值 | 边界值分析 | invalid | 获取财富等级经验及等级权益：query.ticket 空值边界 | {"action": "replace", "field": "query.ticket", "value": ""} | 接口按Schema和业务规则接受或明确拒绝，不能产生500。 | Newman | READY |
| API-00007 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 参数校验 | 等价类划分 | invalid | 获取财富等级经验及等级权益：query.ticket 类型错误 | {"action": "replace", "field": "query.ticket", "value": 123456, "expected_type": "string"} | 接口返回参数错误，不产生500和业务脏数据。 | Newman | READY |
| API-00008 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 参数校验 | 等价类划分 | invalid | 获取财富等级经验及等级权益：缺失必填字段 query.uid | {"action": "remove", "field": "query.uid"} | 接口明确拒绝请求，不产生错误业务数据。 | Newman | READY |
| API-00009 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 参数校验 | 等价类划分 | invalid | 获取财富等级经验及等级权益：query.uid 非法null | {"action": "replace", "field": "query.uid", "value": null} | 接口拒绝必填且不可为空字段的null值，不产生500或脏数据。 | Newman | READY |
| API-00010 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 边界值 | 边界值分析 | invalid | 获取财富等级经验及等级权益：query.uid 空值边界 | {"action": "replace", "field": "query.uid", "value": ""} | 接口按Schema和业务规则接受或明确拒绝，不能产生500。 | Newman | READY |
| API-00011 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 参数校验 | 等价类划分 | invalid | 获取财富等级经验及等级权益：query.uid 类型错误 | {"action": "replace", "field": "query.uid", "value": 123456, "expected_type": "string"} | 接口返回参数错误，不产生500和业务脏数据。 | Newman | READY |
| API-00012 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 安全 | 攻击输入 | invalid | 获取财富等级经验及等级权益：query.uid SQL注入字符 | {"action": "replace", "field": "query.uid", "value": "' OR '1'='1' --"} | 接口不执行注入语义，不泄露数据库错误，不绕过鉴权或条件。 | pytest | REVIEW_REQUIRED |
| API-00013 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 安全 | 攻击输入 | invalid | 获取财富等级经验及等级权益：query.uid XSS脚本字符 | {"action": "replace", "field": "query.uid", "value": "<script>alert(1)</script>"} | 响应和持久化数据不得执行脚本，输出应安全编码。 | pytest | REVIEW_REQUIRED |
| API-00014 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 边界值 | 边界值分析 | boundary | 获取财富等级经验及等级权益：query.language 空值边界 | {"action": "replace", "field": "query.language", "value": ""} | 接口按Schema和业务规则接受或明确拒绝，不能产生500。 | Newman | READY |
| API-00015 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 参数校验 | 等价类划分 | invalid | 获取财富等级经验及等级权益：query.language 类型错误 | {"action": "replace", "field": "query.language", "value": 123456, "expected_type": "string"} | 接口返回参数错误，不产生500和业务脏数据。 | Newman | READY |
| API-00016 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 边界值 | 边界值分析 | boundary | 获取财富等级经验及等级权益：query.systemLanguage 空值边界 | {"action": "replace", "field": "query.systemLanguage", "value": ""} | 接口按Schema和业务规则接受或明确拒绝，不能产生500。 | Newman | READY |
| API-00017 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 参数校验 | 等价类划分 | invalid | 获取财富等级经验及等级权益：query.systemLanguage 类型错误 | {"action": "replace", "field": "query.systemLanguage", "value": 123456, "expected_type": "string"} | 接口返回参数错误，不产生500和业务脏数据。 | Newman | READY |
| API-00018 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 边界值 | 边界值分析 | boundary | 获取财富等级经验及等级权益：query.appVersion 空值边界 | {"action": "replace", "field": "query.appVersion", "value": ""} | 接口按Schema和业务规则接受或明确拒绝，不能产生500。 | Newman | READY |
| API-00019 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 参数校验 | 等价类划分 | invalid | 获取财富等级经验及等级权益：query.appVersion 类型错误 | {"action": "replace", "field": "query.appVersion", "value": 123456, "expected_type": "string"} | 接口返回参数错误，不产生500和业务脏数据。 | Newman | READY |
| API-00020 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 边界值 | 边界值分析 | boundary | 获取财富等级经验及等级权益：query.deviceType 空值边界 | {"action": "replace", "field": "query.deviceType", "value": ""} | 接口按Schema和业务规则接受或明确拒绝，不能产生500。 | Newman | READY |
| API-00021 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 参数校验 | 等价类划分 | invalid | 获取财富等级经验及等级权益：query.deviceType 类型错误 | {"action": "replace", "field": "query.deviceType", "value": 123456, "expected_type": "string"} | 接口返回参数错误，不产生500和业务脏数据。 | Newman | READY |
| API-00022 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 认证授权 | 等价类划分 | invalid | 获取财富等级经验及等级权益：缺失认证凭证 | {"action": "remove_auth"} | 返回401或403，不返回受保护业务数据。 | Newman | READY |
| API-00023 | 获取财富等级经验及等级权益 | GET | `/level/exeperience/v2/get` | 认证授权 | 等价类划分 | invalid | 获取财富等级经验及等级权益：无效或伪造认证凭证 | {"action": "replace_auth", "value": "invalid-token"} | 返回401或403，不泄露凭证校验细节。 | Newman | READY |
