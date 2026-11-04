@echo off
cd /d "%~dp0"
echo ALL-LIFE INTELLIGENCE 1.6.2 - OFFLINE DIAGNOSE OHNE API
where py >nul 2>nul
if %errorlevel%==0 (py -3 diagnose_single_v162.py --open) else (python diagnose_single_v162.py --open)
echo.
pause
