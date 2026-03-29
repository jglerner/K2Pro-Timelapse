@echo off
REM K2Pro Timelapse launcher — Windows
REM Usage:  k2pro-timelapse.bat [PRINTER-IP]
REM Runs in auto mode: monitors the printer and captures one timelapse per print,
REM then waits for the next print automatically.

cd /d "%~dp0"
call venv\Scripts\activate
python k2pro_timelapse.py --auto %*
