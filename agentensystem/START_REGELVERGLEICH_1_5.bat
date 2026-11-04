@echo off
cd /d "%~dp0"
echo ALL-LIFE INTELLIGENCE 1.5 - Regelvergleich offline und kostenlos
where py >nul 2>nul
if %errorlevel%==0 (py -3 rule_comparison_v15.py --open) else (python rule_comparison_v15.py --open)
echo.
pause
