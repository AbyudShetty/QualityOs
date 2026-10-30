# Predeclared acceptance expectations

Preparation baseline, 30 October 2026. These are human-authored expected behaviours derived from the handoff. They are not tests executed, generated results or a replacement for the independent validation corpus. Preserve this version when creating the first runnable corpus; record amendments with their reason before evaluating changed behaviour.

## First executable slice

| Case | Input condition | Expected observation |
|---|---|---|
| P01 | Run A's exact pair/configuration has available applicable valid synthetic torque and independent functional proof | Evidence gate ACCEPT for declared checks; simulated production still requires QA permission |
| P02 | Run A changes closure to a lot outside that proof's exact/approved scope | Old study remains in history; current evidence gate HOLD with explicit missing applicable qualification; prior permission cannot authorize new units |
| P03 | New observation is numerically within tolerance but its declared reference is invalid at measurement time | Reading reliability INVALID; cannot supply satisfied proof or clear P02's HOLD |
| P04 | Independent run B retains its own complete valid qualification | Run B is not held merely because run A changed |
| P05 | A change is genuinely inside a documented approved envelope | No automatic requirement for a new full qualification solely because the lot identifier changed |
| P06 | Required uncertainty or independent functional proof is missing/unavailable | UNKNOWN requirement and HOLD, never ACCEPT based on the convenient torque value |

Keep measurement reliability distinct from package conformance: an invalid observation is not proof that the package failed. When no eligible valid proof exists, the relevant sufficiency requirement is unknown. Preserve explicit reasons and distinguish this from a valid applicable functional failure. Final predicate-to-aggregation mapping must be documented alongside the M1 contract so it cannot contradict the required HOLD prefix.

## Persistence, roles and guarded production

| Case | Condition / command | Expected observation |
|---|---|---|
| P07 | Identical successful command is retried after its first commit advances context | Original receipt/effect returned once; stale revision does not create a duplicate or renew permission |
| P08 | Same idempotency/source key carries different content | Conflict; no second effect |
| P09 | Context change races with permission/production | Serialized check/use; no unit committed under inapplicable permission |
| P10 | VIEWER or OPERATOR calls QA authorization directly; ADMIN lacks QA role | Server denies unauthorized signing irrespective of UI state |
| P11 | Active hold, expired permit, exhausted budget, required source gap or store failure | No unauthorized committed unit; explicit reason and safe visible failure |
| P12 | A transaction fails partway, or a committed command is retried after process restart | All-or-none mutation; committed history/receipt survives; no repair by deleting history |
| P13 | An unrelated comment or compatible evidence arrives for independent scope | No indiscriminate invalidation through a global audit count |

## Complete recovery and temporal history

| Case | Condition / command | Expected observation |
|---|---|---|
| P14 | QA records a fresh calibration after an invalid old observation | Old reading remains invalid; a new eligible observation is needed |
| P15 | Certificate expired today but was valid at retained observation time | Expiry now alone does not invalidate that historical reading |
| P16 | Torque passes while the independent delayed leak endpoint is still pending | HOLD; torque cannot stand in for functional proof |
| P17 | A valid applicable independent functional result fails | Reject proposed configuration with retained failure; do not select a convenient later pass to hide it |
| P18 | Approved action changes configuration, followed by fresh exact-scope independent verification | Current evidence may ACCEPT while workflow hold remains active; QA can explicitly resolve the hold and issue bounded simulation permission |
| P19 | Action is assessed using pre-action, wrong-scope or self-generated assertion alone | No VERIFIED/effective shortcut; missing verification remains explicit |
| P20 | A late revocation invalidates a past supporting reference interval | Original AS_KNOWN receipt preserved; current reassessment/permission and potentially affected population updated |
| P21 | Affected product genealogy is partial | Conservative possible scope and missing-link reason; no false exact/minimal impact claim |
| P22 | Scenario clock jumps 24 hours | No claim of instant physical testing; permit expiry/source freshness reevaluated; no fabricated heartbeat |
| P23 | Rebuild/replay after a restart | Same normalized semantic outcomes/history, independent of volatile process timestamps or generated IDs |

## Four workspaces and actual independent evaluation

- All primary W1 actions can be executed through actual persisted backend commands from the UI; W2 and W3 are inspectable and functional.
- Line distinguishes evidence recommendation, active hold and QA permission; no client-only 'approved' state.
- Evidence graph/table/timeline use real records, preserve three times and provide read-only AS_KNOWN/current reassessment views.
- Qualification displays independent functional tests, numeric uncertainty and reference-at-measurement-time reasoning.
- Investigation preserves competing explanations, action lifecycle, new verification and scoped effectiveness; association is not confirmed causation.
- Desktop/mobile, direct routes, navigation/reload, keyboard/focus, contrast, console/API errors and restart are checked in an actual browser.
- Independent oracle, version-unaware example, competent SOP, legitimate blanket hold and evidence-aware reference see the same declared information cuts. Parity is an acceptable reported result.
- No production evaluator may import simulator hidden truth or independent expected labels. Synthetic-case pass counts are software results, not estimated factory safety or defect-reduction rates.
- I01–I14 and FR/NFR mapping remain authoritative in the handoff; these selected cases supplement rather than replace them.

Future result reports must link the actual case records, protocol/corpus version, command, denominator, provenance and limits. Empty evaluation state reads 'not run'. No passing number is filled in during preparation.
