import json
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from qualityos.api import create_app
from qualityos.domain import digest
from qualityos.service import Problem


@pytest.fixture
def system(tmp_path):
    db = tmp_path / "quality.sqlite"
    creds = tmp_path / "private.json"
    app = create_app(db, creds)
    client = TestClient(app)
    users = json.loads(creds.read_text())
    response = client.post(
        "/api/v1/auth/session", json={"username": "qa", "password": users["qa"]["password"]}
    )
    assert response.status_code == 200
    client.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    w = client.post("/api/v1/demo/workspaces", json={"name": "Independent test"}).json()[
        "workspace_id"
    ]
    return app, client, w, users, db, creds


def snap(client, w, run=None):
    response = client.get(f"/api/v1/workspaces/{w}/snapshot", params={"run_id": run} if run else {})
    assert response.status_code == 200
    return response.json()


def command(client, w, op, payload, reason="Independent test review", status=200):
    s = snap(client, w)
    response = client.post(
        f"/api/v1/workspaces/{w}/commands/{op}",
        json={
            "expected_context_revision": s["workspace"]["revision"],
            "reason": reason,
            "payload": payload,
        },
        headers={"Idempotency-Key": uuid.uuid4().hex},
    )
    assert response.status_code == status, response.text
    return response


def find(s, kind, suffix=None):
    return [
        r
        for r in s["records"].values()
        if r["kind"] == kind and (not suffix or r["id"].endswith(suffix))
    ]


def authorize(client, w, rid):
    s = snap(client, w, rid)
    return command(
        client,
        w,
        "authorize",
        {
            "run_id": rid,
            "decision_id": s["decision"]["id"],
            "fingerprint": s["decision"]["applicability_fingerprint"],
            "max_units": 20,
            "minutes": 15,
        },
    )


def recover(client, w):
    s = snap(client, w)
    rid = s["run"]["id"]
    command(
        client,
        w,
        "change_context",
        {"run_id": rid, "field": "closure_lot_id", "value": find(s, "lot", "closure-c02")[0]["id"]},
    )
    command(client, w, "produce", {"run_id": rid, "units": 1}, status=409)
    assert snap(client, w)["decision"]["recommendation"] == "HOLD"
    command(client, w, "open_study", {"run_id": rid})
    s = snap(client, w)
    study = find(s, "study")[-1]["id"]
    oldcal = find(s, "calibration", "calibration-02-old")[0]
    command(
        client, w, "measure", {"study_id": study, "calibration_id": oldcal["id"], "value": "1.00"}
    )
    assert snap(client, w)["decision"]["recommendation"] == "HOLD"
    command(
        client,
        w,
        "calibrate",
        {
            "instrument_id": oldcal["instrument_id"],
            "method_id": "reference-test-v1",
            "basis": "Independent synthetic reference qualification",
        },
    )
    s = snap(client, w)
    fresh = [x for x in find(s, "calibration") if x["instrument_id"] == oldcal["instrument_id"]][-1]
    command(
        client, w, "measure", {"study_id": study, "calibration_id": fresh["id"], "value": "1.00"}
    )
    command(client, w, "functional", {"study_id": study, "outcome": "FAIL"}, status=409)
    command(client, w, "advance", {"hours": 24})
    command(client, w, "refresh_source", {"run_id": rid})
    command(client, w, "functional", {"study_id": study, "outcome": "FAIL"})
    assert snap(client, w)["decision"]["recommendation"] == "REJECT"
    command(
        client,
        w,
        "investigate",
        {
            "run_id": rid,
            "title": "Packaging condition investigation",
            "problem_definition": "Observed synthetic delayed functional failure; competing hypotheses retained.",
        },
    )
    s = snap(client, w)
    incident = find(s, "investigation")[-1]
    command(
        client,
        w,
        "hypothesis",
        {
            "investigation_id": incident["id"],
            "statement": "Application configuration may explain the functional result",
            "mechanism": "Test a bounded alternative setting; material identity alone is not causation",
            "supporting_ids": [],
            "refuting_ids": [],
        },
    )
    command(
        client,
        w,
        "propose_action",
        {
            "investigation_id": incident["id"],
            "config_id": find(s, "config", "capper-v2")[0]["id"],
            "verification_plan": "Fresh scoped torque and independent functional endpoint after dwell",
        },
    )
    action = find(snap(client, w), "action")[-1]
    command(client, w, "execute_action", {"action_id": action["id"]}, status=409)
    command(client, w, "approve_action", {"action_id": action["id"]})
    command(client, w, "execute_action", {"action_id": action["id"]})
    command(client, w, "assess_action", {"action_id": action["id"]}, status=409)
    command(client, w, "open_study", {"run_id": rid, "action_id": action["id"]})
    study2 = find(snap(client, w), "study")[-1]["id"]
    command(
        client, w, "measure", {"study_id": study2, "calibration_id": fresh["id"], "value": "1.00"}
    )
    command(client, w, "advance", {"hours": 24})
    command(client, w, "refresh_source", {"run_id": rid})
    command(client, w, "functional", {"study_id": study2, "outcome": "PASS"})
    s = snap(client, w)
    assert s["decision"]["recommendation"] == "ACCEPT"
    assert any(h["status"] == "ACTIVE" for h in find(s, "hold"))
    command(client, w, "assess_action", {"action_id": action["id"]})
    s = snap(client, w)
    command(
        client,
        w,
        "resolve_hold",
        {
            "run_id": rid,
            "decision_id": s["decision"]["id"],
            "fingerprint": s["decision"]["applicability_fingerprint"],
        },
    )
    authorize(client, w, rid)
    command(client, w, "produce", {"run_id": rid, "units": 5})
    return rid, fresh["id"]


