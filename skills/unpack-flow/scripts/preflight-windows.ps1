#requires -Version 5.1
[CmdletBinding()]
param([switch]$InstallDependencies)

$ErrorActionPreference = 'Stop'
Write-Host "os=Windows"
Write-Host "powershell=$($PSVersionTable.PSVersion)"
Write-Host "architecture=$env:PROCESSOR_ARCHITECTURE"

$scriptRoot = Split-Path -Parent $PSCommandPath
$toolArch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'windows-arm64' } else { 'windows-x64' }
$portableCandidates = @(
    (Join-Path $scriptRoot "tools\$toolArch\7z.exe"),
    (Join-Path (Split-Path -Parent $scriptRoot) "tools\$toolArch\7z.exe")
)
$seven = $portableCandidates | Where-Object {
    (Test-Path -LiteralPath $_ -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path (Split-Path -Parent $_) '7z.dll') -PathType Leaf)
} | Select-Object -First 1
if (-not $seven) { $seven = Get-Command 7zz.exe,7z.exe,7za.exe -ErrorAction SilentlyContinue | Select-Object -First 1 }
if (-not $seven) {
    foreach ($path in @("$env:ProgramFiles\7-Zip\7z.exe", "${env:ProgramFiles(x86)}\7-Zip\7z.exe")) {
        if ($path -and (Test-Path -LiteralPath $path)) { $seven = Get-Item -LiteralPath $path; break }
    }
}

if ($seven) {
    $sevenPath = if ($seven -is [string]) { $seven } elseif ($seven.PSObject.Properties.Name -contains 'Source' -and $seven.Source) { $seven.Source } else { $seven.FullName }
    Write-Host "seven_zip=$sevenPath"
    Write-Host 'status=ready'
    exit 0
}

Write-Host 'seven_zip=missing'
if (-not $InstallDependencies) {
    Write-Host 'status=missing_dependencies'
    Write-Host 'install=winget install --id 7zip.7zip --exact'
    Write-Host 'Re-run with -InstallDependencies only after approving system changes.'
    exit 2
}

$winget = Get-Command winget.exe -ErrorAction SilentlyContinue
if ($winget) {
    & $winget.Source install --id 7zip.7zip --exact --accept-source-agreements --accept-package-agreements
} else {
    $choco = Get-Command choco.exe -ErrorAction SilentlyContinue
    if (-not $choco) { throw 'Neither winget nor Chocolatey is available. Install official 7-Zip manually.' }
    & $choco.Source install 7zip -y
}
if ($LASTEXITCODE -ne 0) { throw '7-Zip installation failed.' }
Write-Host 'status=installed; open a new PowerShell window and run preflight again.'
