"""Pure policy. No persistence, scenario generator or evaluator imports."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def instant(value: str) -> datetime:
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("Timezone information is required")
    return dt.astimezone(timezone.utc)


def number(value: Any) -> Decimal:
    if not isinstance(value, str):
        raise ValueError("Exact quantities must be decimal strings")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Invalid decimal quantity") from exc
    if not result.is_finite():
        raise ValueError("Nonfinite quantities are forbidden")
    if len(result.as_tuple().digits) > 18 or not -12 <= result.as_tuple().exponent <= 12:
        raise ValueError("Engineering quantities require at most 18 digits and exponent -12 to 12")
    return result


def reliability(m: dict, records: dict, now: str) -> dict:
    reasons = []
    cal = records.get(m.get("calibration_id"), {})
    instrument = records.get(m.get("instrument_id"), {})
    if not cal or not instrument:
        return {"verdict": "UNKNOWN", "reasons": ["REFERENCE_MISSING"]}
    if instant(cal.get("available_at", now)) > instant(now):
        return {"verdict": "UNKNOWN", "reasons": ["REFERENCE_NOT_AVAILABLE"]}
    if m.get("unit") != instrument.get("unit"):
        return {"verdict": "INVALID", "reasons": ["UNIT_MISMATCH"]}
    when = instant(m["occurred_at"])
    if cal.get("instrument_id") != m.get("instrument_id"):
        reasons.append("REFERENCE_IDENTITY_MISMATCH")
    if not instant(cal["valid_from"]) <= when <= instant(cal["valid_until"]):
        reasons.append("REFERENCE_OUTSIDE_VALIDITY")
    for rev in records.values():
        if rev.get("kind") == "revocation" and rev.get("calibration_id") == cal["id"]:
            if instant(rev["available_at"]) <= instant(now) and instant(
                rev["effective_from"]
            ) <= when <= instant(rev["effective_until"]):
                reasons.append("REFERENCE_REVOKED")
    if m.get("raw_quality_flags") or not instrument.get("active", True):
        reasons.append("INSTRUMENT_FAULT")
    if reasons:
        return {"verdict": "INVALID", "reasons": reasons}
    uncertainty = m.get("uncertainty") or {}
    if uncertainty.get("kind") != "ENGINEERING_BOUND" or not uncertainty.get("basis"):
        return {"verdict": "UNKNOWN", "reasons": ["UNCERTAINTY_UNSUPPORTED_OR_MISSING"]}
    if uncertainty.get("unit") != m["unit"]:
        return {"verdict": "INVALID", "reasons": ["UNCERTAINTY_UNIT_MISMATCH"]}
    if number(uncertainty["half_width"]) < 0:
        return {"verdict": "INVALID", "reasons": ["NEGATIVE_UNCERTAINTY"]}
    return {"verdict": "VALID", "reasons": ["MEASUREMENT_TIME_REFERENCE_VALID"]}


SCOPE_FIELDS = ("product_id", "bottle_lot_id", "closure_lot_id", "config_id", "policy_id")


def scope_of(run: dict) -> dict:
    return {key: run[key] for key in SCOPE_FIELDS}


def applicable(study: dict, run: dict) -> bool:
    scope = study.get("scope", {})
    envelope = study.get("approved_envelope", {})
    return all(
        scope.get(k) == run.get(k) or run.get(k) in envelope.get(k, []) for k in SCOPE_FIELDS
    )


def evaluate(run: dict, records: dict, now: str) -> dict:
    requirements = []

    def check(code: str, verdict: str, reason: str, refs: list[str], next_action: str):
        requirements.append(
            {
                "type": code,
                "verdict": verdict,
                "reason": reason,
                "evidence_refs": refs,
                "next_action": next_action,
            }
        )

    studies = sorted(
        (
            s
            for s in records.values()
            if s.get("kind") == "study"
            and applicable(s, run)
            and instant(s["available_at"]) <= instant(now)
        ),
        key=lambda s: s["id"],
    )
    check(
        "EXACT_SCOPE_MATCH",
        "SATISFIED" if studies else "UNKNOWN",
        "Applicable qualification scope found"
        if studies
        else "New component or configuration has no applicable qualification",
        [s["id"] for s in studies],
        "Open a scoped qualification study",
    )
    policy = records.get(run["policy_id"], {})
    minimum = policy.get("minimum_specimens", 3)
    low, high = number(policy.get("torque_low", "0.90")), number(policy.get("torque_high", "1.10"))
    study_ids = {s["id"] for s in studies}
    superseded = {
        x.get("supersedes_id")
        for x in records.values()
        if x.get("kind") == "correction" and instant(x["available_at"]) <= instant(now)
    }
    ms = sorted(
        (
            m
            for m in records.values()
            if m.get("kind") == "measurement"
            and m.get("study_id") in study_ids
            and m["id"] not in superseded
            and instant(m["occurred_at"]) <= instant(m["available_at"]) <= instant(now)
        ),
        key=lambda m: m["id"],
    )
    details = []
    valid = []
    unknown_interval = False
    violated = False
    for m in ms:
        rel = reliability(m, records, now)
        specimen = records.get(m.get("sample_id"), {})
        if (
            specimen.get("kind") != "specimen"
            or specimen.get("study_id") != m["study_id"]
            or m.get("endpoint") != "application_torque"
            or not m.get("method_id")
        ):
            rel = {"verdict": "UNKNOWN", "reasons": ["SUBJECT_OR_METHOD_MISMATCH"]}
        item = {**m, "reliability": rel}
        if rel["verdict"] == "VALID" and m["unit"] == "N_m":
            v, u = number(m["value"]), number(m["uncertainty"]["half_width"])
            a, b = v - u, v + u
            item["interval"] = [str(a), str(b)]
            item["conformance"] = (
                "SATISFIED"
                if low <= a <= b <= high
                else "VIOLATED"
                if b < low or a > high
                else "UNKNOWN"
            )
            violated |= item["conformance"] == "VIOLATED"
            unknown_interval |= item["conformance"] == "UNKNOWN"
            valid.append(m)
        details.append(item)
    specimen_ids = {m["sample_id"] for m in valid}
    enough = len(specimen_ids) >= minimum
    invalid_count = sum(d["reliability"]["verdict"] != "VALID" for d in details)
    check(
        "MEASUREMENT_RELIABILITY",
        "SATISFIED" if enough else "UNKNOWN",
        f"{len(specimen_ids)}/{minimum} distinct specimens with valid references; {invalid_count} unusable observations retained",
        [m["id"] for m in valid],
        "Record new observations using a valid reference",
    )
    check(
        "ENDPOINT_CONFORMANCE",
        "VIOLATED" if violated else "UNKNOWN" if unknown_interval or not enough else "SATISFIED",
        "A valid torque interval lies outside the illustrative tolerance"
        if violated
        else "Interval overlaps a limit or eligible proof is incomplete"
        if unknown_interval or not enough
        else "Valid engineering intervals are within 0.90–1.10 N·m",
        [m["id"] for m in valid],
        "Investigate the condition; obtain appropriate new verification",
    )
    fs = [
        f
        for f in records.values()
        if f.get("kind") == "functional"
        and f.get("study_id") in study_ids
        and f["id"] not in superseded
        and instant(f["occurred_at"]) <= instant(f["available_at"]) <= instant(now)
    ]
    # The same identified specimen must have been prepared/observed before its
    # declared dwell starts. Study age alone cannot establish specimen dwell.
    observations = {
        (m["study_id"], m["sample_id"]): m
        for m in ms
        if records.get(m.get("sample_id"), {}).get("study_id") == m["study_id"]
    }
    qualified_tests = [
        f
        for f in fs
        if f.get("endpoint") == "leak_integrity"
        and f.get("method_id")
        and (f["study_id"], f["sample_id"]) in observations
        and instant(observations[(f["study_id"], f["sample_id"])]["occurred_at"])
        <= instant(f["condition_start"])
        and instant(f["condition_end"]) <= instant(f["occurred_at"])
        and (instant(f["condition_end"]) - instant(f["condition_start"])).total_seconds()
        >= policy.get("dwell_hours", 24) * 3600
    ]
    outcomes = {f["outcome"] for f in qualified_tests}
    conflict = "PASS" in outcomes and "FAIL" in outcomes
    passes = {f["sample_id"] for f in qualified_tests if f["outcome"] == "PASS"} & specimen_ids
    fv = (
        "UNKNOWN"
        if conflict
        else "VIOLATED"
        if "FAIL" in outcomes
        else "SATISFIED"
        if len(passes) >= minimum
        else "UNKNOWN"
    )
    check(
        "FUNCTIONAL_ENDPOINT",
        fv,
        "Conflicting functional outcomes require disposition"
        if conflict
        else "Independent delayed functional test failed"
        if fv == "VIOLATED"
        else f"{len(passes)}/{minimum} independent functional passes after the declared dwell",
        [f["id"] for f in qualified_tests],
        "Complete the independent leak test after 24 replay hours",
    )
    source = records.get(run.get("source_id"), {})
    fresh = (
        bool(source.get("complete"))
        and bool(source.get("last_seen_at"))
        and 0
        <= (instant(now) - instant(source["last_seen_at"])).total_seconds()
        <= source.get("ttl_seconds", 3600)
    )
    check(
        "REQUIRED_SOURCE_HEALTH",
        "SATISFIED" if fresh else "UNKNOWN",
        "Required source is complete and fresh"
        if fresh
        else "Required source is stale, incomplete or has a sequence gap",
        [source["id"]] if source else [],
        "Confirm the source watermark and refresh its health",
    )
    complete = run.get("lineage", "UNKNOWN") == "COMPLETE"
    check(
        "IDENTITY_COMPLETENESS",
        "SATISFIED" if complete else "UNKNOWN",
        "Exact material and run identity is complete"
        if complete
        else "Genealogy is incomplete; conservative impact scope required",
        [run["id"]],
        "Reconcile the missing material identities",
    )
    verdicts = {r["verdict"] for r in requirements}
    recommendation = (
        "REJECT" if "VIOLATED" in verdicts else "HOLD" if "UNKNOWN" in verdicts else "ACCEPT"
    )
    support = sorted({i for r in requirements for i in r["evidence_refs"]})
    # Fingerprints bind the qualifying scope and policy, not unrelated audit counters.
    fingerprint = digest({"scope": scope_of(run), "policy": policy})
    return {
        "run_id": run["id"],
        "recommendation": recommendation,
        "requirements": requirements,
        "measurements": details,
        "study_ids": sorted(study_ids),
        "evidence_refs": support,
        "applicability_fingerprint": fingerprint,
        "evaluated_at": now,
        "scope": scope_of(run),
        "provenance": "SYNTHETIC",
        "time_basis": "SCENARIO_UTC",
    }
