@echo off
setlocal
cd /d "%~dp0"

if exist "%~dp0dist\DocxToMD\DocxToMD.exe" (
  start "" "%~dp0dist\DocxToMD\DocxToMD.exe"
  exit /b 0
)

if exist "%~dp0dist\DocxToMD.exe" (
  start "" "%~dp0dist\DocxToMD.exe"
  exit /b 0
)

python "%~dp0app.py"
exit /b %ERRORLEVEL%
