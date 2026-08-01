# Runs every Sunday via Windows Task Scheduler (task name
# "UniversalDirectoryWeeklyBuild") — Neo: "之後。我們每周日更新。先以周為單位。
# 然後才是月，年". Deliberately a LOCAL scheduled task, not a claude.ai cloud
# routine: the build depends on local state a fresh cloud clone can't
# reach — the SQLite DB holding the archive's actual history
# (storage/metadata/directory.db, gitignored, never committed), plus this
# machine's wrangler and `gh` CLI logins. A cloud agent would have none of
# that and every "weekly" build would start the archive over from zero.
#
# Only fires if this machine is on and awake at the scheduled time —
# known limitation of a local-only schedule, not a bug.
#
# Uses plain `*>`/`*>>` file redirection rather than `2>&1`/Tee-Object:
# PowerShell 5.1 wraps a native command's stderr lines into ErrorRecord
# objects when merged into a pipeline, so Crawl4AI's own (harmless)
# console banners on stderr would otherwise look like terminating
# errors. Exit codes are checked explicitly via $LASTEXITCODE instead of
# relying on exception propagation from stderr output.

$root = "D:\Ai\work together\universal-directory"
Set-Location $root

$logDir = Join-Path $root "logs"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
$timestamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$logFile = Join-Path $logDir "weekly_update_$timestamp.log"

$env:GITHUB_TOKEN = (gh auth token)

& "$root\.venv\Scripts\python.exe" -m directory build --verbose *> $logFile
$buildExit = $LASTEXITCODE

& npx wrangler pages deploy site --project-name universal-directory --branch main *>> $logFile
$deployExit = $LASTEXITCODE

if ($buildExit -ne 0 -or $deployExit -ne 0) {
    Add-Content -Path $logFile -Value "`n=== weekly update FAILED (build exit=$buildExit, deploy exit=$deployExit) at $(Get-Date -Format o) ==="
    exit 1
} else {
    Add-Content -Path $logFile -Value "`n=== weekly update completed successfully at $(Get-Date -Format o) ==="
}
