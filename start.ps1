param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
foreach ($port in @(8000,5173)) {
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
        throw "Port $port is already in use. Inspect the existing server before starting another."
    }
}
$projectPython = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) { throw 'Install the Python environment first; see README.md.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'frontend\node_modules\.bin\vite.cmd'))) { throw 'Install frontend dependencies first with npm ci.' }
$backendProcess = Start-Process -FilePath $projectPython -ArgumentList @('-m','uvicorn','app.main:app','--app-dir','backend','--host','127.0.0.1','--port','8000') -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectRoot 'backend-output.log') -RedirectStandardError (Join-Path $projectRoot 'backend-error.log')
$nodeExecutable = (Get-Command node.exe).Source
$frontendProcess = Start-Process -FilePath $nodeExecutable -ArgumentList @('node_modules/vite/bin/vite.js','--host','127.0.0.1') -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $projectRoot 'frontend-output.log') -RedirectStandardError (Join-Path $projectRoot 'frontend-error.log')
@{backend=@{id=$backendProcess.Id;started=$backendProcess.StartTime.ToUniversalTime().ToString('o')};frontend=@{id=$frontendProcess.Id;started=$frontendProcess.StartTime.ToUniversalTime().ToString('o')}} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $projectRoot '.server-processes.json')
Write-Output 'ThermoTrack starting at http://127.0.0.1:5173. Logs are in the project folder.'
if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:5173' }
