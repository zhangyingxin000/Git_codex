import json

from quality_hub_backend.services.performance_analysis import (
    diagnose_performance,
    evaluate_gate,
    summarize_account_usage,
    summarize_jtl,
    thresholds_for,
)


def test_jtl_summary_uses_real_sample_window_and_separates_rps_from_tps(tmp_path):
    jtl = tmp_path / "result.jtl"
    jtl.write_text(
        "timeStamp,elapsed,label,responseCode,responseMessage,success,failureMessage,latency,connect,bytes,sentBytes,allThreads\n"
        "1000,200,read,200,OK,true,,150,20,1024,256,1\n"
        "1200,400,read,500,Error,false,boom,300,30,2048,512,2\n",
        encoding="utf-8",
    )

    summary = summarize_jtl(jtl)

    assert summary["duration_seconds"] == 0.6
    assert summary["throughput_rps"] == 3.33
    assert summary["request_throughput_rps"] == 3.33
    assert summary["transaction_throughput_tps"] is None
    assert summary["active_threads_peak"] == 2
    assert summary["by_label"][0]["errors"] == 1


def test_profiles_cover_full_performance_channel_and_stability_alias():
    assert thresholds_for({"performance_profile": "concurrency"})["profile"] == "concurrency"
    assert thresholds_for({"performance_profile": "spike"})["profile"] == "spike"
    assert thresholds_for({"performance_profile": "stress"})["profile"] == "stress"
    assert thresholds_for({"performance_profile": "stability"})["profile"] == "soak"


def test_baseline_metrics_can_exclude_declared_warmup_samples(tmp_path):
    jtl = tmp_path / "result.jtl"
    jtl.write_text(
        "timeStamp,elapsed,label,responseCode,responseMessage,success,failureMessage,Latency,Connect,allThreads,bytes,sentBytes\n"
        "1000,9000,read,200,OK,true,,9000,8800,1,100,20\n"
        "11000,100,read,200,OK,true,,100,0,1,100,20\n"
        "11500,120,read,200,OK,true,,120,0,1,100,20\n",
        encoding="utf-8",
    )

    summary = summarize_jtl(jtl, warmup_samples_per_label=1)

    assert summary["raw_requests"] == 3
    assert summary["requests"] == 2
    assert summary["warmup_samples_excluded"] == 1
    assert summary["max_ms"] == 120
    assert summary["measurement_policy"]["raw_jtl_preserved"] is True


def test_warmup_policy_never_removes_every_sample_for_a_label(tmp_path):
    jtl = tmp_path / "short-run.jtl"
    jtl.write_text(
        "timeStamp,elapsed,label,responseCode,responseMessage,success,failureMessage\n"
        "1000,100,read,200,OK,true,\n"
        "1000,110,TX::read-flow,200,OK,true,\n",
        encoding="utf-8",
    )

    summary = summarize_jtl(jtl, warmup_samples_per_label=1)

    assert summary["requests"] == 1
    assert summary["transaction_samples"] == 1
    assert summary["warmup_samples_excluded"] == 0
    assert summary["error_rate"] == 0
    assert summary["measurement_policy"]["retain_at_least_one_sample_per_label"] is True


def test_automatic_stop_socket_close_is_preserved_in_jtl_but_excluded_from_gate_metrics(tmp_path):
    jtl = tmp_path / "auto-stopped.jtl"
    jtl.write_text(
        "timeStamp,elapsed,label,responseCode,responseMessage,success,failureMessage\n"
        "1000,100,read,200,OK,true,\n"
        "1200,150,read,200,OK,true,\n"
        "1400,2500,read,Non HTTP response code: java.net.SocketException,Non HTTP response message: Socket closed,false,interrupted by StopTestNow\n",
        encoding="utf-8",
    )

    summary = summarize_jtl(
        jtl,
        exclude_automatic_stop_artifacts=True,
    )

    assert summary["raw_requests"] == 3
    assert summary["requests"] == 2
    assert summary["errors"] == 0
    assert summary["automatic_stop_samples_excluded"] == 1
    assert summary["measurement_policy"]["automatic_stop_artifacts_excluded"] is True


def test_diagnosis_does_not_claim_server_root_cause_without_external_evidence(tmp_path):
    jtl = tmp_path / "result.jtl"
    jtl.write_text(
        "timeStamp,elapsed,label,responseCode,responseMessage,success,failureMessage\n"
        "1000,10000,read,500,Server Error,false,boom\n",
        encoding="utf-8",
    )
    summary = summarize_jtl(jtl)
    gate = evaluate_gate(summary, {"performance_profile": "baseline"})
    diagnosis = diagnose_performance(summary, gate)

    assert diagnosis["evidence_boundary"]["requires_external_evidence"]
    assert diagnosis["bottleneck_hypotheses"][0]["confidence"] == "low"
    assert "不能单独确认" in diagnosis["bottleneck_hypotheses"][0]["reason"]


def test_transaction_parent_samples_produce_tps_separate_from_request_rps(tmp_path):
    jtl = tmp_path / "transactions.jtl"
    jtl.write_text(
        "timeStamp,elapsed,label,responseCode,responseMessage,success,failureMessage\n"
        "1000,100,GET applicant,200,OK,true,\n"
        "1100,120,GET proxy,200,OK,true,\n"
        "1000,250,TX::salary-flow,200,OK,true,\n"
        "2000,110,GET applicant,200,OK,true,\n"
        "2100,130,GET proxy,200,OK,true,\n"
        "2000,260,TX::salary-flow,200,OK,true,\n",
        encoding="utf-8",
    )

    summary = summarize_jtl(jtl)

    assert summary["requests"] == 4
    assert summary["transaction_samples"] == 2
    assert summary["request_throughput_rps"] != summary["transaction_throughput_tps"]
    assert summary["transaction_error_rate"] == 0
    assert summary["transaction_p95_ms"] > 0


