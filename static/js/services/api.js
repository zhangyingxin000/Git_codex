(function bootstrapApiService(global) {
  const namespace = global.QualityHub = global.QualityHub || {};
  namespace.services = namespace.services || {};

  const select = selector => document.querySelector(selector);
  const selectAll = selector => [...document.querySelectorAll(selector)];
  const escapeHtml = value => String(value ?? "").replace(
    /[&<>"']/g,
    character => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"})[character],
  );

  async function request(path, options = {}) {
    const next = {...options};
    next.headers = {"Content-Type": "application/json", ...(next.headers || {})};
    const response = await fetch(path, next);
    let payload = {};
    try {
      payload = await response.json();
    } catch {}
    if (!response.ok) {
      if (response.status === 404 && path.startsWith("/api/")) {
        throw new Error("平台后端尚未加载此功能，请重新启动 AutoTest AI 后重试");
      }
      throw new Error(payload.error || `请求失败（HTTP ${response.status}）`);
    }
    return payload;
  }

  namespace.services.api = {request, select, selectAll, escapeHtml};
})(window);
