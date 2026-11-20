Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host "               STARTING PHARMINTEL HEALTHCARE PLATFORM" -ForegroundColor Green
Write-Host "   AI-Powered Smart Pharmacy Network for Drug Safety and Delivery" -ForegroundColor White
Write-Host "=====================================================================" -ForegroundColor Cyan

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "`n[1/2] Starting FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir\backend'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

Start-Sleep -Seconds 3

Write-Host "[2/2] Starting Vite Frontend on http://localhost:5173 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptDir\frontend'; npm run dev"

Write-Host "`n=====================================================================" -ForegroundColor Cyan
Write-Host "PharmIntel running!" -ForegroundColor Green
Write-Host "Frontend Portal:  http://localhost:5173" -ForegroundColor White
Write-Host "Interactive APIs: http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "=====================================================================" -ForegroundColor Cyan
