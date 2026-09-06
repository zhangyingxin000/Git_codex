# 财富等级 - 结构化测试用例

- 生成时间：2026-09-04T18:31:16+08:00
- 用例数：195
- 带DB校验：0
- 带Redis校验：0
- Redis可选证据建议：152
- 质量分级：{"MANUAL_ONLY": 190, "READY": 5}
- 脚本生成就绪：{"MANUAL_ONLY": 190, "SCRIPT_GENERATION_READY": 5}
- 总览：当前需求包 195 条用例，5 条脚本生成就绪，0 条待证据确认，190 条人工验证，脚本生成就绪率 2.6%。
- 需求用例Skill：requirement-test-case-generation v1.0
- Skill质量门禁：PASS

## 生成前数据准备检查

- 状态：READY_WITH_WARNINGS

- 账号模型：READY；已读取 C:\Users\DELL\Documents\Codex\2026-08-19\new-chat\outputs\AutoTest-AI\requirements\wealth-level\account_model.yaml
- 通用运行数据：READY_WITH_WARNINGS；当前需求包按 account_model.yaml 声明的数据来源做静态判断，不默认强制CSV、Redis或DB。
- 场景数据准备：WARNING；场景预检有 7 个场景需要关注。；下一步：确认未绑定证据规则或人工/定时流程是否符合预期
- 需求资源预检：WARNING；无运行阻断；有 1 个提醒、0 个建议。；下一步：确认资源登记或对非必要项执行确认忽略

## 用例到 JMeter 映射总览

- JMeter目标用例：0
- 脚本就绪：0
- 待证据：0
- 非JMeter目标：5

## 缺口清单

### 人工验证或长等待

- 数量：190
- 下一步：导出人工测试清单，必要时拆成后台/定时任务专项

- 个人等级区域完整展示：- ；建议工具 manual；原因 缺少可直接执行的接口 method/path。
- 用户ID与登录账号一致：- ；建议工具 manual；原因 缺少可直接执行的接口 method/path。
- 当前等级展示与数据库一致：- ；建议工具 manual；原因 缺少可直接执行的接口 method/path。
- 当前经验位于等级区间中间值：- ；建议工具 manual；原因 缺少可直接执行的接口 method/path。
- 经验等于当前等级起点：- ；建议工具 manual；原因 缺少可直接执行的接口 method/path。
- 距离下一等级只差1经验：- ；建议工具 manual；原因 缺少可直接执行的接口 method/path。
- 经验刚好达到升级阈值：- ；建议工具 manual；原因 缺少可直接执行的接口 method/path。
- 经验超过升级阈值但等级未更新：- ；建议工具 manual；原因 缺少可直接执行的接口 method/path。

## 用例明细

## 个人等级区域完整展示

- 优先级：P0
- 场景类型：正常
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：账号已登录且财富接口成功
2. 进入财富等级页面
3. 等待个人等级区域加载
4. 核对头像、昵称、ID、等级、勋章、进度和升级提示

### 预期结果
- 所有需求字段可见，值与接口和账号一致

### 分级原因
- 缺少可直接执行的接口 method/path。

## 用户ID与登录账号一致

- 优先级：P0
- 场景类型：一致性
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：使用显示号30010025登录
2. 完成登录
3. 进入财富等级页面
4. 对比页面ID、登录响应UID和数据库账号

### 预期结果
- 页面nickId为30010025，UID为1454694

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：data_constraint_exception。

## 当前等级展示与数据库一致

- 优先级：P0
- 场景类型：一致性
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：data_constraint_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：数据库users.exper_level已知
2. 查询数据库等级
3. 调用财富接口
4. 进入页面核对等级

### 预期结果
- 页面、接口和数据库等级完全一致

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：data_constraint_exception。

## 当前经验位于等级区间中间值

- 优先级：P0
- 场景类型：正常
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：data_constraint_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：准备区间中间经验账号
2. 查询数据库经验和等级阈值
3. 调用财富接口
4. 计算页面升级差值

### 预期结果
- 当前等级、经验进度和升级差值计算正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：data_constraint_exception。

## 经验等于当前等级起点

- 优先级：P0
- 场景类型：边界
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：data_constraint_exception, requirement_exception
- Redis可选证据：用例涉及缓存语义，但当前需求包未提供稳定Key，先作为可选证据。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：将测试账号经验设置为等级起点
2. 刷新缓存
3. 调用接口
4. 进入页面

### 预期结果
- 进度从0开始，当前等级不发生错误变化

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：data_constraint_exception, requirement_exception。

## 距离下一等级只差1经验

- 优先级：P0
- 场景类型：边界
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：requirement_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：经验=下一等级阈值-1
2. 调用接口
3. 检查进度和提示
4. 增加1经验后刷新

### 预期结果
- 升级前仍为当前等级；达到阈值后切换为下一等级

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：requirement_exception。

## 经验刚好达到升级阈值

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：data_constraint_exception
- Redis可选证据：用例涉及缓存语义，但当前需求包未提供稳定Key，先作为可选证据。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：经验=下一等级阈值
2. 更新测试数据
3. 清理相关缓存
4. 调用接口并进入页面

### 预期结果
- 等级升级、进度重置、权益和勋章同步更新

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：data_constraint_exception。

## 经验超过升级阈值但等级未更新

- 优先级：P0
- 场景类型：异常一致性
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：data_constraint_exception, requirement_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：构造经验和等级不一致数据
2. 调用接口
3. 查询MySQL和Redis
4. 观察平台告警

### 预期结果
- 平台识别数据不一致；客户端不应长期展示错误等级

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：data_constraint_exception, requirement_exception。

## 最高等级100

- 优先级：P0
- 场景类型：边界
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：requirement_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：准备等级100账号
2. 调用接口
3. 进入页面
4. 检查下一等级提示

### 预期结果
- 显示最高等级状态，不展示不存在的升级目标

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：requirement_exception。

## 经验换算规则

- 优先级：P0
- 场景类型：待确认
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：尚未提供送礼消费到经验的换算规则
2. 记录消费和经验变化
3. 等待产品配置
4. 补充精确断言

### 预期结果
- 待确认：消费金额与经验的换算及舍入规则

### 分级原因
- 缺少可直接执行的接口 method/path。

## Level 0展示规则

- 优先级：P0
- 场景类型：待确认
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：需求出现Level 0但接口从Level 1开始
2. 记录接口缺口
3. 与产品确认Level 0数据来源
4. 检查客户端组合逻辑

### 预期结果
- 待确认：Level 0是否存在、数据来源及权益

### 分级原因
- 缺少可直接执行的接口 method/path。

## 每个等级段权益数组正确

- 优先级：P0
- 场景类型：业务规则
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception
- Redis可选证据：用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：获取真实experRights
2. 逐段读取right1/right2
3. 与权益配置对照
4. 记录缺失和额外项

### 预期结果
- 每段权益种类、数量和解锁等级与配置一致

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception。

## 登录UID与财富UID一致

- 优先级：P0
- 场景类型：一致性
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：正常登录成功
2. 记录登录UID
3. 调用财富接口
4. 比较myExperLevelInfo.uid

### 预期结果
- 两个真实响应UID一致

### 分级原因
- 缺少可直接执行的接口 method/path。

## 接口等级与MySQL一致

- 优先级：P0
- 场景类型：一致性
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：data_constraint_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：可查询users表
2. 读取users.exper_level
3. 调用财富接口
4. 比较currentLevel

### 预期结果
- 接口等级等于数据库等级

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：data_constraint_exception。

## 接口经验与MySQL一致

- 优先级：P0
- 场景类型：一致性
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：data_constraint_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：确认财富经验数据库字段
2. 读取数据库经验
3. 调用财富接口
4. 比较currentExperValue

### 预期结果
- 经验值一致；字段映射待最终确认

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：data_constraint_exception。

## Redis等级缓存与MySQL一致

- 优先级：P0
- 场景类型：一致性
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：data_constraint_exception
- Redis可选证据：用例涉及缓存语义，但当前需求包未提供稳定Key，先作为可选证据。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：定位账号相关等级缓存Key
2. 读取MySQL等级
3. 读取Redis缓存
4. 调用接口

### 预期结果
- 三方等级一致；Key映射需确认后锁定

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：data_constraint_exception。

## 数据库更新但缓存未刷新

- 优先级：P0
- 场景类型：异常一致性
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：data_constraint_exception, requirement_exception
- Redis可选证据：用例涉及缓存语义，但当前需求包未提供稳定Key，先作为可选证据。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：允许修改测试账号数据
2. 备份原值和TTL
3. 修改数据库等级或经验
4. 不清缓存调用接口
5. 观察告警后恢复

### 预期结果
- 识别缓存陈旧；最终一致性策略符合设计

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：data_constraint_exception, requirement_exception。

## 缺失Token

- 优先级：P0
- 场景类型：认证异常
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, requirement_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：不传ticket
2. 调用财富接口
3. 记录HTTP和业务码
4. 检查敏感信息

