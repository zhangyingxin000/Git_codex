from __future__ import annotations

import json
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any

from ..repositories.sqlite_read_model import QualityReadModelRepository
from ..schemas.diagnosis import (
    DiagnosisItem,
    DiagnosisSeverity,
    DiagnosisSummary,
    ProjectDiagnosis,
    QualityModule,
)


def _uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


class ProjectDiagnosisService:
    """Diagnose whether a project can close the enterprise quality loop."""

    def __init__(self, repository: QualityReadModelRepository) -> None:
        self._repository = repository

    def diagnose(self, project_id: str, *, persist: bool = True) -> ProjectDiagnosis:
        project = self._repository.project(project_id)
        if not project:
            raise ValueError("项目不存在")

        sources = self._repository.sources(project_id)
        requirements = self._repository.requirements(project_id)
        trace_links = self._repository.trace_links(project_id)
        endpoints = self._repository.endpoints(project_id)
        cases = self._repository.test_cases(project_id)
        rules = self._repository.consistency_rules(project_id)
        runs = self._repository.consistency_runs(project_id)
        db_tables = self._repository.db_tables(project_id)
        db_maps = self._repository.db_mappings(project_id)
        redis_sources = self._repository.redis_sources(project_id)
        redis_maps = self._repository.redis_mappings(project_id)
        accounts = self._repository.accounts(project_id)
        reports = self._repository.reports(project_id)
        project_settings = self._repository.project_settings(project_id)
        source_kinds = {source.get("kind") for source in sources}

        items: list[DiagnosisItem] = []

        def add(
            severity: DiagnosisSeverity,
            module: QualityModule,
            title: str,
            description: str,
            action_label: str,
            action_target: QualityModule,
            details: list[dict[str, Any]] | None = None,
        ) -> None:
            items.append(
                DiagnosisItem(
                    id=_uid("diag"),
                    severity=severity,
                    module=module,
                    title=title,
                    description=description,
                    action_label=action_label,
                    action_target=action_target,
                    details=details or [],
                )
            )

        if not sources:
            add(
                DiagnosisSeverity.p0,
                "sources",
                "补齐需求或接口资料",
                "请接入需求文档、链接、图片、文字描述、OpenAPI 或 HAR 抓包记录，平台才能继续生成测试点、用例和链路。",
                "添加资料",
                "sources",
            )
        if not requirements:
            add(
                DiagnosisSeverity.p1,
                "sources",
                "补齐结构化需求",
                "当前还没有可追踪的需求条目，后续报告无法证明需求覆盖。",
                "生成需求资产",
                "sources",
            )
        if not endpoints:
            add(
                DiagnosisSeverity.p0,
                "sources",
                "补齐接口定义",
                "当前没有接口资产。可导入 OpenAPI、HAR 抓包记录或手工接口片段，否则接口自动化、性能测试和数据验证都无法闭环。",
                "导入接口",
                "sources",
            )
        if endpoints and not any(
            case.get("method") and case.get("path") for case in cases
        ):
            add(
                DiagnosisSeverity.p0,
                "sources",
                "补齐可执行用例",
                "已有接口但缺少可直接执行的用例，需要从接口文档、HAR 抓包样例或需求资料生成。",
                "生成用例",
                "sources",
            )
        if endpoints and "openapi" not in source_kinds:
            add(
                DiagnosisSeverity.p1,
                "sources",
                "补齐接口文档基线",
                "当前接口资产没有正式 OpenAPI/Swagger 来源。若文档过旧，可以先导入 HAR 抓包样例，再由平台反向沉淀接口文档。",
                "导入接口文档",
                "sources",
            )
        if endpoints and "har" not in source_kinds:
            add(
                DiagnosisSeverity.p2,
                "sources",
                "补齐真实抓包样例",
                "已有接口资产，但缺少真实抓包样例。抓包可帮助平台补齐请求头、设备上下文、参数示例和链路变量。",
                "导入HAR",
                "sources",
            )
        if (
            endpoints
            and requirements
            and not any(int(link.get("selected") or 0) == 1 for link in trace_links)
        ):
            add(
                DiagnosisSeverity.p1,
                "sources",
                "补齐需求到接口覆盖关系",
                "需求、接口都已存在，但尚未形成可展示的需求到接口追踪链。",
                "计算覆盖",
                "sources",
            )
        if not project.get("base_url"):
            add(
                DiagnosisSeverity.p0,
                "automation",
                "补齐测试环境地址",
                "缺少 Base URL，平台不能调用企业认可的接口测试工具执行真实请求。",
                "配置环境",
                "automation",
            )
        if not accounts:
            add(
                DiagnosisSeverity.p1,
                "automation",
                "补齐测试账号池",
                "登录态、鉴权接口、业务链路和部分数据验证需要测试账号与凭证。",
                "添加账号",
                "automation",
            )
        elif not any(
            account.get("has_ticket") or account.get("has_password")
            for account in accounts
        ):
            add(
                DiagnosisSeverity.p1,
                "automation",
                "补齐可复用凭证",
                "已有账号资料，但没有可复用 Ticket 或加密密码，真实链路容易被登录步骤阻断。",
                "补凭证",
                "automation",
            )
        if not project_settings.get("max_p95_ms") or not project_settings.get(
            "max_error_rate"
        ):
            add(
                DiagnosisSeverity.p1,
                "automation",
                "补齐项目 SLA 阈值",
                "缺少团队认可的性能准入阈值。可先填写冒烟/基准默认值，后续接入监控数据后再校准。",
                "配置SLA",
                "automation",
            )
        if not project_settings.get("monitoring_url"):
            add(
                DiagnosisSeverity.p2,
                "automation",
                "补齐监控数据来源",
                "尚未登记监控或 APM 看板地址，平台暂不能根据历史线上指标推荐 SLA。",
                "登记监控",
                "automation",
            )
        data_validation_started = bool(rules or runs or db_maps or redis_maps)
        if data_validation_started and not any(
            source.get("status") == "connected" for source in redis_sources
        ):
            add(
                DiagnosisSeverity.p2,
                "dataquality",
                "可补齐 Redis 只读连接",
                "当前需求未强制 Redis 核对；仅当需要缓存前后比对时再接入只读 Redis。",
                "配置Redis",
                "dataquality",
            )
        if data_validation_started and not db_tables:
            add(
                DiagnosisSeverity.p2,
                "dataquality",
                "可补齐 MySQL Schema",
                "当前需求未强制数据库映射；仅当需要用库表证明状态、金额或流水一致时再补充 Schema。",
                "导入Schema",
                "dataquality",
            )

        endpoint_details = self._endpoint_closure_gaps(
            endpoints, cases, rules, runs, db_maps, redis_maps
        )
        if endpoint_details:
            has_execution_blocker = any(
                "可执行用例" in detail["missing"] or "响应断言字段" in detail["missing"]
                for detail in endpoint_details
            )
            add(
                DiagnosisSeverity.p0 if has_execution_blocker else DiagnosisSeverity.p1,
                "sources" if has_execution_blocker else "automation",
                "补齐接口执行材料",
                f"{len(endpoint_details)} 个接口还有可执行用例、参数样例或响应断言缺口。",
                "查看资产",
                "sources",
                endpoint_details,
            )

        failed_runs = self._repository.failed_runs(project_id)
        if failed_runs:
            add(
                DiagnosisSeverity.p1,
                "reports",
                "归纳失败执行证据",
                f"{len(failed_runs)} 条最近失败/异常执行需要确认是环境、鉴权、断言还是业务缺陷。",
                "查看报告",
                "reports",
                failed_runs,
            )
        if not reports:
            add(
                DiagnosisSeverity.p1,
                "reports",
                "补齐可归档报告",
                "尚未形成接口、性能、数据验证或完整证据报告，无法支撑企业交付和面试展示。",
                "执行并归档",
                "automation",
            )
        if not items:
            add(
                DiagnosisSeverity.passed,
                "reports",
                "当前闭环材料已齐",
                "项目已有资产、执行、数据验证和报告证据，可继续扩大接口范围或做回归。",
                "查看报告",
                "reports",
            )

        items = sorted(
            items,
            key=lambda item: (
                self._severity_order(item.severity),
                item.module,
                item.title,
            ),
        )
        summary = self._summary(items)
        status = (
            "PASSED"
            if items and items[0].severity == DiagnosisSeverity.passed
            else "BLOCKED" if summary.p0 else "ATTENTION"
        )
        diagnosis = ProjectDiagnosis(
            project_id=project_id,
            generated_at=datetime.now().astimezone(),
            status=status,
            summary=summary,
            items=items,
        )
        if persist:
            self._repository.save_diagnosis(
                project_id,
                diagnosis.generated_at.isoformat(timespec="seconds"),
                [item.model_dump(mode="json") for item in items],
            )
        return diagnosis

    def _endpoint_closure_gaps(
        self,
        endpoints: list[dict[str, Any]],
        cases: list[dict[str, Any]],
        rules: list[dict[str, Any]],
        runs: list[dict[str, Any]],
        db_maps: list[dict[str, Any]],
        redis_maps: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        cases_by_endpoint = {}
        for case in cases:
            if case.get("method") and case.get("path"):
                key = (case["method"].upper(), case["path"].split("?", 1)[0])
                cases_by_endpoint.setdefault(key, case)
        rules_by_endpoint: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for rule in rules:
            rules_by_endpoint[rule["endpoint_id"]].append(rule)
        db_by_endpoint: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for mapping in db_maps:
            db_by_endpoint[mapping["endpoint_id"]].append(mapping)
        redis_by_endpoint: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for mapping in redis_maps:
            redis_by_endpoint[mapping["endpoint_id"]].append(mapping)
        run_rule_ids = {run["rule_id"] for run in runs}
        details = []
        for endpoint in endpoints:
            key = (endpoint["method"].upper(), endpoint["path"])
            setup_only = endpoint["path"] == "/userserv/id/login"
            endpoint_rules = rules_by_endpoint.get(endpoint["id"], [])
            endpoint_case = cases_by_endpoint.get(key)
            has_db_mapping = bool(db_by_endpoint.get(endpoint["id"]))
            has_redis_mapping = bool(redis_by_endpoint.get(endpoint["id"]))
            has_run_evidence = bool(
                endpoint_case and endpoint_case.get("execution_status") == "PASSED"
            )
            missing = []
            if not endpoint_case:
                missing.append("可执行用例")
            data_validation_enabled = bool(
                endpoint_rules or has_db_mapping or has_redis_mapping
            )
            if setup_only:
                pass
            elif has_db_mapping and any(
                rule.get("mysql_table") and not rule.get("mysql_condition")
                for rule in endpoint_rules
            ):
                missing.append("MySQL查询条件")
            if setup_only:
                pass
            elif (
                data_validation_enabled
                and endpoint_rules
                and not any(rule["id"] in run_rule_ids for rule in endpoint_rules)
                and not has_run_evidence
            ):
                missing.append("验证执行证据")
            try:
                responses = json.loads(endpoint.get("responses") or "{}")
            except Exception:
                responses = {}
            if not responses:
                missing.append("响应断言字段")
            if missing:
                details.append(
                    {
                        "endpoint": f"{endpoint['method']} {endpoint['path']}",
                        "name": endpoint.get("summary") or endpoint["path"],
                        "missing": missing,
                    }
                )
        return details

    def _summary(self, items: list[DiagnosisItem]) -> DiagnosisSummary:
        modules: dict[str, int] = {}
        for item in items:
            modules[item.module] = modules.get(item.module, 0) + 1
        return DiagnosisSummary(
            total=len(items),
            p0=sum(item.severity == DiagnosisSeverity.p0 for item in items),
            p1=sum(item.severity == DiagnosisSeverity.p1 for item in items),
            p2=sum(item.severity == DiagnosisSeverity.p2 for item in items),
            modules=modules,
        )

    def _severity_order(self, severity: DiagnosisSeverity) -> int:
        return {
            DiagnosisSeverity.p0: 0,
            DiagnosisSeverity.p1: 1,
            DiagnosisSeverity.p2: 2,
            DiagnosisSeverity.passed: 9,
        }.get(severity, 5)