def test_request_only_mode_does_not_publish_tps_from_legacy_transaction_samples(tmp_path):
    jtl = tmp_path / "legacy-request-only.jtl"
    jtl.write_text(
        "timeStamp,elapsed,label,responseCode,responseMessage,threadName,success,failureMessage,URL\n"
        "1000,20,GET /health,200,OK,thread-1,true,,https://example.test/health\n"
        "1000,22,TX::legacy-wrapper,200,OK,thread-1,true,,\n"
        "1100,18,GET /health,200,OK,thread-1,true,,https://example.test/health\n"
        "1100,19,TX::legacy-wrapper,200,OK,thread-1,true,,\n",
        encoding="utf-8",
    )

    summary = summarize_jtl(jtl, include_transaction_metrics=False)

    assert summary["measurement_mode"] == "request_only"
    assert summary["observed_transaction_samples"] == 2
    assert summary["transaction_samples"] == 0
    assert summary["transaction_throughput_tps"] is None
    assert summary["request_throughput_rps"] > 0


def test_account_usage_tracks_thread_sources_and_runtime_rotation(tmp_path):
    jtl = tmp_path / "account-rotation.jtl"
    jtl.write_text(
        "timeStamp,elapsed,label,responseCode,responseMessage,threadName,success,failureMessage,URL\n"
        "1000,20,read,401,Unauthorized,baseline 性能执行 1-1,false,,https://example.test/read?uid=1001&ticket=redacted\n"
        "1100,18,read,200,OK,baseline 性能执行 1-1,true,,https://example.test/read?uid=1002&ticket=redacted\n"
        "1200,17,read,200,OK,baseline 性能执行 1-1,true,,https://example.test/read?uid=1002&ticket=redacted\n",
        encoding="utf-8",
    )
    allocations = [
        {"applicant_uid": "1001", "applicant_source": "requirements/demo/accounts.csv"},
        {"applicant_uid": "1002", "applicant_source": "requirements/demo/accounts.csv"},
    ]

    summary = summarize_jtl(jtl, account_allocations=allocations)
    usage = summary["account_usage"]

    assert usage["status"] == "TRACKED"
    assert usage["threads"] == 1
    assert usage["unique_accounts"] == 2
    assert usage["rotation_count"] == 1
    assert usage["by_thread"][0]["uid_sequence"] == ["1001", "1002"]
    assert usage["by_thread"][0]["accounts"][0]["source"] == "requirements/demo/accounts.csv"
    assert "redacted" not in str(usage).lower()


def test_account_usage_marks_requests_without_identity_as_partial():
    usage = summarize_account_usage([
        {"threadName": "thread-1", "URL": "https://example.test/read?uid=1001", "success": "true"},
        {"threadName": "thread-1", "URL": "https://example.test/health", "success": "true"},
    ])

    assert usage["status"] == "PARTIAL"
    assert usage["tracked_requests"] == 1
    assert usage["untracked_requests"] == 1


def test_account_usage_maps_mcp_jtl_thread_to_deterministic_account_slot():
    allocations = [{
        "slot": 1,
        "applicant_uid": "1001",
        "applicant_source": "applicants.csv",
        "proxy_uid": "2001",
        "proxy_source": "proxies.csv",
    }]
    usage = summarize_account_usage([
        {
            "threadName": "baseline 性能执行 1-1",
            "URL": "https://example.test/userserv/salary/trade/order/create",
            "success": "true",
        },
        {
            "threadName": "baseline 性能执行 1-1",
            "URL": "https://example.test/userserv/salary/trade/agent/order/accept",
            "success": "true",
        },
    ], allocations)

    assert usage["status"] == "TRACKED_BY_ALLOCATION"
    assert usage["tracked_requests"] == 2
    assert usage["allocation_inferred_requests"] == 2
    assert [(item["role"], item["uid"], item["source"]) for item in usage["by_thread"][0]["accounts"]] == [
        ("applicant", "1001", "applicants.csv"),
        ("proxy", "2001", "proxies.csv"),
    ]


def test_account_usage_uses_endpoint_side_when_url_contains_both_roles():
    allocations = [{
        "applicant_uid": "1001",
        "applicant_source": "applicants.csv",
        "proxy_uid": "2001",
        "proxy_source": "proxies.csv",
    }]
    usage = summarize_account_usage([
        {
            "threadName": "thread-1",
            "URL": "https://example.test/union/get?uid=1001&agentUid=2001&proxyUid=2001",
            "success": "true",
        },
        {
            "threadName": "thread-1",
            "URL": "https://example.test/userserv/salary/trade/agent/notice?uid=2001&agentUid=2001",
            "success": "true",
        },
    ], allocations)

    accounts = usage["by_thread"][0]["accounts"]
    assert [(item["role"], item["uid"], item["source"]) for item in accounts] == [
        ("applicant", "1001", "applicants.csv"),
        ("proxy", "2001", "proxies.csv"),
    ]
