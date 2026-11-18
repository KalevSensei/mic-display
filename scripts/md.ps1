# Windows wrapper: runs scripts/md.py with the project's Python. Usage: scripts\md.ps1 <command>
$home_ = if ($env:MD_HOME) { $env:MD_HOME } else { Join-Path $env:LOCALAPPDATA 'mic-display' }
$py = Join-Path $home_ 'venv\Scripts\python.exe'
if (-not (Test-Path $py)) { Write-Error 'Project Python missing: run scripts\setup-windows.ps1 first'; exit 1 }
& $py -I (Join-Path $PSScriptRoot 'md.py') @args
exit $LASTEXITCODE
