param([string]$RepoRoot)
$ErrorActionPreference = "Stop"
Set-Location $RepoRoot
New-Item -ItemType Directory -Force -Path dist | Out-Null

$proj = Get-Content pyproject.toml -Raw
$name = if ($proj -match '(?m)^name = "(.*)"') { $matches[1] } else { Split-Path -Leaf $PWD }
$ver = if ($proj -match '(?m)^version = "(.*)"') { $matches[1] } else { "0.1.0" }
$pkg = $name -replace '-', '_'

Write-Host "=== $name MCPB pack (fresh-stage) ===" -ForegroundColor Cyan

# Step 1: fresh-stage src/<pkg> -> mcpb/src/<pkg> (MCPB_PACKAGING_STANDARDS: wipe+recopy)
$srcPkg = Join-Path $RepoRoot "src\$pkg"
$dstPkg = Join-Path $RepoRoot "mcpb\src\$pkg"
if (-not (Test-Path $srcPkg)) { throw "Source package not found: $srcPkg" }
if (Test-Path (Join-Path $RepoRoot "mcpb\src")) { Remove-Item (Join-Path $RepoRoot "mcpb\src") -Recurse -Force }
New-Item -ItemType Directory -Force -Path (Split-Path $dstPkg) | Out-Null
Copy-Item -Path $srcPkg -Destination $dstPkg -Recurse -Force
Get-ChildItem -Path $dstPkg -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    ForEach-Object { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }
Write-Host "  staged src/$pkg -> mcpb/src/$pkg" -ForegroundColor Green

# Step 2: fresh entry point + manifest
if (Test-Path (Join-Path $RepoRoot "run_server.py")) {
    Copy-Item (Join-Path $RepoRoot "run_server.py") (Join-Path $RepoRoot "mcpb\run_server.py") -Force
    Write-Host "  staged run_server.py" -ForegroundColor Green
}
$manifest = Join-Path $RepoRoot "mcpb\manifest.json"
if (-not (Test-Path $manifest)) { throw "mcpb\manifest.json missing" }

# Step 3: import assertion - entry point's top-level import must resolve inside mcpb/src
$assert = @"
import sys, importlib.util as u
sys.path.insert(0, r"$dstPkg\..")
s = u.find_spec("$pkg")
print("origin:", s.origin if s else "NOT FOUND")
assert s and r"mcpb\src" in s.origin, "bundle cannot import itself"
"@
uv run python -c $assert
Write-Host "  import assertion PASSED (origin inside mcpb/src)" -ForegroundColor Green

# Step 4: junk gate
$junk = Get-ChildItem (Join-Path $RepoRoot "mcpb") -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match '\.(pyc|bak)$' -or $_.Name -like '*.bak.*' }
if ($junk) { $junk | ForEach-Object { Remove-Item $_.FullName -Force } ; Write-Host "  purged $($junk.Count) junk files" -ForegroundColor Yellow }
else { Write-Host "  no junk under mcpb/" -ForegroundColor Green }

# Step 5: pack
$out = Join-Path $RepoRoot "dist\$name-v$ver.mcpb"
if (Test-Path $out) { Remove-Item $out -Force }
npx --yes @anthropic-ai/mcpb pack (Join-Path $RepoRoot "mcpb") $out
if (-not (Test-Path $out)) { throw "pack failed - no output at $out" }
$sizeKB = [math]::Round((Get-Item $out).Length / 1KB, 1)
if ((Get-Item $out).Length -lt 10KB) { throw "bundle suspiciously small ($sizeKB KB)" }
Write-Host "Bundle: $out ($sizeKB KB)" -ForegroundColor Green
