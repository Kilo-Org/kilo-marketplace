[CmdletBinding()]
param([string]$Engine = (Join-Path (Split-Path -Parent $PSScriptRoot) 'scripts/unpack-flow.ps1'))

$ErrorActionPreference = 'Stop'
$root = Join-Path ([IO.Path]::GetTempPath()) "unpack-flow-input-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Path $root | Out-Null
try {
    foreach ($name in @(
        'bundle.zip', 'bundle.zip.sha256',
        'data.part1.exe', 'data.part2.rar', 'data.part03.rar',
        'set.part01.rar', 'set.part02.rar',
        'split.7z.001', 'split.7z.002',
        'numbered.zip.001', 'numbered.zip.002',
        'classic.rar', 'classic.r00', 'notes.txt'
    )) {
        New-Item -ItemType File -Path (Join-Path $root $name) | Out-Null
    }

    $expanded = @(Get-ChildItem -LiteralPath $root | ForEach-Object FullName)
    $output = @(& pwsh -NoLogo -NoProfile -File $Engine list @expanded 2>&1 | Out-String)
    if ($LASTEXITCODE -ne 0) { throw "list failed: $output" }

    foreach ($expected in @('bundle.zip','data.part1.exe','set.part01.rar','split.7z.001','numbered.zip.001','classic.rar')) {
        if ($output -notmatch [regex]::Escape($expected)) { throw "missing entry volume: $expected`n$output" }
    }
    foreach ($unexpected in @('bundle.zip.sha256','data.part2.rar','data.part03.rar','set.part02.rar','split.7z.002','numbered.zip.002','classic.r00','notes.txt')) {
        if ($output -match [regex]::Escape($unexpected)) { throw "unexpected continuation/non-archive: $unexpected`n$output" }
    }
    Write-Output 'PowerShell input normalization: PASS'
} finally {
    Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
