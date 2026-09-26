#requires -Version 5.1
$ErrorActionPreference = 'Stop'
$project = Split-Path -Parent $PSScriptRoot
$engine = Join-Path $project 'scripts/unpack-flow.ps1'
$root = Join-Path ([IO.Path]::GetTempPath()) "unpack-flow-recursive-$([guid]::NewGuid().ToString('N'))"
try {
    $source = Join-Path $root 'source'
    $sameName = Join-Path $source 'nested'
    $payload = Join-Path $root 'payload'
    New-Item -ItemType Directory -Path $sameName,$payload | Out-Null
    Set-Content -LiteralPath (Join-Path $payload 'marker.txt') -Value 'recursive pass' -Encoding ASCII
    Compress-Archive -Path (Join-Path $payload 'marker.txt') -DestinationPath (Join-Path $sameName 'nested.zip')

    $listed = (& $engine list (Join-Path $source '*') -r | Out-String)
    if ($listed -notmatch 'nested\.zip') { throw 'recursive list did not discover nested.zip' }

    & $engine run (Join-Path $source '*') -r -Output $source
    if (-not (Test-Path -LiteralPath (Join-Path $source 'nested-unpacked/marker.txt'))) { throw 'recursive collision-safe output missing' }

    $oldVersion = Join-Path $source 'legacy-set'
    New-Item -ItemType Directory -Path $oldVersion | Out-Null
    Compress-Archive -Path (Join-Path $payload 'marker.txt') -DestinationPath (Join-Path $oldVersion 'sample-backup.zip')
    New-Item -ItemType Directory -Path (Join-Path $source 'sample-backup') | Out-Null
    & $engine run (Join-Path $oldVersion 'sample-backup.zip') -r -Output $source
    if (-not (Test-Path -LiteralPath (Join-Path $source 'sample-backup-legacy-set-unpacked/marker.txt'))) { throw 'source-parent collision name missing' }
    & $engine run (Join-Path $oldVersion 'sample-backup.zip') -r -Output $source
    if (-not (Test-Path -LiteralPath (Join-Path $source 'sample-backup-legacy-set-unpacked-2/marker.txt'))) { throw 'numeric collision suffix missing' }
    'PowerShell recursive mode: PASS'
} finally {
    if (Test-Path -LiteralPath $root) { Remove-Item -LiteralPath $root -Recurse -Force }
}
