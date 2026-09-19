$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$apiRoot = Join-Path $projectRoot "apps/api"
$webRoot = Join-Path $projectRoot "apps/web"

Write-Host "Creating Python environment..."
python -m venv (Join-Path $apiRoot ".venv")
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& (Join-Path $apiRoot ".venv/Scripts/python.exe") -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& (Join-Path $apiRoot ".venv/Scripts/python.exe") -m pip install -e "$apiRoot[dev]"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Installing web dependencies..."
Push-Location $webRoot
try {
    npm install
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

Write-Host "Docflow dependencies are ready."
