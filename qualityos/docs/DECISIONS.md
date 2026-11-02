# QualityOS decisions

Started during preparation on 30 October 2026. ADR-001–006 record that stage. Subsequent ADRs record implementation choices after the user's explicit authorization.

## ADR-001 — Canonical workspace relocation

Decision: all new product work belongs under `C:/ABYUD/HACKATHONS/LOREAL/qualityos`.

Authority: the user's latest instruction states that both previous handoff/reassessment folders were copied into this workspace and all writing will occur here. The previous target `C:/ABYUD/JOB/LOREAL/qualityos` is superseded. The sandbox permits writing in the current LOREAL folder, resolving the earlier access blocker.

| Historical reference | Current reference |
|---|---|
| `C:/ABYUD/JOB/LOREAL` | `C:/ABYUD/HACKATHONS/LOREAL` |
| `C:/ABYUD/JOB/LOREAL/qualityos` | `C:/ABYUD/HACKATHONS/LOREAL/qualityos` |
| `C:/ABYUD/JOB/LOREAL/qualityos_handoff_2026-10-30_01` | `../qualityos_handoff_2026-10-30_01` from the product root |
| `C:/ABYUD/JOB/LOREAL/reassessment_2026-10-30_01` | `../reassessment_2026-10-30_01` from the product root |

Read-only checks found all 11 local handoff files and all 13 local reassessment files identical to corresponding files at the previous location. Preserve these source copies unchanged. A source manifest records the current files and SHA-256 hashes. External project paths in the handoff remain optional read-only references; they are not relocated application dependencies.

## ADR-002 — Preparation-only boundary

Decision: create product-local planning/readiness documents and repository metadata; do not implement M1 or install/start the application until the user starts implementation.

Reason: this explicitly supersedes the preceding instruction to build immediately. No application skeleton, package manifests, executable test fixtures, lockfiles, migrations, database, frontend or generated results are created during this stage. An acceptance table can be frozen now; runnable test expectations are created before the evaluator in M1.

## ADR-003 — User owns version control

Decision: the LOREAL root is the proposed single Git repository; the user executes every Git command. No nested repository under `qualityos`.

Reason: preserves the case, research, specifications and product in one traceable history without moving existing files. Root AGENTS.md records the prohibition on running even read-only Git commands. Setup instructions include explicit paths and staged review before committing; no remote or public push is assumed.

## ADR-004 — Retain the canonical product architecture

Decision: plan Python 3.10-compatible FastAPI/Pydantic 2/SQLAlchemy 2 with SQLite, plus React/TypeScript/Vite, native CSS and bounded SVG views. One backend process; append-only facts plus transactional projections; server-owned roles and guarded simulation permissions; one-second cursor polling.

Reason: complete specification already defines the product and its invariants. The local Python/Node/browser tools support proceeding to compatibility checks. Version pins remain provisional until isolated tests pass. No broad architecture change or new research cycle is justified by preparation findings.

Planned migration choice: ordered SQL migrations with a version table and explicit transactional upgrade tests, avoiding an additional migration dependency for this small SQLite prototype. This is a proposed implementation choice. Adopt Alembic instead if an implementation-time compatibility/maintainability check justifies it; document that change and preserve migration/recovery acceptance.

## ADR-005 — Contract and validation order

Decision: freeze independent expected cases before the production evaluator; make OpenAPI the API schema source and produce a checked frontend contract during M2/M4. The browser owns selection/drafts only, never the authoritative evidence or permission decision.

Reason: avoids self-validating tests and frontend-only state. Keep simulator hidden truth outside policy imports. A correct evidence-aware reference may match QualityOS. No comparative manufacturing superiority follows from corpus parity.

## ADR-006 — Historical physical gates and current software scope

Decision: follow the latest QualityOS handoff for software scope. Earlier reassessment requests for a physical PackPair feasibility experiment gate physical/statistical efficacy claims, not this explicitly synthetic software product.

Reason: the handoff explicitly changes PackPair from adaptive test allocation into a qualification applicability workflow. Do not revive the earlier RightStart recommendation, add utility-air modules or claim an unearned sample-efficiency improvement. Physical observations may be added only under their own provenance and approved protocol.

## Future ADR template

