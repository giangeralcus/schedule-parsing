@echo off
title Schedule Parser GUI
cd /d "%~dp0"
python schedule_gui.py %*
if %ERRORLEVEL% NEQ 0 pause
