#requires -Version 5.1
[CmdletBinding()]
param([switch]$Check)

$ErrorActionPreference = 'Stop'
$scriptRoot = Split-Path -Parent $PSCommandPath
$sourceRoot = Split-Path -Parent $scriptRoot
$arch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'windows-arm64' } else { 'windows-x64' }
$tool = Join-Path $sourceRoot "tools\$arch\7za.exe"
$unrar = Join-Path $sourceRoot "tools\$arch\UnRAR.exe"
Write-Host "os=Windows"
Write-Host "architecture=$arch"
Write-Host "bundled_seven_zip=$tool"
if ($arch -eq 'windows-x64') { Write-Host "bundled_unrar=$unrar" }
if (-not (Test-Path -LiteralPath $tool -PathType Leaf)) {
    Write-Host 'status=missing_bundled_tool'
    Write-Host 'install_command=winget install --id 7zip.7zip --exact'
    exit 2
}
if ($arch -eq 'windows-x64' -and -not (Test-Path -LiteralPath $unrar -PathType Leaf)) {
    Write-Host 'status=missing_bundled_unrar'
    exit 2
}
if ($Check) { Write-Host 'status=ready'; exit 0 }

$installRoot = Join-Path $env:LOCALAPPDATA 'unpack-flow'
$binDir = Join-Path $env:USERPROFILE '.local\bin'
New-Item -ItemType Directory -Force -Path $installRoot,$binDir | Out-Null
Copy-Item -LiteralPath (Join-Path $scriptRoot 'unpack-flow.ps1') -Destination $installRoot -Force
Copy-Item -LiteralPath (Join-Path $sourceRoot 'tools') -Destination $installRoot -Recurse -Force
$cmd = "@echo off`r`npowershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File `"$installRoot\unpack-flow.ps1`" %*`r`n"
[IO.File]::WriteAllText((Join-Path $binDir 'unpack-flow.cmd'), $cmd, [Text.Encoding]::ASCII)
$userPath = [Environment]::GetEnvironmentVariable('Path','User')
if (($userPath -split ';') -notcontains $binDir) {
    [Environment]::SetEnvironmentVariable('Path', (($userPath.TrimEnd(';') + ';' + $binDir).TrimStart(';')), 'User')
    Write-Host 'path_updated=user; open a new PowerShell window'
}
Write-Host "installed=$binDir\unpack-flow.cmd"
Write-Host 'verify_command=unpack-flow version'
