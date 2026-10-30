"""Explicit expected story order plus adverse/return-visitor boundaries."""
from fastapi.testclient import TestClient

from qualityos.api import create_app
from test_workflow import command, find, snap, system


EXPECTED = [
    "authorize_initial",
    "produce_initial",
    "change_caps",
    "open_first",
    "measure_old",
    "new_reference",
    "measure_valid",
    "wait_first",
    "source_first",
    "fail_first",
    "investigate",
    "hypothesis",
    "propose",
    "approve",
    "execute",
    "open_fresh",
    "measure_fresh",
    "wait_fresh",
    "source_fresh",
    "pass_fresh",
    "assess",
    "resolve",
    "authorize_new",
    "produce_new",
    "complete",
]


def new_story(client):
    response = client.post(
        "/api/v1/demo/workspaces",
        json={"name": "A beginner follows the packaging story", "guided": True},
    )
    assert response.status_code == 200, response.text
    return response.json()["workspace_id"]


def advance_story(client, w):
    s = snap(client, w)
    j = s["journey"]
    return command(client, w, j["operation"], j["payload"], reason=j["reason"])


def test_complete_guide_follows_actual_persisted_work_not_clicks(system):
    app, c, legacy, *_ = system
    assert snap(c, legacy)["journey"] is None
    w = new_story(c)
    initial = snap(c, w)
    for index, expected in enumerate(EXPECTED):
        s = snap(c, w)
        j = s["journey"]
        assert j["id"] == expected, (index, j["id"], expected)
        assert j["step_index"] == index
        before = app.state.store.semantic_digest(w)
        assert snap(c, w)["journey"] == j
        assert app.state.store.semantic_digest(w) == before
        if expected == "complete":
            break
        if expected == "open_first":
            assert s["decision"]["recommendation"] == "HOLD"
            assert next(x for x in s["runs"] if x["id"] != s["run"]["id"])["state"] != "HELD"
        if expected == "new_reference":
            assert all(
                x["reliability"]["verdict"] == "INVALID" for x in s["decision"]["measurements"]
            )
        if expected == "investigate":
            assert s["decision"]["recommendation"] == "REJECT"
        if expected == "resolve":
            assert s["decision"]["recommendation"] == "ACCEPT"
            assert any(x["status"] == "ACTIVE" for x in find(s, "hold"))
        advance_story(c, w)
    final = snap(c, w)
    assert final["journey"]["status"] == "COMPLETE"
    assert len(find(final, "unit")) == 7
    assert any(x["outcome"] == "FAIL" for x in find(final, "functional"))
    assert find(final, "guide") and app.state.store.semantic_digest(
        w
    ) == app.state.store.replay_digest(w)
    historical = c.get(
        f"/api/v1/workspaces/{w}/snapshot", params={"decision_id": initial["decision"]["id"]}
    ).json()
    assert (
        historical["journey"]["status"] == "HISTORICAL"
        and historical["journey"]["operation"] is None
    )
    control = next(x["id"] for x in final["runs"] if x["id"] != final["run"]["id"])
    assert snap(c, w, control)["journey"]["status"] == "CONTROL"
    command(c, w, "complete_run", {"run_id": final["run"]["id"]})
    assert snap(c, w)["journey"]["status"] == "COMPLETE"
    assert snap(c, w)["run"]["state"] == "COMPLETED"
    verified = find(final, "action")[0]
    fresh_study = next(x for x in find(final, "study") if x.get("action_id") == verified["id"])
    observation = next(x for x in find(final, "measurement") if x["study_id"] == fresh_study["id"])
    command(
        c,
        w,
        "revoke_calibration",
        {
            "calibration_id": observation["calibration_id"],
            "effective_from": observation["occurred_at"],
            "effective_until": observation["occurred_at"],
        },
    )
    late = snap(c, w)
    assert late["journey"]["status"] == "LATE_DISCOVERY" and late["journey"]["operation"] is None
    assert len(late["impact"]["units"]) == 5


def test_resume_story_in_new_app_and_preserve_server_role_guards(system):
    app, c, _, users, db, creds = system
    w = new_story(c)
    advance_story(c, w)
    advance_story(c, w)
    assert snap(c, w)["journey"]["id"] == "change_caps"
    app.state.store.engine.dispose()
    fresh = TestClient(create_app(db, creds))
    response = fresh.post(
        "/api/v1/auth/session", json={"username": "qa", "password": users["qa"]["password"]}
    ).json()
    fresh.headers["X-CSRF-Token"] = response["csrf_token"]
    assert snap(fresh, w)["journey"]["id"] == "change_caps"
    # The guide supplies a proposal, never a signing capability.
    other = new_story(fresh)
    s = snap(fresh, other)
    response = fresh.post(
        "/api/v1/auth/session",
        json={"username": "operator", "password": users["operator"]["password"]},
    ).json()
    fresh.headers["X-CSRF-Token"] = response["csrf_token"]
    command(fresh, other, "authorize", s["journey"]["payload"], status=403)
    assert snap(fresh, other)["journey"]["id"] == "authorize_initial"


def test_manual_alternative_result_is_explained_without_forcing_failure(system):
    _, c, *_ = system
    w = new_story(c)
    for expected in EXPECTED:
        s = snap(c, w)
        assert s["journey"]["id"] == expected
        if expected == "fail_first":
            payload = {**s["journey"]["payload"], "outcome": "PASS"}
            command(c, w, "functional", payload)
            break
        advance_story(c, w)
    after = snap(c, w)
    assert after["journey"]["status"] == "NEEDS_REVIEW"
    assert after["journey"]["operation"] is None
    assert not find(after, "action")
    assert all(x["outcome"] == "PASS" for x in find(after, "functional"))


def test_guided_variant_is_bounded_and_never_mutates_an_existing_workspace(system):
    app, c, legacy, *_ = system
    before = app.state.store.semantic_digest(legacy)
    assert (
        c.post("/api/v1/demo/workspaces", json={"guided": True, "scenario": "S2"}).status_code
        == 422
    )
    w = new_story(c)
    assert app.state.store.semantic_digest(legacy) == before
    assert snap(c, w)["workspace"]["scenario_version"].endswith("/guided-story-v1")
    assert snap(c, w)["journey"]["id"] == "authorize_initial"
    s = snap(c, w)
    original = find(s, "measurement", "torque-initial-1-1")[0]
    command(
        c,
        w,
        "revoke_calibration",
        {
            "calibration_id": original["calibration_id"],
            "effective_from": original["occurred_at"],
            "effective_until": original["occurred_at"],
        },
    )
    changed = snap(c, w)
    assert changed["decision"]["recommendation"] == "HOLD"
    assert (
        changed["journey"]["status"] == "NEEDS_REVIEW" and changed["journey"]["operation"] is None
    )


def test_edited_out_of_range_reading_cannot_be_narrated_as_passing(system):
    _, c, *_ = system
    w = new_story(c)
    for expected in EXPECTED:
        s = snap(c, w)
        assert s["journey"]["id"] == expected
        if expected == "measure_valid":
            command(c, w, "measure", {**s["journey"]["payload"], "value": "1.50"})
            break
        advance_story(c, w)
    s = snap(c, w)
    assert s["decision"]["recommendation"] == "REJECT"
    assert s["journey"]["status"] == "NEEDS_REVIEW"
    assert s["journey"]["operation"] is None
    assert "readings" in s["journey"]["title"]
    assert not any(x["study_id"] in s["decision"]["study_ids"] for x in find(s, "functional"))