def test_complete_recovery_correction_history_restart(system):
    app, client, w, users, db, creds = system
    rid, cal = recover(client, w)
    before = snap(client, w)
    assert len(find(before, "unit")) == 5
    historical = before["decision"]["id"]
    other = next(x for x in before["runs"] if x["id"] != rid)
    command(client, w, "refresh_source", {"run_id": other["id"]})
    command(
        client,
        w,
        "revoke_calibration",
        {
            "calibration_id": cal,
            "effective_from": "2026-01-15T00:00:00Z",
            "effective_until": before["clock"],
        },
    )
    current = snap(client, w)
    assert current["decision"]["recommendation"] == "HOLD"
    assert len(current["impact"]["units"]) == 5
    assert snap(client, w, other["id"])["decision"]["recommendation"] == "ACCEPT"
    old = client.get(
        f"/api/v1/workspaces/{w}/snapshot", params={"run_id": rid, "decision_id": historical}
    ).json()
    assert old["historical"] and old["decision"]["recommendation"] == "ACCEPT"
    command(client, w, "produce", {"run_id": rid, "units": 1}, status=409)
    assert app.state.store.semantic_digest(w) == app.state.store.replay_digest(w)
    app.state.store.engine.dispose()
    app2 = create_app(db, creds)
    assert app2.state.store.semantic_digest(w) == app2.state.store.replay_digest(w)
    assert len(app2.state.service.snapshot(w)["impact"]["units"]) == 5


def test_idempotency_budget_and_clean_control(system):
    app, c, w, *_ = system
    rid = snap(c, w)["run"]["id"]
    authorize(c, w, rid)
    s = snap(c, w)
    body = {
        "expected_context_revision": s["workspace"]["revision"],
        "payload": {"run_id": rid, "units": 5},
        "reason": "Paired retry test",
    }
    headers = {"Idempotency-Key": "fixed-unique-key"}
    url = f"/api/v1/workspaces/{w}/commands/produce"
    first = c.post(url, json=body, headers=headers)
    second = c.post(url, json=body, headers=headers)
    assert first.status_code == second.status_code == 200
    assert second.json()["replayed"]
    assert len(find(snap(c, w), "unit")) == 5
    changed = {**body, "payload": {"run_id": rid, "units": 2}}
    assert c.post(url, json=changed, headers=headers).status_code == 409
    command(c, w, "comment", {"run_id": rid, "text": "Unrelated review comment"})
    clean = snap(c, w)
    command(
        c,
        w,
        "measure",
        {
            "study_id": find(clean, "study", "study-initial-1")[0]["id"],
            "calibration_id": find(clean, "calibration", "calibration-01")[0]["id"],
            "value": "1.00",
            "count": 1,
        },
    )
    command(c, w, "produce", {"run_id": rid, "units": 15})
    command(c, w, "produce", {"run_id": rid, "units": 1}, status=409)
    assert len(find(snap(c, w), "unit")) == 20
    assert app.state.store.semantic_digest(w) == app.state.store.replay_digest(w)


