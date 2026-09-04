(function bootstrapNotifications(global) {
  const namespace = global.QualityHub = global.QualityHub || {};
  namespace.components = namespace.components || {};

  function toast(message, type) {
    const text = String(message || "操作完成");
    let resolvedType = type;
    if (!resolvedType) {
      resolvedType = /失败|错误|异常|不存在|不能为空|请选择/.test(text)
        ? "error"
        : /警告|风险|阻止|卡点|未完成/.test(text)
          ? "warning"
          : /完成|成功|已连接|已保存|已生成|正常/.test(text)
            ? "success"
            : "info";
    }
    const container = document.querySelector("#toast");
    if (!container) return;
    const node = document.createElement("div");
    node.className = `toast ${resolvedType}`;
    node.textContent = text;
    node.setAttribute("role", "status");
    container.append(node);
    setTimeout(() => {
      node.style.opacity = "0";
      node.style.transform = "translateY(8px)";
      setTimeout(() => node.remove(), 220);
    }, 3200);
  }

  namespace.components.notifications = {toast};
})(window);
