# Expose http://localhost:5000 as a public HTTPS link (free Cloudflare quick tunnel).
# Your PC must stay on and Docker must be running (.\deploy.ps1 -Up).
param(
    [int]$Port = 5000
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

$cloudflared = Join-Path $Root "tools\cloudflared.exe"
if (-not (Test-Path $cloudflared)) {
    Write-Host "Downloading cloudflared..."
    New-Item -ItemType Directory -Force -Path (Join-Path $Root "tools") | Out-Null
    $url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    Invoke-WebRequest -Uri $url -OutFile $cloudflared -UseBasicParsing
}

try {
    $code = (Invoke-WebRequest -Uri "http://localhost:$Port/" -UseBasicParsing -TimeoutSec 5).StatusCode
} catch {
    Write-Host "ERROR: Nothing is listening on http://localhost:$Port"
    Write-Host "Start the app first: .\deploy.ps1 -Up"
    exit 1
}
if ($code -ne 200) {
    Write-Host "WARN: localhost:$Port returned HTTP $code"
}

Write-Host ""
Write-Host "Starting public tunnel (Ctrl+C to stop)..."
Write-Host "Copy the https://....trycloudflare.com URL from the output below and share it."
Write-Host ""

& $cloudflared tunnel --url "http://localhost:$Port"
