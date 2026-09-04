# Route Test Coverage

- Routes: 122
- Covered by static evidence: 41
- Unmapped: 69
- Integration required: 12
- P0 routes: 19
- P0 unmapped: 0

| Priority | Methods | Path | Coverage | Evidence |
| --- | --- | --- | --- | --- |
| P0 | GET | `/api/health` | COVERED | test_route_coverage.py, test_task_queue.py |
| P2 | GET | `/api/system/storage-policy` | UNMAPPED | - |
| P2 | GET | `/api/system/environment-config` | COVERED | handler-reference |
| P2 | GET | `/api/system/route-coverage` | COVERED | handler-reference |
| P0 | GET | `/api/tasks` | COVERED | test_route_coverage.py, test_task_queue.py |
| P2 | GET | `/api/tasks/types` | COVERED | test_route_coverage.py, test_task_queue.py |
| P0 | GET | `/api/tasks/{task_id}` | COVERED | test_route_coverage.py, test_task_queue.py |
| P0 | POST | `/api/tasks` | COVERED | test_route_coverage.py, test_task_queue.py |
| P2 | GET | `/api/projects/{project_id}/environment-config` | UNMAPPED | - |
| P2 | GET | `/api/projects/{project_id}/multi-account-context` | COVERED | test_project_routes.py |
| P0 | GET | `/api/projects/{project_id}/jmeter/generation-skill` | COVERED | handler-reference |
| P2 | GET | `/api/projects` | COVERED | test_package_status_model.py, test_project_routes.py, test_requirement_routes.py |
| P1 | POST | `/api/projects` | COVERED | test_package_status_model.py, test_project_routes.py, test_requirement_routes.py |
| P1 | PUT | `/api/projects/{project_id}` | COVERED | test_package_status_model.py, test_project_routes.py, test_requirement_routes.py |
| P2 | GET | `/api/projects/{project_id}/dashboard` | COVERED | handler-reference |
| P2 | GET | `/api/projects/{project_id}/diagnosis` | COVERED | handler-reference |
| P2 | GET | `/api/projects/{project_id}/control-plane` | COVERED | handler-reference |
| P2 | GET | `/api/projects/{project_id}/requirement-packages` | COVERED | test_package_status_model.py, test_project_routes.py, test_requirement_routes.py |
| P1 | POST | `/api/projects/{project_id}/requirement-packages` | COVERED | test_package_status_model.py, test_project_routes.py, test_requirement_routes.py |
| P2 | GET | `/api/projects/{project_id}/requirement-packages/{package_id}/account-model` | COVERED | handler-reference |
| P1 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/account-model` | COVERED | handler-reference |
| P2 | GET | `/api/projects/{project_id}/requirement-packages/{package_id}/resource-manifest` | COVERED | handler-reference |
| P1 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/resource-manifest` | UNMAPPED | - |
| P2 | GET | `/api/projects/{project_id}/requirement-packages/{package_id}/resource-preflight` | COVERED | test_package_status_model.py |
| P1 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/resource-preflight` | COVERED | test_package_status_model.py |
| P2 | GET | `/api/projects/{project_id}/requirement-packages/{package_id}/evidence-rules` | COVERED | handler-reference |
| P1 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/api-test-cases` | COVERED | test_requirement_routes.py |
| P2 | GET | `/api/projects/{project_id}/requirement-packages/{package_id}/execution-plan` | COVERED | test_requirement_routes.py |
| P1 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/execution-plan` | COVERED | test_requirement_routes.py |
| P1 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/tool-assets` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/runs` | COVERED | test_package_status_model.py |
| P2 | GET | `/api/projects/{project_id}/requirement-packages/{package_id}/runs` | COVERED | test_package_status_model.py |
| P2 | GET | `/api/projects/{project_id}/requirement-packages/{package_id}/runs/{run_id}` | COVERED | test_package_status_model.py |
| P0 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/newman/run` | INTEGRATION_REQUIRED | - |
| P0 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/pytest/run` | INTEGRATION_REQUIRED | - |
| P0 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/pipeline/run` | COVERED | test_package_status_model.py, test_requirement_routes.py |
| P0 | POST | `/api/projects/{project_id}/salary-trade/jmeter-harvest` | INTEGRATION_REQUIRED | - |
| P0 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/jmeter-load-plan` | INTEGRATION_REQUIRED | - |
| P0 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/jmeter-load-run` | COVERED | test_requirement_routes.py |
| P1 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/scenario-report` | COVERED | test_package_status_model.py |
| P2 | GET | `/api/projects/{project_id}/requirement-packages/{package_id}/report-index` | COVERED | test_package_status_model.py, test_requirement_routes.py |
| P2 | GET | `/api/projects/{project_id}/requirement-packages/{package_id}/schema-audit` | COVERED | test_package_status_model.py, test_requirement_routes.py |
| P1 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/schema-upgrade` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/ai-review` | COVERED | test_requirement_routes.py |
| P1 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/performance-ai-review` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/newman-analysis` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/structured-test-cases` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/candidate-evidence-rules` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/accept-candidate-evidence-rules` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/business-evidence-plan` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/business-evidence-run` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/metadata-hallucination-audit` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/metadata-hallucination-correction` | UNMAPPED | - |
| P2 | GET | `/api/projects/{project_id}/quality-profile` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/quality-profile` | UNMAPPED | - |
| P2 | GET | `/api/projects/{project_id}/reports` | COVERED | handler-reference |
| P2 | GET | `/api/projects/{project_id}/test-accounts` | UNMAPPED | - |
| P2 | GET | `/api/projects/{project_id}/evidence-center` | UNMAPPED | - |
| P2 | GET | `/api/projects/{project_id}/capture-reports` | UNMAPPED | - |
| P2 | GET | `/api/projects/{project_id}/interface-document` | COVERED | handler-reference |
| P1 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/apifox-export` | COVERED | test_package_status_model.py |
| P1 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/apifox/openapi/import` | COVERED | test_package_status_model.py |
| P1 | POST | `/api/projects/{project_id}/requirement-packages/{package_id}/apifox-cli/run` | COVERED | test_package_status_model.py |
| P1 | POST | `/api/projects/{project_id}/delivery-package` | UNMAPPED | - |
| P2 | GET | `/api/projects/{project_id}/toolchain` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/tool-assets` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/toolchain/run` | UNMAPPED | - |
| P0 | POST | `/api/projects/{project_id}/jmeter/open-gui` | INTEGRATION_REQUIRED | - |
| P0 | POST | `/api/projects/{project_id}/jmeter/harvest-gui-report` | INTEGRATION_REQUIRED | - |
| P0 | GET | `/api/projects/{project_id}/jmeter/case-script-model` | INTEGRATION_REQUIRED | - |
| P0 | POST | `/api/projects/{project_id}/jmeter/generate-from-cases` | INTEGRATION_REQUIRED | - |
| P2 | GET | `/api/projects/{project_id}/execution-profile` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/execution-profile` | UNMAPPED | - |
| P2 | GET | `/api/projects/{project_id}/redis-mappings` | UNMAPPED | - |
| P2 | GET | `/api/projects/{project_id}/consistency` | UNMAPPED | - |
| P2 | GET | `/api/projects/{project_id}/wealth-latest-report` | UNMAPPED | - |
| P2 | GET | `/api/projects/{project_id}/gift-latest-report` | UNMAPPED | - |
| P2 | GET | `/api/projects/{project_id}/wealth-reward-configs` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/test-accounts` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/redis-manual-result` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/sources` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/generate` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/db-schema` | UNMAPPED | - |
| P0 | GET | `/api/projects/{project_id}/mysql/status` | INTEGRATION_REQUIRED | - |
| P0 | POST | `/api/projects/{project_id}/mysql/test` | INTEGRATION_REQUIRED | - |
| P0 | POST | `/api/projects/{project_id}/mysql/query` | INTEGRATION_REQUIRED | - |
| P0 | POST | `/api/projects/{project_id}/mysql/import-schema-live` | INTEGRATION_REQUIRED | - |
| P1 | POST | `/api/projects/{project_id}/salary-trade/db-evidence` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/redis-sources` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/auto-match-data` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/generate-consistency` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/consistency/run-ready` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/evidence-check` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/assistant` | UNMAPPED | - |
| P1 | POST | `/api/consistency-rules/{rule_id}/run` | UNMAPPED | - |
| P1 | POST | `/api/redis-sources/{source_id}/test` | UNMAPPED | - |
| P1 | POST | `/api/redis-sources/{source_id}/scan` | UNMAPPED | - |
| P1 | POST | `/api/redis-sources/{source_id}/inspect` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/generate-workflows` | UNMAPPED | - |
| P1 | POST | `/api/workflows/{workflow_id}/run` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/generate-nonfunctional` | UNMAPPED | - |
| P1 | POST | `/api/suites/{suite_id}/run` | UNMAPPED | - |
| P1 | POST | `/api/performance/{plan_id}/run` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/generate-operations` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/security-scan` | UNMAPPED | - |
| P1 | POST | `/api/jobs/{job_id}/run` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/endpoints` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/jobs` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/refresh-trace` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/ai-pipeline` | UNMAPPED | - |
| P1 | POST | `/api/requirements/{requirement_id}/link` | UNMAPPED | - |
| P1 | POST | `/api/requirements/{requirement_id}/generate-workflow` | UNMAPPED | - |
| P1 | POST | `/api/cases/{case_id}/run` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/gift-chain` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/login-performance` | UNMAPPED | - |
| P1 | POST | `/api/projects/{project_id}/run-all` | UNMAPPED | - |
| P1 | POST | `/api/settings` | UNMAPPED | - |
| P1 | POST | `/api/system/reload` | UNMAPPED | - |
| P1 | PUT | `/api/cases/{case_id}` | UNMAPPED | - |
| P1 | PUT | `/api/jobs/{job_id}` | UNMAPPED | - |
| P1 | PUT | `/api/endpoints/{endpoint_id}` | UNMAPPED | - |
| P1 | PUT | `/api/requirements/{requirement_id}` | COVERED | handler-reference |