### 预期结果
- 请求被拒绝且不返回用户财富数据

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, requirement_exception。

## 无效Token

- 优先级：P0
- 场景类型：认证异常
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, requirement_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：使用随机无效ticket
2. 调用财富接口
3. 记录响应
4. 检查日志追踪

### 预期结果
- 请求被拒绝且错误信息明确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, requirement_exception。

## 过期Token

- 优先级：P0
- 场景类型：认证异常
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, requirement_exception, state_machine_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：准备过期真实Token
2. 调用财富接口
3. 观察客户端处理
4. 重新登录后重试

### 预期结果
- 提示会话失效并可通过重新登录恢复

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, requirement_exception, state_machine_exception。

## Token UID与参数UID不一致

- 优先级：P0
- 场景类型：越权
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：使用A账号Token和B账号UID
2. 调用财富接口
3. 检查返回用户
4. 检查安全日志

### 预期结果
- 拒绝越权或强制使用Token所属UID，不泄露B数据

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception。

## 真实登录到财富页面

- 优先级：P0
- 场景类型：端到端
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：客户端真实登录参数可用
2. 调用登录接口
3. 提取真实access_token
4. 调用财富接口
5. 进入页面核对

### 预期结果
- 两接口成功，页面与接口核心数据一致

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception。

## 送礼增加经验但未升级

- 优先级：P0
- 场景类型：端到端
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：data_constraint_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：准备可送礼账号且经验远离阈值
2. 记录经验和等级
3. 完成真实送礼
4. 刷新MySQL/Redis/接口/页面

### 预期结果
- 经验按规则增加，等级和权益状态不误变

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：data_constraint_exception。

## 送礼触发等级升级

- 优先级：P0
- 场景类型：端到端
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：data_constraint_exception
- Redis可选证据：用例涉及缓存语义，但当前需求包未提供稳定Key，先作为可选证据。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：经验距离阈值较近
2. 记录前置数据
3. 完成真实送礼
4. 核对数据库、缓存、接口和页面

### 预期结果
- 等级、经验、勋章、区间和权益同步升级

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：data_constraint_exception。

## 财富等级矩阵：Lv.1奖励明细正确

- 优先级：P0
- 场景类型：边界
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception, requirement_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.1应拥有的全部奖励
4. 调用财富等级接口并计算Lv.1生效奖励
5. 查询MySQL/Redis中的Lv.1奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.1奖励的金色勾选/灰锁状态

### 预期结果
- Lv.1的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception, requirement_exception。

## 财富等级矩阵：Lv.2奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.2应拥有的全部奖励
4. 调用财富等级接口并计算Lv.2生效奖励
5. 查询MySQL/Redis中的Lv.2奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.2奖励的金色勾选/灰锁状态

### 预期结果
- Lv.2的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.3奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.3应拥有的全部奖励
4. 调用财富等级接口并计算Lv.3生效奖励
5. 查询MySQL/Redis中的Lv.3奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.3奖励的金色勾选/灰锁状态

### 预期结果
- Lv.3的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.4奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.4应拥有的全部奖励
4. 调用财富等级接口并计算Lv.4生效奖励
5. 查询MySQL/Redis中的Lv.4奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.4奖励的金色勾选/灰锁状态

### 预期结果
- Lv.4的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.5奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.5应拥有的全部奖励
4. 调用财富等级接口并计算Lv.5生效奖励
5. 查询MySQL/Redis中的Lv.5奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.5奖励的金色勾选/灰锁状态

### 预期结果
- Lv.5的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.6奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.6应拥有的全部奖励
4. 调用财富等级接口并计算Lv.6生效奖励
5. 查询MySQL/Redis中的Lv.6奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.6奖励的金色勾选/灰锁状态

### 预期结果
- Lv.6的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.7奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.7应拥有的全部奖励
4. 调用财富等级接口并计算Lv.7生效奖励
5. 查询MySQL/Redis中的Lv.7奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.7奖励的金色勾选/灰锁状态

### 预期结果
- Lv.7的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.8奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.8应拥有的全部奖励
4. 调用财富等级接口并计算Lv.8生效奖励
5. 查询MySQL/Redis中的Lv.8奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.8奖励的金色勾选/灰锁状态

### 预期结果
- Lv.8的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.9奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.9应拥有的全部奖励
4. 调用财富等级接口并计算Lv.9生效奖励
5. 查询MySQL/Redis中的Lv.9奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.9奖励的金色勾选/灰锁状态

### 预期结果
- Lv.9的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.10奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.10应拥有的全部奖励
4. 调用财富等级接口并计算Lv.10生效奖励
5. 查询MySQL/Redis中的Lv.10奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.10奖励的金色勾选/灰锁状态

### 预期结果
- Lv.10的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.11奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.11应拥有的全部奖励
4. 调用财富等级接口并计算Lv.11生效奖励
5. 查询MySQL/Redis中的Lv.11奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.11奖励的金色勾选/灰锁状态

### 预期结果
- Lv.11的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.12奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.12应拥有的全部奖励
4. 调用财富等级接口并计算Lv.12生效奖励
5. 查询MySQL/Redis中的Lv.12奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.12奖励的金色勾选/灰锁状态

### 预期结果
- Lv.12的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.13奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.13应拥有的全部奖励
4. 调用财富等级接口并计算Lv.13生效奖励
5. 查询MySQL/Redis中的Lv.13奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.13奖励的金色勾选/灰锁状态

### 预期结果
- Lv.13的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.14奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.14应拥有的全部奖励
4. 调用财富等级接口并计算Lv.14生效奖励
5. 查询MySQL/Redis中的Lv.14奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.14奖励的金色勾选/灰锁状态

### 预期结果
- Lv.14的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.15奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.15应拥有的全部奖励
4. 调用财富等级接口并计算Lv.15生效奖励
5. 查询MySQL/Redis中的Lv.15奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.15奖励的金色勾选/灰锁状态

### 预期结果
- Lv.15的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.16奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.16应拥有的全部奖励
4. 调用财富等级接口并计算Lv.16生效奖励
5. 查询MySQL/Redis中的Lv.16奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.16奖励的金色勾选/灰锁状态

### 预期结果
- Lv.16的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.17奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.17应拥有的全部奖励
4. 调用财富等级接口并计算Lv.17生效奖励
5. 查询MySQL/Redis中的Lv.17奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.17奖励的金色勾选/灰锁状态

### 预期结果
- Lv.17的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.18奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.18应拥有的全部奖励
4. 调用财富等级接口并计算Lv.18生效奖励
5. 查询MySQL/Redis中的Lv.18奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.18奖励的金色勾选/灰锁状态

### 预期结果
- Lv.18的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.19奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.19应拥有的全部奖励
4. 调用财富等级接口并计算Lv.19生效奖励
5. 查询MySQL/Redis中的Lv.19奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.19奖励的金色勾选/灰锁状态

### 预期结果
- Lv.19的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.20奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.20应拥有的全部奖励
4. 调用财富等级接口并计算Lv.20生效奖励
5. 查询MySQL/Redis中的Lv.20奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.20奖励的金色勾选/灰锁状态

### 预期结果
- Lv.20的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.21奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.21应拥有的全部奖励
4. 调用财富等级接口并计算Lv.21生效奖励
5. 查询MySQL/Redis中的Lv.21奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.21奖励的金色勾选/灰锁状态

### 预期结果
- Lv.21的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.22奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.22应拥有的全部奖励
4. 调用财富等级接口并计算Lv.22生效奖励
5. 查询MySQL/Redis中的Lv.22奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.22奖励的金色勾选/灰锁状态

### 预期结果
- Lv.22的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.23奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.23应拥有的全部奖励
4. 调用财富等级接口并计算Lv.23生效奖励
5. 查询MySQL/Redis中的Lv.23奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.23奖励的金色勾选/灰锁状态

### 预期结果
- Lv.23的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.24奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.24应拥有的全部奖励
4. 调用财富等级接口并计算Lv.24生效奖励
5. 查询MySQL/Redis中的Lv.24奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.24奖励的金色勾选/灰锁状态

### 预期结果
- Lv.24的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.25奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.25应拥有的全部奖励
4. 调用财富等级接口并计算Lv.25生效奖励
5. 查询MySQL/Redis中的Lv.25奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.25奖励的金色勾选/灰锁状态

### 预期结果
- Lv.25的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.26奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.26应拥有的全部奖励
4. 调用财富等级接口并计算Lv.26生效奖励
5. 查询MySQL/Redis中的Lv.26奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.26奖励的金色勾选/灰锁状态

### 预期结果
- Lv.26的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.27奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.27应拥有的全部奖励
4. 调用财富等级接口并计算Lv.27生效奖励
5. 查询MySQL/Redis中的Lv.27奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.27奖励的金色勾选/灰锁状态

