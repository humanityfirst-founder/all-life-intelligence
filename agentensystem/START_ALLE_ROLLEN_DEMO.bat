@echo off
cd /d "%~dp0"
echo ALL-LIFE INTELLIGENCE v1.3 - kostenlose Voll-Demo
where py >nul 2>nul
if %errorlevel%==0 (py -3 agent.py --mode demo --roles A1,A2,A3,A4,A5,A7 --open-report) else (python agent.py --mode demo --roles A1,A2,A3,A4,A5,A7 --open-report)
echo.
pause
