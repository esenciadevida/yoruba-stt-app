$ErrorActionPreference = "Continue"
$root = $PSScriptRoot
$pwsh = "C:\Users\ZBOOK\Tools\PowerShell-7.6.4\pwsh.exe"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   Bami-Soro App - Starting All Servers    " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# --- Kill old processes on known ports ---
Write-Host "Stopping old servers..." -ForegroundColor DarkYellow
@(8000, 3000) | ForEach-Object {
    $port = $_
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conns) {
        $conns | ForEach-Object {
            $processId = $_.OwningProcess
            if ($processId -and $processId -ne 0) {
                Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                Write-Host "  Killed PID $processId on port $port" -ForegroundColor Red
            }
        }
    }
}
Start-Sleep -Seconds 2
Write-Host ""

# --- Backend (FastAPI) ---
Write-Host "[1/2] Starting Backend (FastAPI on port 8000)..." -ForegroundColor Yellow
Start-Process $pwsh -ArgumentList @(
    "-NoExit", "-Command",
    "chcp 65001 > `$null; " +
    "`$env:PYTHONIOENCODING='utf-8'; " +
    "`$env:PYTHONUTF8=1; " +
    "cd '$root\backend'; " +
    "& '$root\venv\Scripts\activate.ps1'; " +
    "python -m uvicorn main:app --reload --port 8000"
) -WindowStyle Normal

Start-Sleep -Seconds 2

# --- Frontend (Next.js) ---
Write-Host "[2/2] Starting Frontend (Next.js on port 3000)..." -ForegroundColor Yellow
Start-Process $pwsh -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$root\frontend'; " +
    "npm run dev"
) -WindowStyle Normal

Write-Host ""
Write-Host "  NOTE: The Streamlit app (app.py, port 8501) is DEPRECATED." -ForegroundColor DarkGray
Write-Host "        Use the web app (http://localhost:3000) instead. It offers" -ForegroundColor DarkGray
Write-Host "        the same transcription/translation features plus much more." -ForegroundColor DarkGray
Write-Host "        Remove app.py + streamlit from requirements.txt when ready." -ForegroundColor DarkGray
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  All servers launched in separate windows  " -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend  : http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend : http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Close this window to keep servers running." -ForegroundColor DarkGray
