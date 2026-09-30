@echo off
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -LiteralPath C:\UF212\package.zip -DestinationPath C:\UF212\package -Force"
if errorlevel 1 exit /b %ERRORLEVEL%
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File C:\UF212\windows-native-run.ps1 > C:\UF212\windows-launcher.txt 2>&1
echo LAUNCHER_RC=%ERRORLEVEL%>> C:\UF212\windows-launcher.txt
exit /b %ERRORLEVEL%
