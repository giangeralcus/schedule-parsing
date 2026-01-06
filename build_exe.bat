@echo off
echo ================================================
echo   Building Schedule Parser EXE
echo ================================================
echo.

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing PyInstaller...
    pip install pyinstaller
)

echo.
echo Building EXE...
echo.

pyinstaller --onefile --windowed ^
    --name "ScheduleParser" ^
    --icon "icon.ico" ^
    --add-data "core;core" ^
    --add-data "processors;processors" ^
    --add-data "formatters;formatters" ^
    --hidden-import "PIL" ^
    --hidden-import "cv2" ^
    --hidden-import "numpy" ^
    --hidden-import "pytesseract" ^
    --hidden-import "pyperclip" ^
    --hidden-import "tkinterdnd2" ^
    schedule_gui.py

echo.
if exist "dist\ScheduleParser.exe" (
    echo ================================================
    echo   SUCCESS! EXE created at: dist\ScheduleParser.exe
    echo ================================================
    echo.
    echo Copy these to the same folder as EXE:
    echo   - 1_screenshots folder
    echo   - 2_hasil folder
) else (
    echo Build failed! Check errors above.
)

pause