### 预期结果
- Lv.27的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.28奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.28应拥有的全部奖励
4. 调用财富等级接口并计算Lv.28生效奖励
5. 查询MySQL/Redis中的Lv.28奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.28奖励的金色勾选/灰锁状态

### 预期结果
- Lv.28的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.29奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.29应拥有的全部奖励
4. 调用财富等级接口并计算Lv.29生效奖励
5. 查询MySQL/Redis中的Lv.29奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.29奖励的金色勾选/灰锁状态

### 预期结果
- Lv.29的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.30奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.30应拥有的全部奖励
4. 调用财富等级接口并计算Lv.30生效奖励
5. 查询MySQL/Redis中的Lv.30奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.30奖励的金色勾选/灰锁状态

### 预期结果
- Lv.30的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.31奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.31应拥有的全部奖励
4. 调用财富等级接口并计算Lv.31生效奖励
5. 查询MySQL/Redis中的Lv.31奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.31奖励的金色勾选/灰锁状态

### 预期结果
- Lv.31的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.32奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.32应拥有的全部奖励
4. 调用财富等级接口并计算Lv.32生效奖励
5. 查询MySQL/Redis中的Lv.32奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.32奖励的金色勾选/灰锁状态

### 预期结果
- Lv.32的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.33奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.33应拥有的全部奖励
4. 调用财富等级接口并计算Lv.33生效奖励
5. 查询MySQL/Redis中的Lv.33奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.33奖励的金色勾选/灰锁状态

### 预期结果
- Lv.33的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.34奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.34应拥有的全部奖励
4. 调用财富等级接口并计算Lv.34生效奖励
5. 查询MySQL/Redis中的Lv.34奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.34奖励的金色勾选/灰锁状态

### 预期结果
- Lv.34的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.35奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.35应拥有的全部奖励
4. 调用财富等级接口并计算Lv.35生效奖励
5. 查询MySQL/Redis中的Lv.35奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.35奖励的金色勾选/灰锁状态

### 预期结果
- Lv.35的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.36奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.36应拥有的全部奖励
4. 调用财富等级接口并计算Lv.36生效奖励
5. 查询MySQL/Redis中的Lv.36奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.36奖励的金色勾选/灰锁状态

### 预期结果
- Lv.36的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.37奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.37应拥有的全部奖励
4. 调用财富等级接口并计算Lv.37生效奖励
5. 查询MySQL/Redis中的Lv.37奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.37奖励的金色勾选/灰锁状态

### 预期结果
- Lv.37的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.38奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.38应拥有的全部奖励
4. 调用财富等级接口并计算Lv.38生效奖励
5. 查询MySQL/Redis中的Lv.38奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.38奖励的金色勾选/灰锁状态

### 预期结果
- Lv.38的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.39奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.39应拥有的全部奖励
4. 调用财富等级接口并计算Lv.39生效奖励
5. 查询MySQL/Redis中的Lv.39奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.39奖励的金色勾选/灰锁状态

### 预期结果
- Lv.39的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.40奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.40应拥有的全部奖励
4. 调用财富等级接口并计算Lv.40生效奖励
5. 查询MySQL/Redis中的Lv.40奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.40奖励的金色勾选/灰锁状态

### 预期结果
- Lv.40的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.41奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.41应拥有的全部奖励
4. 调用财富等级接口并计算Lv.41生效奖励
5. 查询MySQL/Redis中的Lv.41奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.41奖励的金色勾选/灰锁状态

### 预期结果
- Lv.41的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.42奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.42应拥有的全部奖励
4. 调用财富等级接口并计算Lv.42生效奖励
5. 查询MySQL/Redis中的Lv.42奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.42奖励的金色勾选/灰锁状态

### 预期结果
- Lv.42的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.43奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.43应拥有的全部奖励
4. 调用财富等级接口并计算Lv.43生效奖励
5. 查询MySQL/Redis中的Lv.43奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.43奖励的金色勾选/灰锁状态

### 预期结果
- Lv.43的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.44奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.44应拥有的全部奖励
4. 调用财富等级接口并计算Lv.44生效奖励
5. 查询MySQL/Redis中的Lv.44奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.44奖励的金色勾选/灰锁状态

### 预期结果
- Lv.44的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.45奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.45应拥有的全部奖励
4. 调用财富等级接口并计算Lv.45生效奖励
5. 查询MySQL/Redis中的Lv.45奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.45奖励的金色勾选/灰锁状态

### 预期结果
- Lv.45的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.46奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.46应拥有的全部奖励
4. 调用财富等级接口并计算Lv.46生效奖励
5. 查询MySQL/Redis中的Lv.46奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.46奖励的金色勾选/灰锁状态

### 预期结果
- Lv.46的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.47奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.47应拥有的全部奖励
4. 调用财富等级接口并计算Lv.47生效奖励
5. 查询MySQL/Redis中的Lv.47奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.47奖励的金色勾选/灰锁状态

### 预期结果
- Lv.47的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.48奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.48应拥有的全部奖励
4. 调用财富等级接口并计算Lv.48生效奖励
5. 查询MySQL/Redis中的Lv.48奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.48奖励的金色勾选/灰锁状态

### 预期结果
- Lv.48的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.49奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.49应拥有的全部奖励
4. 调用财富等级接口并计算Lv.49生效奖励
5. 查询MySQL/Redis中的Lv.49奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.49奖励的金色勾选/灰锁状态

### 预期结果
- Lv.49的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.50奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.50应拥有的全部奖励
4. 调用财富等级接口并计算Lv.50生效奖励
5. 查询MySQL/Redis中的Lv.50奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.50奖励的金色勾选/灰锁状态

### 预期结果
- Lv.50的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.51奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.51应拥有的全部奖励
4. 调用财富等级接口并计算Lv.51生效奖励
5. 查询MySQL/Redis中的Lv.51奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.51奖励的金色勾选/灰锁状态

### 预期结果
- Lv.51的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.52奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.52应拥有的全部奖励
4. 调用财富等级接口并计算Lv.52生效奖励
5. 查询MySQL/Redis中的Lv.52奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.52奖励的金色勾选/灰锁状态

### 预期结果
- Lv.52的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.53奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.53应拥有的全部奖励
4. 调用财富等级接口并计算Lv.53生效奖励
5. 查询MySQL/Redis中的Lv.53奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.53奖励的金色勾选/灰锁状态

### 预期结果
- Lv.53的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.54奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.54应拥有的全部奖励
4. 调用财富等级接口并计算Lv.54生效奖励
5. 查询MySQL/Redis中的Lv.54奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.54奖励的金色勾选/灰锁状态

### 预期结果
- Lv.54的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.55奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.55应拥有的全部奖励
4. 调用财富等级接口并计算Lv.55生效奖励
5. 查询MySQL/Redis中的Lv.55奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.55奖励的金色勾选/灰锁状态

### 预期结果
- Lv.55的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.56奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.56应拥有的全部奖励
4. 调用财富等级接口并计算Lv.56生效奖励
5. 查询MySQL/Redis中的Lv.56奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.56奖励的金色勾选/灰锁状态

### 预期结果
- Lv.56的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.57奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.57应拥有的全部奖励
4. 调用财富等级接口并计算Lv.57生效奖励
5. 查询MySQL/Redis中的Lv.57奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.57奖励的金色勾选/灰锁状态

### 预期结果
- Lv.57的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.58奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.58应拥有的全部奖励
4. 调用财富等级接口并计算Lv.58生效奖励
5. 查询MySQL/Redis中的Lv.58奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.58奖励的金色勾选/灰锁状态

### 预期结果
- Lv.58的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.59奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.59应拥有的全部奖励
4. 调用财富等级接口并计算Lv.59生效奖励
5. 查询MySQL/Redis中的Lv.59奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.59奖励的金色勾选/灰锁状态

### 预期结果
- Lv.59的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.60奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.60应拥有的全部奖励
4. 调用财富等级接口并计算Lv.60生效奖励
5. 查询MySQL/Redis中的Lv.60奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.60奖励的金色勾选/灰锁状态

### 预期结果
- Lv.60的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.61奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.61应拥有的全部奖励
4. 调用财富等级接口并计算Lv.61生效奖励
5. 查询MySQL/Redis中的Lv.61奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.61奖励的金色勾选/灰锁状态

### 预期结果
- Lv.61的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.62奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.62应拥有的全部奖励
4. 调用财富等级接口并计算Lv.62生效奖励
5. 查询MySQL/Redis中的Lv.62奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.62奖励的金色勾选/灰锁状态

### 预期结果
- Lv.62的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.63奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.63应拥有的全部奖励
4. 调用财富等级接口并计算Lv.63生效奖励
5. 查询MySQL/Redis中的Lv.63奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.63奖励的金色勾选/灰锁状态

### 预期结果
- Lv.63的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.64奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.64应拥有的全部奖励
4. 调用财富等级接口并计算Lv.64生效奖励
5. 查询MySQL/Redis中的Lv.64奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.64奖励的金色勾选/灰锁状态

