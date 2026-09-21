$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$apiRoot = Join-Path $projectRoot "apps/api"
$webRoot = Join-Path $projectRoot "apps/web"
$python = Join-Path $apiRoot ".venv/Scripts/python.exe"
$ruff = Join-Path $apiRoot ".venv/Scripts/ruff.exe"
$mypy = Join-Path $apiRoot ".venv/Scripts/mypy.exe"

if (-not (Test-Path $python)) {
    throw "Python environment is missing. Run .\scripts\bootstrap.ps1 first."
}

Push-Location $apiRoot
try {
    & $python -m pytest
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $ruff check . (Join-Path $projectRoot "scripts")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $ruff format --check . (Join-Path $projectRoot "scripts")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $mypy src
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

Push-Location $webRoot
try {
    npm run lint
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    npm run build
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

Write-Host "All Docflow checks passed."
