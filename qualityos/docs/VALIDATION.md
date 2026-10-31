# Current validation: user-controlled experiments

31 October 2026. The previous guided-story UI passed automated checks but failed the user's first-visit comprehension review. It was replaced as the default experience. The retained older reports below do not establish acceptance of the current UI.

| Current check | Actual result | Evidence |
|---|---|---|
| Backend domain/API/storage/workflow/migration tests | 67 passed | [checks.json](validation/checks.json), including test_experiments.py |
| Frontend boundary tests | 3 passed | [checks.json](validation/checks.json) |
| TypeScript, production build and contracts | Passed | [checks.json](validation/checks.json), docs/contracts |
| User-controlled real-browser workflow | 16 checks; no captured runtime/console errors | [experiments-browser.json](validation/experiments-browser.json) |
| Current contrast screen | 0 failures across 761 text elements over five selected page states | [experiments-contrast.json](validation/experiments-contrast.json) |
| Frozen synthetic outcome corpus | 20/20; regenerated without changing frozen expectations | [evaluation-v1.json](validation/evaluation-v1.json) |
| User data preservation | Consistent private backup of 11 sessions, 231 events, 462 decisions; unchanged counts confirmed before restart | Private ignored var backup; ADR-015 |

Browser coverage uses actual forms against a separate 8112 backend/database. It exercises explicit FAIL then investigation/fresh verification/PASS, invalid references, varied readings, bounded QA permission, persisted sample units, old decisions, reload, custom setup, covered-cap alternative, session filtering, and all four tabs at 1024 and 390 pixels. Backend tests separately cover direct PASS without investigation, atomic/idempotent multi-reading submission, custom input validation and migration from schema 1 without deleting facts or decisions. No results were set directly to a desired policy decision.

Screenshots: [Introduction](validation/screenshots/experiment-introduction.png), [Reading entry](validation/screenshots/experiment-readings.png), [Mobile tests](validation/screenshots/experiment-mobile-tests.png). These and developer visual inspection do not replace independent novice usability feedback. The contrast scan handles computed solid colors and selected states only; it is not a full accessibility audit.

The running older server on 8107 requires a restart to load the new API and migration. The isolated current build is what was tested. No unfamiliar user process was killed. The backup is private and was not committed. All observations/results remain synthetic; there are no physical trials or measured savings. The existing environment/dependency warning and missing local case PDF limitations below remain applicable.

---

# Retained earlier core and guided-story validation

30 October 2026. This report describes the implemented local synthetic core. Counts describe declared software tests and scenarios, not independent manufacturing trials or an estimated factory failure probability.

## Recorded checks

| Check | Executed result | Reproducible evidence |
|---|---|---|
| Backend domain/API/storage/property/workflow tests | 58 passed, including guided-story boundaries | [checks.json](validation/checks.json), `verify.ps1`, `backend/tests` |
| Frontend presentation boundary tests | 3 passed | [checks.json](validation/checks.json), `web/src/api.test.ts` |
| TypeScript and production build | Passed | [checks.json](validation/checks.json); built SPA served locally |
| Independent declared outcome corpus | 20/20 QualityOS and reference matches | [evaluation-v1.json](validation/evaluation-v1.json), frozen `scenarios/expected-v1.json` |
| Actual browser workflow | 16 checks passed in the final authenticated-session run, no captured unhandled runtime/console errors | [browser.json](validation/browser.json), `web/scripts/browser-check.mjs` |
| First-visit guided story | 11 checks passed, including fresh login, all 24 reviewed actions, control comparison, resume and mobile | [story-browser.json](validation/story-browser.json), [UX record](UX_GUIDED_STORY.md) |
| Fresh store and actual process restart | Same three units, original receipt and semantic digest after restart | [recovery.json](validation/recovery.json), `scripts/restart_check.py` |
| Original core contrast screen | No failures among 1,086 checked text elements in the initial core review | [contrast.json](validation/contrast.json), `web/scripts/contrast-check.mjs` |
| Guided-story contrast screen | No failures among 1,347 checked text elements across Start here and four guided page states | [contrast-story.json](validation/contrast-story.json) |
| Preserved source files | All 24 available handoff/reassessment hashes matched; original PDF missing locally | [source-integrity.json](validation/source-integrity.json), [source status](SOURCE_STATUS.md) |
| Initial core 10,000-event software fixture | Snapshot p50 8.497 ms / p95 10.249 ms; read plus comment p50 22.632 ms / p95 26.320 ms; replay digest matched; retained initial benchmark | [performance.json](validation/performance.json), `scripts/benchmark.py` |

The final browser run used the actual built frontend against the restarted API over localhost. Initial fresh-login smoke and backend/HTTP recovery tests separately exercised login; the final browser profile already had an authenticated session. The script performs commands through application forms and inspects actual persisted responses. It does not set decisions directly.