### 预期结果
- Lv.64的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.65奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.65应拥有的全部奖励
4. 调用财富等级接口并计算Lv.65生效奖励
5. 查询MySQL/Redis中的Lv.65奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.65奖励的金色勾选/灰锁状态

### 预期结果
- Lv.65的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.66奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.66应拥有的全部奖励
4. 调用财富等级接口并计算Lv.66生效奖励
5. 查询MySQL/Redis中的Lv.66奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.66奖励的金色勾选/灰锁状态

### 预期结果
- Lv.66的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.67奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.67应拥有的全部奖励
4. 调用财富等级接口并计算Lv.67生效奖励
5. 查询MySQL/Redis中的Lv.67奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.67奖励的金色勾选/灰锁状态

### 预期结果
- Lv.67的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.68奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.68应拥有的全部奖励
4. 调用财富等级接口并计算Lv.68生效奖励
5. 查询MySQL/Redis中的Lv.68奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.68奖励的金色勾选/灰锁状态

### 预期结果
- Lv.68的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.69奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.69应拥有的全部奖励
4. 调用财富等级接口并计算Lv.69生效奖励
5. 查询MySQL/Redis中的Lv.69奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.69奖励的金色勾选/灰锁状态

### 预期结果
- Lv.69的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.70奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.70应拥有的全部奖励
4. 调用财富等级接口并计算Lv.70生效奖励
5. 查询MySQL/Redis中的Lv.70奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.70奖励的金色勾选/灰锁状态

### 预期结果
- Lv.70的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.71奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.71应拥有的全部奖励
4. 调用财富等级接口并计算Lv.71生效奖励
5. 查询MySQL/Redis中的Lv.71奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.71奖励的金色勾选/灰锁状态

### 预期结果
- Lv.71的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.72奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.72应拥有的全部奖励
4. 调用财富等级接口并计算Lv.72生效奖励
5. 查询MySQL/Redis中的Lv.72奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.72奖励的金色勾选/灰锁状态

### 预期结果
- Lv.72的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.73奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.73应拥有的全部奖励
4. 调用财富等级接口并计算Lv.73生效奖励
5. 查询MySQL/Redis中的Lv.73奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.73奖励的金色勾选/灰锁状态

### 预期结果
- Lv.73的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.74奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.74应拥有的全部奖励
4. 调用财富等级接口并计算Lv.74生效奖励
5. 查询MySQL/Redis中的Lv.74奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.74奖励的金色勾选/灰锁状态

### 预期结果
- Lv.74的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.75奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.75应拥有的全部奖励
4. 调用财富等级接口并计算Lv.75生效奖励
5. 查询MySQL/Redis中的Lv.75奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.75奖励的金色勾选/灰锁状态

### 预期结果
- Lv.75的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.76奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.76应拥有的全部奖励
4. 调用财富等级接口并计算Lv.76生效奖励
5. 查询MySQL/Redis中的Lv.76奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.76奖励的金色勾选/灰锁状态

### 预期结果
- Lv.76的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.77奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.77应拥有的全部奖励
4. 调用财富等级接口并计算Lv.77生效奖励
5. 查询MySQL/Redis中的Lv.77奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.77奖励的金色勾选/灰锁状态

### 预期结果
- Lv.77的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.78奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.78应拥有的全部奖励
4. 调用财富等级接口并计算Lv.78生效奖励
5. 查询MySQL/Redis中的Lv.78奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.78奖励的金色勾选/灰锁状态

### 预期结果
- Lv.78的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.79奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.79应拥有的全部奖励
4. 调用财富等级接口并计算Lv.79生效奖励
5. 查询MySQL/Redis中的Lv.79奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.79奖励的金色勾选/灰锁状态

### 预期结果
- Lv.79的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.80奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.80应拥有的全部奖励
4. 调用财富等级接口并计算Lv.80生效奖励
5. 查询MySQL/Redis中的Lv.80奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.80奖励的金色勾选/灰锁状态

### 预期结果
- Lv.80的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.81奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.81应拥有的全部奖励
4. 调用财富等级接口并计算Lv.81生效奖励
5. 查询MySQL/Redis中的Lv.81奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.81奖励的金色勾选/灰锁状态

### 预期结果
- Lv.81的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.82奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.82应拥有的全部奖励
4. 调用财富等级接口并计算Lv.82生效奖励
5. 查询MySQL/Redis中的Lv.82奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.82奖励的金色勾选/灰锁状态

### 预期结果
- Lv.82的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.83奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.83应拥有的全部奖励
4. 调用财富等级接口并计算Lv.83生效奖励
5. 查询MySQL/Redis中的Lv.83奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.83奖励的金色勾选/灰锁状态

### 预期结果
- Lv.83的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.84奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.84应拥有的全部奖励
4. 调用财富等级接口并计算Lv.84生效奖励
5. 查询MySQL/Redis中的Lv.84奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.84奖励的金色勾选/灰锁状态

### 预期结果
- Lv.84的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.85奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.85应拥有的全部奖励
4. 调用财富等级接口并计算Lv.85生效奖励
5. 查询MySQL/Redis中的Lv.85奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.85奖励的金色勾选/灰锁状态

### 预期结果
- Lv.85的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.86奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.86应拥有的全部奖励
4. 调用财富等级接口并计算Lv.86生效奖励
5. 查询MySQL/Redis中的Lv.86奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.86奖励的金色勾选/灰锁状态

### 预期结果
- Lv.86的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.87奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.87应拥有的全部奖励
4. 调用财富等级接口并计算Lv.87生效奖励
5. 查询MySQL/Redis中的Lv.87奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.87奖励的金色勾选/灰锁状态

### 预期结果
- Lv.87的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.88奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.88应拥有的全部奖励
4. 调用财富等级接口并计算Lv.88生效奖励
5. 查询MySQL/Redis中的Lv.88奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.88奖励的金色勾选/灰锁状态

### 预期结果
- Lv.88的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.89奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.89应拥有的全部奖励
4. 调用财富等级接口并计算Lv.89生效奖励
5. 查询MySQL/Redis中的Lv.89奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.89奖励的金色勾选/灰锁状态

### 预期结果
- Lv.89的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.90奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.90应拥有的全部奖励
4. 调用财富等级接口并计算Lv.90生效奖励
5. 查询MySQL/Redis中的Lv.90奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.90奖励的金色勾选/灰锁状态

### 预期结果
- Lv.90的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.91奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.91应拥有的全部奖励
4. 调用财富等级接口并计算Lv.91生效奖励
5. 查询MySQL/Redis中的Lv.91奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.91奖励的金色勾选/灰锁状态

### 预期结果
- Lv.91的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.92奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.92应拥有的全部奖励
4. 调用财富等级接口并计算Lv.92生效奖励
5. 查询MySQL/Redis中的Lv.92奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.92奖励的金色勾选/灰锁状态

### 预期结果
- Lv.92的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.93奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.93应拥有的全部奖励
4. 调用财富等级接口并计算Lv.93生效奖励
5. 查询MySQL/Redis中的Lv.93奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.93奖励的金色勾选/灰锁状态

### 预期结果
- Lv.93的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.94奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.94应拥有的全部奖励
4. 调用财富等级接口并计算Lv.94生效奖励
5. 查询MySQL/Redis中的Lv.94奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.94奖励的金色勾选/灰锁状态

### 预期结果
- Lv.94的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.95奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.95应拥有的全部奖励
4. 调用财富等级接口并计算Lv.95生效奖励
5. 查询MySQL/Redis中的Lv.95奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.95奖励的金色勾选/灰锁状态

### 预期结果
- Lv.95的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.96奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.96应拥有的全部奖励
4. 调用财富等级接口并计算Lv.96生效奖励
5. 查询MySQL/Redis中的Lv.96奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.96奖励的金色勾选/灰锁状态

### 预期结果
- Lv.96的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.97奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.97应拥有的全部奖励
4. 调用财富等级接口并计算Lv.97生效奖励
5. 查询MySQL/Redis中的Lv.97奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.97奖励的金色勾选/灰锁状态

### 预期结果
- Lv.97的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.98奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.98应拥有的全部奖励
4. 调用财富等级接口并计算Lv.98生效奖励
5. 查询MySQL/Redis中的Lv.98奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.98奖励的金色勾选/灰锁状态

### 预期结果
- Lv.98的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.99奖励明细正确

- 优先级：P0
- 场景类型：奖励配置
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.99应拥有的全部奖励
4. 调用财富等级接口并计算Lv.99生效奖励
5. 查询MySQL/Redis中的Lv.99奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.99奖励的金色勾选/灰锁状态

### 预期结果
- Lv.99的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.100奖励明细正确

