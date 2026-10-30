"""Independent declared corpus and reference. Policy imports none of this module."""
from __future__ import annotations

import json
import statistics
import time
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

from sqlalchemy import text

from .domain import canonical, digest, evaluate
from .scenarios import START, seed_records
from .security import utcnow


CORPUS = Path(__file__).parents[2] / "scenarios/expected-v1.json"


def inputs(change):
    records = seed_records()
    run = records["run-1"]
    updates = {
        "outside_lot": ("closure_lot_id", "closure-c02"),
        "covered_lot": ("closure_lot_id", "closure-c03"),
        "new_config": ("config_id", "capper-v2"),
        "partial_lineage": ("lineage", "PARTIAL"),
        "new_policy": ("policy_id", "policy-new"),
    }
    if change in updates:
        key, value = updates[change]
        run[key] = value
    if change == "invalid_calibration":
        records["calibration-01"]["valid_until"] = "2026-01-01T00:00:00Z"
    if change == "expired_now_valid_then":
        records["calibration-01"]["valid_until"] = "2026-01-14T23:59:00Z"
    if change == "retroactive_revocation":
        records["rev"] = {
            "id": "rev",
            "kind": "revocation",
            "calibration_id": "calibration-01",
            "available_at": START,
            "effective_from": "2025-12-01T00:00:00Z",
            "effective_until": START,
        }
    for item in records.values():
        if item.get("study_id") != "study-initial-1":
            continue
        if item["kind"] == "measurement":
            if change == "missing_uncertainty":
                item["uncertainty"] = None
            if change == "expanded_uncertainty":
                item["uncertainty"]["kind"] = "EXPANDED_UNCERTAINTY"
            if change == "overlap":
                item["value"] = "1.10"
            if change == "outside_interval":
                item["value"] = "1.50"
            if change == "wrong_unit":
                item["unit"] = "g"
            if change == "future_available":
                item["available_at"] = "2026-01-17T00:00:00Z"
        if item["kind"] == "functional":
            if change == "pending_functional":
                item["available_at"] = "2026-01-17T00:00:00Z"
            if change == "failed_functional":
                item["outcome"] = "FAIL"
    if change == "conflict":
        records["leak-initial-1-1"]["outcome"] = "FAIL"
    if change == "source_gap":
        records["source-1"]["complete"] = False
    return records


def reference(records):
    """Small independently written checklist; separate from production helpers."""
    from datetime import datetime
    from decimal import Decimal

    def dt(s):
        return datetime.fromisoformat(s.replace("Z", "+00:00"))

    run = records["run-1"]
    now = dt(START)
    fields = ["product_id", "bottle_lot_id", "closure_lot_id", "config_id", "policy_id"]
    studies = {
        x["id"]
        for x in records.values()
        if x["kind"] == "study"
        and all(
            x["scope"].get(k) == run[k] or run[k] in x.get("approved_envelope", {}).get(k, [])
            for k in fields
        )
    }
    source = records[run["source_id"]]
    incomplete = not studies or not source["complete"] or run["lineage"] != "COMPLETE"
    count = 0
    fail = False
    values = set()
    pass_samples = set()
    for row in records.values():
        if (
            row.get("study_id") not in studies
            or row["kind"] not in {"measurement", "functional"}
            or dt(row["available_at"]) > now
        ):
            continue
        if row["kind"] == "measurement":
            c = records[row["calibration_id"]]
            u = row.get("uncertainty") or {}
            usable = (
                row["unit"] == "N_m"
                and dt(c["valid_from"]) <= dt(row["occurred_at"]) <= dt(c["valid_until"])
                and u.get("kind") == "ENGINEERING_BOUND"
            )
            usable = usable and not any(
                v["kind"] == "revocation"
                and v["calibration_id"] == c["id"]
                and dt(v["effective_from"]) <= dt(row["occurred_at"]) <= dt(v["effective_until"])
                for v in records.values()
            )
            if usable:
                count += 1
                a, b = Decimal(row["value"]) - Decimal(u["half_width"]), Decimal(
                    row["value"]
                ) + Decimal(u["half_width"])
                fail |= b < Decimal("0.90") or a > Decimal("1.10")
                incomplete |= not (Decimal("0.90") <= a <= b <= Decimal("1.10")) and not fail
        else:
            values.add(row["outcome"])
            if row["outcome"] == "PASS":
                pass_samples.add(row["sample_id"])
    conflict = "PASS" in values and "FAIL" in values
    if fail or ("FAIL" in values and not conflict):
        return "REJECT"
    return "HOLD" if incomplete or count < 3 or len(pass_samples) < 3 or conflict else "ACCEPT"


def run_evaluation(store=None):
    cases = json.loads(CORPUS.read_text())["cases"]
    results = []
    latencies = []
    for case in cases:
        records = inputs(case["change"])
        begin = time.perf_counter()
        actual = evaluate(records["run-1"], records, START)["recommendation"]
        latencies.append((time.perf_counter() - begin) * 1000)
        checklist = reference(records)
        results.append(
            {
                **case,
                "actual": actual,
                "reference": checklist,
                "matched": actual == case["expected"] and checklist == case["expected"],
                "version_unaware": "ACCEPT",
                "blanket_hold": "HOLD",
            }
        )
    report = {
        "id": "evaluation-" + uuid4().hex,
        "status": "COMPLETED",
        "provenance": "SYNTHETIC",
        "corpus_version": "qualityos-independent-v1",
        "corpus_sha256": digest(json.loads(CORPUS.read_text())),
        "created_at": utcnow(),
        "total": len(results),
        "passed": sum(x["matched"] for x in results),
        "cases": results,
        "policies": [
            {"name": "QualityOS", "matches": sum(x["actual"] == x["expected"] for x in results)},
            {
                "name": "Competent SOP / evidence-aware reference",
                "matches": sum(x["reference"] == x["expected"] for x in results),
            },
            {
                "name": "Version-unaware example",
                "matches": sum(x["version_unaware"] == x["expected"] for x in results),
            },
            {
                "name": "Blanket hold",
                "matches": sum(x["blanket_hold"] == x["expected"] for x in results),
            },
        ],
        "latency_ms": {
            "p50": round(statistics.median(latencies), 3),
            "p95": round(sorted(latencies)[int(0.95 * (len(latencies) - 1))], 3),
            "basis": "Pure policy calls on the 20-case corpus; not the separate 10k-event API benchmark",
        },
        "limits": [
            "Declared software cases, not independent manufacturing trials",
            "Parity with competent evidence-aware practice is expected and retained",
            "No commercial MES installation was benchmarked",
            "No physical defects prevented, factory savings or human-time benefit measured",
        ],
    }
    if store:
        with store.transaction() as c:
            c.execute(
                text("INSERT INTO reports VALUES (:id,:p,:at)"),
                {"id": report["id"], "p": canonical(report), "at": report["created_at"]},
            )
    return report
