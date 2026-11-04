@echo off
cd /d "%~dp0"
echo ALL-LIFE INTELLIGENCE v1.3 - Offline-Verbesserungsanalyse, keine API-Kosten
where py >nul 2>nul
if %errorlevel%==0 (py -3 improvement_agent.py --open) else (python improvement_agent.py --open)
echo.
pause
