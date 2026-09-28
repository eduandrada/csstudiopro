@echo off
chcp 65001 >nul
title CS 1.6 Spray WAD Generator
cd /d "%~dp0"
echo ====================================================================
echo           CS 1.6 SPRAY WAD GENERATOR - MOTOR GOLDRSC
echo ====================================================================
echo.
echo [1/2] Verificando dependencias Python...
python -m pip install -r requirements.txt --quiet
echo [2/2] Iniciando servidor web en http://localhost:5000...
echo.
start http://localhost:5000
python app.py
pause
