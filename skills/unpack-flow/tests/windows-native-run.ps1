#requires -Version 5.1
$ErrorActionPreference = 'Stop'
$share = if ($env:UNPACK_FLOW_WINDOWS_SHARE) { $env:UNPACK_FLOW_WINDOWS_SHARE } elseif (Test-Path -LiteralPath 'C:\UF212' -PathType Container) { 'C:\UF212' } else { '\\host.lan\Data\1111' }
$result = Join-Path $share 'windows-native-result.txt'
$localRoot = 'C:\UnpackFlowTest-2.1.4'
$childOut = Join-Path $localRoot 'child-out.txt'
$childErr = Join-Path $localRoot 'child-err.txt'

function Remove-TestTree([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    $full = [IO.Path]::GetFullPath($Path)
    $extended = if ($full.StartsWith('\\')) { '\\?\UNC\' + $full.TrimStart('\') } else { '\\?\' + $full }
    [IO.Directory]::Delete($extended, $true)
}

for ($attempt = 1; $attempt -le 90; $attempt++) {
    if (Test-Path -LiteralPath $share -PathType Container) { break }
    Start-Sleep -Seconds 2
}
if (-not (Test-Path -LiteralPath $share -PathType Container)) { exit 10 }

"WINDOWS_NATIVE_TEST_START $([DateTime]::UtcNow.ToString('o'))" | Set-Content -LiteralPath $result -Encoding UTF8
try {
    # This path is dedicated to this disposable test. Remove stale extraction
    # and installation output before every Windows run.
    if (Test-Path -LiteralPath $localRoot) { Remove-TestTree $localRoot }
    New-Item -ItemType Directory -Path $localRoot | Out-Null

    $package = Join-Path $share 'package'
    $installer = Join-Path $package 'install.bat'
    $install = Start-Process cmd.exe -ArgumentList "/d /c call `"$installer`"" -Wait -PassThru -RedirectStandardOutput $childOut -RedirectStandardError $childErr
    "INSTALL_RC=$($install.ExitCode)" | Add-Content -LiteralPath $result -Encoding UTF8
    Get-Content -LiteralPath $childOut -ErrorAction SilentlyContinue | Add-Content -LiteralPath $result -Encoding UTF8
    Get-Content -LiteralPath $childErr -ErrorAction SilentlyContinue | Add-Content -LiteralPath $result -Encoding UTF8
    if ($install.ExitCode -ne 0) { throw "install.bat failed: $($install.ExitCode)" }

    $cli = Join-Path $env:USERPROFILE '.local\bin\unpack-flow.cmd'
    $version = (& $cli version | Out-String).Trim()
    "VERSION=$version" | Add-Content -LiteralPath $result -Encoding UTF8
    if ($version -ne '2.1.4') { throw "unexpected version: $version" }

    $scan = Join-Path $localRoot 'scan'
    New-Item -ItemType Directory -Path $scan | Out-Null
    foreach ($name in @('bundle.zip','bundle.zip.sha256','data.part1.exe','data.part2.rar','data.part03.rar','set.part01.rar','set.part02.rar','split.7z.001','split.7z.002','numbered.zip.001','numbered.zip.002','classic.rar','classic.r00','notes.txt')) {
        New-Item -ItemType File -Path (Join-Path $scan $name) | Out-Null
    }
    $expanded = @(Get-ChildItem -LiteralPath $scan | ForEach-Object FullName)
    $scanOutput = (& $cli list @expanded 2>&1 | Out-String)
    foreach ($expected in @('bundle.zip','data.part1.exe','set.part01.rar','split.7z.001','numbered.zip.001','classic.rar')) {
        if ($scanOutput -notmatch [regex]::Escape($expected)) { throw "missing entry: $expected" }
    }
    foreach ($unexpected in @('bundle.zip.sha256','data.part2.rar','data.part03.rar','set.part02.rar','split.7z.002','numbered.zip.002','classic.r00','notes.txt')) {
        if ($scanOutput -match [regex]::Escape($unexpected)) { throw "unexpected input: $unexpected" }
    }
    'INPUT_NORMALIZATION=PASS' | Add-Content -LiteralPath $result -Encoding UTF8

    $recursiveSource = Join-Path $localRoot 'recursive-source'
    $sameName = Join-Path $recursiveSource 'nested'
    $recursivePayload = Join-Path $localRoot 'recursive-payload'
    New-Item -ItemType Directory -Path $sameName,$recursivePayload | Out-Null
    Set-Content -LiteralPath (Join-Path $recursivePayload 'marker.txt') -Value 'recursive pass' -Encoding ASCII
    Compress-Archive -Path (Join-Path $recursivePayload 'marker.txt') -DestinationPath (Join-Path $sameName 'nested.zip')
    & $cli run (Join-Path $recursiveSource '*') -r -Output $recursiveSource | Out-Null
    if (-not (Test-Path -LiteralPath (Join-Path $recursiveSource 'nested-unpacked\marker.txt'))) { throw 'recursive collision-safe output missing' }
    'RECURSIVE_MODE=PASS' | Add-Content -LiteralPath $result -Encoding UTF8

    $input = Join-Path $localRoot 'input'
    $output = Join-Path $localRoot 'output'
    New-Item -ItemType Directory -Path $input,$output | Out-Null
    Copy-Item -LiteralPath (Join-Path $share 'unpack-flow-minimal-testcases-v1.zip') -Destination $input
    Set-Content -LiteralPath (Join-Path $input 'unpack-flow-minimal-testcases-v1.zip.sha256') -Value 'test checksum sidecar' -Encoding ASCII
    $startOutput = (& $cli start (Join-Path $input '*') -r -Output $output 2>&1 | Out-String)
    "START_OUTPUT_BEGIN`r`n$startOutput`r`nSTART_OUTPUT_END" | Add-Content -LiteralPath $result -Encoding UTF8
    $jobMatch = [regex]::Match($startOutput, '\d{8}_\d{6}_\d{3}_[0-9a-fA-F]{8}')
    if (-not $jobMatch.Success) { throw 'background job ID missing' }
    $jobId = $jobMatch.Value
    $escapePattern = [regex]::Escape([string][char]27) + '\[[0-9;?]*[A-Za-z]'
    if ($startOutput -match $escapePattern -or $startOutput -match '[0-9]+;[0-9]+R') { throw 'terminal escape leaked during start' }
    $fullRunLog = Join-Path $localRoot 'full-run.log'
    $savedErrorAction = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        & $cli wait $jobId | Out-Null
        $runExit = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $savedErrorAction
    }
    & $cli log $jobId *> $fullRunLog
    'BACKGROUND_TERMINAL_ISOLATION=PASS' | Add-Content -LiteralPath $result -Encoding UTF8
    Copy-Item -LiteralPath $fullRunLog -Destination (Join-Path $share 'windows-full-run.log') -Force
    "FULL_RUN_RC=$runExit" | Add-Content -LiteralPath $result -Encoding UTF8
    if ($runExit -ne 1) { throw "expected partial-failure exit 1, got $runExit" }

    $expectedCount = @(Get-ChildItem -LiteralPath $output -Filter EXPECTED.txt -File -Recurse).Count
    $exeCount = @(Get-ChildItem -LiteralPath $output -Filter demo.EXE -File -Recurse).Count
    $failedCount = @(Get-ChildItem -LiteralPath $output -File -Recurse | Where-Object { $_.Name -match '(?i)^MiniSfx\.part0*1\.exe$' }).Count
    Get-ChildItem -LiteralPath $output -File -Recurse | ForEach-Object FullName | Set-Content -LiteralPath (Join-Path $share 'windows-output-files.txt') -Encoding UTF8
    "EXPECTED_COUNT=$expectedCount" | Add-Content -LiteralPath $result -Encoding UTF8
    "EXE_COUNT=$exeCount" | Add-Content -LiteralPath $result -Encoding UTF8
    "FAILED_FIRST_VOLUMES=$failedCount" | Add-Content -LiteralPath $result -Encoding UTF8
    if ($expectedCount -lt 6 -or $exeCount -lt 5 -or $failedCount -lt 1) { throw 'compact extraction counts differ from acceptance baseline' }

    'WINDOWS_NATIVE_PASS' | Add-Content -LiteralPath $result -Encoding UTF8
    exit 0
} catch {
    "WINDOWS_NATIVE_FAIL $($_.Exception.Message)" | Add-Content -LiteralPath $result -Encoding UTF8
    ($_ | Format-List * -Force | Out-String) | Add-Content -LiteralPath $result -Encoding UTF8
    exit 1
}
