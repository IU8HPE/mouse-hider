@echo off
setlocal
cd /d %~dp0

set INST=%~dp0python-3.11.9-x86-installer.exe
set TARGET=%~dp0py311x86

if not exist "%INST%" (
  echo Missing installer: %INST%
  echo Download python-3.11.9.exe (32-bit) from python.org and place it in this folder.
  exit /b 1
)

"%INST%" /quiet InstallAllUsers=0 TargetDir="%TARGET%" PrependPath=0 Include_launcher=0 Include_pip=1 Include_test=0
if errorlevel 1 exit /b 1

if not exist "%TARGET%\python.exe" (
  echo Python x86 installation failed.
  exit /b 1
)

"%TARGET%\python.exe" -m ensurepip --upgrade
exit /b %errorlevel%
