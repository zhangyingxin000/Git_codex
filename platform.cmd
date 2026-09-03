@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0platform.ps1" %*
exit /b %ERRORLEVEL%
