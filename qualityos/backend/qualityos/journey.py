"""Explain saved demo facts. This module never authorizes or changes a run."""
from math import ceil

from .domain import instant, reliability, scope_of


CHAPTERS = [
    "Before the change",
    "A new delivery",
    "A number is not proof",
    "Test a better condition",
    "Earn permission again",
]
ORDER = [
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


def describe_journey(run, records, decision, now, impact, historical=False):
    guide = next((x for x in records.values() if x["kind"] == "guide"), None)
    if not guide:
        return None
    base = {
        "version": "packaging-story-v1",
        "run_id": guide["run_id"],
        "chapters": CHAPTERS,
        "provenance": "SYNTHETIC",
        "total_steps": len(ORDER) - 1,
        "control_run_id": next(
            (
                x["id"]
                for x in records.values()
                if x["kind"] == "run" and x["id"] != guide["run_id"]
            ),
            None,
        ),
    }

    def stage(
        key,
        chapter,
        title,
        story,
        why,
        label,
        page="line",
        operation=None,
        payload=None,
        preview=None,
        expected="",
        status="ACTIVE",
    ):
        return {
            **base,
            "id": key,
            "chapter": chapter,
            "step_index": ORDER.index(key) if key in ORDER else None,
            "title": title,
            "story": story,
            "why": why,
            "action_label": label,
            "page": page,
            "operation": operation,
            "payload": payload or {},
            "preview": preview or [],
            "expected": expected,
            "status": status,
            "reason": "Guided synthetic scenario: "
            + title
            + ". Review applies only to the displayed demonstration scope.",
        }

    if historical:
        return stage(
            "history",
            0,
            "You are looking at an earlier decision.",
            "This is what the team knew at that moment. Later discoveries have not been written into this record.",
            "Return to the present before recording an action. History is evidence, not a current permission.",
            "Return to the present",
            "evidence",
            status="HISTORICAL",
        )
    if run["id"] != guide["run_id"]:
        return stage(
            "control",
            1,
            "This is the comparison line.",
            "The story takes place on AUR-015. This separate run helps you inspect whether a change was kept within its affected scope.",
            "Independent work should only pause when its own evidence or source requires it.",
            "Return to the story",
            status="CONTROL",
        )

    def rows(kind):
        return [x for x in records.values() if x["kind"] == kind]

    def latest(items):
        return max(
            items,
            key=lambda x: (x.get("recorded_revision", 0), x.get("created_at", ""), x["id"]),
            default=None,
        )

    rid = run["id"]
    run_payload = {"run_id": rid}
    review = {
        **run_payload,
        "decision_id": decision["id"],
        "fingerprint": decision["applicability_fingerprint"],
    }
    holds = [x for x in rows("hold") if x["run_id"] == rid and x["status"] == "ACTIVE"]
    permits = [
        x
        for x in rows("permit")
        if x["run_id"] == rid
        and x["status"] == "ACTIVE"
        and x["used_units"] < x["max_units"]
        and instant(now) < instant(x["expires_at"])
    ]
    units = [x for x in rows("unit") if x["run_id"] == rid]
    baseline = [x for x in units if x["scope"] == guide["initial_scope"]]
    fresh_units = [
        x
        for x in units
        if x["scope"]["closure_lot_id"] == guide["replacement_closure_id"]
        and x["scope"]["config_id"] == guide["alternate_config_id"]
    ]
    source_ok = next(
        q["verdict"] == "SATISFIED"
        for q in decision["requirements"]
        if q["type"] == "REQUIRED_SOURCE_HEALTH"
    )
    is_new = run["config_id"] == guide["alternate_config_id"]
    chapter = 4 if is_new else 2

    def interrupted(title, detail):
        return stage(
            "different_path",
            chapter,
            title,
            detail,
            "The guide follows your saved evidence. It will not invent a passing result or overwrite a choice to keep the story moving.",
            "Inspect the current evidence",
            "qualification",
            status="NEEDS_REVIEW",
        )

    if fresh_units and impact["units"]:
        return stage(
            "late_discovery",
            4,
            "New information changes what we can trust.",
            f"Current reassessment lists {len(impact['units'])} potentially affected simulated units. Their original records and earlier decisions still exist.",
            "Potentially affected is not the same as defective. Follow the actual evidence dependencies and let QA determine handling.",
            "Inspect the affected units",
            "investigation",
            status="LATE_DISCOVERY",
        )

    if scope_of(run) == guide["initial_scope"]:
        chapter = 0
        if run["state"] == "COMPLETED":
            return interrupted(
                "This run has already been completed.",
                "That recorded choice is preserved. Inspect its history or start a separate story instead of reopening completed work.",
            )
        if not source_ok:
            return stage(
                "source_recovery",
                0,
                "The starting records need a current source check.",
                "The required source is stale or incomplete, so the original condition is not ready for a new permission.",
                "Confirm complete current synthetic records before relying on the starting tests.",
                "Confirm current records",
                "qualification",
                "refresh_source",
                {**run_payload, "complete": True},
            )
        if decision["recommendation"] != "ACCEPT":
            reason = next(
                q["reason"] for q in decision["requirements"] if q["verdict"] != "SATISFIED"
            )
            return interrupted(
                "The starting evidence needs review.",
                reason
                + ". The guide cannot describe this condition as ready or offer a quality permission.",
            )
        if len(baseline) < 2:
            candidate = (
                stage(
                    "produce_initial",
                    0,
                    "The original combination has permission.",
                    "The bottle, cap and machine setup match the earlier tests. QA has granted a limited permission for this simulation.",
                    "Make two demonstration units so there is a real saved baseline to compare with the later change.",
                    "Make the first two units",
                    operation="produce",
                    payload={**run_payload, "units": 2 - len(baseline)},
                    preview=[
                        {
                            "label": "Demonstration output",
                            "value": f"{2 - len(baseline)} simulated units",
                        }
                    ],
                    expected="Saved unit records will appear. Nothing operates a physical line.",
                )
                if permits
                else stage(
                    "authorize_initial",
                    0,
                    "A lotion line is ready to begin.",
                    "Aurelia's 100 g lotion uses bottle B01 and cap C01. Earlier tests cover this exact combination and machine setup.",
                    "Passing evidence means ready for review. A quality reviewer still needs to give a bounded permission before any simulated units are made.",
                    "Review the starting permission",
                    operation="authorize",
                    payload={**review, "max_units": 20, "minutes": 15},
                    preview=[
                        {"label": "Evidence", "value": "Earlier tests match B01 + C01 + setup v1"},
                        {
                            "label": "Permission limit",
                            "value": "20 simulated units · 15 replay minutes",
                        },
                    ],
                    expected="The run becomes authorized; no units are created yet.",
                )
            )
        else:
            return stage(
                "change_caps",
                1,
                "A replacement delivery of caps arrives.",
                "The line has made its first two demonstration units. The next delivery is cap lot C02: the same general family, but a different identified batch.",
                "Would tests on C01 justify continuing with C02? Change the assignment and watch QualityOS reassess that question.",
                "Introduce the new cap delivery",
                operation="change_context",
                payload={
                    **run_payload,
                    "field": "closure_lot_id",
                    "value": guide["replacement_closure_id"],
                },
                preview=[
                    {"label": "Change", "value": "C01 → C02"},
                    {"label": "Stays the same", "value": "Bottle B01 and machine setup v1"},
                ],
                expected="Only the affected run loses its applicable qualification and pauses.",
            )
    elif run["closure_lot_id"] != guide["replacement_closure_id"] or run["config_id"] not in {
        guide["initial_scope"]["config_id"],
        guide["alternate_config_id"],
    }:
        return interrupted(
            "Your workspace has taken a different path.",
            "The guided scenario uses cap C02 and machine setups v1/v2. Your manual changes are saved; inspect their actual evidence or start a separate guided story.",
        )
    else:
        first_study = latest(
            [
                x
                for x in rows("study")
                if x.get("run_id") == rid
                and x["scope"]["closure_lot_id"] == guide["replacement_closure_id"]
                and x["scope"]["config_id"] == guide["initial_scope"]["config_id"]
                and not x.get("action_id")
            ]
        )
        fresh_cal = latest(
            [
                x
                for x in rows("calibration")
                if x["instrument_id"] == guide["teaching_instrument_id"]
                and x["id"] != guide["expired_reference_id"]
                and instant(x["valid_from"]) <= instant(now) <= instant(x["valid_until"])
                and not any(
                    v["calibration_id"] == x["id"]
                    and instant(v["effective_from"])
                    <= instant(now)
                    <= instant(v["effective_until"])
                    for v in rows("revocation")
                )
            ]
        )

        def measurement(study, calibration):
            return {
                "study_id": study["id"],
                "calibration_id": calibration,
                "value": "1.00",
                "unit": "N_m",
                "half_width": "0.02",
                "count": 3,
                "uncertainty_kind": "ENGINEERING_BOUND",
                "basis": "Assumed engineering bound for the explicitly synthetic guided scenario",
            }

        def dwell_or_result(study, fresh):
            ms = [x for x in rows("measurement") if x["study_id"] == study["id"]]
            latest_observation = max(instant(x["occurred_at"]) for x in ms)
            remaining = 24 - (instant(now) - latest_observation).total_seconds() / 3600
            if remaining > 0:
                return stage(
                    "wait_fresh" if fresh else "wait_first",
                    4 if fresh else 2,
                    "A tight cap is not yet a leak test.",
                    "The new readings describe application torque: the twisting effort used to apply the cap. Leak integrity is a separate endpoint with a declared 24-hour dwell.",
                    "Move the fictional clock forward. This demonstrates waiting for evidence; it does not physically perform a test in seconds.",
                    "Advance the story by 24 hours",
                    "qualification",
                    "advance",
                    {"hours": min(48, max(1, ceil(remaining)))},
                    [{"label": "Time being changed", "value": "Synthetic replay time only"}],
                    "Independent testing can be recorded after every specimen has completed its dwell.",
                )
            if not source_ok:
                return stage(
                    "source_fresh" if fresh else "source_first",
                    4 if fresh else 2,
                    "The wait is over. Confirm the records are current.",
                    "Advancing the clock did not manufacture a heartbeat from the line's evidence source. Its status is now stale.",
                    "For this demonstration, explicitly confirm a complete current source before relying on the arriving test result.",
                    "Confirm the demonstration records are current",
                    "qualification",
                    "refresh_source",
                    {**run_payload, "complete": True},
                    expected="Source freshness is restored. This does not itself prove package integrity.",
                )
            outcome = "PASS" if fresh else "FAIL"
            return stage(
                "pass_fresh" if fresh else "fail_first",
                4 if fresh else 2,
                "The new independent test is ready."
                if fresh
                else "The independent test brings a different answer.",
                "The supplied fictional leak-test observation is PASS for these fresh specimens."
                if fresh
                else "The supplied fictional leak-test observation is FAIL, even though the trustworthy torque readings are in range.",
                "This outcome is explicitly supplied scenario evidence. QualityOS does not infer it from torque or predict seal physics.",
                "Record the supplied passing result"
                if fresh
                else "Record the supplied failing result",
                "qualification",
                "functional",
                {"study_id": study["id"], "outcome": outcome},
                [{"label": "Supplied synthetic endpoint", "value": "Leak integrity · " + outcome}],
                "Evidence can be reviewed, but the hold and QA permission remain separate."
                if fresh
                else "The proposed condition is rejected; simulated production stays blocked.",
            )

        if not is_new:
            if not first_study:
                return stage(
                    "open_first",
                    1,
                    "The old tests no longer answer today's question.",
                    "C02 is outside the earlier qualification. This does not prove the new caps are bad; it means the existing proof does not cover them.",
                    "Open a test study tied to the actual bottle, new cap and current machine setup. Keep the pause scoped to this run.",
                    "Start a study for the new combination",
                    "qualification",
                    "open_study",
                    run_payload,
                    expected="There is now a place to collect new evidence. Opening a study does not qualify the package.",
                )
            ms = [x for x in rows("measurement") if x["study_id"] == first_study["id"]]
            if not ms:
                return stage(
                    "measure_old",
                    2,
                    "The reading looks reassuring. Can you trust it?",
                    "The next supplied observation is 1.00 N·m, within the illustrative torque range. It comes from T-02 using its old reference record.",
                    "Record the observation and let the system check both the number and whether its instrument reference was valid when measured.",
                    "Record the first torque readings",
                    "qualification",
                    "measure",
                    measurement(first_study, guide["expired_reference_id"]),
                    [
                        {
                            "label": "Supplied readings",
                            "value": "Three fresh synthetic specimens · 1.00 N·m",
                        },
                        {"label": "Reference", "value": "T-02 · old certificate"},
                    ],
                    "The numeric reading is retained, even if its reliability is invalid.",
                )
            valid_ms = [x for x in ms if reliability(x, records, now)["verdict"] == "VALID"]
            if len({x["sample_id"] for x in valid_ms}) < 3:
                if not fresh_cal:
                    return stage(
                        "new_reference",
                        2,
                        "A passing number came from an expired reference.",
                        "Those observations cannot count as trustworthy proof. Their old reference was invalid at measurement time.",
                        "Record a new assumed reference for T-02. It starts now and cannot repair the old readings; new observations must follow.",
                        "Establish a new instrument reference",
                        "qualification",
                        "calibrate",
                        {
                            "instrument_id": guide["teaching_instrument_id"],
                            "method_id": "synthetic-reference-v1",
                            "basis": "Assumed new reference for the fictional guided experiment; no physical calibration claimed",
                        },
                        expected="The old readings remain invalid. A new reference becomes available for new readings.",
                    )
                return stage(
                    "measure_valid",
                    2,
                    "Now collect new, trustworthy observations.",
                    "A new reference exists for T-02. The earlier invalid observations are still in the history.",
                    "Use fresh synthetic specimens and this new reference. Even valid torque will not replace the independent leak test.",
                    "Repeat the torque check with the new reference",
                    "qualification",
                    "measure",
                    measurement(first_study, fresh_cal["id"]),
                    [
                        {"label": "Reference", "value": "New T-02 reference"},
                        {
                            "label": "New observations",
                            "value": "Three distinct synthetic specimens · 1.00 N·m",
                        },
                    ],
                    "Measurement reliability can pass while functional evidence is still missing.",
                )
            torque = next(
                q for q in decision["requirements"] if q["type"] == "ENDPOINT_CONFORMANCE"
            )
            if torque["verdict"] != "SATISFIED":
                return interrupted(
                    "These readings do not establish torque conformance.",
                    torque["reason"]
                    + ". Review the actual observations before following the supplied experiment further.",
                )
            fs = [x for x in rows("functional") if x["study_id"] == first_study["id"]]
            if not fs:
                return dwell_or_result(first_study, False)
            if {x["outcome"] for x in fs} != {"FAIL"}:
                return interrupted(
                    "Your first test took a different path.",
                    "The recorded independent result differs from the supplied failing observation. The guide will not turn your result into a failure or claim a corrective action is necessary. Review the evidence or start a separate story.",
                )
            incident = latest([x for x in rows("investigation") if x["run_id"] == rid])
            if not incident:
                return stage(
                    "investigate",
                    3,
                    "A real question to investigate, not a supplier to blame.",
                    "In this scenario, the C02/setup-v1 condition failed its independent test. The cap delivery alone does not establish the cause.",
                    "Retain the failure and open an investigation with competing material, application and measurement explanations.",
                    "Open the packaging investigation",
                    "investigation",
                    "investigate",
                    {
                        **run_payload,
                        "title": "Why did the new combination fail its leak test?",
                        "problem_definition": "Supplied synthetic leak results failed for B01/C02/setup-v1 despite valid in-range application torque. Compare material, application and measurement explanations without declaring a confirmed cause.",
                    },
                )
            hypotheses = [x for x in rows("hypothesis") if x["investigation_id"] == incident["id"]]
            if not hypotheses:
                return stage(
                    "hypothesis",
                    3,
                    "Make an explanation testable.",
                    "One possible explanation is an interaction between this package pair and its application conditions. Other explanations remain possible.",
                    "Link the failed leak observations and the in-range torque evidence, then test a bounded alternative rather than declaring causation.",
                    "Record a working explanation",
                    "investigation",
                    "hypothesis",
                    {
                        "investigation_id": incident["id"],
                        "statement": "Package/application interaction may explain the failed leak endpoint",
                        "mechanism": "Compare a bounded alternate application configuration while retaining material and measurement explanations; association is not proven causation.",
                        "supporting_ids": [x["id"] for x in fs][:3],
                        "refuting_ids": [x["id"] for x in valid_ms][:3],
                    },
                )
            action = latest(
                [
                    x
                    for x in rows("action")
                    if x["investigation_id"] == incident["id"]
                    and x["config_id"] == guide["alternate_config_id"]
                ]
            )
            if not action:
                return stage(
                    "propose",
                    3,
                    "Change one condition, then test it again.",
                    "The proposed next experiment uses machine setup v2 with the same identified bottle and cap lots.",
                    "An action plan must say how fresh observations and a new independent test will verify the new condition. A changed setting is not proof of improvement.",
                    "Propose the alternate setup",
                    "investigation",
                    "propose_action",
                    {
                        "investigation_id": incident["id"],
                        "config_id": guide["alternate_config_id"],
                        "verification_plan": "Fresh identified specimens with a valid torque reference plus an independent leak observation after the full 24-hour dwell. No physical efficacy or universal cause claim.",
                    },
                )
            if action["status"] == "PROPOSED":
                return stage(
                    "approve",
                    3,
                    "The proposed experiment needs a quality review.",
                    "The alternate setup and verification plan are recorded. The line has not changed yet.",
                    "A quality engineer approves the proposed action before an operator can record its execution.",
                    "Review and approve the action",
                    "investigation",
                    "approve_action",
                    {"action_id": action["id"]},
                )
            return stage(
                "execute",
                3,
                "Apply the approved change in the simulation.",
                "QA approved the bounded experiment. Record its execution so subsequent evidence can be tied to setup v2.",
                "Approval, execution and proof that an action worked are different records.",
                "Record the move to setup v2",
                "investigation",
                "execute_action",
                {"action_id": action["id"]},
                expected="The run moves to setup v2. Old-scope proof still cannot qualify the new condition.",
            )

        action = latest(
            [
                x
                for x in rows("action")
                if x["run_id"] == rid
                and x["config_id"] == guide["alternate_config_id"]
                and x["status"] in {"EXECUTED", "VERIFYING", "VERIFIED"}
            ]
        )
        if not action:
            return interrupted(
                "A setup change is not an approved action record.",
                "The current setup is v2, but no matching executed action is recorded. Review the investigation instead of claiming the action was verified.",
            )
        study = latest([x for x in rows("study") if x.get("action_id") == action["id"]])
        if not study:
            return stage(
                "open_fresh",
                4,
                "The new setup must earn its own evidence.",
                "The failed v1 results remain in the history. A new study must follow the executed action and match the current v2 condition.",
                "Reusing earlier observations would not tell us whether the changed condition works.",
                "Start fresh verification",
                "qualification",
                "open_study",
                {**run_payload, "action_id": action["id"]},
            )
        ms = [
            x
            for x in rows("measurement")
            if x["study_id"] == study["id"] and reliability(x, records, now)["verdict"] == "VALID"
        ]
        if len({x["sample_id"] for x in ms}) < 3:
            if not fresh_cal:
                return interrupted(
                    "Fresh verification needs a usable reference.",
                    "No current T-02 reference is available for the new observations. Establish a reference in Qualification before continuing.",
                )
            return stage(
                "measure_fresh",
                4,
                "New condition. New specimens. New observations.",
                "Collect three fresh synthetic torque observations under setup v2 using the valid reference.",
                "These records belong to the new study; they cannot erase the failed earlier condition.",
                "Record the fresh torque observations",
                "qualification",
                "measure",
                measurement(study, fresh_cal["id"]),
                [
                    {"label": "Current condition", "value": "B01 + C02 + setup v2"},
                    {
                        "label": "Supplied observations",
                        "value": "Three fresh synthetic specimens · 1.00 N·m",
                    },
                ],
            )
        torque = next(q for q in decision["requirements"] if q["type"] == "ENDPOINT_CONFORMANCE")
        if torque["verdict"] != "SATISFIED":
            return interrupted(
                "The fresh readings still need review.",
                torque["reason"]
                + ". New observations do not automatically make the new condition acceptable.",
            )
        fs = [x for x in rows("functional") if x["study_id"] == study["id"]]
        if not fs:
            return dwell_or_result(study, True)
        if not source_ok:
            return stage(
                "source_recovery",
                4,
                "The test is recorded, but the source needs a fresh check.",
                "The required evidence source is stale or incomplete. Keep the result and confirm the source separately.",
                "A recorded passing result cannot silently fill a source-health gap.",
                "Confirm current records",
                "qualification",
                "refresh_source",
                {**run_payload, "complete": True},
            )
        if decision["recommendation"] != "ACCEPT":
            return interrupted(
                "The new evidence has not cleared the gate.",
                "A failure, conflict or missing prerequisite still blocks this condition. A convenient later result cannot silently erase it.",
            )
        if action["status"] != "VERIFIED":
            candidate = stage(
                "assess",
                4,
                "Review what the new evidence actually supports.",
                "The fresh condition now has adequate torque and independent functional evidence in this scenario.",
                "Assess the action against its fresh verification. The strongest allowed conclusion is support within this simulation, not confirmed real-world causation.",
                "Assess the action against fresh evidence",
                "investigation",
                "assess_action",
                {"action_id": action["id"]},
            )
        elif holds:
            candidate = stage(
                "resolve",
                4,
                "Evidence is ready. The pause still needs a QA decision.",
                "All stated evidence checks accept the current condition, but the hold remains active.",
                "QA reviews the current evidence and explicitly resolves the scoped hold. That still does not issue permission to make units.",
                "Review and resolve the hold",
                "qualification",
                "resolve_hold",
                review,
            )
        elif not permits and len(fresh_units) < 5:
            candidate = stage(
                "authorize_new",
                4,
                "Give permission for this exact condition.",
                "The hold is resolved. The old permission belonged to a different condition and cannot simply be reused.",
                "QA grants a new limited simulation permission tied to the current evidence and exact material/setup identities.",
                "Review the new simulation permission",
                "qualification",
                "authorize",
                {**review, "max_units": 20, "minutes": 15},
                [
                    {
                        "label": "Permission",
                        "value": "Current condition only · 20 units · 15 replay minutes",
                    }
                ],
            )
        elif len(fresh_units) < 5:
            candidate = stage(
                "produce_new",
                4,
                "Continue, with a check at the moment of use.",
                "Fresh evidence, a resolved hold and a live QA permission now agree on this condition.",
                "Create five demonstration units. Permission and evidence are checked again as the units are recorded.",
                "Make five units under the new condition",
                operation="produce",
                payload={**run_payload, "units": 5 - len(fresh_units)},
                preview=[
                    {"label": "New simulated output", "value": f"{5 - len(fresh_units)} units"}
                ],
                expected="Each unit retains the actual scope, permission and evidence it depended on.",
            )
        else:
            return stage(
                "complete",
                4,
                "The decision is recorded. The evidence stays.",
                f"Your story has {len(baseline)} earlier units and {len(fresh_units)} units under the freshly verified condition. They are saved demonstration records, not measured factory output.",
                "You can trace a justified decision: the changed condition needed matching evidence, the failed earlier test stayed visible, and fresh verification plus QA earned a new permission. Reliable measurements and independent functional results answer different questions.",
                "Follow the evidence behind the decision",
                "evidence",
                preview=[
                    {"label": "Earlier condition", "value": f"{len(baseline)} simulated units"},
                    {
                        "label": "Freshly verified condition",
                        "value": f"{len(fresh_units)} simulated units",
                    },
                ],
                status="COMPLETE",
            )

    # A source outage or leftover hold may interrupt an otherwise legal next
    # step. Explain it, without bypassing the same command guards as manual use.
    if not source_ok:
        return stage(
            "source_recovery",
            candidate["chapter"],
            "First, restore a current view of the records.",
            "The evidence source is stale or incomplete. A previous passing status is not enough while its required input is unknown.",
            "Confirm a complete current synthetic source, then return to this story step.",
            "Confirm current records",
            "qualification",
            "refresh_source",
            {**run_payload, "complete": True},
        )
    if candidate["operation"] == "authorize" and holds:
        return stage(
            "hold_recovery",
            candidate["chapter"],
            "An earlier pause still needs to be resolved.",
            "Current evidence may be ready, but an active hold is a separate record.",
            "Review and resolve the hold before issuing another permission.",
            "Review the active hold",
            "qualification",
            "resolve_hold",
            review,
        )
    return candidate
