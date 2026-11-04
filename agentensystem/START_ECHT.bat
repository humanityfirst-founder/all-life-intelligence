@echo off
cd /d "%~dp0"
echo ALL-LIFE INTELLIGENCE v1.3 - kostenpflichtige Forschungsrunde
where py >nul 2>nul
if %errorlevel%==0 (py -3 agent.py --mode live --open-report) else (python agent.py --mode live --open-report)
echo.
pause
