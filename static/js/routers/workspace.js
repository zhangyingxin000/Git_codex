(function bootstrapWorkspaceRouter(global) {
  const namespace = global.QualityHub = global.QualityHub || {};
  namespace.routers = namespace.routers || {};

  const aliases = {
    manual: "sources",
    changes: "sources",
    apis: "sources",
    runs: "automation",
    operations: "automation",
    points: "sources",
    cases: "sources",
    database: "dataquality",
    redis: "dataquality",
  };
  const titles = {
    overview: ["质量总览", "测试资产、执行任务、数据验证与报告证据统一管理"],
    sources: ["需求资产", "需求输入、测试点、用例与接口覆盖归纳"],
    automation: ["执行中心", "调度接口测试、性能测试和真实链路执行"],
    dataquality: ["数据验证", "接口返回、MySQL、Redis与后台配置一致性核对"],
    reports: ["报告中心", "测试结论、缺陷风险、性能结果与完整证据归档"],
  };

  function switchTab(requestedId, context) {
    const id = aliases[requestedId] || requestedId;
    const {$, $$, current, data} = context;
    if (!current) {
      $$(".side-tab").forEach(item => item.classList.toggle("active", item.dataset.tab === id));
      return id;
    }
    $("#welcome")?.classList.add("hidden");
    $("#workspace")?.classList.remove("hidden");
    $$(".tab").forEach(item => item.classList.add("hidden"));
    $("#" + id)?.classList.remove("hidden");
    $$(".tabs button,.side-tab").forEach(item => item.classList.toggle("active", item.dataset.tab === id));
    if (data?.project) {
      const title = titles[id] || [data.project.name, data.project.description || "质量工程控制台"];
      $("#pageTitle").textContent = title[0];
      $("#subtitle").textContent = title[1];
    }
    return id;
  }

  namespace.routers.workspace = {switchTab};
})(window);
