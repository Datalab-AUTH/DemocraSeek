[CmdletBinding()]
param(
    [string]$Only,
    [switch]$Force,
    [switch]$Reindex,
    [switch]$Status,
    [switch]$Yes
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$composeFile = Join-Path $projectRoot "deployment\docker-compose.yml"
$envFile = Join-Path $projectRoot ".env"

function Write-Step {
    param([string]$Message)
    Write-Host "[DemocraSeek] $Message" -ForegroundColor Cyan
}

function Get-EnvValue {
    param([string]$Name)

    foreach ($line in Get-Content -LiteralPath $envFile) {
        if ($line -match "^\s*$([regex]::Escape($Name))\s*=\s*(.*)\s*$") {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return ""
}

function Test-Ollama {
    try {
        $null = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 3
        return $true
    }
    catch {
        return $false
    }
}

function Test-LocalOllamaUrl {
    param([string]$Url)
    return $Url -match '^https?://(host\.docker\.internal|localhost|127\.0\.0\.1):11434(?:/|$)'
}

function Test-Docker {
    docker info --format "{{.ServerVersion}}" 2>$null | Out-Null
    return $LASTEXITCODE -eq 0
}

function Wait-Until {
    param(
        [scriptblock]$Condition,
        [int]$TimeoutSeconds,
        [string]$Description
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        if (& $Condition) {
            return
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)

    throw "Timed out waiting for $Description."
}

if (-not (Test-Path -LiteralPath $envFile)) {
    throw ".env is missing. Copy .env.example to .env before ingesting."
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker Desktop is not installed or docker is not available on PATH."
}
if ($Reindex -and -not $Yes) {
    throw "-Reindex rebuilds the whole index from the approved corpus and can take a long time. Re-run as: .\ingest.cmd -Reindex -Yes"
}
if ($Reindex -and ($Only -or $Force)) {
    throw "-Reindex cannot be combined with -Only or -Force. A reindex always rebuilds everything."
}

# Decide the CLI command before touching Docker or Ollama.
if ($Status) {
    $cliArguments = @("status")
    $activity = "Reading corpus status"
}
elseif ($Reindex) {
    $cliArguments = @("reindex", "--yes")
    $activity = "Rebuilding the whole index"
}
else {
    $cliArguments = @("ingest")
    if ($Only) {
        $cliArguments += @("--only", $Only)
    }
    if ($Force) {
        $cliArguments += "--force"
    }
    $activity = "Ingesting the approved corpus"
}

# `status` only reads existing records, so it needs no model endpoint.
$needsModels = -not $Status

if ($needsModels) {
    # Ingestion uses embeddings and optional vision, not answer generation.
    $requiredSettings = @(
        @{ Url = Get-EnvValue "EMBEDDING_BASE_URL"; Model = Get-EnvValue "EMBEDDING_MODEL" }
    )
    if ((Get-EnvValue "VISION_PROVIDER") -ne "none") {
        $requiredSettings += @{
            Url = Get-EnvValue "VISION_BASE_URL"
            Model = Get-EnvValue "VISION_MODEL"
        }
    }
    $localModels = @(
        $requiredSettings |
            Where-Object { Test-LocalOllamaUrl $_.Url } |
            ForEach-Object { $_.Model } |
            Where-Object { $_ } |
            Select-Object -Unique
    )

    if ($localModels.Count -gt 0) {
        Write-Step "Checking local Ollama"
        if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
            throw "Ingestion uses local Ollama, but ollama is not available on PATH."
        }
        if (-not (Test-Ollama)) {
            $ollamaExecutable = (Get-Command ollama -CommandType Application).Source
            Start-Process -FilePath $ollamaExecutable -ArgumentList "serve" -WindowStyle Hidden
            Wait-Until -TimeoutSeconds 45 -Description "local Ollama" -Condition { Test-Ollama }
        }

        $ollamaTags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 5
        $installedModels = @($ollamaTags.models | ForEach-Object { $_.name })

        $missingModels = @()
        foreach ($model in $localModels) {
            $namesToAccept = @($model)
            if ($model -notmatch ":") {
                $namesToAccept += "${model}:latest"
            }
            if (-not ($namesToAccept | Where-Object { $installedModels -contains $_ })) {
                $missingModels += $model
            }
        }
        if ($missingModels.Count -gt 0) {
            $pullCommands = ($missingModels | ForEach-Object { "ollama pull $_" }) -join [Environment]::NewLine
            throw "Ingestion model(s) are missing:`n$pullCommands"
        }
        Write-Host "[       OK] Ollama and the ingestion models are ready" -ForegroundColor Green
    }
    else {
        Write-Host "[     INFO] FILOS endpoints are remote; local Ollama check skipped" -ForegroundColor Yellow
    }
}

Write-Step "Checking Docker Desktop"
if (-not (Test-Docker)) {
    $dockerDesktop = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
    if (-not (Test-Path -LiteralPath $dockerDesktop)) {
        throw "Docker Desktop is installed but its engine is not running. Open Docker Desktop and run ingest.cmd again."
    }
    Start-Process -FilePath $dockerDesktop -WindowStyle Hidden
    Wait-Until -TimeoutSeconds 120 -Description "Docker Desktop" -Condition { Test-Docker }
}
Write-Host "[       OK] Docker is ready" -ForegroundColor Green

Push-Location $projectRoot
try {
    Write-Step $activity
    if (-not $Status) {
        Write-Host "The first run is slow: every kept figure is described by the vision model." -ForegroundColor Yellow
        Write-Host "Do not interrupt it unless necessary." -ForegroundColor Yellow
    }

    # `run` starts the db dependency on its own, so the stack need not be up.
    $composeArguments = @(
        "compose", "-f", $composeFile, "--env-file", $envFile,
        "run", "--rm", "backend", "python", "-m", "app.cli"
    ) + $cliArguments

    & docker $composeArguments
    if ($LASTEXITCODE -ne 0) {
        throw "The CLI command failed. See the output above."
    }

    if (-not $Status) {
        Write-Host ""
        Write-Step "Corpus status after the run"
        docker compose -f $composeFile --env-file $envFile run --rm backend python -m app.cli status

        $reportPath = Join-Path $projectRoot "data\reports"
        Write-Host ""
        Write-Host "Done. The full report was written to: $reportPath" -ForegroundColor Green
        Write-Host "Start or restart the application with: .\start-demo.cmd"
    }
}
finally {
    Pop-Location
}
