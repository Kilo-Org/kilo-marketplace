#requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Position=0)] [ValidateSet('run','start','list','plan','status','wait','log','help','version')] [string]$Command = 'run',
    [Parameter(Position=1, ValueFromRemainingArguments=$true)] [string[]]$InputPath,
    [Alias('o')] [string]$Output = (Get-Location).Path,
    [int]$MaxInnerLayers = 10,
    [Alias('r')] [switch]$Recursive,
    [string]$SevenZip = $env:UNPACK_FLOW_7Z,
    [string]$PasswordsFile = $env:UNPACK_FLOW_PASSWORDS_FILE,
    [switch]$StopOnError,
    [string]$JobFile
)

$ErrorActionPreference = 'Stop'
if ($PSStyle -and $PSStyle.PSObject.Properties.Name -contains 'OutputRendering') {
    $PSStyle.OutputRendering = 'PlainText'
}
$Version = '2.1.2'
$Started = Get-Date
$script:HeartbeatSeconds = 30
$configuredHeartbeat = 0
if ([int]::TryParse($env:UNPACK_FLOW_HEARTBEAT_SECONDS, [ref]$configuredHeartbeat) -and $configuredHeartbeat -gt 0) {
    $script:HeartbeatSeconds = $configuredHeartbeat
}
$StateRoot = if ($env:UNPACK_FLOW_STATE_ROOT) { $env:UNPACK_FLOW_STATE_ROOT } elseif ($env:OS -eq 'Windows_NT') { Join-Path $env:LOCALAPPDATA 'unpack-flow\state' } else { Join-Path $HOME '.local/state/unpack-flow' }

function Get-LatestJobId {
    if (-not (Test-Path -LiteralPath $StateRoot -PathType Container)) { return $null }
    $latest = Get-ChildItem -LiteralPath $StateRoot -Directory -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if ($latest) { return $latest.Name }
    return $null
}

function Get-RequestedJobId {
    if ($InputPath -and $InputPath.Count -gt 0) { return $InputPath[0] }
    return Get-LatestJobId
}

function Read-JobState([string]$Id) {
    if (-not $Id) { throw 'No background jobs / 没有后台任务' }
    $path = Join-Path (Join-Path $StateRoot $Id) 'state.json'
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Job not found / 找不到任务: $Id" }
    return Get-Content -LiteralPath $path -Raw -Encoding UTF8 | ConvertFrom-Json
}

function Write-JobState([string]$Status, [string]$Message, [Nullable[int]]$ExitCode = $null) {
    if (-not $script:CurrentJobDir) { return }
    $previous = $null
    $statePath = Join-Path $script:CurrentJobDir 'state.json'
    if (Test-Path -LiteralPath $statePath) { $previous = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json }
    $state = [ordered]@{
        job_id = $script:CurrentJobId
        status = $Status
        message = $Message
        pid = if ($Status -eq 'queued' -and $previous) { $previous.pid } else { $PID }
        started_at = if ($previous -and $previous.started_at) { $previous.started_at } else { (Get-Date).ToString('o') }
        updated_at = (Get-Date).ToString('o')
        ended_at = if ($Status -in @('completed','partial_failure','failed')) { (Get-Date).ToString('o') } else { $null }
        exit_code = $ExitCode
        output = $Output
        inputs = @($ResolvedInputs)
        log = Join-Path $script:CurrentJobDir 'job.log'
    }
    $state | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $statePath -Encoding UTF8
}

function Show-JobStatus([string]$Id) {
    $state = Read-JobState $Id
    [pscustomobject]@{ Job=$state.job_id; Status=$state.status; PID=$state.pid; Updated=$state.updated_at; Output=$state.output; Message=$state.message; Log=$state.log } | Format-List
}

function Show-JobLog([string]$Id) {
    $state = Read-JobState $Id
    if (-not (Test-Path -LiteralPath $state.log -PathType Leaf)) { throw "Log not found / 找不到日志: $($state.log)" }
    Get-Content -LiteralPath $state.log -Tail 80 -Encoding UTF8
}

function Wait-JobCompletion([string]$Id) {
    if (-not $Id) { $Id = Get-LatestJobId }
    while ($true) {
        $state = Read-JobState $Id
        if ($state.status -in @('completed','partial_failure','failed')) {
            Show-JobStatus $Id | Out-Host
            if ($state.status -eq 'completed') { return 0 }
            return 1
        }
        Start-Sleep -Seconds 2
    }
}

