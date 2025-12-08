@echo off
REM PaperBot Startup Script for Windows
REM This script starts both the backend and frontend servers

setlocal enabledelayedexpansion

set PROJECT_DIR=%~dp0
set BACKEND_DIR=%PROJECT_DIR%
set FRONTEND_DIR=%PROJECT_DIR%frontend
set VENV_DIR=%PROJECT_DIR%venv

echo.
echo ========================================
echo Starting PaperBot
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

REM Activate virtual environment
call "%VENV_DIR%\Scripts\activate.bat"

REM Check dependencies
echo Checking dependencies...
python -c "import django" 2>nul
if errorlevel 1 (
    echo Installing backend dependencies...
    pip install -r requirements.txt
)

if not exist "%FRONTEND_DIR%\node_modules" (
    echo Installing frontend dependencies...
    cd "%FRONTEND_DIR%"
    call npm install
    cd "%BACKEND_DIR%"
)

REM Start backend
echo Starting backend server...
start "PaperBot Backend" cmd /k "cd /d %BACKEND_DIR% && %VENV_DIR%\Scripts\python.exe manage.py runserver 8000"

REM Wait a bit
timeout /t 3 /nobreak >nul

REM Start frontend
echo Starting frontend server...
cd "%FRONTEND_DIR%"
start "PaperBot Frontend" cmd /k "npm run dev"
cd "%BACKEND_DIR%"

echo.
echo ========================================
echo PaperBot Status
echo ========================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Close the command windows to stop the servers.
echo.

pause


