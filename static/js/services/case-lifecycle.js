(function bootstrapCaseLifecycleService(global) {
  const namespace = global.QualityHub = global.QualityHub || {};
  namespace.services = namespace.services || {};

  const request = (...args) => namespace.services.api.request(...args);
  const jsonRequest = (path, method, payload = {}) => request(path, {
    method,
    body: JSON.stringify(payload),
  });

  namespace.services.caseLifecycle = {
    update: (caseId, lifecycleStatus, note, actor = "workbench") => jsonRequest(
      `/api/cases/${encodeURIComponent(caseId)}/lifecycle`,
      "PUT",
      { lifecycle_status: lifecycleStatus, note, actor },
    ),
    history: caseId => request(`/api/cases/${encodeURIComponent(caseId)}/lifecycle-history`),
    bulkUpdate: (projectId, caseIds, lifecycleStatus, note, actor = "workbench") => jsonRequest(
      `/api/projects/${encodeURIComponent(projectId)}/cases/lifecycle/bulk`,
      "PUT",
      { case_ids: caseIds, lifecycle_status: lifecycleStatus, note, actor },
    ),
  };
})(window);
