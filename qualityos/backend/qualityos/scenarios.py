"""Public synthetic observations only; no hidden outcome model imported by policy."""
from __future__ import annotations

from copy import deepcopy


START = "2026-01-15T08:00:00+00:00"
PAST = "2026-01-14T07:00:00+00:00"


def seed_records(prefix: str = "") -> dict:
    records = {}

    def add(name, kind, **data):
        value = {
            "id": prefix + name,
            "kind": kind,
            "provenance": "SYNTHETIC",
            "available_at": START,
            **data,
        }
        records[value["id"]] = value
        return value["id"]

    policy = add(
        "protocol-v1",
        "policy",
        label="PackPair · protocol 1.0",
        revision=1,
        minimum_specimens=3,
        torque_low="0.90",
        torque_high="1.10",
        dwell_hours=24,
        note="Illustrative engineering bounds and sample counts; not industrial qualification limits",
    )
    product = add(
        "lotion-100",
        "product",
        label="Aurelia · Daily Lotion",
        quantity="100",
        unit="g",
        revision=1,
    )
    bottle = add(
        "bottle-b01",
        "lot",
        label="B01 · Original bottle batch",
        component="BOTTLE",
        supplier="Fictional Meridian Packaging",
        specification="28/410 demo family",
        composition="Unknown; no PCR claim",
    )
    closure = add(
        "closure-c01",
        "lot",
        label="C01 · Original cap batch",
        component="CLOSURE",
        supplier="Fictional Linden Components",
        specification="28/410 demo family",
        composition="Unknown",
    )
    add(
        "closure-c02",
        "lot",
        label="C02 · Untested cap batch",
        component="CLOSURE",
        supplier="Fictional Cedar Closures",
        specification="28/410 demo family",
        composition="Unknown; no material-inferiority inference",
    )
    covered = add(
        "closure-c03",
        "lot",
        label="C03 · Cap batch covered by earlier tests",
        component="CLOSURE",
        supplier="Fictional Linden Components",
        specification="28/410 demo family",
        composition="Unknown",
    )
    config = add(
        "capper-v1",
        "config",
        label="Machine setup v1 · Original",
        revision=1,
        torque_setting="1.00",
        unit="N_m",
    )
    add(
        "capper-v2",
        "config",
        label="Machine setup v2 · Alternate",
        revision=2,
        torque_setting="1.04",
        unit="N_m",
    )
    instrument = add(
        "torque-01",
        "instrument",
        label="Torque reference T-01",
        unit="N_m",
        resolution="0.01",
        active=True,
    )
    add(
        "torque-02",
        "instrument",
        label="Torque reference T-02",
        unit="N_m",
        resolution="0.01",
        active=True,
    )
    calibration = add(
        "calibration-01",
        "calibration",
        label="T-01 · reference certificate",
        instrument_id=instrument,
        valid_from="2025-12-01T00:00:00+00:00",
        valid_until="2026-02-01T00:00:00+00:00",
        method_id="synthetic-reference-v1",
        basis="Assumed valid reference for software demonstration",
    )
    add(
        "calibration-02-old",
        "calibration",
        label="T-02 · Expired reference (ineligible for new readings)",
        instrument_id=prefix + "torque-02",
        valid_from="2025-01-01T00:00:00+00:00",
        valid_until="2026-01-01T00:00:00+00:00",
        method_id="synthetic-reference-v1",
        basis="Deliberately invalid at the new measurement time",
    )
    for n, label in [(1, "L01 · Packaging line"), (2, "L02 · Independent control")]:
        run_bottle = (
            bottle
            if n == 1
            else add(
                "bottle-b02",
                "lot",
                label="B02 · Independent bottle lot",
                component="BOTTLE",
                supplier="Fictional Meridian Packaging",
                specification="28/410 demo family",
                composition="Unknown",
            )
        )
        run_instrument = (
            instrument
            if n == 1
            else add(
                "torque-control",
                "instrument",
                label="Independent control reference",
                unit="N_m",
                resolution="0.01",
                active=True,
            )
        )
        run_calibration = (
            calibration
            if n == 1
            else add(
                "calibration-control",
                "calibration",
                label="Control reference certificate",
                instrument_id=run_instrument,
                valid_from="2025-12-01T00:00:00+00:00",
                valid_until="2026-02-01T00:00:00+00:00",
                method_id="synthetic-reference-v1",
                basis="Independent assumed reference for control run",
            )
        )
        source = add(
            f"source-{n}",
            "source",
            label=f"Line {n} · evidence source",
            complete=True,
            last_seen_at=START,
            sequence=1,
            ttl_seconds=3600,
        )
        run = add(
            f"run-{n}",
            "run",
            label=f"AUR-{14+n:03}",
            line=label,
            product_id=product,
            bottle_lot_id=run_bottle,
            closure_lot_id=closure,
            config_id=config,
            policy_id=policy,
            source_id=source,
            lineage="COMPLETE",
            context_revision=1,
            state="READY_FOR_QA",
            target_units=20,
        )
        scope = {
            k: records[run][k]
            for k in ["product_id", "bottle_lot_id", "closure_lot_id", "config_id", "policy_id"]
        }
        study = add(
            f"study-initial-{n}",
            "study",
            label=f"Earlier example tests · run {n}",
            run_id=run,
            scope=scope,
            approved_envelope={"closure_lot_id": [covered]},
            approved_joint_scopes=[{**scope, "closure_lot_id": covered}],
            envelope_approval={"approved_by": "FICTIONAL_QUALIFICATION_OWNER", "basis": "Declared synthetic C03 alternative; all other dimensions fixed", "approved_at": PAST},
            condition_start=PAST,
            created_at=PAST,
        )
        for sample in range(1, 4):
            specimen = add(
                f"specimen-initial-{n}-{sample}",
                "specimen",
                study_id=study,
                label=f"Independent synthetic specimen {sample}",
                fresh_or_reused="FRESH",
                preparation_group=f"initial-{n}",
            )
            add(
                f"torque-initial-{n}-{sample}",
                "measurement",
                label=f"Torque · specimen {sample}",
                study_id=study,
                sample_id=specimen,
                endpoint="application_torque",
                value="1.00",
                unit="N_m",
                instrument_id=run_instrument,
                calibration_id=run_calibration,
                uncertainty={
                    "kind": "ENGINEERING_BOUND",
                    "half_width": "0.02",
                    "unit": "N_m",
                    "basis": "Assumed bounded error; software scenario only",
                },
                occurred_at=PAST,
                method_id="synthetic-torque-v1",
                raw_quality_flags=[],
            )
            add(
                f"leak-initial-{n}-{sample}",
                "functional",
                label=f"Leak integrity · specimen {sample}",
                study_id=study,
                sample_id=specimen,
                endpoint="leak_integrity",
                outcome="PASS",
                method_id="synthetic-leak-v1",
                condition_start=PAST,
                condition_end="2026-01-15T07:00:00+00:00",
                occurred_at="2026-01-15T07:00:00+00:00",
            )
    return deepcopy(records)
