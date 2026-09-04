(function bootstrapTaskService(global) {
  const namespace = global.QualityHub = global.QualityHub || {};
  namespace.services = namespace.services || {};

  async function submit(taskType, payload = {}) {
    return namespace.services.api.request("/api/tasks", {
      method: "POST",
      body: JSON.stringify({task_type: taskType, ...payload}),
    });
  }

  async function get(taskId) {
    return namespace.services.api.request(`/api/tasks/${encodeURIComponent(taskId)}`);
  }

  async function wait(taskId, options = {}) {
    const interval = options.interval || 800;
    const timeout = options.timeout || 120000;
    const started = Date.now();
    while (Date.now() - started < timeout) {
      const task = await get(taskId);
      options.onProgress?.(task);
      if (["PASSED", "FAILED", "INTERRUPTED"].includes(task.status)) return task;
      await new Promise(resolve => setTimeout(resolve, interval));
    }
    throw new Error("后台任务等待超时，可在执行中心继续查看任务状态");
  }

  namespace.services.tasks = {submit, get, wait};
})(window);
