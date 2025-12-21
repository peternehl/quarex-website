@echo off
REM Quarex Candidate Scrapers - Windows Batch File
REM Run this manually or schedule with Windows Task Scheduler

echo ============================================
echo Quarex Candidate Scrapers (2026)
echo ============================================
echo.

cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo Running Senate scraper...
python senate_scraper.py

echo.
echo Running Governor scraper...
python governor_scraper.py

echo.
echo ============================================
echo Scrapers completed.
echo ============================================

pause
