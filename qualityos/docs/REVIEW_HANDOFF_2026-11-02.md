# Engineering handoff after independent-review remediation

2 November 2026. Read the final executed reports in [validation/review-remediation](validation/review-remediation) and [current checks](validation/checks.json). This is a scoped correction of the existing product, not a new platform or competition slide.

## Inspected

The independent review's README, recommendations, implementation handoff, UX and technical audits, industrial validity, slide review, competition fit, sources and adversarial tools/artifacts; root instructions and current implementation/operating/decision documents; relevant canonical architecture/data/UX/validation contracts; actual evaluator, service, API, seeds, persistence, frontend and tests. The complete four-page original brief was read from its published URL; its original local binary remains absent. Existing sources were reused rather than restarting broad research.

Lumafield's packaging qualification account, Capgemini/Everest's supplier-bottle case (printed p.17 / PDF index 18) and Hexagon's original packaging engineering case were retrieved. Hexagon was not actually listed in the local EVIDENCE_AND_SOURCES.md; it was located separately. These support packaging variation/testing relevance, not a demonstrated qualification-control deficiency at L'Oréal. Exact URLs and the distinction are in [the frozen plan](REVIEW_REMEDIATION_2026-11-02.md).

## Corrections delivered

| Review boundary | Implemented behavior |
|---|---|
| T01 correction chain | QA can correct the terminal successor through multiple generations. Conflicting inherited metadata is excluded; immediate predecessor, original attestor, correction actor and recording-error basis remain explicit. Forks reject; prior results and decision cuts remain intact. |
| T02 governing inputs | Missing/wrong-kind/malformed/unavailable policy, invalid revision/count/limits/dwell and missing/wrong packaging identities cannot ACCEPT. Actual authorization rejects invalid policy. No corruption endpoint added. |
| T03 required recovery | QA-approved release-required actions bind to incident/holds and executed scope. Sparse/old proof cannot satisfy fresh verification; assessment remains required before hold resolution, permission or production. Optional/unrelated actions do not impose a blanket block. |
| T04 genuine failures | QA-only scoped study determination requires a distinct independently passing verification and verified linked action. New PASS alone does not clear failure. Another unresolved failed study continues to block. Recording-error correction is a separate QA-only operation. |
| T05 study semantics | New sets are REQUIRED by default; explicit SUPPLEMENTAL is available through the typed API. No cross-set specimen pooling. Empty/planned sets do not count as completed coverage. Required incomplete/inconclusive evidence cannot borrow old proof. Bulk fictional functional input is explicitly labelled; no physical per-specimen data is claimed. |
| T06 retrospective review | Affected historical units receive persisted containment groups, separately from current-scope permission. QA handling is recorded separately. A later different discovery reopens containment rather than inheriting an earlier handling decision; original production/history remains. |
| Scope prior art / provenance | C03 has an explicit synthetic joint tuple and approval provenance. Per-field lists cannot extrapolate unsupported Cartesian combinations. The independent control's separate B02/C03 approval was isolated out of the multi-axis regression so it did not confound the probe. |
| Error / retry | Opaque/non-JSON responses get a useful client message. Uncertain server/network outcomes retain the idempotency key; definite controlled client failures require a fresh review. Unexpected server exceptions return generic JSON, with no raw internals and no partial transaction. |
| Limited reference/history | UI calls the comparator a limited separately specified synthetic checklist, not a complete industrial SOP. Recent history/link caps are explicit, with full workspace export available. |

The original 20-case expected-v1 corpus is untouched. [expected-review-v2.json](../scenarios/expected-review-v2.json) fixes 15 new review groups before implementation. New regression coverage is development/adversarial coverage, not blind external certification or physical trials. Initial red tests include unsupported newly declared contracts as well as demonstrated bugs; they are not all security exploits.

## Primary UX

Getting started offers one recommended **Inspect a packaging change** entry that begins with supported C01/v1 proof. The main screen compares old/current bottles, caps, suppliers and setup; identifies excluded evidence; names affected future production; distinguishes evidence, pause and permission; and offers the server-derived next action. Core direct-pass and failure/recovery routes run from this panel without coordinating tabs. Tabs retain expert inspection; repeated instructions and detailed records are collapsed. Demo clock/feed controls are labelled as synthetic inputs, not physical testing or real source reconciliation.

The main form explains the assumed non-disturbing application-torque observation, eligible reference, separate error assumption and fictional group leak input. Evidence pickers show values/outcomes, specimen, condition and time instead of opaque suffixes. Desktop and narrow-screen layout/task visibility were exercised through actual forms; this was developer-operated browser verification, not a fresh-participant study or a measured 30-second comprehension result.

