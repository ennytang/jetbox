@echo off
title JETBOX v3 - ENNYTANG
echo.
echo ============================================
echo   JETBOX v3 - Type Beat Automation
echo   by ENNYTANG
echo ============================================
echo.

:: ── Kill any leftover processes from previous session ──
echo [0/4] Cleaning up previous session...
taskkill /f /im python.exe >nul 2>&1
:: Kill node processes running on port 5173 or 5174
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173 " 2^>nul') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5174 " 2^>nul') do taskkill /f /pid %%a >nul 2>&1
timeout /t 1 /nobreak >nul

:: ── Create directories if needed ──
if not exist "BEATS"            mkdir BEATS
if not exist "ARTWORKS\RAGE"    mkdir "ARTWORKS\RAGE"
if not exist "ARTWORKS\MELODIC" mkdir "ARTWORKS\MELODIC"
if not exist "OUTPUT"           mkdir OUTPUT

echo [1/4] Installing Python dependencies...
pip install -r requirements.txt -q 2>nul

echo [2/4] Installing frontend dependencies...
cd frontend
call npm install --silent 2>nul
cd ..

echo [3/4] Starting Flask API backend (port 5001)...
start /B cmd /c "cd backend && python app.py"

:: Wait for backend to start
timeout /t 2 /nobreak >nul

echo [4/4] Starting React frontend (port 5173)...
start /B cmd /c "cd frontend && npm run dev -- --port 5173 --strictPort"

:: Wait for frontend to start
timeout /t 4 /nobreak >nul

:: Open browser on fixed port 5173
start http://localhost:5173

echo.
echo ============================================
echo   API:       http://localhost:5001
echo   Dashboard: http://localhost:5173
echo   Health:    http://localhost:5001/api/health
echo ============================================
echo.
echo   Drop WAV files into BEATS/ to get started!
echo.
echo   Press any key to STOP all services...
pause >nul

:: ── Kill all services cleanly ──
echo Stopping services...
taskkill /f /im python.exe >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173 " 2^>nul') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5001 " 2^>nul') do taskkill /f /pid %%a >nul 2>&1
echo Services stopped. Bye!
