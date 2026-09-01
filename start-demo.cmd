@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-demo.ps1" %*
set "DEMO_EXIT_CODE=%ERRORLEVEL%"
if not "%DEMO_EXIT_CODE%"=="0" pause
exit /b %DEMO_EXIT_CODE%
