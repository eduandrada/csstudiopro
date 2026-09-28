@echo off
title CS 1.6 Studio Pro - Compilador EXE (PyInstaller)
color 0A
echo ==============================================================================
echo  CS 1.6 Modding ^& Tuning Studio Pro - Compilador Automatico a .EXE
echo ==============================================================================
echo.

cd /d "%~dp0"

echo [*] Verificando dependencias (Flask, Pillow, pywebview, PyInstaller)...
python -m pip install --quiet pyinstaller pywebview flask pillow

echo [*] Compilando proyecto con PyInstaller a dist\CSStudioPro\CSStudioPro.exe...
python build_exe.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [EXITO] Compilacion completada sin errores.
    echo Puedes ejecutar: dist\CSStudioPro\CSStudioPro.exe
) else (
    echo.
    echo [ERROR] La compilacion ha fallado. Revisa los mensajes anteriores.
)

echo.
pause
