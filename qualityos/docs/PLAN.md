# Controlled implementation plan

Prepared 30 October 2026; implementation subsequently authorized by the user. Product root is `C:/ABYUD/HACKATHONS/LOREAL/qualityos`; repository root is its parent. The user runs all Git commands. The original milestone plan below is retained; executed results and scope limits are in [VALIDATION.md](VALIDATION.md).

## Goal and canonical contracts

Complete one local persisted QualityOS product with four functional workspaces and the full stale-qualification → scoped hold → investigation/action → fresh verification → QA authorization → guarded simulated continuation workflow.

Canonical specifications: [product](../../qualityos_handoff_2026-10-30_01/PRODUCT_SPEC.md), [domain model](../../qualityos_handoff_2026-10-30_01/DATA_MODEL.md), [architecture](../../qualityos_handoff_2026-10-30_01/ARCHITECTURE.md), [UX](../../qualityos_handoff_2026-10-30_01/UX_SPEC.md), [milestones and I01–I14](../../qualityos_handoff_2026-10-30_01/IMPLEMENTATION_PLAN.md), [independent validation](../../qualityos_handoff_2026-10-30_01/VALIDATION_PLAN.md).

No final competition slide, resume work, outside contact, public deployment, live equipment control, additional module suite or mandatory ML. Keep all synthetic/time/uncertainty/causality boundaries. Do not overwrite research, purge a database or use another project's code as a runtime dependency.

## Preparation completed

- Current workspace and new product path established; copied sources verified against previous location.
- Applicable workspace/ancestor instruction locations checked; persistent root instructions added for current user constraints.
- Canonical handoff read; domain/UX/acceptance and latest priority changes understood.
- Python, Node, npm, Python package metadata and browser availability inspected read-only.
- Milestones, acceptance expectations, path mapping, source integrity and user-run Git commands documented.

At the preparation checkpoint M0 was incomplete and no implementation was claimed. Implementation status now supersedes that checkpoint: M0–M6 core work is implemented, subject to the precise executed checks and limits in VALIDATION.md. M7 remains optional and unimplemented. Dependency-download restrictions were handled through the documented ADR-008 fallback rather than global package changes.

## M0 — Finish environment and freeze executable contracts

On implementation authorization:

1. Inspect current files and any new user changes without running Git. Read the latest AGENTS.md and preparation records.
2. Create a product-local Python virtual environment; install a minimal compatible dependency set without altering global packages. Test FastAPI/TestClient/httpx together and record resolved versions.
3. Establish a compatible React/Vite/TypeScript/Vitest toolchain, bundle Inter/JetBrains Mono locally and commit the eventual dependency locks through user-run commands. Verify registry/network access then; availability has not been assumed.
4. Check ports 8107/5177 and choose documented alternatives if occupied. Isolate local runtime stores, credentials and browser profiles under ignored `var`.
5. Finalise ordered SQLite migration strategy and API contract generation. Declare scenario/system time bases, immutable records and protocol/policy versions.
6. Convert [ACCEPTANCE.md](ACCEPTANCE.md) into independently authored executable expected outcomes before writing the evaluator. Keep its fixture version/hash in the eventual validation report.

Exit: isolated compatibility checks pass; no global dependency changes; versioned contracts/expected cases exist; no results inferred from installed packages.

## M1 — Pure evidence-to-decision slice

Implement Decimal/unit/domain types, exact and explicit approved-envelope scope, measurement-time reliability, time cuts, typed predicates and reason-bearing decisions. No persistence/UI dependency in pure policy code.

First slice: initial applicable synthetic proof; changed closure outside scope → HOLD; in-tolerance reading from invalid reference does not clear the gate; unrelated independent run remains qualified. Serialize a real decision receipt from execution. Distinguish invalid evidence from a known functional failure: unusable proof does not imply a defective package.

Exit: independent M1 expected cases and appropriate boundary/property tests pass. Simulator hidden truth is inaccessible to evaluator imports. User may checkpoint the completed slice after reviewing actual checks.

## M2 — Persistence, API, roles and at-use enforcement

Add migrations, foreign keys, workspace isolation, append-only evidence/events, projections and audit/command receipts. Use serialized write transactions for context changes and permission check/use. Implement CAS, idempotency, source sequence/health, server-owned sessions and the exact role matrix.

Build the health/auth/workspace/run/study/measurement/calibration/decision/hold/permit/production API. Use bounded validation/errors, same-origin development proxy, CSRF/Origin checks and hashed local credential setup. No committed default passwords; no arbitrary role field trusted from the browser.

