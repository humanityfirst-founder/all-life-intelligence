@echo off
cd /d "%~dp0"
echo ALL-LIFE INTELLIGENCE 1.6 - KONTEXTPRUEFUNG OHNE API
where py >nul 2>nul
if %errorlevel%==0 (py -3 context_review_v16.py --mode offline --open) else (python context_review_v16.py --mode offline --open)
echo.
pause
