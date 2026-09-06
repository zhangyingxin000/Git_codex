from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from ..config import AppSettings
from ..handlers import TaskDispatcher
from ..services.task_queue import PersistentTaskQueue
from ..startup import application_lifespan
from .routes import (
    build_project_router,
    build_requirement_execution_router,
    build_requirement_report_router,
    build_system_router,
    build_task_router,
)
from ..schemas.requests import (
    GenerateFromSourceRequest,
    ProjectRuntimeRequest,
    RedisInspectRequest,
    RedisScanRequest,
    RedisSourceCreateRequest,
    SourceCreateRequest,
    TestAccountSaveRequest,
)


OPENAPI_TAGS = [
    {"name": "System", "description": "平台健康检查、存储边界和运行时控制。"},
    {"name": "Projects", "description": "项目、工作台看板和质量诊断。"},
    {"name": "Assets", "description": "需求资料、接口资产、测试点、测试用例和追踪关系。"},
    {"name": "Execution", "description": "接口自动化、业务流程、性能、安全和调度执行。"},
    {"name": "Data Validation", "description": "MySQL/Redis 只读映射、快照和一致性规则。"},
    {"name": "Reports", "description": "原始报告、综合报告、证据中心和报告文件。"},
    {"name": "Settings", "description": "平台本地配置，不回写外部业务系统。"},
]


