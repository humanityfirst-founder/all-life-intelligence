@echo off
cd /d "%~dp0"
set ALI_OFFLINE_ONLY=1
py -3 dev_cycle_v18.py
if errorlevel 1 (echo Fehler: Qualitaetsschranke nicht bestanden.)
pause