@pytest.mark.parametrize("role", ["viewer", "operator", "admin"])
def test_direct_role_and_csrf_guards(system, role):
    app, c, w, users, *_ = system
    s = snap(c, w)
    response = c.post(
        "/api/v1/auth/session", json={"username": role, "password": users[role]["password"]}
    )
    c.headers["X-CSRF-Token"] = response.json()["csrf_token"]
    body = {
        "expected_context_revision": s["workspace"]["revision"],
        "reason": "Attempted QA bypass",
        "payload": {
            "run_id": s["run"]["id"],
            "decision_id": s["decision"]["id"],
            "fingerprint": s["decision"]["applicability_fingerprint"],
        },
    }
    assert (
        c.post(
            f"/api/v1/workspaces/{w}/commands/authorize",
            json=body,
            headers={"Idempotency-Key": uuid.uuid4().hex},
        ).status_code
        == 403
    )
    c.headers["X-CSRF-Token"] = "incorrect"
    assert c.post("/api/v1/demo/workspaces", json={}).status_code == 403
    assert (
        c.post(
            "/api/v1/demo/workspaces", json={}, headers={"Origin": "https://untrusted.example"}
        ).status_code
        == 403
    )


def test_stale_context_scope_isolation_expiry(system):
    app, c, w, *_ = system
    s = snap(c, w)
    rid = s["run"]["id"]
    authorize(c, w, rid)
    old = snap(c, w)
    command(
        c,
        w,
        "change_context",
        {"run_id": rid, "field": "closure_lot_id", "value": find(s, "lot", "closure-c02")[0]["id"]},
    )
    response = c.post(
        f"/api/v1/workspaces/{w}/commands/produce",
        json={
            "expected_context_revision": old["workspace"]["revision"],
            "reason": "Stale browser attempt",
            "payload": {"run_id": rid, "units": 1},
        },
        headers={"Idempotency-Key": uuid.uuid4().hex},
    )
    assert response.status_code == 409
    assert not find(snap(c, w), "unit")
    w2 = c.post("/api/v1/demo/workspaces", json={"name": "Isolated"}).json()["workspace_id"]
    command(c, w2, "open_study", {"run_id": rid}, status=422)
    rid2 = snap(c, w2)["run"]["id"]
    authorize(c, w2, rid2)
    command(c, w2, "advance", {"hours": 1})
    command(c, w2, "refresh_source", {"run_id": rid2})
    command(c, w2, "produce", {"run_id": rid2, "units": 1}, status=409)


def test_atomic_context_race(system):
    app, c, w, *_ = system
    s = snap(c, w)
    rid = s["run"]["id"]
    authorize(c, w, rid)
    revision = snap(c, w)["workspace"]["revision"]
    actor = {"id": "qa", "role": "QUALITY_ENGINEER"}
    ops = [
        ("produce", {"run_id": rid, "units": 1}),
        (
            "change_context",
            {
                "run_id": rid,
                "field": "closure_lot_id",
                "value": find(s, "lot", "closure-c02")[0]["id"],
            },
        ),
    ]

    def task(arg):
        op, payload = arg
        try:
            return app.state.service.command(
                w,
                actor,
                op,
                {"expected_context_revision": revision, "reason": "Race test", "payload": payload},
                uuid.uuid4().hex,
            )
        except Problem as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(task, ops))
    assert sum(isinstance(x, dict) for x in results) == 1
    assert "STALE_CONTEXT" in results


def test_append_only_and_transaction_rollback(system):
    app, c, w, *_ = system
    store = app.state.store
    before = store.semantic_digest(w)
    with pytest.raises(RuntimeError):
        with store.transaction() as conn:
            conn.execute(text("UPDATE entities SET data='{}' WHERE workspace_id=:w"), {"w": w})
            raise RuntimeError("Injected before commit")
    assert store.semantic_digest(w) == before
    with pytest.raises(Exception):
        with store.transaction() as conn:
            conn.execute(text("UPDATE events SET type='FAKE' WHERE workspace_id=:w"), {"w": w})
    with store.engine.connect() as conn:
        assert conn.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1


def test_specimen_dwell_and_duplicate_endpoint_are_server_enforced(system):
    _, c, w, *_ = system
    s = snap(c, w)
    rid = s["run"]["id"]
    command(
        c,
        w,
        "change_context",
        {"run_id": rid, "field": "closure_lot_id", "value": find(s, "lot", "closure-c02")[0]["id"]},
    )
    command(c, w, "open_study", {"run_id": rid})
    command(c, w, "advance", {"hours": 24})
    s = snap(c, w)
    study = find(s, "study")[-1]["id"]
    command(
        c,
        w,
        "measure",
        {
            "study_id": study,
            "calibration_id": find(s, "calibration", "calibration-01")[0]["id"],
            "value": "1.00",
        },
    )
    response = command(c, w, "functional", {"study_id": study, "outcome": "PASS"}, status=409)
    assert response.json()["code"] == "DWELL_INCOMPLETE"
    command(c, w, "advance", {"hours": 24})
    command(c, w, "refresh_source", {"run_id": rid})
    command(c, w, "functional", {"study_id": study, "outcome": "PASS"})
    command(c, w, "functional", {"study_id": study, "outcome": "PASS"}, status=409)
    assert snap(c, w)["decision"]["recommendation"] == "ACCEPT"


