@echo off
setlocal
cd /d %~dp0
set PY32=%~dp0py311x86\python.exe
if not exist "%PY32%" (
  echo Missing 32-bit Python at: %PY32%
  echo Install Python 3.11 32-bit or copy it to .\py311x86 first.
  exit /b 1
)
"%PY32%" -m pip install -r requirements_lite32.txt
if errorlevel 1 exit /b 1
"%PY32%" -m PyInstaller --noconfirm --clean MouseHiderLite32.spec
exit /b %errorlevel%