The subsequent first-visit revision adds a separately tested, server-derived story without changing the pure quality policy. Its dedicated browser run explicitly cleared only its own QA profile's cookies/local storage and exercised actual fresh login. See UX_GUIDED_STORY.md for scope and cognitive-usability limits. The retained initial performance fixture was not a guided-story load benchmark.

One existing Starlette `multipart` import PendingDeprecationWarning remains. It does not fail a test. External dependency downloads were blocked; this environment uses the explicitly documented tested local fallback, not a claimed clean online installation.

## Milestone disposition

| Milestone | Delivered core | Material boundary |
|---|---|---|
| M0 | Current workspace audit, local environments, tested versions, locks, frozen expected cases, migrations and generated contracts | Python fallback reads installed system packages; fresh online install not verified |
| M1 | Pure deterministic predicates, exact/envelope scope, reference reliability, engineering intervals, distinct specimens and independent functional results | Illustrative policy and synthetic observations only |
| M2 | SQLite persistence, immutable facts/decisions/audit, sessions/RBAC, typed commands, idempotency, CAS and atomic at-use guard | Local single-worker prototype; no certified identity or equipment interlock |
| M3 | Complete recovery, late correction/revocation, original knowledge cuts, exact/conservative impact, limited investigation/actions/effectiveness | No physical response/causal model or factory integration |
| M4 | Four functional routed workspaces, actual forms, evidence drawer/graph/table, polling, drafts, offline and historical states | Developer/browser review; no external operator usability study |
| M5 | Frozen comparison, properties, adverse paths, API bypass attempts, concurrency, rollback/replay/restart, responsive/keyboard/contrast and declared latency fixture | Limited deterministic development corpus; no commercial MES comparison or manufacturing statistical inference |
| M6 | Local single-origin app, private account initialization, start/verify scripts, walkthrough, exports, actual reviewed evidence and source integrity | No recorded/timed three-minute presentation, final competition slide or public deployment |
| M7 | Deferred optional TareTruth and import refinement | Deliberately outside the completed core |

## I01–I14 trace

| Invariant | Actual coverage and outcome |
|---|---|
| I01 Knowledge cut | Future-availability corpus case holds; historical snapshot test retains the earlier ACCEPT and no future correction/impact. Snapshot reads use an explicit SQLite read transaction. |
| I02 Scope | C02 holds, C03 explicit envelope accepts, configuration/policy changes do not inherit old proof. Random unlisted UUID identities never qualify. Independent run remains qualified after the lot change. |
| I03 Reference time | Invalid-at-observation and effective retrospective revocation hold; expired-now/valid-then accepts. A fresh certificate does not repair old readings. Full workflow retains invalid observations. |
| I04 Unknown/conflict | Missing/unsupported uncertainty, source gaps, pending tests, incomplete lineage and conflicting outcomes hold. Independent known failures reject. Source-gap/adverse-observation API tests block at use. |
| I05 Quantity/subject | Exact finite Decimal boundaries and Hypothesis interval cases; incompatible units and excessive precision/exponents rejected. Missing/wrong-study specimens cannot create proof. Functional dwell cannot predate specimen observation. |
| I06 Idempotency | Same key/content returns one receipt/effect, canonical model input is hashed, changed content collides. Duplicate functional endpoints reject. A real browser drops a response after server commit and retries without duplicate units. |
| I07 Atomic check/use | Concurrent produce/change calls sharing a revision yield one commit and one STALE_CONTEXT; direct stale, active-hold, expired and over-budget calls cannot create an invalid unit. |
| I08 Durability | Injected pre-commit rollback preserves digest. Replay projection equals current projection. A real process terminates after a committed receipt, restarts the same database and returns the same three units/receipt/digest. Migration reentry passes and newer schema is refused. |
| I09 Impact | Hand-authored expected sets identify five newly qualified units after reference revocation, and two dependent units after a functional correction. Incomplete genealogy broadens to all three possible units in that test with explicit CONSERVATIVE certainty. |
| I10 Permission | Direct viewer/operator/admin QA bypass attempts return 403; CSRF/Origin, stale snapshot, hold, expiry and budget checks are exercised. Injected store failure returns 503 with no granted permit or changed semantic state. |
| I11 Action boundary | Execution before approval rejects; assessment before fresh verification rejects. A sparse fresh study cannot borrow adequate old proof to become effective. Full new verification records only SUPPORTED_IN_SIMULATION. |
| I12 Provenance/time | Only synthetic mode accepted; per-workspace logical advance and actual audit receipt remain separate. Export labels and domain/audit separation checked. No bench connector is exposed. |
| I13 Retained adversity | Original results and immutable decisions survive corrections. Supersession chains cannot fork silently. Invalid readings and initial FAIL remain visible after a later different-scope PASS. Append-only triggers reject history edits. |
| I14 Policy isolation | AST boundary check forbids scenario/evaluation imports in pure policy. Toggling an injected simulator-label sentinel does not change its decision. Expected labels are not supplied as policy features. |

