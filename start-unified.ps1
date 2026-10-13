param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
if (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue) { throw 'Port 8000 is occupied. Stop the existing ThermoTrack server first with ./stop.ps1.' }
$projectPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) { throw 'Install the Python environment first; see README.md.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend\dist\index.html'))) { throw 'Build the frontend first: npm --prefix frontend ci; npm --prefix frontend run build' }
$backendProcess = Start-Process -FilePath $projectPython -ArgumentList @('-m','uvicorn','app.main:app','--app-dir','backend','--host','127.0.0.1','--port','8000') -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectRoot 'backend-output.log') -RedirectStandardError (Join-Path $projectRoot 'backend-error.log')
@{backend=@{id=$backendProcess.Id;started=$backendProcess.StartTime.ToUniversalTime().ToString('o')};frontend=$null} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $projectRoot '.server-processes.json')
Write-Output 'ThermoTrack frontend and API starting together at http://127.0.0.1:8000.'
if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:8000' }
