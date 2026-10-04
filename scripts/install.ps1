param([string]$Python = 'python')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot
$runtime = Join-Path $projectRoot '.runtime'
New-Item -ItemType Directory -Force $runtime | Out-Null
if (!(Test-Path '.venv\Scripts\python.exe')) { & $Python -m venv .venv; if ($LASTEXITCODE) { throw 'Python venv creation failed' } }
& '.\.venv\Scripts\python.exe' -m pip install -r backend\requirements.txt
if ($LASTEXITCODE) { throw 'Python dependencies failed' }
Push-Location frontend
try { npm.cmd ci; if ($LASTEXITCODE) { throw 'Frontend dependencies failed' } } finally { Pop-Location }
$mysqlHome = Join-Path $runtime 'mysql-8.4.11-winx64'
if (!(Test-Path "$mysqlHome\bin\mysqld.exe")) {
    if (!(Test-Path "$runtime\mysql.zip")) { curl.exe -f -L --retry 2 'https://cdn.mysql.com/Downloads/MySQL-8.4/mysql-8.4.11-winx64.zip' -o "$runtime\mysql.zip"; if ($LASTEXITCODE) { throw 'MySQL download failed' } }
    Expand-Archive -LiteralPath "$runtime\mysql.zip" -DestinationPath $runtime -Force
}
$basePath = $mysqlHome.Replace('\','/')
$dataPath = "$runtime/mysql-data".Replace('\','/')
$logPath = "$runtime/mysql-error.log".Replace('\','/')
@"
[mysqld]
basedir=$basePath
datadir=$dataPath
port=3307
bind-address=127.0.0.1
mysqlx=0
character-set-server=utf8mb4
log-error=$logPath
"@ | Set-Content "$runtime\my.ini" -Encoding ascii
if (!(Test-Path "$runtime\mysql-data")) {
    & "$mysqlHome\bin\mysqld.exe" "--defaults-file=$runtime\my.ini" --initialize-insecure
    if ($LASTEXITCODE) { throw 'MySQL initialization failed; check .runtime/mysql-error.log' }
}
if (!(Test-Path "$runtime\mysql-credentials.json")) {
    $p = Start-Process -FilePath "$mysqlHome\bin\mysqld.exe" -ArgumentList "--defaults-file=`"$runtime\my.ini`"" -WindowStyle Hidden -PassThru
    $p.Id | Set-Content "$runtime\mysql.pid"
    for ($i=0; $i -lt 40; $i++) {
        $tcp = New-Object System.Net.Sockets.TcpClient
        try { $tcp.Connect('127.0.0.1',3307); break } catch { Start-Sleep -Milliseconds 500 } finally { $tcp.Dispose() }
    }
    & '.\.venv\Scripts\python.exe' scripts\setup_db.py
    if ($LASTEXITCODE) { throw 'Database account setup failed' }
}
& "$PSScriptRoot\start.ps1"
