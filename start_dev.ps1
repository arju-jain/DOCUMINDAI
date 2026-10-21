<#
.SYNOPSIS
    DocuMind AI - Unified Development Starter (Optional Convenience Script)

.DESCRIPTION
    Launches both the FastAPI backend (127.0.0.1:8000) and the static frontend
    HTTP server (127.0.0.1:8081) in separate PowerShell processes so logs remain
    fully visible and each service can be cleanly stopped with Ctrl+C.

    You can also run each command manually:
      Backend:
        .\venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
      Frontend:
        python -m http.server 8081 --bind 127.0.0.1 --directory frontend
#>

$RootPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RootPath

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   DocuMind AI - Unified Full-Stack Development Server   " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Check Python virtual environment
$PythonVenv = Join-Path $RootPath "venv\Scripts\python.exe"
if (-not (Test-Path $PythonVenv)) {
    Write-Warning "Virtual environment not found at .\venv\Scripts\python.exe"
    Write-Host "Using system 'python' as fallback..." -ForegroundColor Yellow
    $PythonCmd = "python"
} else {
    $PythonCmd = $PythonVenv
}

# 2. Check Port Availability
function Test-PortOpen ($Port) {
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Parse("127.0.0.1"), $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

$Port8000Available = Test-PortOpen 8000
$Port8081Available = Test-PortOpen 8081

if (-not $Port8000Available) {
    Write-Warning "Port 8000 is currently occupied (a backend process may already be running)."
    Write-Host "Verify http://127.0.0.1:8000/api/health in your browser." -ForegroundColor Gray
}

if (-not $Port8081Available) {
    Write-Warning "Port 8081 is currently occupied (a frontend server may already be running)."
    Write-Host "Verify http://127.0.0.1:8081 in your browser." -ForegroundColor Gray
}

Write-Host ""
Write-Host "Starting services in dedicated console windows for live logging..." -ForegroundColor Green

# 3. Launch Backend
if ($Port8000Available) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$RootPath'; Write-Host '--- DocuMind AI Backend Server (Port 8000) ---' -ForegroundColor Cyan; & '$PythonCmd' -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"
    Write-Host "  [OK] Backend launching on  http://127.0.0.1:8000 (Swagger: http://127.0.0.1:8000/docs)" -ForegroundColor Cyan
} else {
    Write-Host "  [SKIP] Backend already active on http://127.0.0.1:8000" -ForegroundColor Gray
}

# 4. Launch Frontend
if ($Port8081Available) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$RootPath'; Write-Host '--- DocuMind AI Frontend Server (Port 8081) ---' -ForegroundColor Green; & '$PythonCmd' -m http.server 8081 --bind 127.0.0.1 --directory frontend"
    Write-Host "  [OK] Frontend launching on http://127.0.0.1:8081/" -ForegroundColor Green
} else {
    Write-Host "  [SKIP] Frontend already active on http://127.0.0.1:8081" -ForegroundColor Gray
}

# 5. Launch in Google Chrome
Start-Sleep -Seconds 1
$ChromePaths = @(
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
)
$ChromeExe = $ChromePaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($ChromeExe) {
    Start-Process $ChromeExe -ArgumentList "--new-window http://127.0.0.1:8081"
    Write-Host "  [OK] Launched in Google Chrome: http://127.0.0.1:8081" -ForegroundColor Green
} else {
    Start-Process "http://127.0.0.1:8081"
    Write-Host "  [OK] Launched in default browser: http://127.0.0.1:8081" -ForegroundColor Green
}

Write-Host ""
Write-Host "URLs:" -ForegroundColor White
Write-Host "  - Frontend App:   http://127.0.0.1:8081/" -ForegroundColor Yellow
Write-Host "  - Backend API:    http://127.0.0.1:8000/api" -ForegroundColor Yellow
Write-Host "  - API Swagger UI: http://127.0.0.1:8000/docs" -ForegroundColor Yellow
Write-Host "  - Health Check:   http://127.0.0.1:8000/api/health" -ForegroundColor Yellow
Write-Host ""
Write-Host "To stop services, close the opened PowerShell windows or press Ctrl+C in them." -ForegroundColor Gray
Write-Host "========================================================" -ForegroundColor Cyan
