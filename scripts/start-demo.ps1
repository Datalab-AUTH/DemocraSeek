[CmdletBinding()]
param(
    [switch]$Build,
    [switch]$NoBrowser
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
    throw ".env is missing. Copy .env.example to .env before starting the demo."
}
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker Desktop is not installed or docker is not available on PATH."
}

$frontendPort = Get-EnvValue "FRONTEND_HOST_PORT"
$backendPort = Get-EnvValue "BACKEND_HOST_PORT"
if ([string]::IsNullOrWhiteSpace($frontendPort)) { $frontendPort = "8080" }
if ([string]::IsNullOrWhiteSpace($backendPort)) { $backendPort = "8000" }
$appUrl = "http://localhost:$frontendPort"
$readyUrl = "http://localhost:$backendPort/api/ready"

$localModelSettings = @(
    @{ Url = Get-EnvValue "LLM_BASE_URL"; Model = Get-EnvValue "LLM_MODEL" },
    @{ Url = Get-EnvValue "EMBEDDING_BASE_URL"; Model = Get-EnvValue "EMBEDDING_MODEL" }
)
if ((Get-EnvValue "VISION_PROVIDER") -ne "none") {
    $localModelSettings += @{
        Url = Get-EnvValue "VISION_BASE_URL"
        Model = Get-EnvValue "VISION_MODEL"
    }
}
$localModels = @(
    $localModelSettings |
        Where-Object { Test-LocalOllamaUrl $_.Url } |
        ForEach-Object { $_.Model } |
        Where-Object { $_ } |
        Select-Object -Unique
)

if ($localModels.Count -gt 0) {
    Write-Step "Checking local Ollama"
    if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
        throw "The configured provider uses local Ollama, but ollama is not available on PATH."
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
        throw "Required Ollama model(s) are missing:`n$pullCommands"
    }
    Write-Host "[       OK] Ollama and required local models are ready" -ForegroundColor Green
}
else {
    Write-Host "[     INFO] FILOS endpoints are remote; local Ollama check skipped" -ForegroundColor Yellow
}

Write-Step "Checking Docker Desktop"
if (-not (Test-Docker)) {
    $dockerDesktop = Join-Path $env:ProgramFiles "Docker\Docker\Docker Desktop.exe"
    if (-not (Test-Path -LiteralPath $dockerDesktop)) {
        throw "Docker Desktop is installed but its engine is not running. Open Docker Desktop and run start-demo.cmd again."
    }
    Start-Process -FilePath $dockerDesktop -WindowStyle Hidden
    Wait-Until -TimeoutSeconds 120 -Description "Docker Desktop" -Condition { Test-Docker }
}
Write-Host "[       OK] Docker is ready" -ForegroundColor Green

Push-Location $projectRoot
try {
    Write-Step "Validating configuration"
    docker compose -f $composeFile --env-file $envFile config --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose configuration is invalid."
    }

    Write-Step "Starting the application"
    $composeArguments = @("compose", "-f", $composeFile, "--env-file", $envFile, "up", "-d")
    if ($Build) {
        $composeArguments += "--build"
    }
    & docker $composeArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose could not start the application."
    }

    Write-Step "Waiting for the indexed corpus and API"
    $lastReadiness = "No response received."
    $deadline = (Get-Date).AddMinutes(5)
    $isReady = $false
    do {
        try {
            $responseText = (& curl.exe --silent --max-time 5 $readyUrl) -join ""
            if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($responseText)) {
                $readiness = $responseText | ConvertFrom-Json
                $lastReadiness = $responseText
                if ($readiness.status -eq "ready") {
                    $isReady = $true
                    break
                }
            }
        }
        catch {
            $lastReadiness = $_.Exception.Message
        }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)

    if (-not $isReady) {
        docker compose -f $composeFile --env-file $envFile ps
        throw "The application started but is not ready. Last readiness response: $lastReadiness"
    }

    Write-Host ""
    Write-Host "DemocraSeek is ready: $appUrl" -ForegroundColor Green
    Write-Host "To stop it later, run: .\stop-demo.cmd"

    if (-not $NoBrowser) {
        Start-Process $appUrl
    }
}
finally {
    Pop-Location
}
