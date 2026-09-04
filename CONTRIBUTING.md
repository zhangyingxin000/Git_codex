# Contributing

下面是如何在本地运行格式化、测试与 secret 扫描的说明。

本地快速开始:

1. 安装开发依赖（建议使用虚拟环境）:

   python -m pip install --upgrade pip
   pip install -r requirements-dev.txt

2. 运行格式化/lint:

   # ruff 检查并自动修复（在 pre-commit 钩子中启用 --fix）
   ruff .
   # black 仅检查（要自动格式化请运行 black .）
   black --check .

3. 运行测试（示例使用 pytest）:

   pytest -q

   如果你的测试需要在 PowerShell 下执行，使用 PowerShell Core (pwsh) 运行：

   pwsh -Command "pytest -q"

4. detect-secrets baseline:

   初次将检测密钥时，请在本地生成 baseline 并提交：

   pip install detect-secrets
   detect-secrets scan > .secrets.baseline

   然后用 detect-secrets audit 检查：

   detect-secrets audit .secrets.baseline

CI（GitHub Actions）流程在发现仓库没有 .secrets.baseline 时会失败，提示你先生成并提交 baseline。这是为了避免把真实 secret 误判为 baseline 并放行。
