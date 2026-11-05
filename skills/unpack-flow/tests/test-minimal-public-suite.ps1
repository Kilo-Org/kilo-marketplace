#requires -Version 5.1
[CmdletBinding()]
param([string]$Suite)
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
$engine = Join-Path $project 'scripts/unpack-flow.ps1'
if (-not $Suite) { $Suite = Join-Path $project 'dist/unpack-flow-minimal-testcases-v1.zip' }
if (-not (Test-Path -LiteralPath $Suite -PathType Leaf)) { throw "Fixture not found: $Suite" }
$root = Join-Path ([IO.Path]::GetTempPath()) "unpack-flow-minimal-$([guid]::NewGuid().ToString('N'))"
try {
    New-Item -ItemType Directory -Path $root | Out-Null
    & $engine run $Suite -r -Output $root
    $markers = @(Get-ChildItem -LiteralPath $root -Filter EXPECTED.txt -File -Recurse)
    $inertExe = @(Get-ChildItem -LiteralPath $root -Filter demo.EXE -File -Recurse)
    if ($markers.Count -lt 6) { throw "Expected at least 6 markers, got $($markers.Count)" }
    if ($inertExe.Count -lt 5) { throw "Expected at least 5 inert EXE files, got $($inertExe.Count)" }
    $firstVolumes = @(Get-ChildItem -LiteralPath $root -File -Recurse | Where-Object { $_.Name -match '(?i)\.part0*1\.exe$' })
    if ($firstVolumes.Count -lt 1) { throw 'Multipart SFX first volume was not preserved in expected-failure case' }
    'Minimal public suite PowerShell: PASS'
} finally {
    if (Test-Path -LiteralPath $root) { Remove-Item -LiteralPath $root -Recurse -Force }
}
