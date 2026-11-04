@echo off
cd /d "%~dp0"
set "ALI_OFFLINE_ONLY=1"
python research_board_v19.py
if errorlevel 1 (
  echo.
  echo Forschungsrat nicht bestanden. Kein automatischer Wechsel auf eine neue Version.
)
pause