function Start-BackgroundJob {
    New-Item -ItemType Directory -Path $StateRoot -Force | Out-Null
    $id = "$(Get-Date -Format 'yyyyMMdd_HHmmss_fff')_$([guid]::NewGuid().ToString('N').Substring(0,8))"
    $jobDir = Join-Path $StateRoot $id
    New-Item -ItemType Directory -Path $jobDir | Out-Null
    $requestPath = Join-Path $jobDir 'request.json'
    $logPath = Join-Path $jobDir 'job.log'
    [ordered]@{
        job_id = $id
        input_path = @($ResolvedInputs)
        output = $Output
        max_inner_layers = $MaxInnerLayers
        recursive = [bool]$Recursive
        seven_zip = $SevenZip
        passwords_file = $PasswordsFile
        stop_on_error = [bool]$StopOnError
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $requestPath -Encoding UTF8
    $script:CurrentJobId = $id
    $script:CurrentJobDir = $jobDir
    Write-JobState 'queued' 'Waiting for background worker / 等待后台进程'
    $escapedScript = $PSCommandPath.Replace("'", "''")
    $escapedRequest = $requestPath.Replace("'", "''")
    $escapedLog = $logPath.Replace("'", "''")
    $commandText = "`$ProgressPreference='SilentlyContinue'; & '$escapedScript' run -JobFile '$escapedRequest' *> '$escapedLog'; exit `$LASTEXITCODE"
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($commandText))
    $hostExe = if ($PSVersionTable.PSEdition -eq 'Core') { (Get-Process -Id $PID).Path } else { Join-Path $PSHOME 'powershell.exe' }
    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
    $processInfo.FileName = $hostExe
    $workerArguments = @('-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-EncodedCommand',$encoded)
    if ($processInfo.PSObject.Properties.Name -contains 'ArgumentList') {
        foreach ($argument in $workerArguments) { [void]$processInfo.ArgumentList.Add($argument) }
    } else {
        $processInfo.Arguments = "-NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand $encoded"
    }
    $processInfo.UseShellExecute = $false
    $processInfo.CreateNoWindow = $true
    $processInfo.RedirectStandardInput = $true
    $processInfo.RedirectStandardOutput = $true
    $processInfo.RedirectStandardError = $true
    $process = [System.Diagnostics.Process]::Start($processInfo)
    $process.StandardInput.Close()
    $process.BeginOutputReadLine()
    $process.BeginErrorReadLine()
    $statePath = Join-Path $jobDir 'state.json'
    $state = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
    $state.pid = $process.Id
    $state | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $statePath -Encoding UTF8
    Write-Host "Background job / 后台任务: $id"
    Write-Host "PID: $($process.Id)"
    Write-Host "Status / 状态: unpack-flow status $id"
    Write-Host "Log / 日志: unpack-flow log $id"
    Write-Host "Wait / 等待: unpack-flow wait $id"
}

trap {
    if ($JobFile -and $script:CurrentJobDir) { Write-JobState 'failed' $_.Exception.Message 1 }
    Write-Error $_
    exit 1
}

function Show-Help {
@'
UnpackFlow for Windows and macOS 2.1.2

Usage / 用法:
  unpack-flow run 'X*' -Output 'Extracted'     foreground / 前台运行
  unpack-flow start 'X*' -Output 'Extracted'   background / 后台运行
  unpack-flow list 'X*'                        list matches / 列出匹配项
  unpack-flow plan 'Archive.part01.rar'        inspect only / 只分析不解压
  unpack-flow status [job-id]                  job status / 任务状态
  unpack-flow wait [job-id]                    wait for completion / 等待完成
  unpack-flow log [job-id]                     recent log / 最近日志
  unpack-flow help                             bilingual help / 中英文帮助

Examples / 示例:
  macOS:  unpack-flow run "$HOME/Downloads/Archives/*" -Output "$HOME/Downloads/Extracted"
  Windows: unpack-flow run 'D:\Downloads\Archive*.7z' -Output 'E:\Extracted'
  Background / 后台: unpack-flow start 'D:\Downloads\Archive*' -Output 'E:\Extracted'

Options / 选项:
  -Output PATH         Output root; one folder per package / 输出根目录，每包一目录
  -MaxInnerLayers N   Maximum nested layers; default 10 / 最大内层数，默认 10
  -r, -Recursive      Recursively discover archives in folders and unpack inner layers
                      递归发现文件夹中的压缩包，并继续解压内层归档
  -SevenZip PATH      Custom 7-Zip executable / 指定 7-Zip 程序
  -PasswordsFile PATH Password candidates, one per line / 密码候选文件，每行一个
  -StopOnError        Stop on the first failure / 首次失败时停止

Defaults / 默认值:
  Input patterns are resolved in the current directory.
  Quoted patterns and shell-expanded '*' inputs are both accepted. Checksums,
  unrelated files and continuation volumes are filtered before extraction.
  Output is the current directory. Every package gets its own folder.
  Recursive extraction continues up to 10 inner layers. Failed inner archives
  are preserved and skipped so other archives can continue.
  输入和输出默认都是当前目录；带引号的通配符和 Shell 展开的 `*` 均可使用。
  解压前会自动过滤校验文件、无关文件和非首卷，每个归档任务建立独立目录。
  默认最多递归10个内层；失败的内层归档保留并跳过，其他归档继续处理。

Requirements / 环境:
  Windows PowerShell 5.1+; the release ZIP includes portable 7-Zip Extra.
  macOS requires PowerShell 7+ and 7zz (brew install powershell sevenzip).
  Windows normally needs no separate 7-Zip installation.
  Windows 使用 PowerShell 5.1+，发布包内置便携 7-Zip。
  macOS 使用 PowerShell 7+ 和 7zz；Windows 通常不需另装 7-Zip。

Progress / 进度:
  Shows the current package, phase, elapsed time, and extraction layer.
  Long-running external tools refresh elapsed time every second and emit a
  persistent running heartbeat every 30 seconds.
  显示当前包、阶段、耗时和解压层级，不再盲等。
  外部解压工具长时间运行时每秒刷新耗时，每30秒记录一次运行心跳。

Security / 安全:
  The script extracts Windows self-extracting archives through 7-Zip; it never
  executes unknown EXE files. Existing destinations are not overwritten.
  通过 7-Zip 读取自解压包，不执行未知 EXE，也不覆盖已有目标目录。
'@
}