Record the decision, implementation evidence, alternatives, affected contracts/tests and migration implications. Use observed results only after those checks actually execute. Do not edit source research to make it appear that a later architectural decision was always part of the original work.

## ADR-007 — Implementation authorization and local core

The user's later instruction explicitly starts implementation. It supersedes ADR-002's temporary preparation-only boundary. Follow M0–M6 without routine approval pauses; maintain user-only Git and preserve original inputs. No slide, resume, external communication or public deployment is authorized. The resulting application is local SYNTHETIC_DEMO only; the database forbids another mode, so bench and synthetic evidence cannot mix.

## ADR-008 — Offline dependency fallback

External pip/npm downloads failed under the sandbox (Windows socket permission error 10013 and unavailable offline metadata). A clean Python environment could not fetch packages. The working `.venv` was configured with `--system-site-packages`, exposing existing tested versions read-only. This is a product-local launcher, not a fully isolated dependency installation. Global installations were not modified. `requirements.lock.txt` records the 41-distribution declared runtime/test dependency closure, rather than an unrelated global freeze.

For npm, dependency files were restored from the observed local TRACKSHIFT dependency installation, without copying its application code or configuration. Every declared package version was verified. `npm install --package-lock-only --offline --ignore-scripts` subsequently succeeded and pruned/resolved the product lock. The product now builds using its own manifests, source and dependency directory. Network-enabled clean `npm ci`/pip installation remains unverified. Node 25 is the observed tested version, not an LTS support claim.

Official documentation consulted: [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/) and [SQLAlchemy SQLite transaction behavior](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html). In particular, explicit read BEGIN pins coherent multi-query snapshots; write BEGIN IMMEDIATE serializes check/use.

## ADR-009 — Typed registry and shared command boundary

Use an entity registry (`kind` plus validated JSON projection), composite workspace foreign keys on relational evidence edges, and immutable event/decision/audit tables instead of dozens of mostly empty entity-specific tables. Commands validate referenced type, exact workspace, units, transitions and identity before one serialized commit. The pure policy contains no DB/UI/scenario/evaluation imports. The actual SQLite schema is versioned by ordered transactional SQL migrations.

Tradeoff: critical JSON references rely on service validation in addition to relational constraints; this is not a fully normalized industrial schema. Test direct cross-workspace calls and FK enforcement. Full record snapshots simplify historical replay but grow with entity count; the measured 10k-event fixture does not establish 10k-entity performance. Retention, pagination and finer projections belong to an industrial scaling phase.

Expose one typed command envelope at `/workspaces/{id}/commands/{operation}`, rather than a different transport route for each entity. Operation-specific Pydantic models reject extra fields. Generated OpenAPI and command schemas are versioned under `docs/contracts`; frontend snapshot types are checked TypeScript declarations with real API/browser validation, not automatically generated clients. No arbitrary rule expressions or policy editor are exposed; protocol v1 is a fixed, explicitly assumed demo policy.

## ADR-010 — Stable authorization with pinned proof

The applicability fingerprint binds scope and immutable policy. The reviewed decision ID binds a specific immutable evidence cut; a permit stores its sufficient supporting IDs and a separate evidence fingerprint including reference dependencies. Additional harmless records do not revoke that pinned set. At-use validation checks current adverse/conflicting evidence, active holds, scope/policy, pinned dependency validity, expiry and unit budget inside the same write transaction. Existing persisted pre-fingerprint permits retain the earlier explicit supporting-ID validity checks; newly issued permits include the additional digest.

Workspace revision is a conservative CAS boundary: unrelated concurrent changes can require a fresh review, but do not automatically revoke an independent permit. Idempotency receipt lookup precedes new CAS validation. The browser retains the original key/body revision after an ambiguous network failure; a real-browser dropped-response test verifies exactly one committed effect.

## ADR-011 — Specimen dwell, fresh verification and late impact

Functional dwell is measured from each identified specimen's observation time, not merely study creation. Functional and torque endpoints must match the same specimen/study; the functional outcome remains independently entered and never inferred from torque. Exact decimal inputs have at most 18 digits and exponent -12 to 12 to avoid silent rounding/resource overflow in this engineering demo.

Action effectiveness requires an independently sufficient fresh post-action qualification; old applicable studies cannot fill gaps in a sparse fresh study. Known adverse evidence remains visible. Functional corrections append a successor and correction fact; correcting an already superseded result requires naming its latest replacement. Both revoked measurement dependencies and superseded functional dependencies identify prior potentially affected units. Missing genealogy broadens that retrospective population visibly, without calling those units defective or scrapped.

