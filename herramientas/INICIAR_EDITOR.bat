@echo off
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 goto sinpython

python -X utf8 "editor_horarios.py"
if errorlevel 1 pause
exit /b 0

:sinpython
echo.
echo  No se encontro Python en el PATH.
echo  Instala Python 3.11 o superior desde https://www.python.org/downloads/
echo  y marca la opcion "Add python.exe to PATH".
echo.
pause
exit /b 1
