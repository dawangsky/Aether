# Build embedded API binary into desktop/resources/bin/
$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$Python = if ($env:PYTHON) { $env:PYTHON } else { "python" }
$OutDir = Join-Path $Root "desktop/resources/bin"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

& $Python -m pip install -q -U pip wheel
& $Python -m pip install -q -e .
& $Python -m pip install -q "pyinstaller>=6.3"

Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $Root "build/pyinstaller")
Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $Root "dist/aether-api.exe")

& $Python -m PyInstaller `
  --noconfirm `
  --clean `
  --onefile `
  --name aether-api `
  --distpath (Join-Path $Root "dist") `
  --workpath (Join-Path $Root "build/pyinstaller") `
  --specpath (Join-Path $Root "build/pyinstaller") `
  --paths $Root `
  --hidden-import uvicorn.logging `
  --hidden-import uvicorn.loops `
  --hidden-import uvicorn.loops.auto `
  --hidden-import uvicorn.protocols `
  --hidden-import uvicorn.protocols.http `
  --hidden-import uvicorn.protocols.http.auto `
  --hidden-import uvicorn.protocols.websockets `
  --hidden-import uvicorn.protocols.websockets.auto `
  --hidden-import uvicorn.lifespan `
  --hidden-import uvicorn.lifespan.on `
  --collect-all uvicorn `
  --collect-all fastapi `
  --collect-submodules pydantic `
  lottery/api/sidecar.py

$Src = Join-Path $Root "dist/aether-api.exe"
$Dst = Join-Path $OutDir "aether-api.exe"
Copy-Item $Src $Dst -Force
Write-Host "Built: $Dst"
Get-Item $Dst | Format-List Name, Length, FullName
