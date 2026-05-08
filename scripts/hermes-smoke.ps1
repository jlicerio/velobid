[CmdletBinding()]
param(
    [string]$SkillRoot = $env:CODEX_HERMES_SKILL_ROOT
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $SkillRoot) {
    $candidateRoots = @(
        "C:\Users\xlice\plugins\codex-to-hermes",
        "C:\Users\xlice\Desktop\skills\codex-to-hermes"
    )
    $SkillRoot = $candidateRoots | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $SkillRoot) {
        $SkillRoot = $candidateRoots[0]
    }
}

$delegateScript = Join-Path $PSScriptRoot "hermes-delegate.ps1"
if (-not (Test-Path -LiteralPath $delegateScript)) {
    throw "Missing local delegate wrapper: $delegateScript"
}

& $delegateScript -SmokeTest -SkillRoot $SkillRoot
exit $LASTEXITCODE
