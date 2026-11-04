@echo off
cd /d "%~dp0"
echo ALL-LIFE INTELLIGENCE 1.6.1 - KOSTENLOSE KORREKTUR DES BERICHTS
where py >nul 2>nul
if %errorlevel%==0 (py -3 resume_context_v161.py --open) else (python resume_context_v161.py --open)
echo.
pause
