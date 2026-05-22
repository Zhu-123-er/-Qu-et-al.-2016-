@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================
echo Qu2016 precipitation method reproduction
echo Running offline demo mode
echo ==========================================
echo.

echo Checking Python...
python --version
if errorlevel 1 (
    echo Python was not found. Please install Python 3.10 or later.
    pause
    exit /b 1
)

echo.
echo Creating virtual environment if needed...
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
)

echo.
echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Running full workflow with deterministic demo data...
python scripts\00_run_all.py --demo
if errorlevel 1 (
    echo Demo workflow failed.
    pause
    exit /b 1
)

echo.
echo Demo workflow finished successfully.
echo This verifies the code without internet access.
pause
