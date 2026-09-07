@echo off
echo.
echo ================================================
echo   Voice Medical Agent - Starting...
echo ================================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat 2>nul
if errorlevel 1 (
    echo ERROR: Virtual environment not found!
    echo Run setup.ps1 first to create it.
    echo.
    echo   PowerShell: .\setup.ps1
    echo.
    pause
    exit /b 1
)

REM Start server
echo Starting server on http://localhost:8000
echo Press Ctrl+C to stop.
echo.
python server.py
