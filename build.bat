@echo off
setlocal
cd /d "%~dp0"

echo [1/2] 安裝打包依賴...
python -m pip install -r requirements.txt -r requirements-build.txt
if errorlevel 1 exit /b 1

echo [2/2] 使用 PyInstaller 打包（onedir、關閉 UPX）...
if exist "%~dp0dist\DocxToMD.exe" del /f /q "%~dp0dist\DocxToMD.exe"
python -m PyInstaller --noconfirm --clean DocxToMD.spec
if errorlevel 1 exit /b 1

echo.
echo 完成！請整個資料夾一起使用／分享：
echo   %~dp0dist\DocxToMD\
echo   主程式：%~dp0dist\DocxToMD\DocxToMD.exe
echo.
echo 若公司防毒仍誤判，請用「執行原始碼」方式：
echo   python app.py
echo 或請 IT 將 DocxToMD 資料夾加入 Apex One 排除清單。
exit /b 0