def test_late_functional_correction_preserves_history_and_scopes_impact(system):
    _, c, w, *_ = system
    s = snap(c, w)
    rid = s["run"]["id"]
    other = next(x["id"] for x in s["runs"] if x["id"] != rid)
    authorize(c, w, rid)
    command(c, w, "produce", {"run_id": rid, "units": 2})
    authorize(c, w, other)
    command(c, w, "produce", {"run_id": other, "units": 1})
    s = snap(c, w)
    historical = s["decision"]["id"]
    evidence = next(x for x in find(s, "functional") if x["study_id"].endswith("study-initial-1"))
    command(c, w, "correct_evidence", {"evidence_id": evidence["id"], "outcome": "FAIL"})
    current = snap(c, w)
    assert (
        current["decision"]["recommendation"] == "HOLD"
    )  # retained conflicting independent passes
    assert len(current["impact"]["units"]) == 2 and current["impact"]["certainty"] == "EXACT"
    assert snap(c, w, other)["run"]["state"] == "AUTHORIZED"
    old = c.get(
        f"/api/v1/workspaces/{w}/snapshot", params={"run_id": rid, "decision_id": historical}
    ).json()
    assert old["decision"]["recommendation"] == "ACCEPT" and not old["impact"]["units"]
    assert current["records"][evidence["id"]]["outcome"] == "PASS"
    command(
        c, w, "correct_evidence", {"evidence_id": evidence["id"], "outcome": "PASS"}, status=409
    )
    command(c, w, "change_context", {"run_id": rid, "field": "lineage", "value": "PARTIAL"})
    broader = snap(c, w)
    assert broader["impact"]["certainty"] == "CONSERVATIVE" and len(broader["impact"]["units"]) == 3


def test_read_audit_export_and_restarted_retry_do_not_change_domain(system):
    app, c, w, users, db, creds = system
    s = snap(c, w)
    rid = s["run"]["id"]
    authorize(c, w, rid)
    s = snap(c, w)
    body = {
        "expected_context_revision": s["workspace"]["revision"],
        "reason": "Commit then restart retry",
        "payload": {"run_id": rid, "units": 1},
    }
    url = f"/api/v1/workspaces/{w}/commands/produce"
    headers = {"Idempotency-Key": "persisted-retry-key"}
    original = c.post(url, json=body, headers=headers).json()
    state = app.state.store.semantic_digest(w)
    exported = c.get(f"/api/v1/workspaces/{w}/export").json()
    assert exported["semantic_digest"] == state
    assert any(a["action"] == "SNAPSHOT_READ" for a in exported["audit_system_time"])
    assert any(a["action"] == "DECISION_CREATED" for a in exported["audit_system_time"])
    assert exported["decisions"] and exported["provenance"] == "SYNTHETIC"
    assert app.state.store.semantic_digest(w) == state
    app.state.store.engine.dispose()
    fresh = TestClient(create_app(db, creds))
    auth = fresh.post(
        "/api/v1/auth/session", json={"username": "qa", "password": users["qa"]["password"]}
    ).json()
    fresh.headers["X-CSRF-Token"] = auth["csrf_token"]
    retry = fresh.post(url, json=body, headers=headers)
    assert (
        retry.status_code == 200
        and retry.json()["event_id"] == original["event_id"]
        and retry.json()["replayed"]
    )
    assert len(find(snap(fresh, w), "unit")) == 1


def test_store_failure_rolls_back_and_never_grants_permission(system, monkeypatch):
    from sqlalchemy.exc import OperationalError

    app, c, w, *_ = system
    s = snap(c, w)
    rid = s["run"]["id"]
    before = app.state.store.semantic_digest(w)

    def fail_commit(*args, **kwargs):
        raise OperationalError("Injected write outage", {}, RuntimeError("offline"))

    monkeypatch.setattr(app.state.service, "_commit", fail_commit)
    response = command(
        c,
        w,
        "authorize",
        {
            "run_id": rid,
            "decision_id": s["decision"]["id"],
            "fingerprint": s["decision"]["applicability_fingerprint"],
        },
        status=503,
    )
    assert response.json()["code"] == "STORE_UNAVAILABLE"
    assert app.state.store.semantic_digest(w) == before
    assert not find(snap(c, w), "permit")