def create_app() -> FastAPI:
    import app as legacy

    legacy.init_db()
    settings = AppSettings.from_environment(legacy.ROOT)
    task_queue = PersistentTaskQueue(settings.task_database, settings.task_workers)
    dispatcher = TaskDispatcher(legacy, settings)
    api = FastAPI(
        title="AutoTest AI Quality Hub",
        version="0.1.0",
        description=(
            "Enterprise quality orchestration platform backend. "
            "The platform writes only local assets, mappings, evidence and reports; "
            "company MySQL and Redis integrations are readonly."
        ),
        openapi_tags=OPENAPI_TAGS,
        lifespan=application_lifespan(task_queue),
    )
    api.state.settings = settings
    api.state.task_queue = task_queue
    api.state.task_dispatcher = dispatcher
    # FastAPI 0.141 wraps include_router() entries in _IncludedRouter. Appending the
    # concrete APIRoutes keeps legacy route introspection and coverage tooling stable.
    api.router.routes.extend(build_system_router(legacy, settings).routes)
    api.router.routes.extend(build_task_router(task_queue, dispatcher).routes)
    api.router.routes.extend(build_project_router(legacy).routes)
    api.router.routes.extend(build_requirement_execution_router(legacy).routes)
    api.router.routes.extend(build_requirement_report_router(legacy).routes)

    @api.exception_handler(HTTPException)
    def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else json.dumps(exc.detail, ensure_ascii=False)
        return JSONResponse(status_code=exc.status_code, content={"error": message, "detail": exc.detail})

    @api.exception_handler(RequestValidationError)
    def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"error": "请求参数校验失败", "detail": exc.errors()})

    @api.exception_handler(ValueError)
    def value_error_handler(_: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"error": str(exc), "detail": str(exc)})

    @api.post("/api/projects/{project_id}/structured-test-cases", tags=["Assets"], summary="生成结构化测试用例")
    def structured_test_cases(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.generate_structured_test_cases(project_id, payload)

    @api.post("/api/projects/{project_id}/candidate-evidence-rules", tags=["Data Validation"], summary="生成候选证据规则")
    def candidate_evidence_rules(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.generate_candidate_evidence_rules(project_id, payload)

    @api.post("/api/projects/{project_id}/accept-candidate-evidence-rules", tags=["Data Validation"], summary="采纳候选证据规则")
    def accept_candidate_evidence_rules(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.accept_candidate_evidence_rules(project_id, payload)

    @api.post("/api/projects/{project_id}/business-evidence-plan", tags=["Data Validation"], summary="生成业务证据计划")
    def business_evidence_plan(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.generate_business_evidence_plan(project_id, payload)

    @api.post("/api/projects/{project_id}/business-evidence-run", tags=["Data Validation"], summary="执行业务证据规则")
    def business_evidence_run(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.run_business_evidence_rules(project_id, payload)

    @api.post("/api/projects/{project_id}/metadata-hallucination-audit", tags=["Data Validation"], summary="AI输出元数据静态校验")
    def metadata_hallucination_audit(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.metadata_hallucination_audit(project_id, payload)

    @api.post("/api/projects/{project_id}/metadata-hallucination-correction", tags=["Data Validation"], summary="生成一次元数据修正版")
    def metadata_hallucination_correction(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.metadata_hallucination_correction(project_id, payload)

    @api.get("/api/projects/{project_id}/quality-profile", tags=["Projects"], summary="项目配置画像")
    def quality_profile(project_id: str) -> dict[str, Any]:
        try:
            return legacy.project_quality_profile(project_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @api.post("/api/projects/{project_id}/quality-profile", tags=["Projects"], summary="保存项目配置画像")
    def save_quality_profile(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        try:
            return legacy.save_project_quality_profile(project_id, payload)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @api.get("/api/projects/{project_id}/reports", tags=["Reports"], summary="项目报告列表")
    def reports(project_id: str) -> list[dict[str, Any]]:
        return legacy.list_generated_reports(project_id)

    @api.get("/api/projects/{project_id}/test-accounts", tags=["Execution"], summary="测试账号池")
    def test_accounts(project_id: str) -> list[dict[str, Any]]:
        return legacy.list_test_accounts(project_id)

    @api.get("/api/projects/{project_id}/evidence-center", tags=["Reports"], summary="证据中心状态")
    def evidence_center(project_id: str) -> dict[str, Any]:
        return legacy.evidence_center_status(project_id)

    @api.get("/api/projects/{project_id}/capture-reports", tags=["Assets"], summary="资料采集完整性报告")
    def capture_reports(project_id: str) -> list[dict[str, Any]]:
        return legacy.rows(
            "SELECT * FROM source_capture_reports WHERE project_id=? ORDER BY created_at DESC",
            (project_id,),
        )

    @api.get("/api/projects/{project_id}/interface-document", tags=["Assets"], summary="导出脱敏接口文档基线")
    def interface_document(project_id: str) -> dict[str, Any]:
        try:
            return legacy.build_project_interface_document(project_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @api.post("/api/projects/{project_id}/requirement-packages/{package_id}/apifox-export", tags=["Assets"], summary="生成当前需求包Apifox交换包")
    def apifox_package(project_id: str, package_id: str) -> dict[str, Any]:
        try:
            return legacy.build_apifox_collaboration_package(project_id, package_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api.post("/api/projects/{project_id}/requirement-packages/{package_id}/apifox/openapi/import", tags=["Assets"], summary="导入Apifox OpenAPI并生成pytest基础层")
    def apifox_openapi_import(project_id: str, package_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        try:
            return legacy.import_apifox_openapi_to_package(project_id, package_id, payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api.post("/api/projects/{project_id}/requirement-packages/{package_id}/apifox-cli/run", tags=["Execution"], summary="运行Apifox CLI发布冒烟并回收报告")
    def apifox_cli_run(project_id: str, package_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        try:
            return legacy.run_requirement_package_apifox_cli(project_id, package_id, payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api.post("/api/projects/{project_id}/delivery-package", tags=["Assets"], summary="生成测试资产交付包")
    def delivery_package(project_id: str) -> dict[str, Any]:
        try:
            return legacy.build_test_asset_delivery_package(project_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api.get("/api/projects/{project_id}/toolchain", tags=["Execution"], summary="企业测试工具链预检")
    def toolchain(project_id: str) -> dict[str, Any]:
        try:
            return legacy.enterprise_toolchain_status(project_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @api.post("/api/projects/{project_id}/tool-assets", tags=["Execution"], summary="生成企业测试工具资产")
    def tool_assets(project_id: str) -> dict[str, Any]:
        try:
            return legacy.generate_enterprise_tool_assets(project_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api.post("/api/projects/{project_id}/toolchain/run", tags=["Execution"], summary="执行企业测试工具链")
    def run_toolchain(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        try:
            return legacy.run_enterprise_toolchain(project_id, payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api.post("/api/projects/{project_id}/jmeter/open-gui", tags=["Execution"], summary="打开 JMeter GUI 并加载线程组")
    def open_jmeter_gui(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        try:
            return legacy.open_jmeter_gui(project_id, payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api.post("/api/projects/{project_id}/jmeter/harvest-gui-report", tags=["Execution"], summary="回收 JMeter GUI 执行报告")
    def harvest_jmeter_gui_report(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        try:
            return legacy.harvest_jmeter_workbench_report(project_id, payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api.get("/api/projects/{project_id}/jmeter/case-script-model", tags=["Execution"], summary="查看测试用例到 JMeter 脚本模型")
    def jmeter_case_script_model(project_id: str) -> dict[str, Any]:
        try:
            return legacy.salary_trade_case_to_jmeter_model(project_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api.post("/api/projects/{project_id}/jmeter/generate-from-cases", tags=["Execution"], summary="按测试用例生成 JMeter 脚本")
    def generate_jmeter_from_cases(project_id: str) -> dict[str, Any]:
        try:
            return legacy.generate_salary_trade_jmeter_from_cases(project_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api.get("/api/projects/{project_id}/execution-profile", tags=["Execution"], summary="项目运行参数与执行策略")
    def execution_profile(project_id: str) -> dict[str, Any]:
        try:
            return legacy.project_execution_profile(project_id)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @api.post("/api/projects/{project_id}/execution-profile", tags=["Execution"], summary="保存项目运行参数与执行策略")
    def save_execution_profile(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        try:
            return legacy.save_project_execution_profile(project_id, payload)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @api.get("/api/projects/{project_id}/redis-mappings", tags=["Data Validation"], summary="接口到 Redis 映射")
    def redis_mappings(project_id: str) -> list[dict[str, Any]]:
        return legacy.rows(
            """
            SELECT m.*,e.method,e.path,e.summary
            FROM api_redis_mappings m
            JOIN api_endpoints e ON e.id=m.endpoint_id
            WHERE m.project_id=?
            ORDER BY m.confidence DESC
            LIMIT 1000
            """,
            (project_id,),
        )

    @api.get("/api/projects/{project_id}/consistency", tags=["Data Validation"], summary="数据一致性规则与执行记录")
    def consistency(project_id: str) -> dict[str, Any]:
        return {
            "summary": legacy.data_consistency_summary(project_id),
            "rules": legacy.rows(
                """
                SELECT r.*,e.method,e.path,e.summary
                FROM consistency_rules r
                JOIN api_endpoints e ON e.id=r.endpoint_id
                WHERE r.project_id=?
                ORDER BY r.confidence DESC
                """,
                (project_id,),
            ),
            "runs": legacy.rows(
                """
                SELECT x.*,r.redis_pattern,e.path
                FROM consistency_runs x
                JOIN consistency_rules r ON r.id=x.rule_id
                JOIN api_endpoints e ON e.id=r.endpoint_id
                WHERE x.project_id=?
                ORDER BY x.created_at DESC
                LIMIT 100
                """,
                (project_id,),
            ),
        }

    @api.get("/api/projects/{project_id}/wealth-latest-report", tags=["Reports"], summary="最新财富等级综合报告")
    def wealth_latest_report(project_id: str) -> dict[str, Any]:
        report_dir = legacy.ROOT / "reports"
        files = (
            sorted(
                report_dir.glob("wealth-full-real-test-*.json"),
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )
            if report_dir.exists()
            else []
        )
        if not files:
            return {}
        payload = json.loads(files[0].read_text(encoding="utf-8"))
        payload["report_path"] = str(files[0])
        wealth_api = payload.get("wealth_api", {})
        payload["functional"] = (
            wealth_api.get("http_status") == 200 and wealth_api.get("business_code") == 200
        )
        payload["reward_matrix_ok"] = bool(payload.get("reward_matrix", {}).get("ok"))
        payload["backend_config_ok"] = bool(payload.get("backend_config", {}).get("ok"))
        return payload

    @api.get("/api/projects/{project_id}/gift-latest-report", tags=["Reports"], summary="最新送礼链路报告")
    def gift_latest_report(project_id: str) -> dict[str, Any]:
        report_dir = legacy.ROOT / "reports"
        files = (
            sorted(
                report_dir.glob("gift-wealth-chain-*.json"),
                key=lambda item: item.stat().st_mtime,
                reverse=True,
            )
            if report_dir.exists()
            else []
        )
        if not files:
            return {}
        payload = json.loads(files[0].read_text(encoding="utf-8"))
        payload["report_path"] = str(files[0])
        return payload

    @api.get("/api/projects/{project_id}/wealth-reward-configs", tags=["Data Validation"], summary="财富奖励配置核对数据")
    def wealth_reward_configs(project_id: str) -> dict[str, Any]:
        return {
            "configs": legacy.rows(
                "SELECT * FROM wealth_backend_reward_configs WHERE project_id=? ORDER BY level",
                (project_id,),
            ),
            "expectations": legacy.rows(
                "SELECT * FROM wealth_reward_expectations WHERE project_id=? ORDER BY level_min,source_row",
                (project_id,),
            ),
            "issues": legacy.rows(
                "SELECT * FROM reward_matrix_issues WHERE project_id=? ORDER BY source_row",
                (project_id,),
            ),
        }

    @api.post("/api/projects/{project_id}/test-accounts", status_code=201, tags=["Execution"], summary="保存测试账号")
    def save_test_account(
        project_id: str,
        payload: TestAccountSaveRequest,
    ) -> dict[str, Any]:
        return legacy.upsert_test_account(project_id, payload.model_dump())

    @api.post("/api/projects/{project_id}/redis-manual-result", tags=["Data Validation"], summary="补充人工 Redis 核对结果")
    def redis_manual_result(
        project_id: str,
        payload: dict[str, Any] = Body(default_factory=dict),
    ) -> dict[str, Any]:
        return legacy.attach_manual_redis_result(project_id, payload)

    @api.post("/api/projects/{project_id}/sources", status_code=201, tags=["Assets"], summary="导入需求、文档、图片、OpenAPI 或 HAR")
    def add_source(project_id: str, payload: SourceCreateRequest) -> dict[str, Any]:
        payload = payload.model_dump()
        source_id = legacy.uid("src")
        kind = payload.get("kind", "requirement")
        browser_images = []
        page_meta = None
        if payload.get("browser_capture") and payload.get("source_url"):
            content, browser_images, page_meta = legacy.browser_capture_source(payload["source_url"])
            content = (payload.get("content", "") + "\n" + content).strip()
        else:
            content = legacy.extract_source_content(payload)
        capture_entries = 0
        if kind == "har":
            content, capture_entries = legacy.parse_har_capture(content)
        image_values = []
        all_images = legacy.extract_source_images(payload) + browser_images
        if all_images:
            status, analysis = legacy.vision_analyze_bundle(content, all_images)
            for index, (image_name, mime, data_b64) in enumerate(all_images):
                asset_analysis = analysis if index == 0 else "已纳入同一份需求的图文联合分析，综合结论见首张资源"
                image_values.append(
                    (
                        legacy.uid("asset"),
                        project_id,
                        source_id,
                        image_name,
                        mime,
                        data_b64,
                        status,
                        asset_analysis,
                        legacy.now(),
                    )
                )
            content += f"\n\n[文字与{len(all_images)}张图片联合分析]\n{analysis}"
        legacy.execute(
            "INSERT INTO sources VALUES (?,?,?,?,?,?)",
            (
                source_id,
                project_id,
                payload.get("name", payload.get("file_name") or payload.get("source_url") or "资料"),
                kind,
                content,
                legacy.now(),
            ),
        )
        if page_meta is not None:
            score, capture_status, capture_blockers = legacy.evaluate_capture_completeness(page_meta)
            legacy.execute(
                "INSERT INTO source_capture_reports VALUES (?,?,?,?,?,?,?)",
                (
                    source_id,
                    project_id,
                    payload.get("source_url", ""),
                    score,
                    capture_status,
                    json.dumps(page_meta.get("completeness", {}), ensure_ascii=False),
                    json.dumps(capture_blockers, ensure_ascii=False),
                    legacy.now(),
                ),
            )
        if image_values:
            with legacy.db() as conn:
                conn.executemany("INSERT INTO source_assets VALUES (?,?,?,?,?,?,?,?,?)", image_values)
        result = (
            legacy.store_endpoints_incremental(
                project_id,
                source_id,
                content,
                payload.get("requirement_source_id"),
                payload.get("batch_name") or payload.get("name", "接口变更"),
            )
            if kind in {"openapi", "har"}
            else {"endpoints": 0}
        )
        result["requirement_items"] = (
            legacy.analyze_requirement_source(project_id, source_id, content)
            if kind == "requirement"
            else 0
        )
        result["images"] = len(image_values)
        if kind == "har":
            result["capture_entries"] = capture_entries
        if page_meta is not None:
            result.update(
                {
                    "capture_score": score,
                    "capture_status": capture_status,
                    "capture_blockers": capture_blockers,
                }
            )
        return {"id": source_id, **result}

    @api.post("/api/projects/{project_id}/generate", tags=["Assets"], summary="根据资料生成测试资产")
    def generate_assets(project_id: str, payload: GenerateFromSourceRequest) -> dict[str, Any]:
        return legacy.generate_assets(project_id, payload.source_id, payload.force)

    @api.post("/api/projects/{project_id}/db-schema", tags=["Data Validation"], summary="导入 MySQL Schema 元数据")
    def db_schema(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.import_db_schema(project_id, payload.get("content", "{}"))

    @api.get("/api/projects/{project_id}/mysql/status", tags=["Data Validation"], summary="MySQL只读连接状态")
    def mysql_status(project_id: str) -> dict[str, Any]:
        return legacy.mysql_connection_status(project_id)

    @api.post("/api/projects/{project_id}/mysql/test", tags=["Data Validation"], summary="测试MySQL只读连接")
    def mysql_test(project_id: str) -> dict[str, Any]:
        return legacy.mysql_test_connection(project_id)

    @api.post("/api/projects/{project_id}/mysql/query", tags=["Data Validation"], summary="执行MySQL只读查询")
    def mysql_query(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.mysql_readonly_query(project_id, payload)

    @api.post("/api/projects/{project_id}/mysql/import-schema-live", tags=["Data Validation"], summary="从MySQL实时读取Schema元数据")
    def mysql_import_schema_live(project_id: str) -> dict[str, Any]:
        return legacy.import_mysql_schema_live(project_id)

    @api.post("/api/projects/{project_id}/salary-trade/db-evidence", tags=["Data Validation"], summary="工资交易MySQL只读证据核查")
    def salary_trade_db_evidence(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.salary_trade_db_evidence_check(project_id, payload)

    @api.post("/api/projects/{project_id}/redis-sources", status_code=201, tags=["Data Validation"], summary="接入 Redis 只读数据源")
    def add_redis_source(project_id: str, payload: RedisSourceCreateRequest) -> dict[str, Any]:
        payload = payload.model_dump()
        redis_id = legacy.uid("redis")
        host = str(payload.get("host", "")).strip()
        port = int(payload.get("port", 6379))
        db_no = int(payload.get("db_no", 0))
        if not host:
            raise HTTPException(status_code=400, detail="Host不能为空")
        if not (1 <= port <= 65535) or not (0 <= db_no <= 1024):
            raise HTTPException(status_code=400, detail="Port或DB编号无效")
        legacy.execute(
            "INSERT INTO redis_sources VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                redis_id,
                project_id,
                payload.get("name", "Redis测试数据源"),
                host,
                port,
                db_no,
                int(bool(payload.get("use_tls", False))),
                1,
                "unknown",
                "",
                "",
                None,
                legacy.now(),
            ),
        )
        result = legacy.check_redis_source(redis_id)
        return {**legacy.row("SELECT * FROM redis_sources WHERE id=?", (redis_id,)), **result}

    @api.post("/api/projects/{project_id}/auto-match-data", tags=["Data Validation"], summary="自动匹配接口、MySQL 与 Redis")
    def auto_match_data(project_id: str) -> dict[str, Any]:
        return legacy.auto_match_project_data(project_id)

    @api.post("/api/projects/{project_id}/generate-consistency", tags=["Data Validation"], summary="生成一致性验证规则")
    def generate_consistency(project_id: str) -> dict[str, Any]:
        return legacy.prepare_consistency_rules(project_id)

    @api.post("/api/projects/{project_id}/consistency/run-ready", tags=["Data Validation"], summary="运行已补齐的一致性规则")
    def run_ready_consistency(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.run_ready_consistency_rules(project_id, payload.get("limit", 5), payload.get("scope", "core"))

    @api.post("/api/projects/{project_id}/evidence-check", tags=["Data Validation"], summary="发起一次按需数据证据核查")
    def manual_evidence_check(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.run_manual_evidence_check(project_id, payload)

    @api.post("/api/projects/{project_id}/assistant", tags=["Assets"], summary="平台助手对话")
    def assistant(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.assistant_reply(project_id, payload.get("message", ""))

    @api.post("/api/consistency-rules/{rule_id}/run", tags=["Data Validation"], summary="执行单条一致性规则")
    def run_consistency(rule_id: str) -> dict[str, Any]:
        return legacy.run_consistency_rule(rule_id)

    @api.post("/api/redis-sources/{source_id}/test", tags=["Data Validation"], summary="测试 Redis 只读连接")
    def test_redis_source(source_id: str) -> dict[str, Any]:
        return legacy.check_redis_source(source_id)

    @api.post("/api/redis-sources/{source_id}/scan", tags=["Data Validation"], summary="扫描 Redis Key")
    def scan_redis_source(
        source_id: str,
        payload: RedisScanRequest,
    ) -> dict[str, Any]:
        return legacy.scan_redis_keys(source_id, payload.pattern, payload.limit)

    @api.post("/api/redis-sources/{source_id}/inspect", tags=["Data Validation"], summary="查看 Redis Key 只读快照")
    def inspect_redis_source(
        source_id: str,
        payload: RedisInspectRequest,
    ) -> dict[str, Any]:
        return legacy.inspect_redis_key(source_id, payload.key)

    @api.post("/api/projects/{project_id}/generate-workflows", tags=["Assets"], summary="生成业务流程")
    def generate_workflows(project_id: str) -> dict[str, Any]:
        return legacy.generate_workflows(project_id)

    @api.post("/api/workflows/{workflow_id}/run", tags=["Execution"], summary="执行业务流程")
    def run_workflow(workflow_id: str) -> dict[str, Any]:
        return legacy.execute_workflow(workflow_id)

    @api.post("/api/projects/{project_id}/generate-nonfunctional", tags=["Assets"], summary="生成自动化、性能与异常测试资产")
    def generate_nonfunctional(project_id: str) -> dict[str, Any]:
        return legacy.generate_nonfunctional(project_id)

    @api.post("/api/suites/{suite_id}/run", tags=["Execution"], summary="执行接口自动化套件")
    def run_suite(suite_id: str) -> dict[str, Any]:
        return legacy.run_suite(suite_id)

    @api.post("/api/performance/{plan_id}/run", tags=["Execution"], summary="执行性能测试计划")
    def run_performance(plan_id: str) -> dict[str, Any]:
        return legacy.run_performance(plan_id)

    @api.post("/api/projects/{project_id}/generate-operations", tags=["Assets"], summary="生成安全、UI 与调度资产")
    def generate_operations(project_id: str) -> dict[str, Any]:
        return legacy.generate_operations_assets(project_id)

    @api.post("/api/projects/{project_id}/security-scan", tags=["Execution"], summary="执行安全扫描")
    def security_scan(project_id: str) -> dict[str, Any]:
        return legacy.run_security_scan(project_id)

    @api.post("/api/jobs/{job_id}/run", tags=["Execution"], summary="执行调度任务")
    def run_job(job_id: str) -> dict[str, Any]:
        job = legacy.row("SELECT * FROM scheduled_jobs WHERE id=?", (job_id,))
        return legacy.dispatch_job(job)

    @api.post("/api/projects/{project_id}/endpoints", status_code=201, tags=["Assets"], summary="手工新增接口资产")
    def add_endpoint(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.add_manual_endpoint(project_id, payload)

    @api.post("/api/projects/{project_id}/jobs", status_code=201, tags=["Execution"], summary="创建调度任务")
    def add_job(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any] | None:
        job_id = legacy.uid("job")
        interval = max(1, int(payload.get("interval_minutes", 60)))
        enabled = int(bool(payload.get("enabled", False)))
        legacy.execute(
            "INSERT INTO scheduled_jobs VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                job_id,
                project_id,
                payload.get("name", "自定义任务"),
                payload.get("job_type", "security"),
                payload.get("target_id", ""),
                interval,
                enabled,
                None,
                legacy.now() if enabled else None,
                "NEVER",
                legacy.now(),
            ),
        )
        return legacy.row("SELECT * FROM scheduled_jobs WHERE id=?", (job_id,))

    @api.post("/api/projects/{project_id}/refresh-trace", tags=["Assets"], summary="刷新需求到接口追踪关系")
    def refresh_trace(project_id: str) -> dict[str, Any]:
        return {"links": legacy.refresh_traceability(project_id)}

    @api.post("/api/projects/{project_id}/ai-pipeline", tags=["Execution"], summary="运行 AI 质量流水线")
    def ai_pipeline(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.run_ai_pipeline(project_id, payload)

    @api.post("/api/requirements/{requirement_id}/link", tags=["Assets"], summary="设置需求与接口关联")
    def requirement_link(
        requirement_id: str,
        payload: dict[str, Any] = Body(default_factory=dict),
    ) -> dict[str, Any]:
        return legacy.set_requirement_link(
            requirement_id,
            payload["endpoint_id"],
            payload.get("selected", True),
            payload.get("sort_order", 0),
        )

    @api.post("/api/requirements/{requirement_id}/generate-workflow", tags=["Assets"], summary="按需求生成业务流程")
    def requirement_workflow(requirement_id: str) -> dict[str, Any]:
        return legacy.generate_requirement_workflow(requirement_id)

    @api.post("/api/cases/{case_id}/run", tags=["Execution"], summary="执行单条测试用例")
    def run_case(case_id: str) -> dict[str, Any]:
        return legacy.execute_case(case_id)

    @api.post("/api/projects/{project_id}/gift-chain", tags=["Execution"], summary="执行送礼业务链路")
    def gift_chain(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.run_gift_business_chain(project_id, payload)

    @api.post("/api/projects/{project_id}/login-performance", tags=["Execution"], summary="执行多账号登录性能专项")
    def login_performance(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.run_login_performance_special(project_id, payload)

    @api.post("/api/projects/{project_id}/run-all", tags=["Execution"], summary="执行当前项目可运行测试")
    def run_all(project_id: str, payload: ProjectRuntimeRequest = Body(default_factory=ProjectRuntimeRequest)) -> dict[str, Any]:
        payload = payload.model_dump()
        primary = legacy.resolve_primary_business_chain(project_id)
        if primary:
            result = legacy.run_business_chain_full_test(
                project_id,
                int(payload.get("performance_requests", 20)),
                payload,
            )
            total = legacy.row("SELECT COUNT(*) n FROM test_cases WHERE project_id=?", (project_id,))["n"]
            executable = legacy.row(
                "SELECT COUNT(*) n FROM test_cases WHERE project_id=? AND method<>'' AND path<>'' AND COALESCE(lifecycle_status,'ACTIVE')='ACTIVE'",
                (project_id,),
            )["n"]
            return {
                "total_cases": total,
                "executable": executable,
                "not_executed": max(0, total - executable),
                "primary_flow": "凭证复用/真实登录 → 内存变量传递 → 财富接口 → 业务校验 → 性能测试 → 报告",
                "full_test": result,
            }
        cases = legacy.rows(
            "SELECT id FROM test_cases WHERE project_id=? AND method<>'' AND path<>'' AND COALESCE(lifecycle_status,'ACTIVE')='ACTIVE'",
            (project_id,),
        )
        results = [legacy.execute_case(item["id"]) for item in cases]
        total = legacy.row("SELECT COUNT(*) n FROM test_cases WHERE project_id=?", (project_id,))["n"]
        return {
            "total_cases": total,
            "executable": len(results),
            "not_executed": total - len(results),
            "results": results,
        }

    @api.post("/api/settings", tags=["Settings"], summary="保存平台本地设置")
    def save_settings(payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, bool]:
        existing = legacy.row("SELECT value FROM settings WHERE key='api_key'")
        if payload.get("api_key") == "••••••••" and existing:
            payload["api_key"] = existing["value"]
        with legacy.db() as conn:
            for key in ("api_key", "api_base", "model"):
                if key in payload:
                    conn.execute(
                        "INSERT INTO settings(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                        (key, str(payload[key])),
                    )
        return {"ok": True}

    @api.post("/api/system/reload", tags=["System"], summary="重载平台后端")
    def reload_system() -> dict[str, Any]:
        threading.Timer(0.35, lambda: os._exit(75)).start()
        return {"ok": True, "message": "平台正在重新加载"}

    @api.put("/api/cases/{case_id}", tags=["Assets"], summary="更新测试用例")
    def update_case(case_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, bool]:
        fields = [
            "title",
            "method",
            "path",
            "headers",
            "payload",
            "expected_status",
            "expected_contains",
            "priority",
            "status",
            "steps",
            "expected",
        ]
        old = legacy.row("SELECT * FROM test_cases WHERE id=?", (case_id,))
        if not old:
            raise HTTPException(status_code=404, detail="用例不存在")
        values = [payload.get(field, old[field]) for field in fields]
        legacy.execute(
            f"UPDATE test_cases SET {','.join(field + '=?' for field in fields)} WHERE id=?",
            (*values, case_id),
        )
        return {"ok": True}

    @api.put("/api/cases/{case_id}/lifecycle", tags=["Assets"], summary="更新测试用例生命周期")
    def update_case_lifecycle(case_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.set_test_case_lifecycle(
            case_id,
            payload.get("lifecycle_status"),
            payload.get("note", ""),
            payload.get("actor", "workbench"),
        )

    @api.get("/api/cases/{case_id}/lifecycle-history", tags=["Assets"], summary="测试用例生命周期历史")
    def case_lifecycle_history(case_id: str) -> dict[str, Any]:
        return legacy.test_case_lifecycle_history(case_id)

    @api.put("/api/projects/{project_id}/cases/lifecycle/bulk", tags=["Assets"], summary="批量审批测试用例生命周期")
    def bulk_case_lifecycle(project_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, Any]:
        return legacy.bulk_set_test_case_lifecycle(
            project_id,
            payload.get("case_ids") or [],
            payload.get("lifecycle_status"),
            payload.get("note", ""),
            payload.get("actor", "workbench"),
        )

    @api.put("/api/jobs/{job_id}", tags=["Execution"], summary="更新调度任务")
    def update_job(job_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, bool]:
        job = legacy.row("SELECT * FROM scheduled_jobs WHERE id=?", (job_id,))
        if not job:
            raise HTTPException(status_code=404, detail="任务不存在")
        enabled = int(bool(payload.get("enabled", job["enabled"])))
        interval = max(1, int(payload.get("interval_minutes", job["interval_minutes"])))
        legacy.execute(
            "UPDATE scheduled_jobs SET enabled=?,interval_minutes=?,next_run_at=? WHERE id=?",
            (enabled, interval, legacy.now() if enabled else None, job_id),
        )
        return {"ok": True}

    @api.put("/api/endpoints/{endpoint_id}", tags=["Assets"], summary="更新接口资产")
    def update_endpoint(endpoint_id: str, payload: dict[str, Any] = Body(default_factory=dict)) -> dict[str, bool]:
        old = legacy.row("SELECT * FROM api_endpoints WHERE id=?", (endpoint_id,))
        if not old:
            raise HTTPException(status_code=404, detail="接口不存在")
        legacy.execute(
            "UPDATE api_endpoints SET method=?,path=?,summary=?,tags=?,auth_required=? WHERE id=?",
            (
                payload.get("method", old["method"]).upper(),
                payload.get("path", old["path"]),
                payload.get("summary", old["summary"]),
                json.dumps([payload.get("module")], ensure_ascii=False)
                if payload.get("module")
                else old["tags"],
                int(payload.get("auth_required", old["auth_required"])),
                endpoint_id,
            ),
        )
        legacy.refresh_traceability(old["project_id"])
        return {"ok": True}

    @api.put("/api/requirements/{requirement_id}", tags=["Assets"], summary="更新需求条目")
    def update_requirement(
        requirement_id: str,
        payload: dict[str, Any] = Body(default_factory=dict),
    ) -> dict[str, bool]:
        old = legacy.row("SELECT * FROM requirement_items WHERE id=?", (requirement_id,))
        if not old:
            raise HTTPException(status_code=404, detail="需求不存在")
        fields = ["title", "description", "acceptance_criteria", "priority", "risk_level", "status"]
        values = [payload.get(field, old[field]) for field in fields]
        legacy.execute(
            "UPDATE requirement_items SET title=?,description=?,acceptance_criteria=?,priority=?,risk_level=?,status=? WHERE id=?",
            (*values, requirement_id),
        )
        legacy.refresh_traceability(old["project_id"])
        return {"ok": True}

    reports_dir = legacy.ROOT / "reports"
    static_dir = legacy.ROOT / "static"
    if reports_dir.exists():
        api.mount("/reports", StaticFiles(directory=reports_dir), name="reports")
    requirement_reports_dir = legacy.REQUIREMENT_PACKAGE_ROOT
    if requirement_reports_dir.exists():
        api.mount("/requirement-reports", StaticFiles(directory=requirement_reports_dir), name="requirement-reports")

    @api.get("/{path:path}", include_in_schema=False)
    def static_files(path: str = "") -> Response:
        target = static_dir / (path or "index.html")
        headers = {"Cache-Control": "no-store, no-cache, must-revalidate", "Pragma": "no-cache"}
        if target.is_file() and static_dir.resolve() in target.resolve().parents:
            if target.resolve() == (static_dir / "index.html").resolve():
                return HTMLResponse(legacy.render_static_index(), headers=headers)
            return FileResponse(target, headers=headers)
        return HTMLResponse(legacy.render_static_index(), headers=headers)

    return api


app = create_app()
