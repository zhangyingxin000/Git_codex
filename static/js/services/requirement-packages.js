(function bootstrapRequirementPackageService(global) {
  const namespace = global.QualityHub = global.QualityHub || {};
  namespace.services = namespace.services || {};

  const request = (...args) => namespace.services.api.request(...args);
  const projectPath = projectId => `/api/projects/${encodeURIComponent(projectId)}`;
  const packagesPath = projectId => `${projectPath(projectId)}/requirement-packages`;
  const packagePath = (projectId, packageId) => (
    `${packagesPath(projectId)}/${encodeURIComponent(packageId)}`
  );
  const jsonRequest = (path, method, payload = {}) => request(path, {
    method,
    body: JSON.stringify(payload),
  });

  const catalog = projectId => request(packagesPath(projectId));
  const create = (projectId, payload) => jsonRequest(packagesPath(projectId), "POST", payload);
  const accountModel = (projectId, packageId, regenerate = false) => (
    regenerate
      ? jsonRequest(`${packagePath(projectId, packageId)}/account-model`, "POST")
      : request(`${packagePath(projectId, packageId)}/account-model`)
  );
  const resourceManifest = (projectId, packageId) => (
    request(`${packagePath(projectId, packageId)}/resource-manifest`)
  );
  const saveResourceManifest = (projectId, packageId, payload) => (
    jsonRequest(`${packagePath(projectId, packageId)}/resource-manifest`, "POST", payload)
  );
  const resourcePreflight = (projectId, packageId, rerun = false) => (
    rerun
      ? jsonRequest(`${packagePath(projectId, packageId)}/resource-preflight`, "POST")
      : request(`${packagePath(projectId, packageId)}/resource-preflight`)
  );
  const executionPlan = (projectId, packageId, regenerate = false, payload = {}) => (
    regenerate
      ? jsonRequest(`${packagePath(projectId, packageId)}/execution-plan`, "POST", payload)
      : request(`${packagePath(projectId, packageId)}/execution-plan`)
  );
  const toolAssets = (projectId, packageId, payload) => (
    jsonRequest(`${packagePath(projectId, packageId)}/tool-assets`, "POST", payload)
  );
  const apiTestCases = (projectId, packageId, payload = {}) => (
    jsonRequest(`${packagePath(projectId, packageId)}/api-test-cases`, "POST", payload)
  );
  const compileInterfaceTests = (projectId, packageId, payload = {}) => (
    jsonRequest(`${packagePath(projectId, packageId)}/interface-tests/compile`, "POST", payload)
  );
  const runInterfaceTests = (projectId, packageId, payload = {}) => (
    jsonRequest(`${packagePath(projectId, packageId)}/interface-tests/newman/run`, "POST", payload)
  );
  const createRun = (projectId, packageId, payload) => (
    jsonRequest(`${packagePath(projectId, packageId)}/runs`, "POST", payload)
  );
  const reportIndex = (projectId, packageId) => (
    request(`${packagePath(projectId, packageId)}/report-index`)
  );
  const performanceOptions = (projectId, packageId) => (
    request(`${packagePath(projectId, packageId)}/performance-options`)
  );
  const runTool = (projectId, packageId, tool, payload) => (
    jsonRequest(`${packagePath(projectId, packageId)}/${tool}/run`, "POST", payload)
  );
  const generateReport = (projectId, packageId, reportType, payload) => (
    jsonRequest(`${packagePath(projectId, packageId)}/${reportType}`, "POST", payload)
  );

  namespace.services.requirementPackages = {
    catalog,
    create,
    accountModel,
    resourceManifest,
    saveResourceManifest,
    resourcePreflight,
    executionPlan,
    apiTestCases,
    compileInterfaceTests,
    runInterfaceTests,
    toolAssets,
    createRun,
    reportIndex,
    performanceOptions,
    runNewman: (projectId, packageId, payload) => runTool(projectId, packageId, "newman", payload),
    runPytest: (projectId, packageId, payload) => runTool(projectId, packageId, "pytest", payload),
    runPipeline: (projectId, packageId, payload) => runTool(projectId, packageId, "pipeline", payload),
    scenarioReport: (projectId, packageId, payload) => generateReport(projectId, packageId, "scenario-report", payload),
    aiReview: (projectId, packageId, payload) => generateReport(projectId, packageId, "ai-review", payload),
    performanceReview: (projectId, packageId, payload) => generateReport(projectId, packageId, "performance-ai-review", payload),
    newmanAnalysis: (projectId, packageId, payload) => generateReport(projectId, packageId, "newman-analysis", payload),
    loadPlan: (projectId, packageId, payload) => generateReport(projectId, packageId, "jmeter-load-plan", payload),
    loadRun: (projectId, packageId, payload) => generateReport(projectId, packageId, "jmeter-load-run", payload),
  };
})(window);
