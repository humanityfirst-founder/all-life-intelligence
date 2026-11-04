@echo off
cd /d "%~dp0"
echo ALL-LIFE INTELLIGENCE v1.3 - Originalquellen-Check (kostenlos)
where py >nul 2>nul
if %errorlevel%==0 (py -3 sourcecheck.py --open-report) else (python sourcecheck.py --open-report)
echo.
pause
