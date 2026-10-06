@echo off
title Retail Analytics - Startup

echo [1/3] Starting Redis...
start /B "" "C:\Users\Gafur\AppData\Local\Redis\redis-server.exe" --port 6379
timeout /T 2 /NOBREAK >nul

echo [2/3] Starting Backend (FastAPI)...
cd /D "%~dp0backend"
start "Backend API" cmd /k "set DATABASE_URL=postgresql+psycopg://retail:retail123@localhost:5432/retail_analytics && set REDIS_URL=redis://localhost:6379/0 && set JWT_SECRET=retail-analytics-secret-key-change-in-production && set CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173 && set AI_SERVICE_API_KEY=ai-service-internal-key && py -m uvicorn app.main:app --host 0.0.0.0 --port 8001"
timeout /T 5 /NOBREAK >nul

echo [3/3] Starting Frontend (React)...
cd /D "%~dp0frontend"
start "Frontend Dashboard" cmd /k "npm run dev"
timeout /T 4 /NOBREAK >nul

echo.
echo ============================================
echo  App is running!
echo  Dashboard : http://localhost:5173
echo  API Docs  : http://localhost:8001/docs
echo  Login     : admin / admin123
echo ============================================
start http://localhost:5173
