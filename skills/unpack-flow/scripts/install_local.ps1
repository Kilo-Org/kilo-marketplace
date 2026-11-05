[CmdletBinding()]
param(
    [Parameter(Position = 0)] [string]$Source = (Split-Path $PSScriptRoot -Parent),
    [string]$CodexHome,
    [switch]$Replace,
    [switch]$SkipAudit
)
$ErrorActionPreference = 'Stop'
$sourcePath = (Resolve-Path $Source).Path
$skillFile = Join-Path $sourcePath 'SKILL.md'
if (-not (Test-Path $skillFile -PathType Leaf)) { throw "Invalid Skill source: $sourcePath" }
$skillText = Get-Content $skillFile -Raw -Encoding UTF8
$nameMatch = [regex]::Match($skillText, '(?m)^name:\s*([a-z0-9-]+)\s*$')
if (-not $nameMatch.Success) { throw 'SKILL.md has no valid hyphen-case name.' }
$skillName = $nameMatch.Groups[1].Value
if ((Split-Path $sourcePath -Leaf) -ne $skillName) { throw "Folder name does not match Skill name: $skillName" }
if (-not $CodexHome) {
    if ($env:CODEX_HOME) { $CodexHome = $env:CODEX_HOME } else { $CodexHome = Join-Path $HOME '.codex' }
}
$skillsRoot = Join-Path ([System.IO.Path]::GetFullPath($CodexHome)) 'skills'
$target = Join-Path $skillsRoot $skillName
New-Item -ItemType Directory -Path $skillsRoot -Force | Out-Null
$backup = $null
if (Test-Path $target) {
    if (-not $Replace) { [Console]::Error.WriteLine("FAIL: installation already exists: $target"); exit 3 }
    $stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
    $backup = Join-Path $skillsRoot "$skillName.backup-$stamp"
    if (Test-Path $backup) { throw "Backup path already exists: $backup" }
    Move-Item -LiteralPath $target -Destination $backup
}
$staging = Join-Path $skillsRoot ".$skillName.installing-$PID"
try {
    New-Item -ItemType Directory -Path $staging | Out-Null
    Get-ChildItem -LiteralPath $sourcePath -Force | Where-Object { $_.Name -notin @('.git', '__pycache__') } | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $staging -Recurse -Force
    }
    Get-ChildItem -LiteralPath $staging -Recurse -Force -File | Where-Object { $_.Extension -eq '.pyc' } | ForEach-Object {
        Remove-Item -LiteralPath $_.FullName -Force -Confirm:$false
    }
    Get-ChildItem -LiteralPath $staging -Recurse -Force -Directory | Where-Object { $_.Name -eq '__pycache__' } | Sort-Object { $_.FullName.Length } -Descending | ForEach-Object {
        Remove-Item -LiteralPath $_.FullName -Recurse -Force -Confirm:$false
    }
    Move-Item -LiteralPath $staging -Destination $target
} catch {
    if (Test-Path $staging) { Remove-Item -LiteralPath $staging -Recurse -Force -Confirm:$false }
    if ($backup -and (Test-Path $backup) -and -not (Test-Path $target)) { Move-Item -LiteralPath $backup -Destination $target }
    throw
}
if (-not $SkipAudit) {
    & (Join-Path $target 'scripts/audit_skill.ps1') -Skill $target
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
Write-Output "INSTALLED: $target"
if ($backup) { Write-Output "BACKUP: $backup" }
