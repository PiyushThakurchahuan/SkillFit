@echo off
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
)
echo Installing requirements...
venv\Scripts\python.exe -m pip install -r requirements.txt
echo.
echo Starting SkillFit at http://127.0.0.1:8001
venv\Scripts\python.exe -m uvicorn backend.main:app --reload --port 8001
pause
