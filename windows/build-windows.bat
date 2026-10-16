@echo off
REM ============================================================
REM  MK1300 RGB Controller — Windows Build Script
REM  Run this on a Windows machine to produce:
REM    dist\mk1300-win.exe          (standalone CLI binary)
REM    dist\mk1300-win-setup-1.0.0.exe  (local installer)
REM ============================================================

echo [1/3] Installing Python dependencies...
pip install pyinstaller hidapi --quiet
if %errorlevel% neq 0 (
    echo ERROR: pip install failed. Make sure Python 3.10+ is on PATH.
    exit /b 1
)

echo [2/3] Building standalone exe with PyInstaller...
pyinstaller mk1300-win.spec --noconfirm --clean
if %errorlevel% neq 0 (
    echo ERROR: PyInstaller build failed.
    exit /b 1
)

echo [3/3] Compiling Inno Setup installer...
REM Try default Inno Setup 6 install paths
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="C:\Program Files\Inno Setup 6\ISCC.exe"

if exist %ISCC% (
    %ISCC% windows\mk1300-win-setup.iss
    echo.
    echo ============================================================
    echo  SUCCESS! Installer ready:
    echo    dist\mk1300-win-setup-1.0.0.exe
    echo ============================================================
) else (
    echo.
    echo NOTE: Inno Setup 6 not found. Standalone exe is ready at:
    echo    dist\mk1300-win.exe
    echo.
    echo To build the .exe installer, install Inno Setup 6 from:
    echo    https://jrsoftware.org/isdl.php
    echo Then run:  windows\mk1300-win-setup.iss
)
