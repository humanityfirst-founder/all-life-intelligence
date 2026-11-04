@echo off
cd /d "%~dp0"
echo ALL-LIFE INTELLIGENCE 1.4 - Robustheitstest (offline / kostenlos)
where py >nul 2>nul
if %errorlevel%==0 (py -3 robustness_lab.py --open) else (python robustness_lab.py --open)
echo.
pause
