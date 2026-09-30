@echo off
setlocal

set "ROOT=%~dp0"
set "INSTALLER=%ROOT%scripts\install-cli-windows.ps1"
if not exist "%INSTALLER%" set "INSTALLER=%ROOT%install-cli-windows.ps1"

if not exist "%INSTALLER%" (
  echo UnpackFlow installer was not found.
  echo Please extract the complete Windows package before running install.bat.
  exit /b 2
)

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%INSTALLER%" %*
set "RESULT=%ERRORLEVEL%"

if not "%RESULT%"=="0" (
  echo.
  echo UnpackFlow installation failed with exit code %RESULT%.
  exit /b %RESULT%
)

echo.
echo UnpackFlow installation completed.
echo Open a new terminal and run: unpack-flow version
exit /b 0
