#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
Push-Location $Root
try {

$Prefix = '[multi-agent-conference]'
$Strict = if ($env:HARNESS_STRICT -eq '1') { $true } else { $false }
[int]$script:Warnings = 0
[int]$script:Failures = 0

function Pass  { param([string]$msg) Write-Host "$Prefix PASS: $msg" }
function Warn  { param([string]$msg) $script:Warnings++; Write-Warning "$Prefix WARN: $msg" }
function Fail  { param([string]$msg) $script:Failures++; Write-Error "$Prefix FAIL: $msg" -ErrorAction Continue }

function Require-Doc {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        Fail "missing required document: $Path"
    } elseif ((Get-Item $Path).Length -eq 0) {
        Warn "$Path is empty; conference context may be missing"
    } else {
        Pass "$Path has content"
    }
}

# Verify SKILL.md definition
$skillFile = '.agents/skills/multi-agent-conference/SKILL.md'
if (-not (Test-Path $skillFile)) {
    Fail "missing $skillFile"
} else {
    $content = Get-Content $skillFile -Raw
    if ($content -match 'name:\s*multi-agent-conference' -and $content -match 'description:') {
        Pass 'SKILL.md has valid YAML frontmatter'
    } else {
        Fail 'SKILL.md missing valid YAML frontmatter'
    }
}

if ($script:Failures -gt 0) { exit 1 }

if ($Strict -and $script:Warnings -gt 0) {
    Fail 'strict mode treats warnings as failures'
    exit 1
}

Pass "multi-agent-conference verification completed with $($script:Warnings) warning(s)"
exit 0

} finally { Pop-Location }
