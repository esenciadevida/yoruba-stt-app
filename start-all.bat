@echo off
chcp 65001 > nul
echo ============================================
echo    Bami-Soro App - Starting All Servers
echo ============================================
echo.

cd /d "%~dp0"

echo [1/3] Starting Backend (FastAPI on port 8000)...
start "Backend - FastAPI" powershell -NoExit -Command "chcp 65001 > `$null; `$env:PYTHONIOENCODING='utf-8'; `$env:PYTHONUTF8=1; cd '%~dp0backend'; & '%~dp0venv\Scripts\activate.ps1'; python -m uvicorn main:app --reload --port 8000"
timeout /t 2 /nobreak > nul

echo [2/3] Starting Frontend (Next.js on port 3000)...
start "Frontend - Next.js" powershell -NoExit -Command "cd '%~dp0frontend'; npm run dev"
timeout /t 2 /nobreak > nul

echo [3/3] Starting Streamlit (on port 8501)...
start "Streamlit" powershell -NoExit -Command "chcp 65001 > `$null; `$env:PYTHONIOENCODING='utf-8'; `$env:PYTHONUTF8=1; cd '%~dp0'; & '%~dp0venv\Scripts\activate.ps1'; streamlit run app.py"

echo.
echo ============================================
echo   All servers launched in separate windows
echo ============================================
echo.
echo   Backend  : http://localhost:8000
echo   Frontend : http://localhost:3000
echo   Streamlit: http://localhost:8501
echo.
echo Close this window to keep servers running.
pause
