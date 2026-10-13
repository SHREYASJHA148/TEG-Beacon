$processFile = Join-Path $PSScriptRoot '.server-processes.json'
if (-not (Test-Path -LiteralPath $processFile)) { Write-Output 'No recorded servers.'; return }
$recordedServers = Get-Content -LiteralPath $processFile -Raw | ConvertFrom-Json
foreach ($server in @($recordedServers.backend,$recordedServers.frontend)) {
    $serverProcess = Get-Process -Id $server.id -ErrorAction SilentlyContinue
    if ($serverProcess -and $serverProcess.StartTime.ToUniversalTime().Ticks -eq ([datetime]$server.started).ToUniversalTime().Ticks) {
        # Windows virtual-environment Python starts a child interpreter.
        $childProcesses = Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $serverProcess.Id }
        foreach ($childProcess in $childProcesses) { Stop-Process -Id $childProcess.ProcessId -ErrorAction SilentlyContinue }
        Stop-Process -Id $serverProcess.Id
    }
}
Write-Output 'Recorded ThermoTrack servers stopped.'
