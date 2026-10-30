$ErrorActionPreference='Stop'
$ProductRoot=$PSScriptRoot
$PythonPath=Join-Path $ProductRoot '.venv/Scripts/python.exe'
$PreviousPythonPath=$env:PYTHONPATH
$EvidenceDir=Join-Path $ProductRoot ('var/check-runs/'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null
Push-Location $ProductRoot
try {
    $env:PYTHONPATH=Join-Path $ProductRoot 'backend'
    & $PythonPath -m pytest -o 'addopts=' -q "--junitxml=$EvidenceDir/backend.xml"
    if ($LASTEXITCODE -ne 0) { throw 'Backend checks failed' }
    Push-Location (Join-Path $ProductRoot 'web')
    try {
        & npm.cmd test -- --reporter=json "--outputFile=$EvidenceDir/frontend.json"
        if ($LASTEXITCODE -ne 0) { throw 'Frontend tests failed' }
        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' }
    } finally { Pop-Location }
    & $PythonPath scripts/export_contracts.py
    if ($LASTEXITCODE -ne 0) { throw 'Contract generation failed' }
    [xml]$BackendResult=Get-Content -LiteralPath (Join-Path $EvidenceDir 'backend.xml') -Raw
    $FrontendResult=Get-Content -LiteralPath (Join-Path $EvidenceDir 'frontend.json') -Raw | ConvertFrom-Json
    $Report=[ordered]@{
        completed_at=[DateTime]::UtcNow.ToString('o')
        basis='Executed product checks; synthetic software only'
        backend=@{tests=[int]$BackendResult.testsuites.testsuite.tests; failures=[int]$BackendResult.testsuites.testsuite.failures; errors=[int]$BackendResult.testsuites.testsuite.errors}
        frontend=@{tests=$FrontendResult.numTotalTests; passed=$FrontendResult.numPassedTests; failed=$FrontendResult.numFailedTests}
        typescript_and_build='PASSED'
        contract_generation='PASSED'
        python_warning='One existing Starlette multipart import PendingDeprecationWarning; no test failure'
    }
    $Report | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $ProductRoot 'docs/validation/checks.json') -Encoding UTF8
} finally { Pop-Location; $env:PYTHONPATH=$PreviousPythonPath }
