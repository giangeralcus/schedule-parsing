@echo off
echo =============================================
echo   Installing Tesseract OCR for Schedule Parser
echo =============================================
echo.

REM Check if winget is available
where winget >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo Installing via winget...
    winget install UB-Mannheim.TesseractOCR --accept-source-agreements --accept-package-agreements
    goto :done
)

REM Check if choco is available
where choco >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo Installing via chocolatey...
    choco install tesseract -y
    goto :done
)

echo.
echo Neither winget nor chocolatey found.
echo Please install Tesseract manually:
echo.
echo   1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
echo   2. Run the installer
echo   3. Install to default location: C:\Program Files\Tesseract-OCR
echo.
start https://github.com/UB-Mannheim/tesseract/wiki
pause
exit /b 1

:done
echo.
echo =============================================
echo   Installation complete!
echo   You may need to restart your terminal.
echo =============================================
pause
