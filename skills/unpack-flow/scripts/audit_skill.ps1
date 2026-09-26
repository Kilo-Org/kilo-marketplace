[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Skill,
    [switch]$PublicExport
)
$root = (Resolve-Path $Skill).Path
$errors = [System.Collections.Generic.List[string]]::new()
$required = @('SKILL.md','README.md','CHANGELOG.md','CONTRIBUTING.md','LICENSE','SECURITY.md','SUPPORT.md','PUBLISHER.md','agents/openai.yaml','install.bat','install-linux.sh','install-macos.sh')
foreach ($relative in $required) {
    $path = Join-Path $root $relative
    if (-not (Test-Path $path -PathType Leaf) -or (Get-Item $path).Length -eq 0) { $errors.Add("missing or empty public file: $relative") }
}
$locales = @('zh-CN','es','hi','ar','pt-BR','fr','de','ja','ru')
$readmes = @((Join-Path $root 'README.md')) + ($locales | ForEach-Object { Join-Path $root "docs/README.$_.md" })
foreach ($path in $readmes) {
    if (-not (Test-Path $path -PathType Leaf)) { $errors.Add("missing localization: $path"); continue }
    $content = Get-Content $path -Raw -Encoding UTF8
    $headingContent = [regex]::Replace($content, '(?ms)^```.*?^```\s*$', '')
    if ([regex]::Matches($headingContent, '(?m)^#\s+\S').Count -ne 1) { $errors.Add("localization must contain exactly one H1: $path") }
    foreach ($value in @('once-email.com','github.com/pangxin12345','tiantuowl@gmail.com')) {
        if (-not $content.Contains($value)) { $errors.Add("missing canonical public identity $value`: $path") }
    }
}
$skillText = Get-Content (Join-Path $root 'SKILL.md') -Raw -Encoding UTF8
$nameMatch = [regex]::Match($skillText, '(?m)^name:\s*([a-z0-9-]+)\s*$')
if (-not $nameMatch.Success -or $nameMatch.Groups[1].Value -ne (Split-Path $root -Leaf)) { $errors.Add('SKILL.md name does not match folder name') }
if ($PublicExport) {
    foreach ($relative in @('.internal','.gitlab-ci.yml','DISTRIBUTION.md','REGRESSION.md','REHEARSAL.md')) {
        if (Test-Path (Join-Path $root $relative)) { $errors.Add("internal file present in public export: $relative") }
    }
}
Write-Output "Public Skill audit: $root"
foreach ($item in $errors) { Write-Output "FAIL: $item" }
if ($errors.Count) { Write-Output "RESULT: FAIL ($($errors.Count) blocking issue(s))"; exit 1 }
Write-Output 'RESULT: PASS'
exit 0
