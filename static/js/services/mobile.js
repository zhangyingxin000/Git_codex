(function bootstrapMobileService(global) {
  const namespace = global.QualityHub = global.QualityHub || {};
  namespace.services = namespace.services || {};

  async function catalog(configPath = "") {
    const query = configPath ? `?config_path=${encodeURIComponent(configPath)}` : "";
    return namespace.services.api.request(`/api/mobile/catalog${query}`);
  }

  async function run(options) {
    return namespace.services.tasks.submit("mobile_appium", {options});
  }

  namespace.services.mobile = {catalog, run};
})(window);
