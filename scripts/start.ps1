$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$runtime = Join-Path $projectRoot '.runtime'
function Is-Listening($port) {
    $client = New-Object System.Net.Sockets.TcpClient
    try { $client.Connect('127.0.0.1', $port); return $true } catch { return $false } finally { $client.Dispose() }
}
function Wait-Port($port) {
    for ($i = 0; $i -lt 40; $i++) { if (Is-Listening $port) { return }; Start-Sleep -Milliseconds 500 }
    throw "Service on port $port did not start. Check .runtime logs."
}
if (!(Test-Path "$projectRoot\backend\.env")) { throw 'Run scripts/install.ps1 first.' }
if (!(Is-Listening 3307)) {
    $mysql = Get-ChildItem "$runtime\mysql-*-winx64\bin\mysqld.exe" | Select-Object -First 1
    if (!$mysql) { throw 'MySQL binary is missing. Run scripts/install.ps1.' }
    $p = Start-Process -FilePath $mysql.FullName -ArgumentList "--defaults-file=`"$runtime\my.ini`"" -WindowStyle Hidden -PassThru
    $p.Id | Set-Content "$runtime\mysql.pid"
    Wait-Port 3307
}
if (!(Is-Listening 8000)) {
    $p = Start-Process -FilePath "$projectRoot\.venv\Scripts\python.exe" -ArgumentList '-m uvicorn app.main:app --host 127.0.0.1 --port 8000' -WorkingDirectory "$projectRoot\backend" -WindowStyle Hidden -RedirectStandardOutput "$runtime\backend.log" -RedirectStandardError "$runtime\backend-error.log" -PassThru
    $p.Id | Set-Content "$runtime\backend.pid"
    Wait-Port 8000
}
if (!(Is-Listening 5173)) {
    $p = Start-Process -FilePath (Get-Command node.exe).Source -ArgumentList "`"$projectRoot\frontend\node_modules\vite\bin\vite.js`" --host 127.0.0.1 --port 5173" -WorkingDirectory "$projectRoot\frontend" -WindowStyle Hidden -RedirectStandardOutput "$runtime\frontend.log" -RedirectStandardError "$runtime\frontend-error.log" -PassThru
    $p.Id | Set-Content "$runtime\frontend.pid"
    Wait-Port 5173
}
$health = Invoke-RestMethod 'http://127.0.0.1:8000/api/health'
Write-Host "Frontend: http://127.0.0.1:5173 | API docs: http://127.0.0.1:8000/docs | Database: $($health.database)"
