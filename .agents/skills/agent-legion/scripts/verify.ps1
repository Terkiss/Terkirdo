#Requires -Version 5.1
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')
Push-Location $Root
try {

$Prefix = '[agent-legion]'
Write-Host "$Prefix INFO: Verifying Agent Legion partition validator and consolidated quality gate..."

python scripts/harness/validate_harness.py --strict
if ($LASTEXITCODE -ne 0) {
    Write-Error "$Prefix FAIL: Harness validation failed."
    exit 1
}

python scripts/harness/run_quality_gate.py --skill agent-legion
if ($LASTEXITCODE -ne 0) {
    Write-Error "$Prefix FAIL: Quality gate failed."
    exit 1
}

Write-Host "$Prefix PASS: Agent Legion verification completed successfully."
exit 0

} finally { Pop-Location }
