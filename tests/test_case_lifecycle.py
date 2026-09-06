import app
import pytest


def test_new_cases_default_to_draft_and_can_be_activated(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(app, "DB_PATH", tmp_path / "lifecycle.db")
    app.init_db()
    created = app.now()
    app.execute(
        "INSERT INTO projects(id,name,description,base_url,created_at,updated_at) VALUES (?,?,?,?,?,?)",
        ("project-1", "测试项目", "", "", created, created),
    )
    app.execute(
        "INSERT INTO test_cases(id,project_id,title,created_at) VALUES (?,?,?,?)",
        ("case-1", "project-1", "新生成用例", created),
    )

    draft = app.row("SELECT lifecycle_status FROM test_cases WHERE id=?", ("case-1",))
    with pytest.raises(ValueError, match="只有 ACTIVE 用例可以执行"):
        app.execute_case("case-1")
    result = app.set_test_case_lifecycle("case-1", "ACTIVE", "评审通过")
    active = app.row("SELECT lifecycle_status,lifecycle_note FROM test_cases WHERE id=?", ("case-1",))

    assert draft["lifecycle_status"] == "DRAFT"
    assert result["previous_status"] == "DRAFT"
    assert active == {"lifecycle_status": "ACTIVE", "lifecycle_note": "评审通过"}
    history = app.test_case_lifecycle_history("case-1")["history"]
    assert history[0]["previous_status"] == "DRAFT"
    assert history[0]["lifecycle_status"] == "ACTIVE"
    assert history[0]["note"] == "评审通过"


def test_lifecycle_rejects_unknown_status(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(app, "DB_PATH", tmp_path / "invalid-lifecycle.db")
    app.init_db()

    try:
        app.set_test_case_lifecycle("missing", "REMOVED")
    except ValueError as exc:
        assert "DRAFT、ACTIVE 或 DEPRECATED" in str(exc)
    else:
        raise AssertionError("unknown lifecycle status must be rejected")


def test_bulk_lifecycle_approval_is_audited_as_one_batch(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(app, "DB_PATH", tmp_path / "bulk-lifecycle.db")
    app.init_db()
    created = app.now()
    app.execute(
        "INSERT INTO projects(id,name,description,base_url,created_at,updated_at) VALUES (?,?,?,?,?,?)",
        ("project-1", "测试项目", "", "", created, created),
    )
    for case_id in ("case-1", "case-2"):
        app.execute(
            "INSERT INTO test_cases(id,project_id,title,created_at) VALUES (?,?,?,?)",
            (case_id, "project-1", case_id, created),
        )

    result = app.bulk_set_test_case_lifecycle(
        "project-1", ["case-1", "case-2"], "ACTIVE", "批量评审通过", "reviewer-a"
    )
    cases = app.rows("SELECT id,lifecycle_status FROM test_cases ORDER BY id")
    history = app.rows("SELECT * FROM test_case_lifecycle_history ORDER BY case_id")

    assert result["updated"] == 2
    assert {item["lifecycle_status"] for item in cases} == {"ACTIVE"}
    assert len({item["batch_id"] for item in history}) == 1
    assert {item["actor"] for item in history} == {"reviewer-a"}


def test_bulk_lifecycle_rejects_foreign_case_without_partial_update(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(app, "DB_PATH", tmp_path / "bulk-atomic.db")
    app.init_db()
    created = app.now()
    for project_id in ("project-1", "project-2"):
        app.execute(
            "INSERT INTO projects(id,name,description,base_url,created_at,updated_at) VALUES (?,?,?,?,?,?)",
            (project_id, project_id, "", "", created, created),
        )
    app.execute("INSERT INTO test_cases(id,project_id,title,created_at) VALUES (?,?,?,?)", ("case-1", "project-1", "A", created))
    app.execute("INSERT INTO test_cases(id,project_id,title,created_at) VALUES (?,?,?,?)", ("case-2", "project-2", "B", created))

    with pytest.raises(ValueError, match="不属于当前项目"):
        app.bulk_set_test_case_lifecycle("project-1", ["case-1", "case-2"], "ACTIVE")

    assert app.row("SELECT lifecycle_status FROM test_cases WHERE id='case-1'")["lifecycle_status"] == "DRAFT"
