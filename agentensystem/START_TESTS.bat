@echo off
cd /d "%~dp0"
echo ALL-LIFE INTELLIGENCE 1.6 - Offline-Tests
where py >nul 2>nul
if %errorlevel%==0 (py -3 -m unittest discover -s tests -v) else (python -m unittest discover -s tests -v)
echo.
pause
