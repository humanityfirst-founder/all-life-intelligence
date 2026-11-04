@echo off
cd /d "%~dp0"
echo ALL-LIFE INTELLIGENCE v1.3 - kostenlose Demo
where py >nul 2>nul
if %errorlevel%==0 (py -3 agent.py --mode demo --open-report) else (python agent.py --mode demo --open-report)
echo.
pause