## ADR-012 — Local UI, browser validation and audit separation

Use native CSS/SVG, bundled fonts and the warm light/forest system, with four routes and shared backend state. No external design service or graphics dependency is required. Local draft/selection state cannot authorize work. Historical views are read-only; offline/context transitions disable writes; rejected stale commands retain the draft and require renewed human review.

Use a dedicated hidden Edge headless profile and CDP port 9239 for browser checks. This environment required `--in-process-gpu --no-sandbox` for that disposable local QA browser; these flags are a test-runner limitation, not an application deployment recommendation. Do not use a personal browser profile or expose that port externally. No Playwright/axe or certified accessibility audit is claimed. Real keyboard/focus checks, responsive screenshots and a computed-style contrast screen are recorded separately.

Decision creation and snapshot/export reads enter append-only audit using actual system time; cursor polling itself does not create domain events or invalidate permits. Export uses one domain cut and includes events, historical decisions, actual-time audit, provenance and a semantic digest. Audit is append-only through this application, not tamper-proof against the machine administrator.

## ADR-013 — Missing local original PDF

Final integrity verification confirmed all 24 copied specification/reassessment files unchanged, but found the original PDF absent from both expected local locations. Keep the original manifest and record a missing entry; do not manufacture a passing hash check. The published four-page PDF was reread through the web tool. Restoring its binary locally was blocked by the same network restriction as package downloads. [SOURCE_STATUS.md](SOURCE_STATUS.md) records the URL, expected hash, current limit and optional non-overwriting restoration command. The application and its tests have no runtime dependency on that binary.

## ADR-014 — Explain the decision before presenting operational detail

The user reported not understanding the application's purpose or how to navigate it. Add `/start` as an orientation page, with a concrete bottle/cap question, a fictional illustrated scenario and a clear guided entry. This is an introduction to the same four workspaces, not another manufacturing module. Direct operational URLs and unguided exploration remain supported.

`CreateWorkspace.guided=true` creates a new S1 workspace containing a versioned guide identity in its initial immutable event. It leaves existing workspaces unchanged and requires no database schema migration. `journey.py` derives the current explanation/action proposal from saved studies, observations, actions, holds, permissions and units. It cannot authorize work, set a decision or mark a lesson complete because a user clicked Next. Domain policy does not import the journey module.

New command-created records retain their actual workspace `recorded_revision`, allowing deterministic study/reference selection without inferring identity from display labels or timestamps. Older records remain readable. Historical and independent-control views have explicit read-only/navigation explanations; they do not receive a fabricated progress sequence. QA roles, CAS, idempotency and at-use enforcement remain unchanged.

Guided dialogs present the story's declared fictional input/result and its purpose before the user records it. Defaults do not predict leak physics or claim measured manufacturing results. Editing the supplied outcome or entering nonconforming torque produces a visible detour and preserves the evidence. The complete 24-command path still passes through independent dwell/source confirmation, action verification, explicit hold resolution and QA permission. A completed run does not restart the story merely because its permission has been retired; later affected units produce a separate late-discovery explanation.

Current decision evidence and dependency IDs are prioritized in the bounded graph; historical records remain accessible. Snapshot transitions explicitly announce loading while writes remain blocked. The export button is labelled Export workspace to match its actual scope. No human-time saving or independently validated first-time comprehension improvement is claimed from developer/browser checks.


## ADR-015 - Explain the process and let the user control experiments

31 October 2026. Direct user feedback rejected ADR-014's default guided story: context was still assumed, names were unclear, fixture workspaces cluttered navigation, and prescribed outcomes obscured user agency. The default UI now introduces bottled-lotion packaging before any cap-change premise. Four visible labels describe tasks: Production setup, Tests & approval, Investigate a problem, Decision history. Existing routes, evidence policy and QA guards remain compatible. The legacy journey API remains available for existing integrations but is not the default UI.

A new experiment persists chosen bottle/cap identities and machine setup, including custom fictional batches/settings. New identities receive no inherited qualification. The engine has no physical response model: machine settings do not generate readings or leak predictions. Readings can differ per specimen; a typed atomic measure_batch command persists 1-12 individual observations. Independent PASS/FAIL/INCONCLUSIVE remains an explicit choice after the example dwell. There is no automatic ending or forced investigation when the evidence already passes.