function Find-SevenZip {
    if ($SevenZip -and (Test-Path -LiteralPath $SevenZip -PathType Leaf)) { return (Resolve-Path -LiteralPath $SevenZip).Path }
    $scriptRoot = Split-Path -Parent $PSCommandPath
    if ($IsWindows -or $env:OS -eq 'Windows_NT') {
        $toolArch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'windows-arm64' } else { 'windows-x64' }
        foreach ($path in @(
            (Join-Path $scriptRoot "tools\$toolArch\7z.exe"),
            (Join-Path (Split-Path -Parent $scriptRoot) "tools\$toolArch\7z.exe"),
            (Join-Path $scriptRoot "tools\$toolArch\7za.exe"),
            (Join-Path (Split-Path -Parent $scriptRoot) "tools\$toolArch\7za.exe")
        )) {
            if (Test-Path -LiteralPath $path -PathType Leaf) { return (Resolve-Path -LiteralPath $path).Path }
        }
    }
    foreach ($name in @('7zz.exe','7z.exe','7za.exe','7zz','7z','7za')) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    foreach ($path in @("$env:ProgramFiles\7-Zip\7z.exe", "${env:ProgramFiles(x86)}\7-Zip\7z.exe")) {
        if ($path -and (Test-Path -LiteralPath $path)) { return $path }
    }
    throw '7-Zip not found. Install 7-Zip or set UNPACK_FLOW_7Z. / 未找到 7-Zip。'
}

