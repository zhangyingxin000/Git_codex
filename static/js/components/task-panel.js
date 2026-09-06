(function bootstrapTaskPanel(global) {
  const namespace = global.QualityHub = global.QualityHub || {};
  namespace.components = namespace.components || {};

  const phaseLabels = {
    jmeter_mcp: '性能预检',
    preparing: '准备环境',
    mcp_connected: '连接执行器',
    jmx_import: '导入脚本',
    jmx_ready: '脚本就绪',
    jmeter_starting: '启动JMeter',
    jmeter_execution: '执行性能请求',
    automatic_stop: '阈值自动停止',
    jtl_collection: '回收JTL',
    html_report: '生成HTML报告',
    artifact_summary: '整理执行产物',
    mcp_completed: 'MCP执行完成',
    jtl_analysis: '指标诊断',
    ai_review: 'AI性能复盘',
    scenario_report: '统一场景报告',
    completed: '完成',
    stage: '性能阶段',
  };

  function progressCell(task, escapeHtml) {
    const progress = task.progress || {};
    const message = task.error || progress.message || task.result?.message || task.result?.status || '-';
    if (progress.percent == null) return escapeHtml(message);
    const percent = Math.max(0, Math.min(100, Number(progress.percent) || 0));
    const phase = phaseLabels[progress.phase] || progress.phase || '处理中';
    return `<div class="task-progress"><div class="task-progress-head"><b>${escapeHtml(phase)}</b><span>${escapeHtml(percent)}%</span></div><div class="task-progress-track"><i style="width:${percent}%"></i></div><small>${escapeHtml(message)}</small></div>`;
  }

  function render(tasks, escapeHtml) {
    const allTasks = Array.isArray(tasks) ? tasks : [];
    const packageTasks = allTasks.filter(task => task.payload?.package_id);
    const rows = packageTasks.slice(0, 8);
    const hiddenDemoTasks = allTasks.length - packageTasks.length;
    const hiddenOlderTasks = packageTasks.length - rows.length;
    const hiddenNote = hiddenDemoTasks > 0 || hiddenOlderTasks > 0
      ? `<p class="policy-note">已隐藏 ${hiddenDemoTasks} 条演示或系统任务${hiddenOlderTasks ? `，以及 ${hiddenOlderTasks} 条较早记录` : ''}，避免与当前需求包执行记录混在一起。</p>`
      : '';
    return `<div class="card"><div class="diagnosis-head"><div><span class="tag PASSED">BACKGROUND TASKS</span><h2>后台执行任务</h2><p>长时间运行不会阻塞页面，刷新后仍可读取任务状态和结果。</p></div><button class="primary" onclick="submitCurrentPackageBackgroundTask()">后台运行当前需求包</button></div>${hiddenNote}${rows.length ? `<table><thead><tr><th>状态</th><th>类型</th><th>需求包</th><th>开始</th><th>进度/结果</th><th></th></tr></thead><tbody>${rows.map(task => `<tr><td><span class="tag ${task.status === 'PASSED' ? 'PASSED' : task.status === 'FAILED' ? 'P0' : 'P1'}">${escapeHtml(task.status)}</span></td><td>${escapeHtml(task.task_type)}</td><td>${escapeHtml(task.payload.package_id)}</td><td>${escapeHtml(task.started_at || task.created_at || '-')}</td><td>${progressCell(task, escapeHtml)}</td><td>${['PENDING','RUNNING'].includes(task.status) ? `<button class="small" onclick="cancelBackgroundTask('${escapeHtml(task.task_id)}')">停止</button>` : ''}</td></tr>`).join('')}</tbody></table>` : '<div class="empty"><b>当前没有正式需求包后台任务</b><p>可直接运行当前选中的需求包；演示任务不会混入这里。</p></div>'}</div>`;
  }

  namespace.components.taskPanel = {render};
})(window);
