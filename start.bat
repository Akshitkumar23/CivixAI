@echo off
title CivixAI - Starting Servers
color 0A

echo.
echo  =============================================
echo   CivixAI - Starting Development Servers
echo  =============================================
echo.

:: Start Python ML API in a new terminal window
echo  [1/2] Starting Python ML API on port 8000...
start "CivixAI ML API (Port 8000)" cmd /k "cd /d %~dp0 && python -m uvicorn services.ml_api.main:app --host 127.0.0.1 --port 8000 --reload"

:: Wait 5 seconds for the ML API to initialize
timeout /t 5 /nobreak > nul

:: Start Next.js frontend in a new terminal window
echo  [2/2] Starting Next.js Frontend on port 3000...
start "CivixAI Frontend (Port 3000)" cmd /k "cd /d %~dp0 && npm run dev"

echo.
echo  Both servers are starting in separate windows.
echo  ML API  : http://127.0.0.1:8000
echo  Frontend: http://127.0.0.1:3000
echo.
pause
