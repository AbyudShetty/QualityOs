param(
    [ValidateSet('serve','init','evaluate')][string]$Mode='serve',
    [ValidateRange(1024,65535)][int]$Port=8107
)
$ErrorActionPreference='Stop'
$ProductRoot=$PSScriptRoot
$PythonPath=Join-Path $ProductRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $PythonPath)) { throw 'Create the product-local Python environment first. See README.md.' }
if ($Mode -eq 'serve' -and -not (Test-Path -LiteralPath (Join-Path $ProductRoot 'web/dist/index.html'))) { throw 'Build the frontend first with npm run build in qualityos/web.' }
$PreviousPythonPath=$env:PYTHONPATH
try {
    $env:PYTHONPATH=Join-Path $ProductRoot 'backend'
    if ($Mode -eq 'serve') { Write-Host "Starting QualityOS at http://127.0.0.1:$Port/start. Keep this terminal open; Ctrl+C stops the server." }
    & $PythonPath -m qualityos $Mode --port $Port
    if ($LASTEXITCODE -ne 0) { throw "QualityOS exited with code $LASTEXITCODE" }
} finally { $env:PYTHONPATH=$PreviousPythonPath }
