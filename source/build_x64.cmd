@echo off
setlocal
cd /d %~dp0
py -3.12 -m pip install -r requirements_x64.txt
if errorlevel 1 exit /b 1
py -3.12 -m PyInstaller --noconfirm --clean MouseHider64.spec
exit /b %errorlevel%