## Files

- Backend: `backend/qualityos/domain.py`, `service.py`, `api.py`, `scenarios.py`, `evaluation.py`; `journey.py` receives only compatibility with the required-assessment gate.
- Frontend: new `web/src/ChangeDecision.tsx`, `change-decision.css`, `decisionLabels.ts`; changes in `App.tsx`, `Experience.tsx`, `FormGuidance.ts`, `api.ts`, `main.tsx`.
- Tests: new `backend/tests/test_review_regressions.py`, `web/src/review.test.tsx`; two prior `test_workflow.py` expectations now require HOLD pending mandatory assessment instead of the old documented bypass. Expected-v1 is unchanged.
- Verification: new `web/scripts/review-remediation-check.mjs`, `scripts/collect_review_remediation.py`, new v2 case declaration and new dated reports/screenshots. Generated command schemas reflect the additive typed contracts and QA restrictions.
- Product-local docs: frozen plan, this handoff, current demo, validation/README/decision updates. Root manual/PDF, research, independent review, Git data, slide and resume are preserved.

## Reproduce and launch

```powershell
# From C:/ABYUD/HACKATHONS/LOREAL
npm start
# Open http://127.0.0.1:8107/start; keep the terminal open. Ctrl+C stops it.
```

`npm run dev` remains the same complete local launch; it is not hot reload. No new dependencies or services. Existing source-built SQLite/local environment limitations remain.

Executed verification commands are recorded with actual results by the collector. Primary commands: `qualityos/verify.ps1` (backend tests, frontend tests, TypeScript/build, contract generation); separate `tsc --noEmit --incremental false`; `node web/scripts/review-remediation-check.mjs` against the isolated 8112 store. The browser verifies explicit baseline → change → hold, direct passing proof → QA → five units, failed testing → reviewed change → fresh verification → required QA assessment → bounded continuation, retained failed history/reload, C03 control, keyboard Escape and 390px/1440×900 visibility.

## Screenshot recommendations, without editing the slide

1. `02-changed-caps-scoped-hold.png` or `12-desktop-change-decision.png`: the clearest central before/current/evidence-gap decision.
2. `01-qualified-baseline.png`: starting proof genuinely covers the original condition.
3. `04-tests-complete-still-paused.png` / `07-required-verification-review.png`: readiness does not falsely authorize production.
4. `05-bounded-qa-authorization.png` / `08-verified-recovery.png`: actual bounded permission after review.
5. `10-explicitly-covered-alternative.png`: a change already inside explicit coverage is not unnecessarily treated as a defect.

These are actual synthetic application screenshots, not physical manufacturing results. Files are under `docs/validation/review-remediation`.

## Remaining limits / do not overclaim

- No measured physical quality, defect prevention, first-pass yield improvement, savings, plant pilot, commercial comparison, adoption or competition-selection result. The residual operational gap remains an industrial hypothesis. Existing systems can implement overlapping controls.
- A packaging expert must validate change triggers, fixed omitted dimensions (formula, line/tool/speed, conditioning), assay, sample plan, application versus removal torque, uncertainty budget and the trial/routine-production boundary. Bulk fictional outcomes do not validate mixed per-specimen physical behavior.
- General required-plan cancellation/replanning and repeated failed-trial recovery are not generalized here. Unverified mandatory evidence can deliberately remain blocked; do not demonstrate untested recovery paths or alter facts to force success.
- Legacy stored C03 envelopes without explicit joint approval may no longer qualify a future command. History is preserved. Use a fresh recommended demo; do not reset the user database. Legacy prescribed-guide API is compatibility code, not the recommended product.
- Local shared demonstration accounts are not enterprise multi-tenant identity or regulated signatures. Clean online installation/industrial integration remains unverified; system-package fallback is documented. No new scaling benchmark was run.
- Root manuals/PDF describe the prior UI and are retained unchanged. Use [the current short demonstration](DEMO_2026-11-02.md).
- Authenticated submission limits/deadline and general BTech CSE eligibility are not newly verified. User handles the one slide/resume. Neither was modified; no public deployment or outside contact occurred.

For sustainability, measure against a competent existing procedure at equal accepted output: unsupported decisions and false holds first; then actual defects, rework, unrecovered formula/packaging, extra specimens, time and review burden. Water/energy only for operations that demonstrably changed. Intended benefit is not measured benefit.