Relational migration 2 adds purpose and creator metadata. Existing sessions are retained as LEGACY_SESSION; recognisable Browser QA/Browser verification fixtures are AUTOMATION_TEST. Default listings show USER_EXPERIMENT only. Earlier sessions remain inspectable and can be kept in the user's list with an audited metadata-only command. Organizing does not rewrite domain events, revisions, decisions or permissions. Export schema version 1 is distinct from relational schema version 2.

A consistent private SQLite backup was made before any user-store migration: 11 workspaces, 231 events and 462 decisions. Read-only comparison confirmed those counts were still preserved. The old application process was left running; restart is required to load the new backend and apply migration 2. No unknown process was terminated. Migration behavior was independently exercised on a version-1 fixture with original event/decision preservation.

Browser checks now require a separate var/ui-checks database on port 8112, with private credentials and an owned browser profile. This prevents future acceptance fixtures appearing in the user's real session list. Automated coverage establishes software behavior and layout constraints, not novice comprehension. External first-time usability feedback remains needed.

## ADR-016 - One root launch command and a first-time user manual

The user requested a short launch command and a complete manual outside the product folder before further usability feedback. Add a scripts-only root package.json: npm start builds the existing frontend and invokes the existing Python/PowerShell launcher; npm run dev is an alias, and npm run build performs only the frontend build. This preserves one backend, the existing product environment and persistent store. No additional service, dependency or global execution-policy setting is introduced. Rebuilding on launch avoids silently serving an old frontend after source changes. This convenience command does not claim hot reload or install missing dependencies.

The underlying launcher accepts an optional validated local port, forwards it to the existing CLI, and prints the URL. Launch was verified on 8114 with an isolated QUALITYOS_DB store: actual TypeScript/build, healthy API and HTTP 200 built frontend. The normal user database was not used for the smoke check. The long PowerShell invocation remains encapsulated for Windows shell compatibility.

QUALITYOS_USER_MANUAL.md belongs in the repository root as requested. It explains the process, synthetic boundary, account roles, terminology, all four tabs, passing/preloaded and fresh-test paths, failed-test investigation, review-note examples, history, experiment choices and troubleshooting. Instructions were cross-checked against current labels, forms, policy and existing workflow checks. No improvement in independent novice comprehension is claimed solely from writing the manual.

## ADR-017 - Remediate independent-review defects and focus one applicability decision

2 November 2026. The user authorized a time-bounded repair, following the independent review. Its demonstrated defects supersede the prior broad completion assumptions. The [frozen review plan](REVIEW_REMEDIATION_2026-11-02.md) and new expected-review-v2 case declaration were written before evaluator edits; expected-v1 and historical evidence are preserved.

Use explicit valid governing policy/identities, per-study sufficiency without unplanned pooling, REQUIRED versus explicitly SUPPLEMENTAL studies, and scoped mandatory action assessment before release. Genuine failed-study QA determination is separate from QA-only recording-error correction; both preserve originals and actor provenance. Historical-unit containment is separate persisted state, with discovery-cut identity so a second discovery cannot silently inherit old handling. No relational schema change or new service is needed; the existing entity/event projection model carries these fields and facts. Legacy scope extensions lacking explicit joint approval fail closed for future use; AS_KNOWN snapshots are not rewritten.

The main UI follows a before/current packaging decision with a server-derived next action. It preserves user-selected synthetic outcomes, expert tabs, source/clock controls and underlying roles/transactions. Empty test plans do not read as completed qualification. There is no asserted physical prediction, causal conclusion, prevented-defect count, measured saving, novel mechanism or weakness in L'Oréal's actual controls. The limited synthetic checklist and bounded history are labelled honestly.

Known existing tests that expected ACCEPT before required action assessment were deliberately strengthened to HOLD and later ACCEPT after review. The legacy journey API remains compatible with that gate but is not revived as the primary UX. New and original tests, actual forms, persistence/reload, desktop/mobile task visibility and the covered-change control are executed separately from industrial validation. Results, exact limits and files are in the [current handoff](REVIEW_HANDOFF_2026-11-02.md).