def test_old_qualification_cannot_complete_sparse_action_verification(system):
    _, c, w, *_ = system
    s = snap(c, w)
    rid = s["run"]["id"]
    command(
        c,
        w,
        "investigate",
        {
            "run_id": rid,
            "title": "Fresh verification boundary",
            "problem_definition": "Test a scoped action independently from prior qualifying evidence.",
        },
    )
    incident = find(snap(c, w), "investigation")[-1]["id"]
    command(
        c,
        w,
        "propose_action",
        {
            "investigation_id": incident,
            "config_id": find(s, "config", "capper-v1")[0]["id"],
            "verification_plan": "Independent new specimen set and delayed functional test",
        },
    )
    action = find(snap(c, w), "action")[-1]["id"]
    command(c, w, "approve_action", {"action_id": action})
    command(c, w, "execute_action", {"action_id": action})
    command(c, w, "open_study", {"run_id": rid, "action_id": action})
    study = find(snap(c, w), "study")[-1]["id"]
    command(
        c,
        w,
        "measure",
        {
            "study_id": study,
            "calibration_id": find(s, "calibration", "calibration-01")[0]["id"],
            "value": "1.00",
            "count": 1,
        },
    )
    command(c, w, "advance", {"hours": 24})
    command(c, w, "refresh_source", {"run_id": rid})
    command(c, w, "functional", {"study_id": study, "outcome": "PASS"})
    assert (
        snap(c, w)["decision"]["recommendation"] == "ACCEPT"
    )  # old unchanged-scope proof remains valid
    response = command(c, w, "assess_action", {"action_id": action}, status=409)
    assert response.json()["code"] == "NEW_VERIFICATION_REQUIRED"
    assert find(snap(c, w), "action")[-1]["status"] == "VERIFYING"


def test_source_gap_and_adverse_compatible_observation_revoke_at_use(system):
    _, c, w, *_ = system
    s = snap(c, w)
    rid = s["run"]["id"]
    authorize(c, w, rid)
    command(c, w, "refresh_source", {"run_id": rid, "complete": False})
    assert snap(c, w)["decision"]["recommendation"] == "HOLD"
    command(c, w, "produce", {"run_id": rid, "units": 1}, status=409)
    command(c, w, "refresh_source", {"run_id": rid, "complete": True})
    s = snap(c, w)
    command(
        c,
        w,
        "resolve_hold",
        {
            "run_id": rid,
            "decision_id": s["decision"]["id"],
            "fingerprint": s["decision"]["applicability_fingerprint"],
        },
    )
    authorize(c, w, rid)
    s = snap(c, w)
    command(
        c,
        w,
        "measure",
        {
            "study_id": find(s, "study", "study-initial-1")[0]["id"],
            "calibration_id": find(s, "calibration", "calibration-01")[0]["id"],
            "value": "1.50",
            "count": 1,
        },
    )
    assert snap(c, w)["decision"]["recommendation"] == "REJECT"
    command(c, w, "produce", {"run_id": rid, "units": 1}, status=409)
    assert not find(snap(c, w), "unit")


def test_migration_reentry_and_newer_schema_refusal(system):
    from qualityos.store import Store

    app, _, w, _, db, _ = system
    current = app.state.store.semantic_digest(w)
    assert Store(db).semantic_digest(w) == current
    with app.state.store.transaction() as conn:
        conn.execute(text("INSERT INTO schema_version VALUES (99,'synthetic-test')"))
    with pytest.raises(RuntimeError, match="newer"):
        Store(db)


def test_chunked_size_and_validation_errors_do_not_echo_secrets(system):
    _, c, w, *_ = system
    response = c.post(
        "/api/v1/auth/session",
        content=iter([b'{"password":"', b"x" * 66000, b'"}']),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 413 and response.json()["code"] == "PAYLOAD_TOO_LARGE"
    secret = "private-placeholder-must-not-be-echoed"
    response = c.post(
        "/api/v1/auth/session", json={"password": secret, "username": {"bad": "shape"}}
    )
    assert response.status_code == 422 and response.json()["code"] == "INVALID_REQUEST"
    assert secret not in response.text