Exit: durable restart; denied production creates no unit; retry creates one effect; collisions/stale context rejected; viewer/operator cannot sign QA permission; ADMIN is not automatically QA; failed transaction/store cannot green-light work. Test migrations, rollback and crash/retry before UI reliance.

## M3 — Complete W1/W2/W3 through backend commands

Finish delayed functional failure, investigation/hypotheses, approved alternate configuration, action execution, fresh independent verification, QA hold resolution and bounded simulated production. Preserve failed and inconclusive paths.

Implement late corrections/revocations, immutable AS_KNOWN snapshots, CURRENT_REASSESSMENT, affected-unit trace with explicit certainty, and incomplete-lineage broadening. Add clean-control and approved-envelope negative controls. Keep evidence readiness independent of hold status so QA recovery does not deadlock.

Exit: full API journeys produce durable receipts. Clock advance rechecks freshness/expiry without inventing heartbeats; compatible/unrelated facts do not revoke independent permissions. Pre-action/wrong-scope evidence cannot verify an action.

## M4 — Four complete frontend workspaces

Build the warm light/forest/ink system and intentional operations layout from UX_SPEC. Shared server-backed context, role session, route/deep-link support, cursor polling and evidence drawer precede feature-specific interactions.

- Line: exact lots/configuration, process rail, decision/hold/permit separation, actual unit progress and next action.
- Evidence: bounded relational graph, equivalent table, three-time timeline and read-only historical/reassessment views.
- Qualification: requirement checklist, measurement interval/reference view, independent test availability, data forms and guarded QA review.
- Investigation: exact/conservative affected scope, supporting/refuting hypotheses, action lifecycle and scoped effectiveness assessment.

Every primary action calls a tested server command and refreshes committed state. Handle offline, stale, unknown, validation error and role restrictions. Preserve drafts and focus; never silently retry a stale QA authorization.

Exit: W1/W2/W3 can be completed/inspected in a real browser; direct routes, reload/back/forward work; no core placeholder. Inspect 1440×900, 1024 px and approximately 390 px with keyboard, contrast and overflow checks. TypeScript/build success alone does not satisfy this milestone.

## M5 — Independent validation and repair

Run the versioned corpus, competent SOP/blanket-hold/evidence-aware baselines, temporal/identity/idempotency properties, atomicity races, source/expiry/budget/conflict checks and replay/recovery comparison. Retain parity and negative results.

Measure actual p50/p95 query/command latency on a declared 10,000-event fixture and environment. The proposed 500 ms target remains a target until measured. Keep potentially affected, held, defective and scrapped counts separate. Synthetic clock latency and actual software response latency are different metrics.

Exercise the real UI, console/network errors, focus, offline failure and complete flow after backend restart. Fix invariant failures before adding features. Record exact commands, outcome counts, source versions and limitations in product-local reports.

Exit: I01–I14 pass for the declared corpus; actual backend/API/migration/recovery/property and frontend tests/build/browser checks recorded. No claim of commercial-system superiority or physical factory performance.

## M6 — Reproducible local completion and polish

Finish setup/start/stop/recovery instructions, private credential mechanism, migrations, scenario/data dictionary, decision/event export and claim boundaries. Where feasible serve the built SPA from FastAPI for a single-origin local demo. Repeat fresh-store launch and persistent-store restart using disposable test stores; preserve user's runtime history.

Prepare a short product walkthrough, inspect visual consistency and verify every primary interaction. If recording a walkthrough, measure its duration rather than claiming a timed demo from a script. Do not create the final competition slide or publish the site.

Exit: complete persisted four-workspace core, reproducible scenarios/evaluation, no core dead ends, honest limits, local launch and restart verified. Report remaining optional work separately.

## M7 — Optional only after core completion

TareTruth may add one complete paired-mass scenario with actual subject/stage matching and explicit engineering-bound arithmetic. Structured import/export refinement may follow using existing validators. Neither is a prerequisite for the core or permission to add a fifth unrelated workspace.

## Working discipline and future validation records

Keep one product and one central story. Use coherent milestones; no need to ask the user about routine implementation choices once implementation is authorised. Stop for genuine blockers, conflicting changes or actions beyond scope. Record justified architecture changes in DECISIONS.md.

Future reports should distinguish planned, executed, passed, failed and blocked checks. Store secrets, databases and browser profiles under ignored paths; keep small reviewed evaluation summaries reproducible and versionable. Preserve independent oracle/data versions so an implementation cannot quietly redefine expected behaviour. Supply Git checkpoint commands to the user; never execute them.
