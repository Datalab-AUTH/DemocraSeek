[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$composeFile = Join-Path $projectRoot "deployment\docker-compose.yml"
$envFile = Join-Path $projectRoot ".env"

if (-not (Test-Path -LiteralPath $envFile)) {
    throw ".env is missing."
}

Push-Location $projectRoot
try {
    Write-Host "[DemocraSeek] Stopping application containers" -ForegroundColor Cyan
    docker compose -f $composeFile --env-file $envFile stop
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose could not stop the application."
    }
    Write-Host "DemocraSeek stopped. The database and index were preserved." -ForegroundColor Green
}
finally {
    Pop-Location
}
