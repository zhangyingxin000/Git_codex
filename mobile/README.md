# Android移动端自动化

正式执行链路：

```text
Appium Inspector辅助定位控件
-> YAML页面对象集中维护
-> 工作台选择设备和场景
-> pytest顶层执行
-> Appium操作真机或模拟器
-> Allure报告、原始证据和性能解读归档
```

## 工具职责

- Appium Inspector只用于人工查看控件树和定位信息，不进入CI执行链路。
- `mobile/pages/*.yaml`集中维护控件定位，业务场景不重复写定位值。
- `mobile/scenarios/*.yaml`维护可复用步骤、风险等级和数据依赖。
- `mobile/pytest_runtime.py`是显式的pytest运行入口；普通平台单元测试不会自动连接手机。
- `scripts/run_mobile_ci.py`负责Appium会话、步骤执行、ADB性能取证和Allure原始结果。
- `scripts/mobile_pytest_evidence.py`将pytest控制台、JUnit和执行链证据归入同一运行批次。

## 覆盖口径

平台通用模板支持登录、注册、支付、CRUD、UI断言、网络异常、系统中断和Android性能采集。模板存在不等于项目已经验证，报告只把实际执行记录为`PASSED`的步骤列入已验证范围。

Soulfree当前正式验证范围：

- 房间主流程、房间页面和包名断言。
- 前后台恢复、保留登录状态重启。
- 房间滑动渲染。
- 冷/热启动、CPU、PSS内存、FPS、卡顿帧、OOM、崩溃和ANR采集。

Soulfree当前未验证范围：

- 注册、支付、删除等写操作。
- 断网重连、弱网、来电和锁屏等模拟器场景。

启动广告检查是`soulfree-room-smoke`完整回归的第一阶段，不再作为独立入口。流程每轮先通过ADB `am force-stop`彻底停止App，再重新拉起并连续采集3次启动页，逐次断言包名、页面源码和截图可用，并比较截图及页面源码的SHA-256指纹；随后跳过实际出现的广告，继续执行房间主流程、前后台恢复、重启与性能采集，所有证据进入同一份Allure报告。广告未出现时，跳过步骤记录为`SKIPPED`并保留原因；只有产品明确要求每次展示不同内容时，才将`require_variation`设为`true`作为强制门禁。

写操作和高风险操作默认关闭。只有准备好隔离测试账号、可清理测试数据和测试支付环境后，才允许在本地配置中显式开启对应门禁。

## 报告目录

每次运行独立归档：

```text
reports/mobile-ci/{run_id}/
|- summary.json
|- coverage-scope.json
|- pytest-console.log
|- pytest-junit.xml
|- pytest-evidence.json
|- appium.log
|- allure-results/
|- allure-report/
`- devices/{udid}/
   |- workflow-result.json
   |- performance.json
   |- performance-interpretation.md
   |- runtime-logcat.txt
   `- screenshots and page source
```

性能解读使用当前行业常见参考线：冷启动小于2000ms、热启动小于1000ms、FPS不低于55、卡顿帧不高于5%。CPU持续高于60%标记为关注项；单次峰值不直接判定缺陷，应使用Android Studio CPU Profiler或Perfetto复测并定位线程与方法。

## Jenkins混合设备链路

当前Jenkins定义包含两条常规Android执行通道和一条按需稳定性通道：

```text
GitHub Push
-> Windows Agent: USB真机设备池
-> Windows Agent: Android Studio模拟器设备池
-> 可选: Windows Agent执行受控Monkey稳定性场景
-> pytest + Appium
-> JUnit + Allure + ADB原始证据上传至ECS Jenkins
-> ECS统一展示和保留报告
```

真机通道使用`config/mobile-ci.soulfree.yaml`。Jenkins参数`ANDROID_REAL_UDIDS`接收逗号分隔的ADB序列号；多台设备先顺序执行，避免共享Appium端口造成不稳定。模拟器通道使用`config/mobile-ci.emulator.yaml`，由`scripts/manage_android_emulator.py`启动指定AVD并等待`sys.boot_completed=1`后再执行。

Windows执行节点需要预先安装JDK、Android SDK、Android Emulator、Appium和Allure，并使用Jenkins`windows`标签。Jenkins控制器部署在ECS，本地Windows Agent主动连接控制器并执行任务，ECS不需要访问本地USB端口；流水线归档动作会自动把报告和制品上传到Jenkins控制器。

外部Docker Grid与KVM执行能力仍通过`config/mobile-ci.grid.yaml`和`server_mode: external`保留，但不进入当前Jenkins日常参数。未来获得支持Nested Virtualization且提供`/dev/kvm`的Linux机器后，可以恢复Grid设备清单和Linux模拟器通道，无需重写页面对象、业务场景或报告模型。

未来Grid节点必须能够访问同一APK URL或共享容器路径。Grid只负责会话路由，不负责创建Android模拟器；Docker模拟器必须由Linux宿主机提供`/dev/kvm`。如果Grid运行节点无法通过ADB访问设备，CPU/PSS/FPS、网络切换、来电和Monkey等能力会继续明确标记为未验证。

APK通过`scripts/prepare_android_apk.py`从Jenkins可访问的本地路径或直接下载地址获取。脚本会拒绝HTML下载页，校验APK结构和可选SHA-256，并记录包名、版本、文件大小及不可变制品路径。

## Monkey稳定性

`android-monkey-stability`是默认关闭的夜间稳定性场景。它固定随机seed、限制系统按键和应用切换，并归档事件日志；发现Crash、ANR、原生崩溃或事件未完整注入时判定失败。

ECS上的Jenkins通过`RUN_ANDROID_MONKEY`发起任务，实际命令仍由能访问ADB设备的Windows Agent执行。`ANDROID_MONKEY_TARGET`选择真机或Android Studio模拟器；选择真机时读取`ANDROID_REAL_UDIDS`，选择模拟器时读取`ANDROID_AVD_NAME`。流水线只有在`CONFIRM_ANDROID_MONKEY_ISOLATED_ENV=true`时才会为本次任务临时放开数据写入、高风险操作和Monkey门禁，完成后归档Monkey日志、截图、JUnit、Allure及APK元数据。ECS本机不需要设备，也不会直接执行ADB命令。
