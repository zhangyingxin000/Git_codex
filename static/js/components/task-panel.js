(function bootstrapTaskPanel(global) {
  const namespace = global.QualityHub = global.QualityHub || {};
  namespace.components = namespace.components || {};

  function render(tasks, escapeHtml) {
    const rows = Array.isArray(tasks) ? tasks : [];
    return `<div class="card"><div class="diagnosis-head"><div><span class="tag PASSED">BACKGROUND TASKS</span><h2>后台执行任务</h2><p>长时间运行不会阻塞页面，刷新后仍可读取任务状态和结果。</p></div><button class="primary" onclick="submitCurrentPackageBackgroundTask()">后台运行当前需求包</button></div>${rows.length ? `<table><thead><tr><th>状态</th><th>类型</th><th>需求包</th><th>开始</th><th>结果</th></tr></thead><tbody>${rows.slice(0,20).map(task => `<tr><td><span class="tag ${task.status === 'PASSED' ? 'PASSED' : task.status === 'FAILED' ? 'P0' : 'P1'}">${escapeHtml(task.status)}</span></td><td>${escapeHtml(task.task_type)}</td><td>${escapeHtml(task.payload?.package_id || '-')}</td><td>${escapeHtml(task.started_at || task.created_at || '-')}</td><td>${escapeHtml(task.error || task.result?.status || '-')}</td></tr>`).join('')}</tbody></table>` : '<div class="empty"><b>暂无后台任务</b><p>适合将 Newman、pytest 和需求包流水线放到后台运行。</p></div>'}</div>`;
  }

  namespace.components.taskPanel = {render};
})(window);
