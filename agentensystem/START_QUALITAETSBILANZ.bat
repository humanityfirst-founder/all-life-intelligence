@echo off
cd /d "%~dp0"
echo ALL-LIFE INTELLIGENCE v1.3 - OFFLINE-Qualitaetsbilanz, keine API-Kosten
where py >nul 2>nul
if %errorlevel%==0 (py -3 review_export.py --open) else (python review_export.py --open)
echo.
pause
