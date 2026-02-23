@echo off
REM Quarex Database Explorer Launcher
REM Starts the server and opens the browser

cd /d E:\projects\websites\Quarex

echo Starting Quarex Database Explorer...
echo.

REM Open browser after a short delay (start in background)
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8765"

REM Start the server (this blocks until Ctrl+C)
python tools/quarex-db-server.py

pause
