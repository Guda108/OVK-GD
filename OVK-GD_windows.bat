@echo off
setlocal
title OVK-GD - Dr. Gerardo Diaz
chcp 65001 >nul
cd /d "%~dp0"

if not exist "OVK-GD.py" (
    echo No se encontro OVK-GD.py. Extrae todo el ZIP antes de abrir este archivo.
    pause
    exit /b 1
)

py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if not errorlevel 1 goto usar_py

python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>nul
if not errorlevel 1 goto usar_python

echo No se encontro Python 3.8 o superior.
where winget >nul 2>nul
if errorlevel 1 (
    echo Instala Python desde https://www.python.org/downloads/windows/
    echo Activa la opcion de agregar Python al PATH y vuelve a abrir este archivo.
    pause
    exit /b 1
)
set /p "RESPUESTA=Instalar Python 3.12 con winget? (S/N): "
if /i not "%RESPUESTA%"=="S" exit /b 1
winget install --id Python.Python.3.12 -e --silent --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo La instalacion no termino correctamente. Revisa el mensaje anterior.
    pause
    exit /b 1
)
echo Cierra esta ventana y vuelve a abrir OVK-GD_windows.bat.
pause
exit /b 0

:usar_py
py -3 OVK-GD.py %*
goto resultado

:usar_python
python OVK-GD.py %*

:resultado
set "RESULTADO=%errorlevel%"
if not "%RESULTADO%"=="0" echo OVK-GD termino con codigo %RESULTADO%.
pause
exit /b %RESULTADO%
