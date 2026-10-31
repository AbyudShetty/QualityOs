# Problem-first, user-controlled experience

31 October 2026. The user rejected the guided-story revision: manufacturing context was still assumed, terminology was unexplained, development fixtures polluted the selector, and prescribed actions/results did not provide meaningful control. Automated completion did not establish comprehension.

Acceptance for this revision:

1. Introduce the cosmetic-factory process and what QualityOS actually decides before mentioning a changed cap batch.
2. Define an experiment as one saved set of chosen inputs, fictional test results and decisions. Keep earlier sessions accessible without mixing development runs into the normal selector.
3. Let the user choose materials, a machine setup (including custom fictional inputs), torque readings, reference reliability, elapsed demonstration time and independent test outcomes. Do not present a physical-response model or infer leaks from torque.
4. Label the existing four routes Production setup, Tests & approval, Investigate a problem, and Decision history. Each page visibly explains what to do, what to enter and what outcome to expect.
5. Remove the prescribed story from the default product. No automatic PASS/FAIL or unexplained next command. Provide field-specific examples and explanations for review notes; keep real QA/transaction guards.
6. Preserve original sessions, facts, audits and decisions. New browser checks use an isolated database instead of creating fixtures in the user's application store.
7. Exercise different user choices, unsuccessful paths, persistence, role restrictions, migrations and the actual responsive UI. State the remaining need for human usability feedback.


## Implemented behavior

Getting started explains the factory process, the purpose of checking existing evidence, and the boundary between a decision experiment and a physical simulation. Choose pretested inputs, untested caps, or custom fictional batches/machine settings. A saved experiment is explicitly defined as one practice session. Production does not start automatically. All new test outcomes require user submission.

| Tab | What to do | Result |
|---|---|---|
| Production setup | Review selected bottles, caps and machine setup; inspect readiness; after permission, choose a sample-unit count. | Persisted scope and guarded sample records. |
| Tests & approval | Start a test set, enter individual readings with a measuring-tool reference, advance example time, confirm current records, and choose an independent leak result. Review pause resolution and bounded permission separately. | Saved observations, eligibility checks, independent result and explicit QA decisions. |
| Investigate a problem | Describe an actual failed/missing-condition problem, record possible explanations and competing evidence, plan/approve/apply a setup change, start fresh verification, and review it after new tests. | A traceable tested explanation; no claim of physical causation. |
| Decision history | Read actual input/action/result summaries, select earlier decision cuts, inspect detailed records if desired. | Original knowledge and adverse results remain available. |

Routine reading entry does not require a fabricated QA explanation. Operations that really require a review note explain its purpose and provide an editable example. The leak result has no default outcome. The 24-hour wait is example demonstration time, not an actual test duration observed by this software. Custom machine settings are saved; their physical consequences are not modeled.

Earlier sessions are retained in a separate section. Known development fixtures no longer enter the ordinary selector. A metadata-only Keep in my experiments operation lets users restore a relevant earlier session. User records are not deleted or renamed automatically.

## Executed review

The current build passed 67 backend tests, 3 frontend boundary tests, TypeScript and production build. The current real-browser script passed 16 checks using an isolated store: context, session separation, user-chosen materials, invalid references, varied readings, explicit independent failure, investigation/recovery, review notes, bounded continuation, history, reload, four tabs at 1024 and 390 pixels, custom inputs, and an explicitly covered alternative cap batch. The backend additionally exercises a direct chosen PASS path with no forced investigation and distinguishes that from QA approval.

The current computed-style screen found zero failures among 761 checked text elements over the introduction and four selected page states. This is a limited solid-color contrast screen, not full accessibility certification. The input dialog was visually inspected: its explanation and field help are visible, its body scrolls independently, and Save remains available in the footer. Screenshots and machine reports are under docs/validation.

Reproduce with verify.ps1. For browser review, start scripts/serve_review.py with the product Python environment and PYTHONPATH=backend, use the dedicated QA Edge profile/CDP 9239, then run web/scripts/experiment-browser-check.mjs and experiment-contrast-check.mjs. The workflow script refuses the user application database. The retained older browser/story reports describe earlier UIs and are not current UI acceptance.

Remaining limitation: no independent novice user study has been performed. Automated completion cannot establish whether a first-time visitor can explain the purpose, choose a sensible experiment, or interpret HOLD versus failed tests without assistance.