function Find-Unrar {
    $scriptRoot = Split-Path -Parent $PSCommandPath
    $toolArch = if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { 'windows-arm64' } else { 'windows-x64' }
    $candidates = @()
    if ($env:OS -eq 'Windows_NT') {
        $candidates += (Join-Path $scriptRoot "tools\$toolArch\UnRAR.exe")
        $candidates += (Join-Path (Split-Path -Parent $scriptRoot) "tools\$toolArch\UnRAR.exe")
    }
    $candidates += (Join-Path $scriptRoot 'tools/macos-arm64/unrar')
    $candidates += (Join-Path (Split-Path -Parent $scriptRoot) 'tools/macos-arm64/unrar')
    foreach ($path in $candidates) {
        if (Test-Path -LiteralPath $path -PathType Leaf) { return (Resolve-Path -LiteralPath $path).Path }
    }
    $cmd = Get-Command unrar -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Find-NativeTar {
    foreach ($name in @('tar.exe','tar','bsdtar.exe','bsdtar')) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    return $null
}

function Remove-Tree([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return }
    try {
        Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
        return
    } catch {
        if (-not ($IsWindows -or $env:OS -eq 'Windows_NT')) { throw }
    }
    $full = [IO.Path]::GetFullPath($Path)
    $extended = if ($full.StartsWith('\\')) { '\\?\UNC\' + $full.TrimStart('\') } else { '\\?\' + $full }
    [IO.Directory]::Delete($extended, $true)
}

function Clear-ExtractionDestination([string]$Destination) {
    if (Test-Path -LiteralPath $Destination -PathType Container) {
        foreach ($child in @(Get-ChildItem -LiteralPath $Destination -Force -ErrorAction SilentlyContinue)) {
            if ($child.PSIsContainer) { Remove-Tree $child.FullName } else { Remove-Item -LiteralPath $child.FullName -Force }
        }
    } else {
        New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    }
}

function Expand-WithNativeTool([string]$Archive, [string]$Destination) {
    $lower = $Archive.ToLowerInvariant()
    $tar = Find-NativeTar
    if ($tar -and $lower -match '(\.tar|\.tar\.gz|\.tgz|\.tar\.bz2|\.tbz2|\.tar\.xz|\.txz)$') {
        Write-Host 'Retrying with native tar / 改用系统 tar 重试'
        & $tar -xf $Archive -C $Destination
        if ($LASTEXITCODE -eq 0) { return $true }
        Clear-ExtractionDestination $Destination
    }
    if ($lower.EndsWith('.zip')) {
        Write-Host 'Retrying with native ZIP support / 改用系统 ZIP 能力重试'
        try {
            Microsoft.PowerShell.Archive\Expand-Archive -LiteralPath $Archive -DestinationPath $Destination -Force
            return $true
        } catch {
            Clear-ExtractionDestination $Destination
        }
    }
    if ($lower.EndsWith('.gz') -and $lower -notmatch '(\.tar\.gz|\.tgz)$') {
        Write-Host 'Retrying with native GZip support / 改用系统 GZip 能力重试'
        $outputName = [IO.Path]::GetFileNameWithoutExtension($Archive)
        $outputPath = Join-Path $Destination $outputName
        try {
            $inputStream = [IO.File]::OpenRead($Archive)
            try {
                $gzipStream = New-Object IO.Compression.GzipStream($inputStream, [IO.Compression.CompressionMode]::Decompress)
                try {
                    $outputStream = [IO.File]::Create($outputPath)
                    try { $gzipStream.CopyTo($outputStream) } finally { $outputStream.Dispose() }
                } finally { $gzipStream.Dispose() }
            } finally { $inputStream.Dispose() }
            return $true
        } catch {
            Clear-ExtractionDestination $Destination
        }
    }
    return $false
}

function Resolve-Inputs([string[]]$Patterns) {
    $seen = @{}
    $result = [System.Collections.Generic.List[string]]::new()
    foreach ($pattern in $Patterns) {
        $candidate = if ([IO.Path]::IsPathRooted($pattern)) { $pattern } else { Join-Path (Get-Location).Path $pattern }
        foreach ($item in @(Get-Item -Path $candidate -ErrorAction SilentlyContinue)) {
            $full = $item.FullName
            if ($seen.ContainsKey($full)) { continue }
            if ($item.PSIsContainer) {
                if ($Recursive) {
                    foreach ($archiveItem in @(Get-ChildItem -LiteralPath $full -File -Recurse -ErrorAction SilentlyContinue | Where-Object { Test-ArchiveEntryFile $_.FullName })) {
                        if (-not $seen.ContainsKey($archiveItem.FullName)) {
                            $seen[$archiveItem.FullName] = $true
                            $result.Add($archiveItem.FullName)
                        }
                    }
                    continue
                }
                if (-not (Find-Archive $full)) { continue }
            } elseif (-not (Test-ArchiveEntryFile $full)) {
                continue
            }
            $seen[$full] = $true
            $result.Add($full)
        }
    }
    return $result.ToArray()
}

function Find-Archive([string]$Source) {
    $patterns = @('*.part01.exe','*.part1.exe','*.part001.exe','*.part01.rar','*.part1.rar','*.part001.rar','*.7z.001','*.zip.001','*.rar','*.7z','*.zip','*.tar','*.tar.gz','*.tgz','*.tar.bz2','*.tbz2','*.tar.xz','*.txz','*.gz','*.bz2','*.xz','*.cab','*.arj','*.lzh','*.chm','*.deb','*.rpm','*.apk','*.cpio','*.iso','*.dmg','*.wim','*.swm','*.esd')
    if (Test-Path -LiteralPath $Source -PathType Leaf) {
        if (Test-ArchiveEntryFile $Source) { return $Source }
        return $null
    }
    foreach ($pattern in $patterns) {
        $hit = Get-ChildItem -LiteralPath $Source -Filter $pattern -File -Recurse -Depth 2 -ErrorAction SilentlyContinue |
            Where-Object { Test-ArchiveEntryFile $_.FullName } |
            Select-Object -First 1
        if ($hit) { return $hit.FullName }
    }
    return $null
}

function Test-ArchiveEntryFile([string]$Path) {
    $name = [IO.Path]::GetFileName($Path)
    if ($name -match '(?i)\.part0*(?:[2-9]|[1-9][0-9]+)\.(?:rar|exe)$') { return $false }
    if ($name -match '(?i)\.(?:7z|zip)\.0*(?:[2-9]|[1-9][0-9]+)$') { return $false }
    if ($name -match '(?i)\.(?:r|z)[0-9]+$') { return $false }
    if ($name -match '(?i)(\.part0*1\.(?:rar|exe)|\.rar|\.7z(?:\.0*1)?|\.zip(?:\.0*1)?|\.tar|\.tar\.gz|\.tgz|\.tar\.bz2|\.tbz2|\.tar\.xz|\.txz|\.gz|\.bz2|\.xz|\.cab|\.arj|\.lzh|\.chm|\.deb|\.rpm|\.apk|\.cpio|\.iso|\.dmg|\.wim|\.swm|\.esd)$') { return $true }
    return (-not [IO.Path]::GetExtension($Path) -and (Test-ArchiveSignature $Path))
}

function Test-ArchiveSignature([string]$Path) {
    try {
        $stream = [IO.File]::OpenRead($Path)
        try {
            $bytes = New-Object byte[] 8
            $count = $stream.Read($bytes, 0, $bytes.Length)
        } finally {
            $stream.Dispose()
        }
        if ($count -ge 4 -and $bytes[0] -eq 0x50 -and $bytes[1] -eq 0x4B -and $bytes[2] -in @(0x03,0x05,0x07) -and $bytes[3] -in @(0x04,0x06,0x08)) { return $true }
        if ($count -ge 6 -and $bytes[0] -eq 0x37 -and $bytes[1] -eq 0x7A -and $bytes[2] -eq 0xBC -and $bytes[3] -eq 0xAF -and $bytes[4] -eq 0x27 -and $bytes[5] -eq 0x1C) { return $true }
        if ($count -ge 7 -and $bytes[0] -eq 0x52 -and $bytes[1] -eq 0x61 -and $bytes[2] -eq 0x72 -and $bytes[3] -eq 0x21 -and $bytes[4] -eq 0x1A -and $bytes[5] -eq 0x07) { return $true }
    } catch {
        return $false
    }
    return $false
}

function Get-InnerArchives([string]$Root) {
    return @(Get-ChildItem -LiteralPath $Root -File -Recurse -ErrorAction SilentlyContinue |
        Where-Object { Test-ArchiveEntryFile $_.FullName } |
        Sort-Object FullName)
}

function Remove-ArchiveVolumes([System.IO.FileInfo]$Archive) {
    $name = $Archive.Name
    $directory = $Archive.DirectoryName
    if ($name -match '(?i)^(.*)\.part0*1\.rar$') {
        $prefix = [regex]::Escape($Matches[1])
        Get-ChildItem -LiteralPath $directory -File | Where-Object { $_.Name -match "(?i)^$prefix\.part[0-9]+\.rar$" } | Remove-Item -Force
    } elseif ($name -match '(?i)^(.*)\.part0*1\.exe$') {
        $prefix = [regex]::Escape($Matches[1])
        Get-ChildItem -LiteralPath $directory -File | Where-Object { $_.Name -match "(?i)^$prefix\.part[0-9]+\.(?:exe|rar)$" } | Remove-Item -Force
    } elseif ($name -match '(?i)^(.*\.zip)\.0*1$') {
        $prefix = [regex]::Escape($Matches[1])
        Get-ChildItem -LiteralPath $directory -File | Where-Object { $_.Name -match "(?i)^$prefix\.[0-9]+$" } | Remove-Item -Force
    } elseif ($name -match '(?i)^(.*)\.zip$') {
        $stem = $Matches[1]
        $prefix = [regex]::Escape($stem)
        $splitParts = @(Get-ChildItem -LiteralPath $directory -File -Filter "$stem.z*" -ErrorAction SilentlyContinue)
        if ($splitParts.Count -gt 0) {
            Get-ChildItem -LiteralPath $directory -File | Where-Object { $_.Name -eq $name -or $_.Name -match "(?i)^$prefix\.z[0-9]+$" } | Remove-Item -Force
        } else {
            Remove-Item -LiteralPath $Archive.FullName -Force
        }
    } else {
        Remove-Item -LiteralPath $Archive.FullName -Force
    }
}

function Merge-Directory([string]$Source, [string]$Destination) {
    if ($IsWindows -or $env:OS -eq 'Windows_NT') {
        $robocopy = Get-Command robocopy.exe -ErrorAction SilentlyContinue
        if ($robocopy) {
            & $robocopy.Source $Source $Destination /E /MOVE /R:0 /W:0 /NFL /NDL /NJH /NJS /NP *> $null
            if ($LASTEXITCODE -lt 8) { return }
            throw "Long-path merge failed / 长路径合并失败: $Source -> $Destination"
        }
    }
    foreach ($item in @(Get-ChildItem -LiteralPath $Source -Recurse -Force)) {
        $relative = $item.FullName.Substring($Source.Length).TrimStart([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
        $target = Join-Path $Destination $relative
        if ($item.PSIsContainer) {
            if (-not (Test-Path -LiteralPath $target -PathType Container)) { New-Item -ItemType Directory -Path $target -Force | Out-Null }
        } else {
            $targetParent = Split-Path -Parent $target
            if (-not (Test-Path -LiteralPath $targetParent -PathType Container)) { New-Item -ItemType Directory -Path $targetParent -Force | Out-Null }
            Copy-Item -LiteralPath $item.FullName -Destination $target -Force
        }
    }
}

function Get-Passwords {
    $passwords = @('')
    if ($PasswordsFile -and (Test-Path -LiteralPath $PasswordsFile)) {
        $passwords += @(Get-Content -LiteralPath $PasswordsFile | Where-Object { $_ -ne '' })
    }
    return $passwords
}

function Show-ActiveProgress {
    if (-not $script:ActiveProgress) { return }
    $p = $script:ActiveProgress
    $elapsed = [int]((Get-Date) - $Started).TotalSeconds
    $text = "[$($p.Index)/$($p.Total)] $($p.Package) | $($p.Phase) | layer/层 $($p.Layer) | elapsed/耗时 $([TimeSpan]::FromSeconds($elapsed).ToString())"
    Write-Progress -Activity 'unpack-flow' -Status $text -PercentComplete ([math]::Floor((($p.Index - 1) / [math]::Max($p.Total,1)) * 100))
    if ($elapsed -gt 0 -and ($elapsed % $script:HeartbeatSeconds) -eq 0 -and $script:LastHeartbeatSecond -ne $elapsed) {
        $script:LastHeartbeatSecond = $elapsed
        Write-Host "$text | running/运行中"
    }
}

function Invoke-MonitoredTool([string]$FilePath, [string[]]$Arguments) {
    $payload = @{ FilePath = $FilePath; Arguments = @($Arguments) }
    $job = Start-Job -ScriptBlock {
        param($Payload)
        $output = @(& $Payload.FilePath @($Payload.Arguments) 2>&1 | ForEach-Object { $_.ToString() })
        [pscustomobject]@{ ExitCode = $LASTEXITCODE; Output = $output }
    } -ArgumentList $payload
    try {
        while ($job.State -in @('NotStarted','Running')) {
            Wait-Job -Job $job -Timeout 1 | Out-Null
            Show-ActiveProgress
        }
        $result = Receive-Job -Job $job
        if (-not $result) { return [pscustomobject]@{ ExitCode = 1; Output = @('Extraction tool returned no result / 解压工具未返回结果') } }
        return $result[-1]
    } finally {
        if ($job.State -in @('NotStarted','Running')) { Stop-Job -Job $job -ErrorAction SilentlyContinue }
        Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    }
}

function Expand-Archive7([string]$Archive, [string]$Destination, [string]$Seven) {
    if (-not (Test-Path -LiteralPath $Destination -PathType Container)) {
        New-Item -ItemType Directory -Path $Destination -Force | Out-Null
    }
    foreach ($password in Get-Passwords) {
        $passwordArg = if ($password) { "-p$password" } else { '-p-' }
        $result = Invoke-MonitoredTool $Seven @('x','-y',"-o$Destination",$passwordArg,'--',$Archive)
        $sevenExit = [int]$result.ExitCode
        if ($sevenExit -eq 0) { return }
        Clear-ExtractionDestination $Destination
    }
    $unrar = Find-Unrar
    if ($unrar -and $Archive -match '(?i)(\.rar|\.part0*1\.rar|\.part0*1\.exe)$') {
        Write-Host '7-Zip unsupported; retrying with bundled UnRAR / 7-Zip 不支持，改用内置 UnRAR'
        foreach ($password in Get-Passwords) {
            $passwordArg = if ($password) { "-p$password" } else { '-p-' }
            $result = Invoke-MonitoredTool $unrar @('t','-idq',$passwordArg,$Archive)
            $testExit = [int]$result.ExitCode
            if ($testExit -ne 0) { continue }
            $result = Invoke-MonitoredTool $unrar @('x','-o-','-idq',$passwordArg,$Archive,"$Destination/")
            if ([int]$result.ExitCode -eq 0) { return }
            Clear-ExtractionDestination $Destination
        }
    }
    if (Expand-WithNativeTool $Archive $Destination) { return }
    throw "Extraction failed / 解压失败: $Archive"
}

function Show-Phase([int]$Index, [int]$Total, [string]$Package, [string]$Phase, [int]$Layer) {
    $script:ActiveProgress = [pscustomobject]@{ Index=$Index; Total=$Total; Package=$Package; Phase=$Phase; Layer=$Layer }
    $script:LastHeartbeatSecond = -1
    $elapsed = [int]((Get-Date) - $Started).TotalSeconds
    $text = "[$Index/$Total] $Package | $Phase | layer/层 $Layer | elapsed/耗时 $([TimeSpan]::FromSeconds($elapsed).ToString())"
    Write-Progress -Activity 'unpack-flow' -Status $text -PercentComplete ([math]::Floor((($Index - 1) / [math]::Max($Total,1)) * 100))
    Write-Host $text
}

if ($Command -eq 'help') { Show-Help; exit 0 }
if ($Command -eq 'version') { $Version; exit 0 }
if ($Command -eq 'status') { Show-JobStatus (Get-RequestedJobId); exit 0 }
if ($Command -eq 'log') { Show-JobLog (Get-RequestedJobId); exit 0 }
if ($Command -eq 'wait') { $waitCode = Wait-JobCompletion (Get-RequestedJobId); exit $waitCode }

if ($JobFile) {
    $request = Get-Content -LiteralPath $JobFile -Raw -Encoding UTF8 | ConvertFrom-Json
    $script:CurrentJobId = $request.job_id
    $script:CurrentJobDir = Split-Path -Parent $JobFile
    $InputPath = @($request.input_path)
    $Output = $request.output
    $MaxInnerLayers = [int]$request.max_inner_layers
    $Recursive = [bool]$request.recursive
    $SevenZip = $request.seven_zip
    $PasswordsFile = $request.passwords_file
    $StopOnError = [bool]$request.stop_on_error
}
if (-not $InputPath -or $InputPath.Count -eq 0) { Show-Help; exit 2 }

$Seven = Find-SevenZip
$Output = [IO.Path]::GetFullPath($Output)
$ResolvedInputs = @(if ($JobFile) { $InputPath } else { Resolve-Inputs $InputPath })
if ($ResolvedInputs.Count -eq 0) { throw 'No matches. Quote wildcard patterns. / 没有匹配项，请给通配符加引号。' }

if ($Command -eq 'start') { Start-BackgroundJob; exit 0 }
if ($JobFile) { $ProgressPreference = 'SilentlyContinue'; Write-JobState 'running' 'Extraction in progress / 正在解压' }

if ($Command -eq 'list') {
    $ResolvedInputs | ForEach-Object { [pscustomobject]@{ Name=(Split-Path $_ -Leaf); Archive=(Find-Archive $_); Path=$_ } } | Format-Table -AutoSize
    exit 0
}
if ($Command -eq 'plan') {
    foreach ($source in $ResolvedInputs) {
        $archive = Find-Archive $source
        Write-Host "=== $(Split-Path $source -Leaf) ==="
        if (-not $archive) { Write-Host 'No supported archive / 未找到支持的压缩包'; continue }
        Write-Host "Archive / 首包: $archive"
        $savedErrorAction = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        $listing = @(& $Seven l -ba -- $archive 2>&1)
        $sevenExit = $LASTEXITCODE
        $ErrorActionPreference = $savedErrorAction
        if ($sevenExit -eq 0) {
            $listing | Select-Object -First 10
        } else {
            $unrar = Find-Unrar
            if (-not $unrar) { throw "Cannot inspect archive / 无法检查压缩包: $archive" }
            & $unrar lb -idq -p- $archive | Select-Object -First 10
            if ($LASTEXITCODE -ne 0) { throw "Cannot inspect archive / 无法检查压缩包: $archive" }
        }
    }
    exit 0
}

if (-not (Test-Path -LiteralPath $Output -PathType Container)) {
    New-Item -ItemType Directory -Path $Output -Force | Out-Null
}
$TempRoot = if ($IsWindows -or $env:OS -eq 'Windows_NT') { Join-Path $env:TEMP 'unpack-flow' } else { $Output }
if (-not (Test-Path -LiteralPath $TempRoot -PathType Container)) {
    New-Item -ItemType Directory -Path $TempRoot -Force | Out-Null
}
$failedArchives = [System.Collections.Generic.List[string]]::new()
for ($i=0; $i -lt $ResolvedInputs.Count; $i++) {
    $source = $ResolvedInputs[$i]; $package = Split-Path $source -Leaf
    Show-Phase ($i+1) $ResolvedInputs.Count $package 'scan/扫描' 0
    $archive = Find-Archive $source
    if (-not $archive) { Write-Warning "Skipped, no archive / 跳过，无压缩包: $source"; continue }
    $work = Join-Path $TempRoot ".uf_$([guid]::NewGuid().ToString('N'))"
    try {
        Show-Phase ($i+1) $ResolvedInputs.Count $package 'extract/解压' 1
        Expand-Archive7 $archive $work $Seven
        $layer = 1
        $failedInner = @{}
        while ($layer -le $MaxInnerLayers) {
            $inners = @(Get-InnerArchives $work | Where-Object { -not $failedInner.ContainsKey($_.FullName) })
            if ($inners.Count -eq 0) { break }
            foreach ($inner in $inners) {
                $next = Join-Path $TempRoot ".ufi_$([guid]::NewGuid().ToString('N'))"
                Show-Phase ($i+1) $ResolvedInputs.Count $package "inner/内层: $($inner.Name)" ($layer+1)
                try {
                    Expand-Archive7 $inner.FullName $next $Seven
                    Remove-ArchiveVolumes $inner
                    Merge-Directory $next $inner.DirectoryName
                } catch {
                    if ($StopOnError) { throw }
                    $failedInner[$inner.FullName] = $true
                    $failedDisplay = $inner.FullName.Substring($work.Length).TrimStart([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
                    $failedArchives.Add("$package :: $failedDisplay")
                    Write-Warning "Skipped failed inner archive / 跳过失败的内层归档: $($inner.FullName)"
                } finally {
                    if (Test-Path -LiteralPath $next) { Remove-Tree $next }
                }
            }
            $layer++
        }
        $children = @(Get-ChildItem -LiteralPath $work -Force)
        $rootPath = if ($children.Count -eq 1 -and $children[0].PSIsContainer) { $children[0].FullName } else { $work }
        $name = if ($rootPath -eq $work) { [IO.Path]::GetFileNameWithoutExtension($package) } else { [IO.Path]::GetFileName($rootPath) }
        $destination = Join-Path $Output $name
        if ($Recursive -and (Test-Path -LiteralPath $destination)) {
            $sourceParent = Split-Path (Split-Path $archive -Parent) -Leaf
            $sourceParent = $sourceParent -replace '[<>:"/\\|?*\x00-\x1F]', '-'
            $collisionName = if ($sourceParent -and $sourceParent -ne $name) { "$name-$sourceParent-unpacked" } else { "$name-unpacked" }
            $destination = Join-Path $Output $collisionName
            $suffix = 2
            while (Test-Path -LiteralPath $destination) {
                $destination = Join-Path $Output "$collisionName-$suffix"
                $suffix++
            }
        }
        if (Test-Path -LiteralPath $destination) { Write-Warning "Destination exists, skipped / 目标已存在: $destination"; continue }
        Show-Phase ($i+1) $ResolvedInputs.Count $package 'finalize/整理' $layer
        if ($rootPath -eq $work) { Move-Item -LiteralPath $work -Destination $destination } else { Move-Item -LiteralPath $rootPath -Destination $destination }
        Get-ChildItem -LiteralPath $destination -Recurse -Force -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq '.DS_Store' -or $_.Name -like '._*' -or $_.Name -eq '__MACOSX' } | Remove-Item -Recurse -Force
        Write-Host "Completed / 完成: $destination" -ForegroundColor Green
    } catch {
        if ($StopOnError) { throw }
        $failedArchives.Add($archive)
        Write-Warning "Skipped failed package / 跳过失败的归档任务: $archive"
    } finally {
        if (Test-Path -LiteralPath $work) { Remove-Tree $work }
        if (Test-Path -LiteralPath "$work.next") { Remove-Tree "$work.next" }
    }
}
Write-Progress -Activity 'unpack-flow' -Completed
if ($failedArchives.Count -gt 0) {
    if ($JobFile) { Write-JobState 'partial_failure' "Completed with $($failedArchives.Count) skipped failure(s) / 完成，有失败项被跳过" 1 }
    Write-Warning "Completed with skipped failures / 已完成，但有失败项被跳过: $($failedArchives.Count)"
    $failedArchives | ForEach-Object { Write-Warning "  $_" }
    exit 1
}
if ($JobFile) { Write-JobState 'completed' 'Extraction completed / 解压完成' 0 }
