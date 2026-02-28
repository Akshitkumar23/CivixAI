param(
  [string]$PythonPath = "py",
  [string]$WorkingDir = (Get-Location).Path,
  [string]$TaskName = "CivixAI_SchemeScraper",
  [string]$Schedule = "DAILY",
  [string]$Time = "02:00"
)

$ErrorActionPreference = "Stop"

if ($Schedule.ToUpperInvariant() -ne "DAILY" -and $Schedule.ToUpperInvariant() -ne "WEEKLY") {
  throw "Unsupported schedule '$Schedule'. Use DAILY or WEEKLY."
}

$scriptPath = Join-Path $WorkingDir "services\scraper\scrape_schemes.py"
$runCmd = "$PythonPath -3 $scriptPath"
$args = "/Create /SC $Schedule /TN `"$TaskName`" /TR `"$runCmd`" /ST $Time /F"

cmd.exe /c "schtasks $args" | Out-Null
Write-Host "Scheduled task created/updated: $TaskName ($Schedule at $Time)"