- 优先级：P0
- 场景类型：边界
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception, requirement_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准的Lv.1～Lv.100奖励配置矩阵已导入平台
2. 完成真实登录并提取Token和UID
3. 读取配置矩阵中Lv.100应拥有的全部奖励
4. 调用财富等级接口并计算Lv.100生效奖励
5. 查询MySQL/Redis中的Lv.100奖励配置
6. 逐项比较名称、阿语名称、类型、资源地址、有效期、解锁等级和是否累计继承
7. 检查页面Lv.100奖励的金色勾选/灰锁状态

### 预期结果
- Lv.100的奖励集合与批准矩阵完全一致；不得缺少、重复、多发或提前解锁；每项名称、类型、图片/MP4/PAG/SVGA资源、有效期和状态正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception, requirement_exception。

## 财富等级矩阵：Lv.9→Lv.10跨段升级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准奖励矩阵；可对测试账号执行升级并恢复数据
2. 完成真实登录并提取Token和UID
3. 记录变更前个人信息、My Level定位、奖励和锁定状态
4. 将账号从Lv.9升级到Lv.10
5. 刷新MySQL、Redis、接口和页面
6. 核对个人等级、勋章、经验、My Level定位、区间高亮和奖励差异
7. 恢复测试数据

### 预期结果
- 定位从Lv.1-9移动到包含Lv.10的新区间；个人信息同步；仅新等级应解锁的奖励变化，其余奖励保持正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.10→Lv.9跨段降级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及缓存语义，但当前需求包未提供稳定Key，先作为可选证据。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准降级及权益回收/保留规则；可恢复测试数据
2. 完成真实登录并提取Token和UID
3. 记录降级前完整状态
4. 将账号从Lv.10降到Lv.9
5. 刷新数据库、缓存、接口和页面
6. 核对定位、个人信息和所有受影响奖励
7. 恢复测试数据

### 预期结果
- 定位回到Lv.1-9；等级、勋章和经验同步；奖励严格按批准的降级回收/保留规则处理

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.19→Lv.20跨段升级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准奖励矩阵；可对测试账号执行升级并恢复数据
2. 完成真实登录并提取Token和UID
3. 记录变更前个人信息、My Level定位、奖励和锁定状态
4. 将账号从Lv.19升级到Lv.20
5. 刷新MySQL、Redis、接口和页面
6. 核对个人等级、勋章、经验、My Level定位、区间高亮和奖励差异
7. 恢复测试数据

### 预期结果
- 定位从Lv.10-19移动到包含Lv.20的新区间；个人信息同步；仅新等级应解锁的奖励变化，其余奖励保持正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.20→Lv.19跨段降级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及缓存语义，但当前需求包未提供稳定Key，先作为可选证据。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准降级及权益回收/保留规则；可恢复测试数据
2. 完成真实登录并提取Token和UID
3. 记录降级前完整状态
4. 将账号从Lv.20降到Lv.19
5. 刷新数据库、缓存、接口和页面
6. 核对定位、个人信息和所有受影响奖励
7. 恢复测试数据

### 预期结果
- 定位回到Lv.10-19；等级、勋章和经验同步；奖励严格按批准的降级回收/保留规则处理

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.29→Lv.30跨段升级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准奖励矩阵；可对测试账号执行升级并恢复数据
2. 完成真实登录并提取Token和UID
3. 记录变更前个人信息、My Level定位、奖励和锁定状态
4. 将账号从Lv.29升级到Lv.30
5. 刷新MySQL、Redis、接口和页面
6. 核对个人等级、勋章、经验、My Level定位、区间高亮和奖励差异
7. 恢复测试数据

### 预期结果
- 定位从Lv.20-29移动到包含Lv.30的新区间；个人信息同步；仅新等级应解锁的奖励变化，其余奖励保持正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.30→Lv.29跨段降级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及缓存语义，但当前需求包未提供稳定Key，先作为可选证据。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准降级及权益回收/保留规则；可恢复测试数据
2. 完成真实登录并提取Token和UID
3. 记录降级前完整状态
4. 将账号从Lv.30降到Lv.29
5. 刷新数据库、缓存、接口和页面
6. 核对定位、个人信息和所有受影响奖励
7. 恢复测试数据

### 预期结果
- 定位回到Lv.20-29；等级、勋章和经验同步；奖励严格按批准的降级回收/保留规则处理

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.39→Lv.40跨段升级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准奖励矩阵；可对测试账号执行升级并恢复数据
2. 完成真实登录并提取Token和UID
3. 记录变更前个人信息、My Level定位、奖励和锁定状态
4. 将账号从Lv.39升级到Lv.40
5. 刷新MySQL、Redis、接口和页面
6. 核对个人等级、勋章、经验、My Level定位、区间高亮和奖励差异
7. 恢复测试数据

### 预期结果
- 定位从Lv.30-39移动到包含Lv.40的新区间；个人信息同步；仅新等级应解锁的奖励变化，其余奖励保持正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.40→Lv.39跨段降级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及缓存语义，但当前需求包未提供稳定Key，先作为可选证据。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准降级及权益回收/保留规则；可恢复测试数据
2. 完成真实登录并提取Token和UID
3. 记录降级前完整状态
4. 将账号从Lv.40降到Lv.39
5. 刷新数据库、缓存、接口和页面
6. 核对定位、个人信息和所有受影响奖励
7. 恢复测试数据

### 预期结果
- 定位回到Lv.30-39；等级、勋章和经验同步；奖励严格按批准的降级回收/保留规则处理

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.49→Lv.50跨段升级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准奖励矩阵；可对测试账号执行升级并恢复数据
2. 完成真实登录并提取Token和UID
3. 记录变更前个人信息、My Level定位、奖励和锁定状态
4. 将账号从Lv.49升级到Lv.50
5. 刷新MySQL、Redis、接口和页面
6. 核对个人等级、勋章、经验、My Level定位、区间高亮和奖励差异
7. 恢复测试数据

### 预期结果
- 定位从Lv.40-49移动到包含Lv.50的新区间；个人信息同步；仅新等级应解锁的奖励变化，其余奖励保持正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.50→Lv.49跨段降级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及缓存语义，但当前需求包未提供稳定Key，先作为可选证据。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准降级及权益回收/保留规则；可恢复测试数据
2. 完成真实登录并提取Token和UID
3. 记录降级前完整状态
4. 将账号从Lv.50降到Lv.49
5. 刷新数据库、缓存、接口和页面
6. 核对定位、个人信息和所有受影响奖励
7. 恢复测试数据

### 预期结果
- 定位回到Lv.40-49；等级、勋章和经验同步；奖励严格按批准的降级回收/保留规则处理

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.59→Lv.60跨段升级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准奖励矩阵；可对测试账号执行升级并恢复数据
2. 完成真实登录并提取Token和UID
3. 记录变更前个人信息、My Level定位、奖励和锁定状态
4. 将账号从Lv.59升级到Lv.60
5. 刷新MySQL、Redis、接口和页面
6. 核对个人等级、勋章、经验、My Level定位、区间高亮和奖励差异
7. 恢复测试数据

### 预期结果
- 定位从Lv.50-59移动到包含Lv.60的新区间；个人信息同步；仅新等级应解锁的奖励变化，其余奖励保持正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.60→Lv.59跨段降级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及缓存语义，但当前需求包未提供稳定Key，先作为可选证据。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准降级及权益回收/保留规则；可恢复测试数据
2. 完成真实登录并提取Token和UID
3. 记录降级前完整状态
4. 将账号从Lv.60降到Lv.59
5. 刷新数据库、缓存、接口和页面
6. 核对定位、个人信息和所有受影响奖励
7. 恢复测试数据

### 预期结果
- 定位回到Lv.50-59；等级、勋章和经验同步；奖励严格按批准的降级回收/保留规则处理

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.69→Lv.70跨段升级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准奖励矩阵；可对测试账号执行升级并恢复数据
2. 完成真实登录并提取Token和UID
3. 记录变更前个人信息、My Level定位、奖励和锁定状态
4. 将账号从Lv.69升级到Lv.70
5. 刷新MySQL、Redis、接口和页面
6. 核对个人等级、勋章、经验、My Level定位、区间高亮和奖励差异
7. 恢复测试数据

### 预期结果
- 定位从Lv.60-69移动到包含Lv.70的新区间；个人信息同步；仅新等级应解锁的奖励变化，其余奖励保持正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.70→Lv.69跨段降级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及缓存语义，但当前需求包未提供稳定Key，先作为可选证据。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准降级及权益回收/保留规则；可恢复测试数据
2. 完成真实登录并提取Token和UID
3. 记录降级前完整状态
4. 将账号从Lv.70降到Lv.69
5. 刷新数据库、缓存、接口和页面
6. 核对定位、个人信息和所有受影响奖励
7. 恢复测试数据

