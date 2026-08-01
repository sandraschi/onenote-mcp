Param([switch]$Headless)
$ErrorActionPreference = "Stop"
$SkipFrontend = $Headless

# --- SOTA Headless Standard ---
if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
    Start-Process pwsh -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden
    exit
}
$WindowStyle = if ($Headless) { 'Hidden' } else { 'Normal' }
# ------------------------------

$env:FASTMCP_LOG_LEVEL = 'WARNING'
$BackendPort = 10907
$FrontendPort = 10906

Write-Host 'Starting onenote-mcp...' -ForegroundColor Cyan
Set-Location $PSScriptRoot

# Clear port zombies before binding
Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

# Launch backend hidden
Start-Process pwsh -ArgumentList '-NoProfile', '-Command', 'uv run -m onenote_mcp --http' -WindowStyle Hidden

# Readiness poll (TCP, not fixed sleep)
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:$BackendPort/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction SilentlyContinue
        if ($r.StatusCode -eq 200) { $ready = $true; break }
    } catch { }
    Start-Sleep -Seconds 1
}
if ($ready) { Write-Host "Backend ready on :$BackendPort" -ForegroundColor Green }
else { Write-Host "WARNING: backend not healthy after 60s" -ForegroundColor Yellow }

if ($SkipFrontend) { return }

Set-Location web_sota
Start-Process "http://127.0.0.1:$FrontendPort"
npm run dev
