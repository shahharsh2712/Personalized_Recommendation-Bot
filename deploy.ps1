# Local / server deploy helper (Windows PowerShell)
param(
    [switch]$Build,
    [switch]$Up,
    [switch]$Down,
    [switch]$Logs,
    [switch]$PullModel,
    [switch]$Share
)

$Root = $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
    Write-Host "ERROR: .env missing. Copy .env.example to .env and fill in values."
    exit 1
}

if ($PullModel) {
    docker compose exec ollama ollama pull nomic-embed-text
    exit $LASTEXITCODE
}

if ($Build) {
    docker compose build
}

if ($Up) {
    docker compose -f docker-compose.yml -f docker-compose.local.yml up -d mongo web
    Write-Host ""
    Write-Host "App: http://localhost:5000"
    Write-Host "Uses host Ollama at http://localhost:11434"
    Write-Host "Ensure: ollama pull nomic-embed-text"
    Write-Host "Load data: docker compose exec web python reembed_with_ollama.py"
}

if ($Down) {
    docker compose down
}

if ($Logs) {
    docker compose logs -f web
}

if ($Share) {
    & "$Root\share.ps1"
    exit $LASTEXITCODE
}

if (-not ($Build -or $Up -or $Down -or $Logs -or $PullModel -or $Share)) {
    Write-Host "Usage:"
    Write-Host "  .\deploy.ps1 -Build -Up     # build and start"
    Write-Host "  .\deploy.ps1 -PullModel     # download Ollama embedding model"
    Write-Host "  .\deploy.ps1 -Logs          # follow web logs"
    Write-Host "  .\deploy.ps1 -Down          # stop all services"
    Write-Host "  .\deploy.ps1 -Share         # public HTTPS link (Cloudflare tunnel)"
    Write-Host ""
    Write-Host "Always-on + free: see DEPLOY-FREE.md (Oracle Cloud)"
}
