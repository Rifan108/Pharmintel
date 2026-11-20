@echo off
echo =====================================================================
echo                STARTING PHARMINTEL HEALTHCARE PLATFORM
echo    AI-Powered Smart Pharmacy Network for Drug Safety and Delivery
echo =====================================================================

echo.
echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "PharmIntel Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak > nul

echo [2/2] Starting Vite Frontend on http://localhost:5173 ...
start "PharmIntel Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo =====================================================================
echo PharmIntel is starting!
echo Frontend: http://localhost:5173
echo Backend API Docs: http://127.0.0.1:8000/docs
echo =====================================================================
