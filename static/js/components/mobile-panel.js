(function bootstrapMobilePanel(global) {
  const namespace = global.QualityHub = global.QualityHub || {};
  namespace.components = namespace.components || {};

  function statusClass(status) {
    return status === "READY" || status === "PASSED" ? "PASSED" : status === "BLOCKED" || status === "FAILED" ? "FAILED" : "P1";
  }

  function deviceKindLabel(kind) {
    if (kind === "emulator") return "模拟器";
    if (kind === "physical") return "真机";
    return "远程设备";
  }

  function taskProgress(task, escapeHtml) {
    if (!task) return "";
    const progress = task.progress || {};
    const percent = Math.max(0, Math.min(100, Number(progress.percent) || 0));
    const message = task.error || progress.message || task.result?.message || task.status;
    const displayStatus = task.result?.status || task.status;
    const alerts = task.result?.performance_alerts || [];
    const alertText = alerts.flatMap(item => item.failed_checks || []).map(item => `${item.name}: ${item.actual} / ${item.limit}`).join("；");
    const resultActions = task.result?.allure_url
      ? `<div class="hub-action-row"><button class="small" onclick="openReport('${escapeHtml(task.result.allure_url)}')">Allure</button>${task.result.pytest_evidence_url ? `<button class="small" onclick="openReport('${escapeHtml(task.result.pytest_evidence_url)}')">pytest证据</button>` : ""}${task.result.coverage_url ? `<button class="small" onclick="openReport('${escapeHtml(task.result.coverage_url)}')">覆盖范围</button>` : ""}</div>`
      : "";
    return `<div class="mobile-task-state"><div><span class="tag ${statusClass(displayStatus)}">${escapeHtml(displayStatus)}</span><b>${escapeHtml(progress.phase || "移动端执行")}</b><span>${escapeHtml(percent)}%</span></div><div class="task-progress-track"><i style="width:${percent}%"></i></div><small>${escapeHtml(message || "-")}${alertText ? `<br>性能提醒：${escapeHtml(alertText)}` : ""}</small>${["PENDING", "RUNNING"].includes(task.status) ? `<button class="small" onclick="cancelBackgroundTask('${escapeHtml(task.task_id)}')">停止任务</button>` : resultActions}</div>`;
  }

  function render(catalog, tasks, escapeHtml) {
    if (!catalog) {
      return `<section class="card mobile-automation-panel"><div class="diagnosis-head"><div><span class="tag P1">MOBILE</span><h2>移动端自动化</h2><p>正在读取设备、页面对象和场景。</p></div><button class="small" onclick="refreshMobileCatalog()">刷新</button></div></section>`;
    }
    const devices = catalog.devices || [];
    const scenarios = catalog.scenarios || [];
    const pageObjects = catalog.page_objects || [];
    const mobileTasks = (tasks || []).filter(task => task.task_type === "mobile_appium");
    const activeTask = mobileTasks.find(task => ["PENDING", "RUNNING"].includes(task.status)) || mobileTasks[0];
    const blockers = catalog.blockers || [];
    const coverage = catalog.coverage || {};
    const currentProject = coverage.current_project || {};
    const platformSupported = coverage.platform_supported || [];
    const configuredScope = currentProject.configured_scope || [];
    const notVerified = currentProject.explicitly_not_verified || [];
    const reproducibleScenarios = currentProject.registered_reproducible_scenarios || [];
    const latestRuns = (catalog.latest_runs || []).slice(0, 5);
    const executionChannel = catalog.server_mode === "external" ? "APPIUM GRID" : "LOCAL APPIUM";
    const deviceOptions = devices.length
      ? devices.map(device => `<label class="mobile-choice"><input type="checkbox" name="mobileDevice" value="${escapeHtml(device.udid)}" checked><span><b>${escapeHtml(device.model || device.udid)}</b><small>${escapeHtml(deviceKindLabel(device.kind))} · ${escapeHtml(device.udid)} · ${escapeHtml(device.source || catalog.device_source || "adb")}</small></span></label>`).join("")
      : `<p class="policy-note">未发现设备。请先启动 Android Studio 模拟器，或连接已开启 USB 调试的手机。</p>`;
    const scenarioOptions = scenarios.length
      ? scenarios.map(item => `<label class="mobile-choice"><input type="checkbox" name="mobileScenario" value="${escapeHtml(item.id)}" ${item.enabled ? "checked" : ""}><span><b>${escapeHtml(item.name)}</b><small>${escapeHtml(item.step_count)} 步 · ${escapeHtml(item.category)}${item.requires_emulator ? " · 仅模拟器系统事件" : ""}</small></span>${item.high_risk ? '<em class="tag FAILED">高风险</em>' : item.mutates_data ? '<em class="tag P1">写操作</em>' : '<em class="tag PASSED">只读</em>'}</label>`).join("")
      : `<p class="policy-note">尚未维护可执行场景。</p>`;
    const runRows = latestRuns.length
      ? latestRuns.map(run => `<tr><td><span class="tag ${statusClass(run.quality_status || run.status)}">${escapeHtml(run.quality_status || run.status)}</span></td><td>${escapeHtml(run.run_id)}</td><td>${escapeHtml((run.finished_at || run.started_at || "-").replace("T", " "))}</td><td><button class="small" onclick="openReport('${escapeHtml(run.allure_url)}')">Allure</button>${run.pytest_evidence_url ? `<button class="small" onclick="openReport('${escapeHtml(run.pytest_evidence_url)}')">pytest</button>` : ""}${run.coverage_url ? `<button class="small" onclick="openReport('${escapeHtml(run.coverage_url)}')">范围</button>` : ""}</td></tr>`).join("")
      : `<tr><td colspan="4">尚无移动端运行报告</td></tr>`;
    return `<section class="card mobile-automation-panel"><div class="diagnosis-head"><div><span class="tag ${statusClass(catalog.status)}">PYTEST + ${executionChannel} · ${escapeHtml(catalog.status)}</span><h2>移动端自动化</h2><p>Inspector 仅辅助识别控件；pytest 调度 Appium 操作设备，并回收 Allure、性能数据和原始证据。</p></div><button class="small" onclick="refreshMobileCatalog()">刷新设备</button></div>${blockers.length ? `<div class="mobile-blockers"><b>运行前还需处理</b><span>${blockers.map(escapeHtml).join("；")}</span></div>` : ""}<details class="compact-details" open><summary><b>能力与验证口径</b><span>${escapeHtml(currentProject.name || "当前项目")}</span></summary><p class="policy-note"><b>平台支持：</b>${escapeHtml(platformSupported.join("；") || "尚未声明")}</p><p class="policy-note"><b>当前配置：</b>${escapeHtml(configuredScope.join("；") || "尚未声明")}</p><p class="policy-note"><b>尚未验证：</b>${escapeHtml(notVerified.join("；") || "无显式未验证项")}</p>${reproducibleScenarios.length ? `<p class="policy-note"><b>已登记可复现：</b>${escapeHtml(reproducibleScenarios.map(item => `${item.name}（${item.status}）`).join("；"))}</p>` : ""}</details><div class="mobile-config-grid"><div><label>移动端配置</label><input id="mobileConfigPath" value="${escapeHtml(catalog.config_path || "config/mobile-ci.local.yaml")}"><label>APK 地址</label><input id="mobileApkPath" value="${escapeHtml(catalog.apk_path || "")}" placeholder="${catalog.server_mode === "external" ? "Grid节点可访问的APK地址" : "本机 APK 完整路径"}"><small>${catalog.installed_package ? `也可直接运行已安装应用：${escapeHtml(catalog.installed_package)}` : "APK 路径只用于本次任务，不写死到页面对象或场景文件中。"}</small></div><div><label>页面对象</label><div class="asset-chip-row">${pageObjects.length ? pageObjects.map(item => `<span class="asset-chip ready">${escapeHtml(item.name)} · ${escapeHtml(item.element_count)} 个控件</span>`).join("") : '<span class="asset-chip pending">尚未维护</span>'}</div><small>Appium Inspector 找到的新控件统一补到 mobile/pages/*.yaml。</small></div></div><div class="mobile-selection-grid"><fieldset><legend>执行设备</legend>${deviceOptions}</fieldset><fieldset><legend>执行场景</legend>${scenarioOptions}</fieldset></div><div class="hub-action-row"><button class="primary" onclick="submitMobileAutomationTask()" ${activeTask && ["PENDING", "RUNNING"].includes(activeTask.status) ? "disabled" : ""}>后台运行所选场景</button><span class="policy-note">真机和模拟器使用同一套页面对象；弱网、来电等系统事件只在模拟器执行。</span></div>${taskProgress(activeTask, escapeHtml)}<details class="compact-details"><summary><b>最近移动端报告</b><span>${escapeHtml(latestRuns.length)} 次运行</span></summary><table><thead><tr><th>状态</th><th>运行批次</th><th>完成时间</th><th>报告</th></tr></thead><tbody>${runRows}</tbody></table></details></section>`;
  }

  namespace.components.mobilePanel = {render};
})(window);
