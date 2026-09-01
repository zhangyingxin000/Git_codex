# 工资代理快速结算：测试用例到 JMeter 脚本映射

## 生成原则
测试用例是输入，JMeter 是执行载体。平台先把用例结构化，再按步骤生成线程组、请求、提取器、断言和报告标签。

## 覆盖流程
- A：创建后申请人取消；账号槽位：applicant_01；订单变量：flow_a_order_no；线程组：工资交易流程A：创建后申请人取消；状态：ready
- B：创建后代理拒绝；账号槽位：applicant_02；订单变量：flow_b_order_no；线程组：工资交易流程B：创建后代理拒绝；状态：planned
- C：接受并转账后申请人确认完成；账号槽位：applicant_03；订单变量：flow_c_order_no；线程组：工资交易流程C：完整成交；状态：planned
- D：转账后申请人投诉，投诉失败；账号槽位：applicant_04；订单变量：flow_d_order_no；线程组：工资交易流程D：投诉失败；状态：planned
- E：转账后申请人投诉，投诉成功；账号槽位：applicant_05；订单变量：flow_e_order_no；线程组：工资交易流程E：投诉成功；状态：planned
- F：创建后代理不处理直到订单过期；账号槽位：applicant_06；订单变量：flow_f_order_no；线程组：工资交易流程F：待接单超时；状态：blocked
- G：代理接受后不转账，12小时过期取消；账号槽位：applicant_07；订单变量：flow_g_order_no；线程组：工资交易流程G：已接受未转账超时；状态：blocked
- H：代理已转账后申请人24小时不确认，订单自动完成；账号槽位：applicant_08；订单变量：flow_h_order_no；线程组：工资交易流程H：已转账未确认超时完成；状态：blocked

## 当前缺口
- P1 超时流程：3条超时流程需要测试环境提供时间加速或后台任务触发方式。

## YAML/CSV 边界
- YAML：环境、工具路径、只读数据源、报告路径、CSV路径。
- 单账号需求：可直接使用运行参数、本机凭证、登录接口或Redis只读缓存。
- 多账号/多流程需求：使用CSV承载账号、角色、国家币种、流程槽位、金额、循环次数等执行数据。
- account_model.yaml：每个需求包自己的账号规则，JMeter生成前必须先读取它。

## 生成产物
- JMX：C:\Users\DELL\Documents\Codex\2026-08-19\new-chat\outputs\AutoTest-AI\outputs\salary-trade-case-driven.jmx
- Manifest：C:\Users\DELL\Documents\Codex\2026-08-19\new-chat\outputs\AutoTest-AI\outputs\salary-trade-case-jmeter-manifest.json
- 账号模型：C:\Users\DELL\Documents\Codex\2026-08-19\new-chat\outputs\AutoTest-AI\requirements\salary-trade\account_model.yaml
- 账号CSV：C:\Users\DELL\Documents\Codex\2026-08-19\new-chat\outputs\AutoTest-AI\data\salary-trade-accounts.csv
- 申请人CSV：C:\Users\DELL\Documents\Codex\2026-08-19\new-chat\outputs\AutoTest-AI\data\salary-trade-applicants.csv
- 流程槽位CSV：C:\Users\DELL\Documents\Codex\2026-08-19\new-chat\outputs\AutoTest-AI\data\salary-trade-flow-slots.csv
- Skill：C:\Users\DELL\Documents\Codex\2026-08-19\new-chat\outputs\AutoTest-AI\skills\jmeter-script-generation\SKILL.md
