# First-visit and guided-story improvement

User finding: the four operational screens did not explain the product's purpose or give an unfamiliar visitor a clear starting point. Technical completeness did not establish usability.

Implementation scope:

- A Start here page explains the packaging problem with a bottle/cap story before asking visitors to interpret specialist screens.
- A new guided workspace is explicitly created without changing an existing workspace. Its guide identity is persisted with the initial event.
- The backend derives the current story step from actual saved observations, studies, actions, holds, permits and units. There is no browser-owned approval or click-based completion counter.
- One explained next action opens the existing validated form. Demonstration inputs/results are declared synthetic, editable and reviewed before recording; QA signatures remain explicit.
- Plain-language purpose, manufacturing terms, progress, result recap and recoverable deviations accompany the existing four workspaces. Manual exploration remains available.
- Reload, historical/control views, role restrictions, offline/stale state and alternative/failing evidence must not fabricate progress or clear a gate.

Acceptance: a visitor can explain the problem from the start screen, launch and finish the guided scenario without a written external walkthrough, resume from stored state, understand why production pauses and distinguish evidence readiness from QA permission. Validate functional navigation in a real browser at desktop/mobile sizes. Developer checks do not substitute for a subsequent first-time-user study.

## Implemented experience

The root URL opens Start here. The opening question is “The cap changed. Should the line keep running?” A simple package illustration distinguishes earlier covered C01 evidence from the new C02 delivery. Three short sections explain noticing the change, checking the proof and justifying continuation. No scenario-code selection is required to begin the guided story.

Five chapters accompany the same four workspaces: Before the change, A new delivery, A number is not proof, Test a better condition, and Earn permission again. Each step describes what happened, why its next move matters and what change to look for. The primary action opens a reviewed real form; technical demonstration inputs are available in an optional expansion. Each page has a plain-language purpose, and a glossary explains lot, closure, scope, qualification, hold, instrument reference, torque, QA and replay time.

Users can compare the independent line, hide/restore the guide, open historical records, resume from saved state and inspect the evidence behind the final decision. Existing workspaces are not converted or reset. The final recap uses actual saved unit counts and explicitly limits its conclusion to a software demonstration.

## Executed checks

- 58 backend tests passed, including five new story-focused integration tests: full expected order, read/replay preservation, new-app resume and role guards, an alternate functional outcome, bounded scenario creation, nonconforming edited readings, completed-run stability and later five-unit impact. Several assertions share a test journey; these are not separate factory trials.
- TypeScript/build and the existing three frontend tests passed. The original 16-check browser workflow still passes.
- A dedicated browser profile's cookies/local storage were cleared to test a fresh visit. The story browser script passed 11 checks, including actual login, orientation, no unexplained scenario selector, all 24 reviewed commands, control comparison, reload/resume, hide/restore, mobile layout and the final evidence link.
- The story contrast screen found no failures among 1,347 text elements across Start here and the four current guided page states. This checks computed solid colors, not every possible state or complete WCAG compliance.

Reviewed results: [story-browser.json](validation/story-browser.json), [contrast-story.json](validation/contrast-story.json), [checks.json](validation/checks.json). Screenshots: [first visit](validation/screenshots/story-start.png), [guided step](validation/screenshots/story-step.png), [recap](validation/screenshots/story-complete.png), [mobile first visit](validation/screenshots/story-mobile.png).

Reproduce with the local app and an owned QA browser on CDP port 9239:

```powershell
node web/scripts/story-browser-check.mjs
$env:QUALITYOS_CONTRAST_STORY='1'
node web/scripts/contrast-check.mjs
```

The first script resets only that dedicated test browser's cookies/local storage, then creates a clearly named Browser QA workspace. It never clears application history or a personal browser profile. All scenario actions still enter the real API. Raw artifacts are kept in ignored `var/story-review`.

The user's initial confusion is real qualitative feedback. The revised experience has functional/content/visual validation; whether unfamiliar users reliably understand it remains a question for a subsequent observed user session. No guaranteed comprehension, operator-error reduction or manufacturing benefit is inferred from these checks.
