[CmdletBinding(DefaultParameterSetName = "Prompt")]
param(
    [Parameter(ParameterSetName = "Prompt", Mandatory = $true)]
    [string]$Prompt,

    [Parameter(ParameterSetName = "Prompt")]
    [string]$ProjectPath = "/home/selfsim/projects/velobid",

    [Parameter(ParameterSetName = "Command", Mandatory = $true)]
    [string[]]$HermesArgs,

    [Parameter(ParameterSetName = "Smoke", Mandatory = $true)]
    [switch]$SmokeTest,

    [string]$SkillRoot = $env:CODEX_HERMES_SKILL_ROOT,
    [string]$HermesBin = "/home/selfsim/.local/bin/hermes",
    [switch]$PrintConnection
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

$invokeScript = Join-Path $SkillRoot "scripts\invoke-hermes.ps1"

if (-not (Test-Path -LiteralPath $invokeScript)) {
    throw "Missing invoke script: $invokeScript"
}

function Quote-PosixSingle {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    return "'" + ($Value -replace "'", "'""'""'") + "'"
}

function Build-HermesRemoteCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    $quotedArgs = @()
    foreach ($arg in $Args) {
        $quotedArgs += (Quote-PosixSingle -Value $arg)
    }

    $command = "$(Quote-PosixSingle -Value $HermesBin) $($quotedArgs -join ' ')"
    if ($ProjectPath) {
        return "cd $(Quote-PosixSingle -Value $ProjectPath) && $command"
    }

    return $command
}

function Invoke-Remote {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RemoteCommand
    )

    if ($PrintConnection) {
        & $invokeScript -RemoteCommand $RemoteCommand -PrintConnection
    } else {
        & $invokeScript -RemoteCommand $RemoteCommand
    }

    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

switch ($PSCmdlet.ParameterSetName) {
    "Smoke" {
        Write-Host "Running Hermes access smoke test..."
        Invoke-Remote -RemoteCommand "echo SSH_OK"
        Invoke-Remote -RemoteCommand "$(Quote-PosixSingle -Value $HermesBin) version"
        Write-Host "HERMES_VERSION_OK"
        $smokeCommand = Build-HermesRemoteCommand -Args @("-z", "Reply with exactly HERMES_SMOKE_OK")
        Invoke-Remote -RemoteCommand $smokeCommand
        exit 0
    }
    "Command" {
        Write-Host "Delegating Hermes command: $($HermesArgs -join ' ')"
        $remoteCommand = Build-HermesRemoteCommand -Args $HermesArgs
        Invoke-Remote -RemoteCommand $remoteCommand
        exit 0
    }
    "Prompt" {
        Write-Host "Delegating prompt to Hermes for project path: $ProjectPath"
        $remoteCommand = Build-HermesRemoteCommand -Args @("-z", $Prompt)
        Invoke-Remote -RemoteCommand $remoteCommand
        exit 0
    }
    default {
        throw "Unsupported parameter set: $($PSCmdlet.ParameterSetName)"
    }
}