### 预期结果
- 定位回到Lv.60-69；等级、勋章和经验同步；奖励严格按批准的降级回收/保留规则处理

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.79→Lv.80跨段升级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准奖励矩阵；可对测试账号执行升级并恢复数据
2. 完成真实登录并提取Token和UID
3. 记录变更前个人信息、My Level定位、奖励和锁定状态
4. 将账号从Lv.79升级到Lv.80
5. 刷新MySQL、Redis、接口和页面
6. 核对个人等级、勋章、经验、My Level定位、区间高亮和奖励差异
7. 恢复测试数据

### 预期结果
- 定位从Lv.70-79移动到包含Lv.80的新区间；个人信息同步；仅新等级应解锁的奖励变化，其余奖励保持正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.80→Lv.79跨段降级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及缓存语义，但当前需求包未提供稳定Key，先作为可选证据。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准降级及权益回收/保留规则；可恢复测试数据
2. 完成真实登录并提取Token和UID
3. 记录降级前完整状态
4. 将账号从Lv.80降到Lv.79
5. 刷新数据库、缓存、接口和页面
6. 核对定位、个人信息和所有受影响奖励
7. 恢复测试数据

### 预期结果
- 定位回到Lv.70-79；等级、勋章和经验同步；奖励严格按批准的降级回收/保留规则处理

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.89→Lv.90跨段升级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准奖励矩阵；可对测试账号执行升级并恢复数据
2. 完成真实登录并提取Token和UID
3. 记录变更前个人信息、My Level定位、奖励和锁定状态
4. 将账号从Lv.89升级到Lv.90
5. 刷新MySQL、Redis、接口和页面
6. 核对个人等级、勋章、经验、My Level定位、区间高亮和奖励差异
7. 恢复测试数据

### 预期结果
- 定位从Lv.80-89移动到包含Lv.90的新区间；个人信息同步；仅新等级应解锁的奖励变化，其余奖励保持正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.90→Lv.89跨段降级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及缓存语义，但当前需求包未提供稳定Key，先作为可选证据。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准降级及权益回收/保留规则；可恢复测试数据
2. 完成真实登录并提取Token和UID
3. 记录降级前完整状态
4. 将账号从Lv.90降到Lv.89
5. 刷新数据库、缓存、接口和页面
6. 核对定位、个人信息和所有受影响奖励
7. 恢复测试数据

### 预期结果
- 定位回到Lv.80-89；等级、勋章和经验同步；奖励严格按批准的降级回收/保留规则处理

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.99→Lv.100跨段升级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准奖励矩阵；可对测试账号执行升级并恢复数据
2. 完成真实登录并提取Token和UID
3. 记录变更前个人信息、My Level定位、奖励和锁定状态
4. 将账号从Lv.99升级到Lv.100
5. 刷新MySQL、Redis、接口和页面
6. 核对个人等级、勋章、经验、My Level定位、区间高亮和奖励差异
7. 恢复测试数据

### 预期结果
- 定位从Lv.90-99移动到包含Lv.100的新区间；个人信息同步；仅新等级应解锁的奖励变化，其余奖励保持正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.100→Lv.99跨段降级联动

- 优先级：P0
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及缓存语义，但当前需求包未提供稳定Key，先作为可选证据。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准降级及权益回收/保留规则；可恢复测试数据
2. 完成真实登录并提取Token和UID
3. 记录降级前完整状态
4. 将账号从Lv.100降到Lv.99
5. 刷新数据库、缓存、接口和页面
6. 核对定位、个人信息和所有受影响奖励
7. 恢复测试数据

### 预期结果
- 定位回到Lv.90-99；等级、勋章和经验同步；奖励严格按批准的降级回收/保留规则处理

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, data_constraint_exception。

## 财富等级矩阵：Lv.1个人信息与定位边界

- 优先级：P0
- 场景类型：边界
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, requirement_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。; 用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准最低/最高等级展示规则；准备对应真实账号
2. 完成真实登录并提取Token和UID
3. 登录边界等级账号
4. 调用财富接口
5. 打开财富页面
6. 点击My Level
7. 核对个人区、进度、升级提示、区间定位和奖励状态

### 预期结果
- Lv.1定位到最低区间，不出现Lv.0或负经验；奖励锁定/解锁正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, requirement_exception。

## 财富等级矩阵：Lv.100个人信息与定位边界

- 优先级：P0
- 场景类型：边界
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, requirement_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：已批准最低/最高等级展示规则；准备对应真实账号
2. 完成真实登录并提取Token和UID
3. 登录边界等级账号
4. 调用财富接口
5. 打开财富页面
6. 点击My Level
7. 核对个人区、进度、升级提示、区间定位和奖励状态

### 预期结果
- Lv.100定位到最高等级，不出现Lv.101、下一等级或错误升级进度；最高奖励完整

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, requirement_exception。

## 缺失UID参数

- 优先级：P0
- 场景类型：参数异常
- 接口：GET /level/exeperience/v2/get
- 接口字段：-
- 运行变量：-
- 质量分级：READY
- 脚本生成就绪：SCRIPT_GENERATION_READY / newman
- 异常来源：api_contract_exception, requirement_exception
- Redis可选证据：-
- 下一步：进入 newman 脚本生成

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 平台自动构造参数并发送只读请求
2. 调用接口：GET /level/exeperience/v2/get

### 预期结果
- 拒绝非法请求或不泄露其他用户数据

### 分级原因
- 接口、变量和证据条件满足当前脚本生成要求。
- 异常来源：api_contract_exception, requirement_exception。

## 非法UID类型

- 优先级：P0
- 场景类型：参数异常
- 接口：GET /level/exeperience/v2/get
- 接口字段：-
- 运行变量：-
- 质量分级：READY
- 脚本生成就绪：SCRIPT_GENERATION_READY / newman
- 异常来源：api_contract_exception, requirement_exception
- Redis可选证据：-
- 下一步：进入 newman 脚本生成

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 平台自动构造参数并发送只读请求
2. 调用接口：GET /level/exeperience/v2/get

### 预期结果
- 拒绝非法请求或不泄露其他用户数据

### 分级原因
- 接口、变量和证据条件满足当前脚本生成要求。
- 异常来源：api_contract_exception, requirement_exception。

## 查询当前用户钱包余额：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /purse/query?deviceType={{deviceType}}&systemLanguage={{systemLanguage}}&appVersion={{appVersion}}&os={{os}}&language={{language}}&appCode={{appCode}}&appid={{appid}}&version={{version}}&channel={{channel}}&ticket={{ticket}}&uid={{uid}}
- 接口字段：appCode, appVersion, appid, channel, deviceType, language, os, systemLanguage, ticket, uid, version
- 运行变量：appCode, appVersion, appid, channel, deviceType, language, os, systemLanguage, ticket, uid, version
- 质量分级：READY
- 脚本生成就绪：SCRIPT_GENERATION_READY / newman
- 异常来源：api_contract_exception, data_constraint_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。
- 下一步：进入 newman 脚本生成

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：appCode, appVersion, appid, channel, deviceType, language, os, systemLanguage, ticket, uid, version

### 操作步骤
1. 使用本机运行凭证发起只读 GET 请求；记录 HTTP 状态、业务响应和耗时。
2. 调用接口：GET /purse/query?deviceType={{deviceType}}&systemLanguage={{systemLanguage}}&appVersion={{appVersion}}&os={{os}}&language={{language}}&appCode={{appCode}}&appid={{appid}}&version={{version}}&channel={{channel}}&ticket={{ticket}}&uid={{uid}}

### 预期结果
- 返回当前登录用户钱包余额，接口只读，不应改变业务数据。

### 分级原因
- 接口、变量和证据条件满足当前脚本生成要求。
- 需要运行时提供变量：appCode, appVersion, appid, channel, deviceType, language, os, systemLanguage, ticket, uid, version。
- 异常来源：api_contract_exception, data_constraint_exception。

## 查询送礼账单记录：正常请求

- 优先级：P0
- 场景类型：正常请求
- 接口：GET /billrecord/get?deviceType={{deviceType}}&systemLanguage={{systemLanguage}}&appVersion={{appVersion}}&os={{os}}&language={{language}}&appCode={{appCode}}&appid={{appid}}&version={{version}}&channel={{channel}}&ticket={{ticket}}&uid={{uid}}&date={{current_time_ms}}&netType={{netType}}&appsflyerId={{appsflyerId}}&deviceId={{deviceId}}&osVersion={{osVersion}}&isVpnConnected={{isVpnConnected}}&model={{model}}&packageName={{packageName}}&ispType={{ispType}}&organic={{organic}}&pageNo=1&pageSize=50&type=1
- 接口字段：appCode, appVersion, appid, appsflyerId, channel, date, deviceId, deviceType, isVpnConnected, ispType, language, model, netType, organic, os, osVersion, packageName, pageNo, pageSize, systemLanguage, ticket, type, uid, version
- 运行变量：appCode, appVersion, appid, appsflyerId, channel, date, deviceId, deviceType, isVpnConnected, ispType, language, model, netType, organic, os, osVersion, packageName, pageNo, pageSize, systemLanguage, ticket, type, uid, version
- 质量分级：READY
- 脚本生成就绪：SCRIPT_GENERATION_READY / newman
- 异常来源：api_contract_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。
- 下一步：进入 newman 脚本生成

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：appCode, appVersion, appid, appsflyerId, channel, date, deviceId, deviceType, isVpnConnected, ispType, language, model, netType, organic, os, osVersion, packageName, pageNo, pageSize, systemLanguage, ticket, type, uid, version

