# Fleet launcher (repo root) - thin delegate to the unified starter.
# All port/backend logic lives in web_sota/start.ps1 + fleet-start.config.ps1.
param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser,
    [switch]$ReuseIfRunning
)

$ErrorActionPreference = 'Stop'
$target = Join-Path $PSScriptRoot 'web_sota' 'start.ps1'
if (-not (Test-Path -LiteralPath $target)) {
    Write-Host "ERROR: Missing web_sota/start.ps1 at $target" -ForegroundColor Red
    exit 1
}
& $target @PSBoundParameters
exit $LASTEXITCODE
