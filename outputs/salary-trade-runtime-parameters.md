# 工资交易 JMeter 运行参数

## 必要参数
- `salary_applicants_csv`：申请人账号CSV，默认读取 `data/salary-trade-applicants.csv`。
- `salary_accounts_csv`：多角色账号CSV，默认读取 `data/salary-trade-accounts.csv`。
- `salary_flow_slots_csv`：8条业务流槽位CSV，默认读取 `data/salary-trade-flow-slots.csv`。
- `salary_result_jtl`：JMeter结果文件路径。

## 启动示例
```powershell
$projectRoot = Split-Path -Parent $PSScriptRoot
$jmeter = $env:AUTOTEST_JMETER
& $jmeter -t (Join-Path $projectRoot 'outputs/salary-trade-case-driven.jmx') -Jproject_root=$projectRoot
```

## 规则
- 不同需求包使用独立 JMX 和独立报告。
- 平台先读取测试用例，再决定是否需要CSV参数化。
- 平台再读取 account_model.yaml，决定账号角色、凭证来源和DB/Redis证据。
- YAML 不保存真实 ticket、密码或公司密钥。