### 操作步骤
1. 使用本机运行凭证发起只读 GET 请求；记录 HTTP 状态、业务响应和耗时。
2. 调用接口：GET /billrecord/get?deviceType={{deviceType}}&systemLanguage={{systemLanguage}}&appVersion={{appVersion}}&os={{os}}&language={{language}}&appCode={{appCode}}&appid={{appid}}&version={{version}}&channel={{channel}}&ticket={{ticket}}&uid={{uid}}&date={{current_time_ms}}&netType={{netType}}&appsflyerId={{appsflyerId}}&deviceId={{deviceId}}&osVersion={{osVersion}}&isVpnConnected={{isVpnConnected}}&model={{model}}&packageName={{packageName}}&ispType={{ispType}}&organic={{organic}}&pageNo=1&pageSize=50&type=1

### 预期结果
- 返回当前登录用户账单列表，接口只读，不应改变业务数据。

### 分级原因
- 接口、变量和证据条件满足当前脚本生成要求。
- 需要运行时提供变量：appCode, appVersion, appid, appsflyerId, channel, date, deviceId, deviceType, isVpnConnected, ispType, language, model, netType, organic, os, osVersion, packageName, pageNo, pageSize, systemLanguage, ticket, type, uid, version。
- 异常来源：api_contract_exception。

## 登录后查询真实财富等级

- 优先级：P0
- 场景类型：正常
- 接口：GET /level/exeperience/v2/get?deviceType=0&systemLanguage=zh&appVersion=100.1.5.4&os=android&ticket={{ticket}}&language=en&appCode=100154&uid={{uid}}&appid=soulfree
- 接口字段：appCode, appVersion, appid, deviceType, language, os, systemLanguage, ticket, uid
- 运行变量：appCode, appVersion, appid, deviceType, language, os, systemLanguage, ticket, uid
- 质量分级：READY
- 脚本生成就绪：SCRIPT_GENERATION_READY / newman
- 异常来源：api_contract_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。
- 下一步：进入 newman 脚本生成

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。
- 运行变量：appCode, appVersion, appid, deviceType, language, os, systemLanguage, ticket, uid

### 操作步骤
1. 使用客户端真实抓包参数运行；敏感值仅运行时注入
2. 调用接口：GET /level/exeperience/v2/get?deviceType=0&systemLanguage=zh&appVersion=100.1.5.4&os=android&ticket={{ticket}}&language=en&appCode=100154&uid={{uid}}&appid=soulfree

### 预期结果
- HTTP与业务码符合预期

### 分级原因
- 接口、变量和证据条件满足当前脚本生成要求。
- 需要运行时提供变量：appCode, appVersion, appid, deviceType, language, os, systemLanguage, ticket, uid。
- 异常来源：api_contract_exception。

## 超长昵称展示

- 优先级：P1
- 场景类型：边界
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：requirement_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：准备超长昵称测试账号
2. 进入页面
3. 观察昵称区域
4. 切换不同屏幕宽度

### 预期结果
- 昵称按设计截断或换行，不覆盖等级信息

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：requirement_exception。

## 当前勋章与等级对应

- 优先级：P1
- 场景类型：业务规则
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：准备各等级段账号
2. 记录当前等级
3. 检查勋章图案和资源
4. 与等级配置对照

### 预期结果
- 勋章样式、名称和等级配置匹配

### 分级原因
- 缺少可直接执行的接口 method/path。

## 个人区域接口失败

- 优先级：P1
- 场景类型：异常
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：requirement_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：财富接口返回服务错误
2. 打开页面
3. 观察错误状态
4. 点击重试

### 预期结果
- 展示可理解的错误和重试入口，恢复后数据正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：requirement_exception。

## 最低等级经验

- 优先级：P1
- 场景类型：边界
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：requirement_exception
- Redis可选证据：用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：准备最低等级账号
2. 调用接口
3. 核对起点和下一阈值
4. 进入页面

### 预期结果
- 最低等级、进度和可解锁权益正确

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：requirement_exception。

## 经验为0

- 优先级：P1
- 场景类型：边界
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：requirement_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：准备经验为0账号
2. 调用接口
3. 进入页面
4. 核对等级归属

### 预期结果
- 按已确认的最低等级规则展示；Level 0规则待产品确认

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：requirement_exception。

## 经验为负数

- 优先级：P1
- 场景类型：异常
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：requirement_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：构造非法负经验
2. 调用接口
3. 检查服务校验和页面降级
4. 检查日志

### 预期结果
- 服务拒绝或修正非法值，页面不显示负进度

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：requirement_exception。

## 经验超出最大配置

- 优先级：P1
- 场景类型：异常
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：requirement_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：构造超过最高阈值经验
2. 调用接口
3. 查询配置
4. 观察页面

### 预期结果
- 按最高等级封顶或明确告警，不溢出

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：requirement_exception。

## 升级所需经验文案

- 优先级：P1
- 场景类型：业务规则
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：使用非最高等级账号
2. 读取当前经验和下一阈值
3. 计算差值
4. 核对页面文案

### 预期结果
- 文案中的所需经验=下一阈值-当前经验

### 分级原因
- 缺少可直接执行的接口 method/path。

## 进度条比例计算

- 优先级：P1
- 场景类型：业务规则
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：准备多个区间位置账号
2. 计算理论比例
3. 截取页面进度条
4. 比较显示比例

### 预期结果
- 比例=(当前经验-区间起点)/(下一阈值-区间起点)

### 分级原因
- 缺少可直接执行的接口 method/path。

## 大经验值显示精度

- 优先级：P1
- 场景类型：边界
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, requirement_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：准备亿级经验账号
2. 调用接口
3. 检查数值格式化
4. 核对精度

### 预期结果
- 无科学计数、溢出或精度损失

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, requirement_exception。

## 连续升级多个等级

- 优先级：P1
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：data_constraint_exception
- Redis可选证据：用例涉及缓存语义，但当前需求包未提供稳定Key，先作为可选证据。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：一次增加跨越多个阈值的经验
2. 更新经验
3. 刷新缓存
4. 重新请求并进入页面

### 预期结果
- 最终等级和权益按最终经验正确计算，不停留在中间等级

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：data_constraint_exception。

## 默认定位当前等级段

- 优先级：P1
- 场景类型：正常
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：等级70账号进入页面
2. 首次进入页面
3. 观察选中等级段
4. 核对Lv.70-79

### 预期结果
- 默认定位并高亮Lv.70-79

### 分级原因
- 缺少可直接执行的接口 method/path。

## 等级段从低到高可完整浏览

- 优先级：P1
- 场景类型：正常
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：权益列表加载成功
2. 从列表起点连续浏览到终点
3. 记录所有等级段
4. 核对无缺失

### 预期结果
- UI按需求从低到高展示完整等级范围

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception。

## 相邻等级段切换

- 优先级：P1
- 场景类型：交互
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：页面已加载
2. 依次切换两个相邻等级段
3. 观察标题和权益列表
4. 返回原区间

### 预期结果
- 区间标题、权益和状态同步切换

### 分级原因
- 缺少可直接执行的接口 method/path。

## 快速连续切换等级段

- 优先级：P1
- 场景类型：并发
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：页面已加载
2. 快速点击多个等级段
3. 等待动画结束
4. 核对最终选中项

### 预期结果
- 最终内容与最后一次选择一致，无错位或重叠

### 分级原因
- 缺少可直接执行的接口 method/path。

## 等级段边界9到10

- 优先级：P1
- 场景类型：边界
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：requirement_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：分别准备等级9和10账号
2. 进入页面
3. 核对默认区间和状态
4. 升级后刷新

### 预期结果
- 等级9属于1-9；等级10属于10-19

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：requirement_exception。

## 等级段边界99到100

- 优先级：P1
- 场景类型：边界
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：requirement_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：分别准备等级99和100账号
2. 进入页面
3. 核对区间
4. 检查最高级特殊展示

### 预期结果
- 99属于90-99；100属于独立100区间

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：requirement_exception。

## 未解锁区间状态

- 优先级：P1
- 场景类型：状态
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：当前等级低于浏览区间
2. 浏览更高等级段
3. 检查锁状态和权益预览
4. 尝试点击

### 预期结果
- 未解锁权益显示灰锁，预览权限符合需求

### 分级原因
- 缺少可直接执行的接口 method/path。

## 已解锁区间状态

- 优先级：P1
- 场景类型：状态
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：当前等级高于浏览区间
2. 浏览较低等级段
3. 检查金色勾选
4. 打开权益详情

