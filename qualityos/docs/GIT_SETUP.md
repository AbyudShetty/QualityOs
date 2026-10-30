# Version control — commands for the user

No Git command has been executed by the assistant. The user owns all Git operations, including inspection commands.

Recommended repository root: `C:/ABYUD/HACKATHONS/LOREAL`. Keep the product, source case and research together; do not initialise another repository inside `qualityos`.

Implementation is now authorized and the core has been built. Repository status has not been inspected with Git. If this folder is already a repository, use it. If it has never been initialized, run `git init -b main` here yourself before the commands below. No remote or public publishing is required.

## Review and checkpoint the implemented product

Run these yourself in PowerShell:

```powershell
Set-Location 'C:/ABYUD/HACKATHONS/LOREAL'
git status --short
git diff --check
git add -- .gitignore .gitattributes AGENTS.md README.md qualityos
git diff --cached --stat
git diff --cached --check
git diff --cached
```

Review the staged content before committing. Credentials, local databases, dependency folders and generated builds are excluded by `.gitignore`; no blanket `git add .` is needed. Never force-add `var` or `.venv`.

The current root ignore file explicitly excludes the copied handoff, reassessment and research folders. That existing setting was preserved. The commands above therefore checkpoint product source and its source-integrity manifest, without force-adding those folders. If you choose to version the research as well, review that ignore policy yourself. The PDF is binary and does not render as a textual diff.

Then, if the staged contents are correct:

```powershell
git commit -m "Build and validate the local QualityOS core"
```

If Git asks for identity configuration, use your preferred existing identity; no name/email or global configuration is chosen by the assistant.

## Optional branch for subsequent work

After the completed checkpoint, an optional branch for later work is:

```powershell
git switch -c feature/qualityos-next
```

No branch has been created by the assistant. Scope any optional adapter separately from the completed core.

## Future checkpoints

After a coherent milestone passes its actual checks, the assistant should report changed paths, commands/results and limitations, and supply an explicit staging/review/commit command for you. Suggested checkpoint subjects:

- `Add scoped quality decision engine`
- `Persist guarded quality workflows and sessions`
- `Complete qualification recovery and historical reassessment`
- `Connect four QualityOS workspaces`
- `Validate replay permissions and independent baselines`
- `Polish and document the local QualityOS demo`

These are proposed future commits, not existing achievements. The assistant does not run Git, create commits through libraries, push, manipulate `.git` or change branches. Do not use hard resets or cleanup operations to repair implementation mistakes; preserve user changes and inspect the actual conflict.
