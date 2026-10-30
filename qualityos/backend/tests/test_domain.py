import json
from copy import deepcopy
from pathlib import Path

import pytest
from hypothesis import given, strategies as st

from qualityos.domain import evaluate, number, reliability
from qualityos.scenarios import START, seed_records


def case_records(change):
    r = seed_records()
    run = r["run-1"]
    if change == "outside_lot":
        run["closure_lot_id"] = "closure-c02"
    if change == "covered_lot":
        run["closure_lot_id"] = "closure-c03"
    if change == "new_config":
        run["config_id"] = "capper-v2"
    if change == "invalid_calibration":
        r["calibration-01"]["valid_until"] = "2026-01-01T00:00:00Z"
    if change == "expired_now_valid_then":
        r["calibration-01"]["valid_until"] = "2026-01-14T23:59:00Z"
    if change == "retroactive_revocation":
        r["rev"] = {
            "id": "rev",
            "kind": "revocation",
            "calibration_id": "calibration-01",
            "available_at": START,
            "effective_from": "2025-12-01T00:00:00Z",
            "effective_until": START,
        }
    for v in r.values():
        if v.get("kind") == "measurement" and v.get("study_id") == "study-initial-1":
            if change == "missing_uncertainty":
                v["uncertainty"] = None
            if change == "expanded_uncertainty":
                v["uncertainty"]["kind"] = "EXPANDED_UNCERTAINTY"
            if change == "overlap":
                v["value"] = "1.10"
            if change == "outside_interval":
                v["value"] = "1.50"
            if change == "wrong_unit":
                v["unit"] = "g"
            if change == "future_available":
                v["available_at"] = "2026-01-17T00:00:00Z"
        if v.get("kind") == "functional" and v.get("study_id") == "study-initial-1":
            if change == "pending_functional":
                v["available_at"] = "2026-01-17T00:00:00Z"
            if change == "failed_functional":
                v["outcome"] = "FAIL"
    if change == "conflict":
        r["leak-initial-1-1"]["outcome"] = "FAIL"
    if change == "source_gap":
        r["source-1"]["complete"] = False
    if change == "partial_lineage":
        run["lineage"] = "PARTIAL"
    if change == "new_policy":
        run["policy_id"] = "policy-new"
    return r


CASES = json.loads((Path(__file__).parents[2] / "scenarios/expected-v1.json").read_text())["cases"]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_frozen_independent_cases(case):
    records = case_records(case["change"])
    result = evaluate(records["run-1"], records, START)
    assert result["recommendation"] == case["expected"]
    if case["change"] not in [
        "invalid_calibration",
        "expired_now_valid_then",
        "retroactive_revocation",
    ]:
        assert evaluate(records["run-2"], records, START)["recommendation"] == "ACCEPT"


@given(
    st.decimals(min_value="0.93", max_value="1.07", places=3, allow_nan=False, allow_infinity=False)
)
def test_inside_engineering_bounds(value):
    records = seed_records()
    records["torque-initial-1-1"]["value"] = str(value)
    assert evaluate(records["run-1"], records, START)["recommendation"] == "ACCEPT"


@pytest.mark.parametrize(
    "value", ["NaN", "Infinity", "-Infinity", "no", 1.0, "1e99999999", "0.1234567890123456789"]
)
def test_exact_finite_decimal_contract(value):
    with pytest.raises(ValueError):
        number(value)


def test_new_calibration_does_not_repair_old_reading():
    records = case_records("invalid_calibration")
    records["fresh"] = {
        **deepcopy(records["calibration-01"]),
        "id": "fresh",
        "valid_from": START,
        "valid_until": "2026-02-01T00:00:00Z",
    }
    assert reliability(records["torque-initial-1-1"], records, START)["verdict"] == "INVALID"
    assert evaluate(records["run-1"], records, START)["recommendation"] == "HOLD"


@pytest.mark.parametrize(
    "field,value",
    [
        ("sample_id", "missing-specimen"),
        ("sample_id", "specimen-initial-2-1"),
        ("endpoint", "unrelated_endpoint"),
        ("method_id", None),
    ],
)
def test_subject_and_endpoint_identity_cannot_manufacture_proof(field, value):
    records = seed_records()
    for m in records.values():
        if m.get("kind") == "measurement" and m.get("study_id") == "study-initial-1":
            m[field] = value
    assert evaluate(records["run-1"], records, START)["recommendation"] == "HOLD"


def test_functional_dwell_cannot_predate_specimen_observation():
    records = seed_records()
    for m in records.values():
        if m.get("kind") == "measurement" and m.get("study_id") == "study-initial-1":
            m["occurred_at"] = "2026-01-15T06:00:00Z"
    assert evaluate(records["run-1"], records, START)["recommendation"] == "HOLD"


def test_policy_boundary_has_no_scenario_or_oracle_access():
    import ast
    import inspect
    from qualityos import domain

    tree = ast.parse(inspect.getsource(domain))
    imports = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert not any(name and ("scenario" in name or "evaluation" in name) for name in imports)
    records = seed_records()
    before = evaluate(records["run-1"], records, START)
    records["sentinel-hidden-label"] = {
        "kind": "SIMULATOR_TRUTH",
        "defective": True,
        "expected": "REJECT",
    }
    assert evaluate(records["run-1"], records, START) == before


@given(st.uuids())
def test_an_unlisted_lot_identity_never_inherits_a_display_family(value):
    records = seed_records()
    records["run-1"]["closure_lot_id"] = "unqualified-" + str(value)
    assert evaluate(records["run-1"], records, START)["recommendation"] == "HOLD"


@given(st.permutations(list(seed_records())))
def test_record_arrival_iteration_does_not_change_the_policy_outcome(order):
    base = seed_records()
    shuffled = {key: base[key] for key in order}
    assert evaluate(shuffled["run-1"], shuffled, START)["recommendation"] == "ACCEPT"
