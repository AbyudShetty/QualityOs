# QualityOS · application guide

QualityOS checks whether packaging qualification evidence still applies after a bottle, cap, supplier or machine-setup change. The local application connects scope comparison, fresh testing, investigation, QA review and guarded simulated continuation in one persisted workflow.

For the product overview and screenshots, see the [repository README](../README.md). For the recommended first run, follow the [current packaging-change demonstration](docs/DEMO_2026-11-02.md).

## Start in the configured workspace

From the repository root:

```powershell
npm start
```

Open **[http://127.0.0.1:8107/start](http://127.0.0.1:8107/start)**, sign in and choose **Inspect a packaging change**. Start with the original tested configuration, then explicitly change the cap/supplier to see the evidence gap and next required action.

The launcher builds the React frontend and starts the Python backend serving both the UI and API. Keep the terminal open. Stop with **Ctrl+C**; restart with the same command to retain saved work. A browser refresh does not load changed Python code, so stop an older server before launching an updated version.

At the repository root, `npm run dev` aliases this complete launch and does not enable hot reload. No root-level dependency installation is required in the already configured workspace.

## Local sign-in

On first backend launch, setup creates random private passwords in `qualityos/var/local-credentials.json`. Read that file privately on your device; do not publish or commit it.

| Account | Purpose |
|---|---|
| `qa` | Complete the demonstration, including quality review, hold resolution and bounded permission |
| `operator` | Record observations, propose changes and execute approved work; cannot sign QA permissions |
| `viewer` | Inspect saved experiments and history without changing them |
| `admin` | Local administrative functions; does not automatically receive QA signing authority |

The display names are fictional demonstration actors. Passwords are not included in the documentation or returned through the API.

## Install dependencies on a fresh environment

The tested development environment uses **Python 3.10.0**, **Node 25.2.0** and **npm 11.19.0**. These are observed versions, not a claim of compatibility with every Python/Node release. Python dependencies are pinned in `requirements.lock.txt`; frontend dependencies are pinned in `web/package-lock.json`.

From the repository root in PowerShell:

```powershell
Set-Location qualityos
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
Set-Location web
npm ci
Set-Location ../..
npm start
```

Clean online installation has not been verified in this restricted environment. The working local Python environment exposes existing system packages through `--system-site-packages`; frontend packages were restored locally and version-checked. No global packages were changed. See **ADR-008** in the [decision log](docs/DECISIONS.md) for the tested fallback and its isolation limits. Do not recreate the working environment simply to view the application.

## Develop locally

Use two terminals from the product directory, `qualityos`.

**Backend**, after a frontend build exists:

```powershell
.\start.ps1
```

**Frontend with Vite development updates**, in the other terminal:

```powershell
Set-Location web
npm run dev
```

Vite serves `http://127.0.0.1:5177` and proxies `/api` to the backend on port `8107`. The built application uses port `8107` for both frontend and API. Fonts are bundled locally; opening the demo needs no external account or CDN.

To build only the frontend from the repository root:

```powershell
npm run build
```

The backend also accepts an alternate local port, for example `.\start.ps1 -Port 8114`, when running from `qualityos`. The Vite proxy remains configured for `8107` unless explicitly changed.

## Verify the implementation

From `qualityos`:

```powershell
.\verify.ps1
```

This runs backend tests, frontend tests, TypeScript/build and isolated contract generation, and updates local validation outputs. The latest [recorded verification](docs/validation/review-remediation/summary.json) reports **94 backend tests**, **8 frontend tests** and **13 real-browser checks**. The browser checks run separately against an isolated test database; the [engineering handoff](docs/REVIEW_HANDOFF_2026-11-02.md) explains their scope and reproduction.

To execute and persist the declared synthetic comparison in the current application store:

```powershell
.\start.ps1 -Mode evaluate
```

Inspect its results under **Production setup → Independent evaluation**. The comparator is a limited separately specified synthetic checklist, not a tested commercial system or validated industrial SOP. API documentation is available at `http://127.0.0.1:8107/docs` while the backend is running.

## State and history

SQLite stores experiments, evidence, decisions, audit records and simulated units under ignored `var`. Restarting preserves these records. To try another condition, create a new experiment instead of deleting a database.

Historical decisions remain read-only. Later corrections and reference withdrawals change current implications while retaining the original records. Export experiment provides the complete workspace record; the on-screen history/link views are explicitly bounded. See [operations](docs/OPERATIONS.md) before backup, migration or recovery work.

## Current documentation

| Document | Use |
|---|---|
| [Current demonstration](docs/DEMO_2026-11-02.md) | Recommended entry, exact inputs, expected decisions and failure/recovery route |
| [Engineering handoff](docs/REVIEW_HANDOFF_2026-11-02.md) | Current behavior, review corrections and remaining limits |
| [Architecture and operations](docs/OPERATIONS.md) | API, transactions, persistence, roles and recovery |
| [Validation](docs/VALIDATION.md) | Executed results and historical validation records |
| [Decisions](docs/DECISIONS.md) | Architectural choices and documented trade-offs |
| [Repository setup](docs/GIT_SETUP.md) | Repository boundary and user-run Git instructions |

The root user manual and visual PDF are retained historical guides; their screenshots predate the focused packaging-change panel. Use the current demonstration above for the implemented interface.

## Demonstration boundary

All products, suppliers, observations and units are synthetic. Test outcomes are supplied inputs; torque does not predict the leak result. Sample counts, limits, dwell and error bounds are illustrative assumptions. Software verification establishes behavior within that declared scope, not physical package safety, factory savings, industrial adoption or commercial release authority.

The current scope is one packaging-change workflow. Additional manufacturing modules, physical adapters, industrial connectors and public deployment are deferred.
