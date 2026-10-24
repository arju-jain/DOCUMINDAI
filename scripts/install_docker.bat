@echo off
setlocal
echo ========================================================
echo DocuMind AI - Docker Desktop ^& Virtual Machine Platform Setup
echo ========================================================
echo.
echo Checking Administrator privileges...
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script requires Administrator privileges!
    echo Please right-click this file and select 'Run as administrator'.
    echo.
    pause
    exit /b 1
)

echo [1/3] Enabling Windows Virtual Machine Platform and WSL...
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
wsl.exe --update

echo.
echo [2/3] Installing Docker Desktop (All-users installation with WSL 2 backend)...
"C:\Users\arjun\OneDrive\Desktop\DockerDesktopInstaller.exe" install --accept-license --backend=wsl-2

echo.
echo [3/3] Docker Desktop installation step finished.
echo If Windows displays a reboot prompt, please restart your computer to finalize virtualization.
echo Otherwise, launch Docker Desktop from the Start Menu.
echo.
pause