These invariants pass within the declared coverage. They are not a proof over every possible input, power-loss sequence, filesystem failure or production integration.

## Baseline fairness and independence

Twenty hand-authored expected outcomes were frozen before the production evaluator. A separately written checklist/reference implementation and the production policy run on the same public synthetic inputs. The reference matches QualityOS on all 20 outcomes; the UI and report retain that parity. B0 is an intentionally version-unaware ACCEPT example; B2 is blanket HOLD. Neither is presented as a measured factory or commercial-system baseline. The competent SOP and evidence-aware reference share one implemented reference; no human SOP experiment was conducted.

Additional edge cases and property tests were developed while implementing/reviewing the system. They are development coverage, not a blind external confirmation dataset. Independent here means separately specified oracle/implementation boundaries, not third-party certification. There is no trained ML model, classifier threshold, manufactured accuracy metric or hidden physical truth consumed by policy.

## Real-browser and visual coverage

W1 was completed through the UI: initial bounded permission and units, outside-scope change, invalid reference, new reference/new observations, delayed independent FAIL, investigation, hypothesis, approval/execution, complete fresh verification, explicit QA resolution/permission and new units. W2 then preserved AS_KNOWN history and scoped five potentially affected units after revocation. W3 negative controls are exercised by API/domain tests and described in the walkthrough.

Desktop review uses 1440×900; all four pages were also exercised at 1024×1000 and 390×1000 without document overflow. Dialog reverse-tab trapping/Escape, keyboard graph-to-drawer activation, network-offline pause/recovery, reload and persisted evaluation are checked. Bundled fonts, visible focus and reduced-motion rules are present. Tables/graph can scroll internally on narrow screens.

The contrast script evaluates computed solid text/background colors at the declared current states, excluding disabled and aria-hidden elements. Its pass does not establish every hover/focus/modal/state combination or certify WCAG compliance. No screen-reader audit, axe run or external usability study was performed.

Reviewed screenshots: [Line](validation/screenshots/01-line-ready.png), [Evidence](validation/screenshots/07-evidence.png), [Qualification](validation/screenshots/05-qualification.png), [Investigation](validation/screenshots/04-investigation.png), [mobile](validation/screenshots/390-qualification.png). Raw generated screenshots remain under ignored `var/browser-review`.

## Performance interpretation

The fixture contains 10,000 event rows, 39 starting projected entities and two runs. Of those events, 9,999 are archival receipts with empty projection changes. It does not contain 10,000 units, full decision snapshots or entities. Forty timed samples follow five warmups. Authenticated in-process ASGI requests include serialization/SQLite; the command metric conservatively includes its preceding snapshot read. It excludes TCP, browser rendering, network latency and multiuser load. The environment and exact fixture are in the JSON report.

The declared p95 software target of 500 ms was met on this fixture. No scale extrapolation follows. Full JSON historical snapshots and broad entity reads require retention/pagination work before industrial volumes. These milliseconds are actual software response measurements, not the simulated 24-hour dwell or a claimed manufacturing warning lead time.

## Adversarial release review

- The product implements a focused applicability/revalidation workflow already possible in capable MES/QMS configurations. No universal novelty, competitor deficiency or commercial superiority is claimed.
- Independent functional observations remain independent of torque. A replay PASS is entered synthetic evidence, not a simulated seal-physics discovery. Graph relations and action support do not establish real causation.
- Hard failures/unknowns cannot be converted into QA permission by a client role field or convenient final reading. A current ACCEPT remains separate from an active hold and from bounded at-use permission.
- Late knowledge changes current implications without rewriting earlier decisions. Potentially affected, held, defective, rejected and scrapped are distinct; the app measures no physical defect/scrap/resource saving.
- No plant data, operator study, benchmark of a commercial installation, equipment integration, regulated audit/e-signature validation or physical uncertainty calibration exists. Manufacturing value and adoption remain hypotheses for later bench/domain/pilot work.
- Known cost/operation limits are explicit: source confirmation is manual synthetic input, hardware/reference assumptions are illustrative, identity truth is not physically sensed, dependency installation uses the local fallback, and retention is designed for a small local prototype.

The core is suitable for demonstrating and inspecting its software decision mechanism. Any physical, economic, sustainability, competition-selection or PPI claim requires separate evidence. No final competition artifact was created or submitted.
