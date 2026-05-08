param(
  [string]$BoardDir = "C:\temp\velobid-kaban",
  [string]$RepoDir = "\\192.168.1.237\Ubuntu-Dev\projects\velobid",
  [string]$FastModel = "opencode-go/kimi-k2.6",
  [string]$DeepModel = "opencode-go/deepseek-v4-pro",
  [int]$PollSeconds = 20
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$KabanArgs = @("-y", "@kaban-board/cli@0.3.1")
$LogFile = Join-Path $BoardDir "opencode-kaban-loop.log"

function Write-LoopLog {
  param([string]$Message)
  $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
  Add-Content -LiteralPath $LogFile -Value $line
  Write-Host $line
}

function Invoke-Kaban {
  param([string[]]$CommandArgs)
  Push-Location -LiteralPath $BoardDir
  try {
    $fullArgs = $KabanArgs + $CommandArgs
    & npx @fullArgs
  }
  finally {
    Pop-Location
  }
}

function Get-NextTodoTask {
  $raw = Invoke-Kaban -CommandArgs @("list", "--json")
  $rawText = ($raw | Out-String).Trim()
  if ([string]::IsNullOrWhiteSpace($rawText)) {
    Write-LoopLog "Kaban returned empty output for list --json"
    return $null
  }

  $jsonMatch = [regex]::Match($rawText, "(?s)\{.*\}")
  if (-not $jsonMatch.Success) {
    Write-LoopLog ("Kaban output did not include JSON. Output: " + $rawText.Replace("`r"," ").Replace("`n"," ").Substring(0, [Math]::Min(300, $rawText.Length)))
    return $null
  }

  try {
    $parsed = $jsonMatch.Value | ConvertFrom-Json
  }
  catch {
    Write-LoopLog ("Failed parsing kaban JSON. Error: " + $_.Exception.Message)
    return $null
  }

  $hasSuccess = $parsed.PSObject.Properties.Name -contains "success"
  if (-not $hasSuccess) {
    Write-LoopLog "Kaban JSON missing success field"
    return $null
  }

  if (-not $parsed.success) {
    Write-LoopLog "Kaban JSON reported success=false"
    return $null
  }

  # Ensure an array result even when exactly one todo item remains.
  $tasks = @(@($parsed.data) | Where-Object { $_.columnId -eq "todo" -and -not $_.archived })
  if ($tasks.Count -eq 0) {
    return $null
  }

  return $tasks |
    Sort-Object -Property createdAt |
    Select-Object -First 1
}

function Resolve-ModelForTask {
  param([string]$Title)
  if ($Title -match "(?i)debug|investigate|root cause|architecture|deep|hard|complex|cross-file|regression") {
    return $DeepModel
  }
  return $FastModel
}

if (-not (Test-Path -LiteralPath $BoardDir)) {
  throw "Board directory not found: $BoardDir"
}

if (-not (Test-Path -LiteralPath (Join-Path $BoardDir ".kaban"))) {
  throw "No .kaban board found in $BoardDir"
}

if (-not (Test-Path -LiteralPath $RepoDir)) {
  throw "Repo directory not found: $RepoDir"
}

Write-LoopLog "Starting OpenCode loop | board=$BoardDir | repo=$RepoDir | fast=$FastModel | deep=$DeepModel"

while ($true) {
  $activeTaskId = $null
  try {
    $task = Get-NextTodoTask
    if ($null -eq $task) {
      Write-LoopLog "No todo tasks. Sleeping ${PollSeconds}s."
      Start-Sleep -Seconds $PollSeconds
      continue
    }

    $taskId = [string]$task.id
    $activeTaskId = $taskId
    $taskTitle = [string]$task.title
    $model = Resolve-ModelForTask -Title $taskTitle

    Write-LoopLog "Picked task $taskId | title='$taskTitle' | model=$model"
    Invoke-Kaban -CommandArgs @("move", $taskId, "in_progress") | Out-Null

    $prompt = @"
You are executing Kaban task $taskId.
Task title: $taskTitle

Work only in this repository: $RepoDir
Apply the changes needed to complete the task end-to-end.
Run focused checks as needed.
Summarize what changed at the end.
"@

    & opencode run --pure --dangerously-skip-permissions --dir $RepoDir -m $model $prompt
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
      Invoke-Kaban -CommandArgs @("done", $taskId) | Out-Null
      Write-LoopLog "Task completed: $taskId"
    }
    else {
      Invoke-Kaban -CommandArgs @("move", $taskId, "todo") | Out-Null
      Write-LoopLog "Task failed (exit=$exitCode): $taskId | moved back to todo"
    }
  }
  catch {
    if ($null -ne $activeTaskId) {
      try {
        Invoke-Kaban -CommandArgs @("move", $activeTaskId, "todo") | Out-Null
        Write-LoopLog "Recovered task $activeTaskId back to todo after loop exception"
      }
      catch {
        Write-LoopLog ("Failed to recover task $activeTaskId to todo: " + $_.Exception.Message)
      }
    }
    Write-LoopLog ("Loop error: " + $_.Exception.Message)
    Start-Sleep -Seconds $PollSeconds
  }
}