### 预期结果
- 已获得权益显示金色勾选

### 分级原因
- 缺少可直接执行的接口 method/path。

## 当前区间状态

- 优先级：P1
- 场景类型：状态
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：浏览当前等级段
2. 检查当前标识、勾选和锁
3. 对照各权益解锁等级

### 预期结果
- 当前区间内各权益根据具体解锁等级正确显示

### 分级原因
- 缺少可直接执行的接口 method/path。

## 列表滚动到末端

- 优先级：P1
- 场景类型：交互
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：等级列表完整
2. 连续滚动到底部
3. 检查末尾等级段
4. 反向滚动

### 预期结果
- 末尾内容可见，无截断和空白

### 分级原因
- 缺少可直接执行的接口 method/path。

## 列表刷新后保持位置

- 优先级：P1
- 场景类型：状态恢复
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：浏览非当前等级段
2. 触发数据刷新
3. 观察滚动位置和选中状态
4. 点击My Level

### 预期结果
- 刷新策略符合设计，My Level仍可正确回位

### 分级原因
- 缺少可直接执行的接口 method/path。

## 等级勋章权益

- 优先级：P1
- 场景类型：正常
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：选择含等级勋章的区间
2. 核对名称、图片和尺寸
3. 进入页面
4. 比较实际渲染

### 预期结果
- 勋章资源和展示与等级段匹配

### 分级原因
- 缺少可直接执行的接口 method/path。

## 进场特效权益

- 优先级：P1
- 场景类型：正常
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：选择已解锁进场特效账号
2. 核对MP4/PAG资源
3. 触发进场场景
4. 观察播放

### 预期结果
- 对应等级进场特效完整播放

### 分级原因
- 缺少可直接执行的接口 method/path。

## 房间图片消息权益

- 优先级：P1
- 场景类型：权限
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：准备已解锁与未解锁账号
2. 进入房间发送图片
3. 比较操作入口和服务响应
4. 核对等级状态

### 预期结果
- 仅满足等级要求的账号可使用

### 分级原因
- 缺少可直接执行的接口 method/path。

## 等级礼物权益

- 优先级：P1
- 场景类型：权限
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：准备不同等级账号
2. 查看等级礼物入口
3. 尝试赠送
4. 核对资产和日志

### 预期结果
- 礼物可见性、赠送权限和扣减符合配置

### 分级原因
- 缺少可直接执行的接口 method/path。

## 聊天气泡权益

- 优先级：P1
- 场景类型：正常
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：准备已解锁气泡账号
2. 发送聊天消息
3. 观察气泡资源
4. 切换场景

### 预期结果
- 气泡样式与对应等级一致

### 分级原因
- 缺少可直接执行的接口 method/path。

## 特殊ID权益

- 优先级：P1
- 场景类型：业务规则
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：检查不同等级段idTitle配置
2. 读取接口idTitle
3. 观察个人ID展示
4. 对比规则

### 预期结果
- 特殊ID位数和样式与等级段一致

### 分级原因
- 缺少可直接执行的接口 method/path。

## 权益重复配置

- 优先级：P1
- 场景类型：异常一致性
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：requirement_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：读取全部等级权益
2. 按type和资源识别重复项
3. 区分继承和新增
4. 与配置确认

### 预期结果
- 不应出现非预期重复或同级冲突

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：requirement_exception。

## 从高等级段回到当前等级

- 优先级：P1
- 场景类型：关联流程
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：当前等级70且正在查看90-99
2. 点击My Level
3. 观察滚动和选中状态
4. 核对权益内容

### 预期结果
- 回到70-79并正确高亮

### 分级原因
- 缺少可直接执行的接口 method/path。

## 从低等级段回到当前等级

- 优先级：P1
- 场景类型：关联流程
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：当前等级70且正在查看10-19
2. 点击My Level
3. 观察回位动画
4. 核对内容

### 预期结果
- 回到70-79，位置准确

### 分级原因
- 缺少可直接执行的接口 method/path。

## 已在当前等级段点击My Level

- 优先级：P1
- 场景类型：幂等
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：用例涉及限流、频控或幂等，Redis可能保存计数或锁，需要研发确认Key规则。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：当前已选中70-79
2. 点击My Level多次
3. 观察位置和请求
4. 检查动画

### 预期结果
- 不重复请求或抖动，状态保持正确

### 分级原因
- 缺少可直接执行的接口 method/path。

## 等级升级后My Level回位

- 优先级：P1
- 场景类型：状态迁移
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：页面打开期间等级从69升到70
2. 刷新数据
3. 浏览其他区间
4. 点击My Level

### 预期结果
- 回到升级后的70-79区间

### 分级原因
- 缺少可直接执行的接口 method/path。

## 列表未加载完成时点击My Level

- 优先级：P1
- 场景类型：异常
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：requirement_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：限制网络速度
2. 页面加载期间点击按钮
3. 等待数据返回
4. 观察最终位置

### 预期结果
- 按钮禁用或延迟执行，不跳到错误位置

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：requirement_exception。

## 接口失败时点击My Level

- 优先级：P1
- 场景类型：异常
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：requirement_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：财富接口失败
2. 点击My Level
3. 观察错误反馈
4. 恢复网络重试

### 预期结果
- 不崩溃，恢复后可正确回位

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：requirement_exception。

## 最高等级My Level

- 优先级：P1
- 场景类型：边界
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：requirement_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：等级100账号
2. 浏览其他区间
3. 点击My Level
4. 核对独立100区间

### 预期结果
- 准确定位Level 100

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：requirement_exception。

## 最低等级My Level

- 优先级：P1
- 场景类型：边界
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：requirement_exception
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：最低等级账号
2. 浏览高等级区间
3. 点击My Level
4. 核对起始区间

### 预期结果
- 准确定位最低等级区间

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：requirement_exception。

## 打开权益预览弹窗

- 优先级：P1
- 场景类型：正常
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：选择可预览权益
2. 点击权益卡片
3. 观察弹窗内容
4. 核对等级区间和权益名

### 预期结果
- 弹窗展示正确的区间、名称和预览资源

### 分级原因
- 缺少可直接执行的接口 method/path。

## 重复请求数据稳定

- 优先级：P1
- 场景类型：幂等
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：data_constraint_exception
- Redis可选证据：用例涉及限流、频控或幂等，Redis可能保存计数或锁，需要研发确认Key规则。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：账号数据不变化
2. 连续请求财富接口10次
3. 比较响应哈希
4. 对比MySQL和Redis

### 预期结果
- 业务数据保持一致，非业务时间字段除外

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：data_constraint_exception。

## 重新登录后数据一致

- 优先级：P1
- 场景类型：关联流程
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：完成两次真实登录
2. 每次提取新Token
3. 请求财富接口
4. 比较业务数据

### 预期结果
- 同一账号数据一致

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception。

## 财富接口响应性能

- 优先级：P1
- 场景类型：性能
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：测试环境稳定
2. 预热接口
3. 连续请求30次
4. 统计平均、P95和失败率

### 预期结果
- 性能阈值待确认；报告真实平均与P95

### 分级原因
- 缺少可直接执行的接口 method/path。

## 大量权益资源加载

- 优先级：P1
- 场景类型：性能
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：-
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：打开多个高等级权益
2. 记录图片和动画请求
3. 滚动列表
4. 观察内存和帧率

### 预期结果
- 资源按需加载，无明显卡顿或内存异常

### 分级原因
- 缺少可直接执行的接口 method/path。

## 升级后浏览新权益并回位

- 优先级：P1
- 场景类型：端到端
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：-
- Redis可选证据：用例涉及处理中互斥或锁语义，Redis可能存在临时状态Key。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：账号刚完成升级
2. 进入财富页面
3. 浏览新解锁权益
4. 切换其他区间
5. 点击My Level

### 预期结果
- 新权益解锁状态和回位目标均正确

### 分级原因
- 缺少可直接执行的接口 method/path。

## Token过期后恢复财富页面

- 优先级：P1
- 场景类型：端到端
- 接口：- 
- 接口字段：-
- 运行变量：-
- 质量分级：MANUAL_ONLY
- 脚本生成就绪：MANUAL_ONLY / manual
- 异常来源：api_contract_exception, state_machine_exception
- Redis可选证据：用例涉及登录态或身份认证，可选读取Redis登录缓存辅助定位401/403。
- 下一步：纳入人工测试清单

### 前置条件
- 需求包：财富等级
- 已准备当前用例所需账号、ticket、设备参数和运行变量。

### 操作步骤
1. 前置条件：准备即将过期Token
2. 打开页面触发失效
3. 重新登录
4. 恢复财富请求和页面状态

### 预期结果
- 重新认证后恢复真实数据，不丢失页面导航状态

### 分级原因
- 缺少可直接执行的接口 method/path。
- 异常来源：api_contract_exception, state_machine_exception。
