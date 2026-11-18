# One-time and after-every-pull setup on Windows. Safe to run again: it only adds or updates what changed.
#   powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1
# Builds, outside the repo in %LOCALAPPDATA%\mic-display (override with $env:MD_HOME):
#   Python 3.12 venv with the pinned CAD packages, arduino-cli + esp32 core + Waveshare's libraries,
#   PrusaSlicer 2.9.7 (portable). Installs the repo's git hooks. Ends with `md doctor`.
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
$home_ = if ($env:MD_HOME) { $env:MD_HOME } else { Join-Path $env:LOCALAPPDATA 'mic-display' }
New-Item -ItemType Directory -Force $home_ | Out-Null

git -C $repo config core.hooksPath .githooks
Write-Host 'git hooks: installed (.githooks)'

function Find-Py312 {
  try { $p = & py -3.12 -c 'import sys; print(sys.executable)' 2>$null; if ($LASTEXITCODE -eq 0 -and $p) { return $p.Trim() } } catch {}
  foreach ($c in @("$env:LOCALAPPDATA\Programs\Python\Python312\python.exe", "C:\Program Files\Python312\python.exe")) { if (Test-Path $c) { return $c } }
  return $null
}
$py = Find-Py312
if (-not $py) {
  Write-Host 'Python 3.12 not found: installing it with winget (user scope)'
  winget install --id Python.Python.3.12 -e --scope user --accept-package-agreements --accept-source-agreements --silent
  $py = Find-Py312
  if (-not $py) { throw 'Python 3.12 still not found after winget; install it from python.org and run this again.' }
}
$venv = Join-Path $home_ 'venv'
if (-not (Test-Path (Join-Path $venv 'Scripts\python.exe'))) { & $py -m venv $venv }
$vpy = Join-Path $venv 'Scripts\python.exe'
& $vpy -m pip install --disable-pip-version-check -q --upgrade pip
& $vpy -m pip install --disable-pip-version-check -q -r (Join-Path $repo 'env\requirements-cad.txt') -c (Join-Path $repo 'env\constraints-cad.txt')
if ($LASTEXITCODE -ne 0) { throw 'pip install failed' }
& $vpy -I (Join-Path $repo 'scripts\md.py') toolchain
if ($LASTEXITCODE -ne 0) { throw 'toolchain install failed' }
& $vpy -I (Join-Path $repo 'scripts\md.py') doctor
