# QualityOS

A local, persisted quality evidence and decision prototype. A packaging change makes old qualification inapplicable; the affected run holds until fresh, reliable, independent verification and explicit QA authorization permit bounded simulated continuation.

Four connected workspaces use one backend: Line, Evidence, Qualification and Investigation. The product includes exact and approved-envelope scope, measurement-time reference checks, delayed functional results, investigation/action verification, immutable historical decisions, late correction impact, role restrictions, idempotency and atomic production checks.

(imp) All supplied observations, suppliers, products and produced units are synthetic. This application does not control equipment, establish package safety, authorize commercial release or demonstrate factory savings.

## Open the local product

If the service is already running, open [Start here](http://127.0.0.1:8107/start). Choose Start the guided story to follow a fictional cap-delivery change with one explained next action at a time. Saved progress resumes from backend evidence, including after a reload. You can also open an unguided workspace or hide the guide and explore the four operational screens.

Otherwise run:

```powershell
Set-Location 'C:/ABYUD/HACKATHONS/LOREAL/qualityos'
.\start.ps1
```

Keep that terminal running. Stop its server with Ctrl+C. Start again with the same command to retain workspaces, audit, accounts and history. Do not delete a database to reset a demonstration; use New workspace.

On first launch the backend generates random private credentials in `var/local-credentials.json`. Open that file privately on this device and sign in as `qa` for the complete workflow. `operator`, `viewer` and `admin` demonstrate different permissions. ADMIN cannot sign QA authorizations. Passwords are not printed by setup or returned through the API. The display names are fictional demo actors.

## Setup on a fresh environment

Tested here: Python 3.10.0, Node 25.2.0, npm 11.19.0, FastAPI 0.111.0, SQLAlchemy 2.0.43, React 19.3.1, TypeScript 7.0.2 and Vite 8.3.4. Exact Python runtime/verification dependencies and npm dependencies are locked.

```powershell
Set-Location 'C:/ABYUD/HACKATHONS/LOREAL/qualityos'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
Set-Location web
npm ci
npm run build
Set-Location ..
.\start.ps1
```

Fresh online installation was not verified in this restricted execution environment: external package downloads were blocked. The working local build uses a product-local Python environment with read access to installed system packages, plus locally restored, version-verified npm dependencies. No global packages were changed and no other project's application code is a runtime dependency. See ADR-008 in [DECISIONS.md](docs/DECISIONS.md) for the exact fallback and its isolation limitation. Do not recreate the working environment merely to view the demo.

The built frontend and API share port 8107. For frontend development, run `npm run dev` from `web` in a separate terminal; Vite uses 5177 and proxies `/api` to 8107. Local fonts are bundled; no CDN or external account is needed.

## Verify and demonstrate

```powershell
.\verify.ps1
.\start.ps1 -Mode evaluate
```

The first command runs backend checks, frontend tests, TypeScript/build and isolated contract generation. The second persists the independent synthetic comparison in the current store. Open Line → Independent evaluation to run and inspect it through the UI.

- [Walkthrough: change, hold, investigate, verify, authorize](docs/WALKTHROUGH.md).
- [First-visit story, design decisions and executed checks](docs/UX_GUIDED_STORY.md).
- [Executed validation, invariant mapping and limitations](docs/VALIDATION.md).
- [Architecture, API contracts, migrations and recovery](docs/OPERATIONS.md).
- [Implementation milestones](docs/PLAN.md) and [decision record](docs/DECISIONS.md).
- [User-run Git commands](docs/GIT_SETUP.md).

Source code is under `backend/qualityos` and `web/src`. Small reviewed results are under `docs/validation`; private databases, credentials, raw browser screenshots, test stores and browser profiles remain in ignored `var`. Handoff and research remain outside the product. The original PDF is currently missing locally; the published case was reread and the gap is documented in [SOURCE_STATUS.md](docs/SOURCE_STATUS.md). The original expected hashes remain in [SOURCE_MANIFEST.json](docs/SOURCE_MANIFEST.json).

Optional TareTruth, physical/bench adapters, industrial connectors, cloud deployment, final competition slide and resume changes are outside this completed core. Competition eligibility, current submission rules and manufacturer adoption remain unverified by this software work.
