# Builds cad/assembly/showcase/*.SLDASM in SolidWorks from md_arm_showcase.py output (Windows PowerShell 5.1).
# Usage: powershell -ExecutionPolicy Bypass -File cad/source/solidworks/sw_showcase.ps1 -Mode build ; then -Mode final (opens both, isometric, saves pictures).
# Mode explode (in-model exploded view via API) is experimental: it displaced components when last tried; the exploded SLDASM is the reliable route.
param([string]$Dir = (Join-Path $PSScriptRoot '../../assembly/showcase'), [string]$Mode = 'build')
$ErrorActionPreference = 'Stop'
$redist = 'C:\Program Files\SOLIDWORKS Corp\SOLIDWORKS\api\redist'
[Reflection.Assembly]::LoadFrom((Join-Path $redist 'SolidWorks.Interop.sldworks.dll')) | Out-Null
[Reflection.Assembly]::LoadFrom((Join-Path $redist 'SolidWorks.Interop.swconst.dll')) | Out-Null
$src = Get-Content -Raw (Join-Path $PSScriptRoot 'SwShow.cs')
Add-Type -TypeDefinition $src -ReferencedAssemblies @((Join-Path $redist 'SolidWorks.Interop.sldworks.dll'), (Join-Path $redist 'SolidWorks.Interop.swconst.dll'))
$j = Get-Content -Raw (Join-Path $Dir 'showcase_parts.json') | ConvertFrom-Json
$m = $j.upper_bar_matrix
$barY = [double[]]@($m[0][1], $m[1][1], $m[2][1])
$barZ = [double[]]@($m[0][2], $m[1][2], $m[2][2])
$dispY = [double[]]$j.display_y_dir
$pl = Get-Content -Raw (Join-Path $Dir 'placements.json') | ConvertFrom-Json
[SwShow]::PNames = [string[]]($pl | % { $_.name }); [SwShow]::PFiles = [string[]]($pl | % { $_.file }); [SwShow]::PMat = [string[]]($pl | % { $_.mat })
[SwShow]::PM = [double[][]]($pl | % { ,[double[]]($_.m | % { $_ }) }); [SwShow]::PMx = [double[][]]($pl | % { ,[double[]]($_.m_exploded | % { $_ }) }); [SwShow]::PRgb = [double[][]]($pl | % { ,[double[]]$_.rgb })
[SwShow]::Run($Dir, $Mode, $barY, $barZ, $dispY)
