#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
CSStudioPro - SISTEMA CENTRALIZADO DE LOGGING ROTATIVO
=============================================================================
Implementa un logger rotativo basado en logging.handlers.RotatingFileHandler:
 - Tamaño máximo por archivo: 5 MB
 - Respaldos rotativos: 2 copias (.1, .2)
 - Salida dual: Archivo `logs/studio.log` y salida a consola estándar.
 - Manejo seguro de rutas en entornos de desarrollo y PyInstaller (--onedir).
=============================================================================
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler

def get_writable_dir() -> str:
    """Devuelve un directorio con permisos de escritura (raíz del ejecutable o proyecto)."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def setup_logger(name: str = "CSStudioPro") -> logging.Logger:
    """Inicializa y devuelve el logger principal con rotación automática."""
    logger_instance = logging.getLogger(name)
    if logger_instance.hasHandlers():
        return logger_instance

    logger_instance.setLevel(logging.DEBUG)

    base_dir = get_writable_dir()
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "studio.log")

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # 1. Handler de archivo con rotación (5 MB, 2 backups)
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=2,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger_instance.addHandler(file_handler)

    # 2. Handler de consola (StreamHandler)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("[%(levelname)s] [%(name)s] %(message)s")
    console_handler.setFormatter(console_formatter)
    logger_instance.addHandler(console_handler)

    return logger_instance

# Instancia global por defecto
logger = setup_logger()
