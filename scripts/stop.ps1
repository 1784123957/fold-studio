$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
foreach ($service in @('frontend','backend')) {
    $pidFile = Join-Path $projectRoot ".runtime\$service.pid"
    if (Test-Path $pidFile) {
        $processId = [int](Get-Content $pidFile)
        $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId=$processId"
        if ($processInfo -and $processInfo.ExecutablePath -and (($service -eq 'backend' -and $processInfo.ExecutablePath -eq "$projectRoot\.venv\Scripts\python.exe") -or ($service -eq 'frontend' -and $processInfo.CommandLine -like "*$projectRoot\frontend\node_modules\vite*"))) {
            Stop-Process -Id $processId
        }
        Remove-Item -LiteralPath $pidFile
    }
}
& "$projectRoot\.venv\Scripts\python.exe" "$PSScriptRoot\stop_db.py"
