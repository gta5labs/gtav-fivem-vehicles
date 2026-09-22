@echo off
setlocal
cd /d "%~dp0"
title FiveLabs Vehicle DB Setup

echo ============================================================
echo  FiveLabs Vehicle DB - Official FiveM Database Setup
echo ============================================================
echo.
echo This downloads the official FiveM vehicle database and
echo official preview images into the local vehicles folder.
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    set "PY=py -3"
    goto :run
)

where python >nul 2>nul
if %errorlevel%==0 (
    set "PY=python"
    goto :run
)

echo [ERROR] Python 3 was not found.
echo.
echo Install Python 3 from https://www.python.org/downloads/
echo and enable "Add Python to PATH", then run this file again.
echo.
pause
exit /b 1

:run
%PY% db_setup.py
if %errorlevel% neq 0 (
    echo.
    echo Setup failed. Read the error above.
    pause
    exit /b 1
)

echo.
echo Opening Vehicle DB...
start "" "%~dp0index.html"
exit /b 0
