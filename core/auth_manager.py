#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
CS 1.6 STUDIO PRO - MÓDULO DE AUTENTICACIÓN Y CIBERSEGURIDAD
=============================================================================
Sistema de acceso cerrado de alta seguridad para CSStudioPro.
Características:
 - Validación de credenciales maestras mediante Hashing SHA-256 (anti-decompilación).
 - Eliminación de credenciales en texto plano en binarios de PyInstaller.
 - Almacenamiento seguro en %LOCALAPPDATA% para evitar errores de permisos en C:\\Program Files.
 - Persistencia de sesión y auto-login cifrado en studio_settings.json.
 - Sesiones seguras mediante JSON Web Tokens (JWT) firmados con HS256.
 - Cookies con atributos HttpOnly, SameSite=Strict y Secure configurable.
 - Protección contra ataques de fuerza bruta (Rate Limiting y bloqueo temporal).
 - Registro público cerrado/deshabilitado de manera predeterminada.
Desarrollador: Edu Andrada (eduandrada)
Créditos de Investigación: yuyito, Hidden /A/, KYAMI, vANS.
=============================================================================
"""

import os
import re
import sys
import json
import time
import sqlite3
import hashlib
import datetime
from pathlib import Path
from functools import wraps
from typing import Dict, Any, Optional, Tuple

import bcrypt
import jwt
from dotenv import load_dotenv

# Cargar variables de entorno desde .env si existe
load_dotenv()


# =============================================================================
# ALMACENAMIENTO SEGURO EN %LOCALAPPDATA% (ESTÁNDAR DE WINDOWS)
# =============================================================================

def get_app_data_dir() -> Path:
    """
    Retorna la ruta segura de almacenamiento de datos para el usuario actual.
    Evita bloqueos de escritura en C:\\Program Files cuando se ejecuta como app de escritorio.
    Crea la carpeta automáticamente si no existe.
    """
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        app_dir = Path(local_app_data) / "CSStudioPro"
    else:
        # Fallback para entornos donde no esté definida la variable
        app_dir = Path.home() / ".csstudiopro"

    data_dir = app_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


DATA_DIR = get_app_data_dir()
APP_SETTINGS_DIR = DATA_DIR.parent
DEFAULT_DB_PATH = str(DATA_DIR / "cs_auth.db")
DB_PATH = os.environ.get("AUTH_DB_PATH", DEFAULT_DB_PATH)
SETTINGS_FILE_PATH = APP_SETTINGS_DIR / "studio_settings.json"

# =============================================================================
# HASHES CRIPTOGRÁFICOS DE ACCESO MAESTRO (SHA-256)
# =============================================================================
# Las credenciales maestras nunca se guardan en texto plano en el binario.
# Se comparan mediante su hash SHA-256 para prevenir extracción por decompiladores.
MASTER_USER_HASH = "f8737b69d6a3468a9a67a8e6b1ab4ccff70986e0047cc89b335cf5f058a73796"
MASTER_PASS_HASH = "07ed400759a0f606a8b5bfa84712aabe7d1b1c45cb6536c8a5727446b6647b84"

# Clave secreta para JWT
JWT_SECRET_KEY = os.environ.get(
    "JWT_SECRET_KEY", 
    "cs16_studio_pro_ultra_secure_jwt_secret_key_2026_@goldsrc"
)
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.environ.get("JWT_EXPIRATION_HOURS", 720))  # 30 días para recordar sesión

# Configuración de Rate Limiting (Protección contra Fuerza Bruta)
RATE_LIMIT_MAX_ATTEMPTS = int(os.environ.get("RATE_LIMIT_MAX_ATTEMPTS", 5))
RATE_LIMIT_LOCKOUT_SECONDS = int(os.environ.get("RATE_LIMIT_LOCKOUT_SECONDS", 900))  # 15 minutos

# Sistema cerrado: Registro público estrictamente deshabilitado
ALLOW_REGISTRATION = False

# Cookie settings
COOKIE_NAME = "cs_auth_token"
COOKIE_HTTPONLY = True
COOKIE_SAMESITE = "Strict"
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() in ("true", "1", "yes")


class AuthManager:
    """Gestor integral de autenticación cerrada, tokens, seguridad y auto-login."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._failed_attempts: Dict[str, list] = {}  # ip/user -> [timestamps]
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self):
        """Inicializa el esquema relacional en SQLite para auditoría y usuarios si procede."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL COLLATE NOCASE,
                        email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL DEFAULT 'admin',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_login TIMESTAMP,
                        is_active INTEGER NOT NULL DEFAULT 1
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS login_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        ip_address TEXT,
                        status TEXT NOT NULL,
                        attempt_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS security_tokens (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        token_jti TEXT UNIQUE NOT NULL,
                        revoked INTEGER NOT NULL DEFAULT 0,
                        expires_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                """)
                conn.commit()
        except Exception as e:
            print(f"[AuthManager] Advertencia inicializando base de datos local: {e}")

    # =========================================================================
    # PROTECCIÓN CONTRA FUERZA BRUTA (RATE LIMITING)
    # =========================================================================

    def is_rate_limited(self, identifier: str) -> Tuple[bool, int]:
        """
        Verifica si un identificador (IP o usuario) ha superado el límite de intentos.
        Retorna (bloqueado, segundos_restantes).
        """
        now = time.time()
        attempts = self._failed_attempts.get(identifier, [])
        valid_attempts = [t for t in attempts if now - t < RATE_LIMIT_LOCKOUT_SECONDS]
        self._failed_attempts[identifier] = valid_attempts

        if len(valid_attempts) >= RATE_LIMIT_MAX_ATTEMPTS:
            oldest_in_window = valid_attempts[0]
            remaining = int(RATE_LIMIT_LOCKOUT_SECONDS - (now - oldest_in_window))
            return True, max(1, remaining)
        return False, 0

    def register_failed_attempt(self, identifier: str):
        """Registra un intento de autenticación fallido."""
        now = time.time()
        if identifier not in self._failed_attempts:
            self._failed_attempts[identifier] = []
        self._failed_attempts[identifier].append(now)

    def reset_failed_attempts(self, identifier: str):
        """Limpia los intentos fallidos tras un inicio de sesión exitoso."""
        if identifier in self._failed_attempts:
            del self._failed_attempts[identifier]

    # =========================================================================
    # COMPARACIÓN SEGURA MEDIANTE HASHES SHA-256
    # =========================================================================

    @staticmethod
    def _hash_sha256(text: str) -> str:
        """Calcula el hash SHA-256 en minúsculas."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def verify_master_credentials(self, user_candidate: str, pass_candidate: str) -> bool:
        """
        Verifica si el usuario y contraseña coinciden con las credenciales maestras
        usando exclusivamente comparación de hashes criptográficos SHA-256.
        """
        if not user_candidate or not pass_candidate:
            return False
        user_hash = self._hash_sha256(user_candidate.strip())
        pass_hash = self._hash_sha256(pass_candidate)
        return (user_hash == MASTER_USER_HASH) and (pass_hash == MASTER_PASS_HASH)

    # =========================================================================
    # AUTENTICACIÓN Y GENERACIÓN DE TOKENS JWT
    # =========================================================================

    def authenticate_user(self, username_or_email: str, password: str, ip_address: str = "") -> Tuple[bool, Any, str]:
        """
        Verifica credenciales contra hashes seguros SHA-256 y base de datos con bcrypt.
        Retorna (éxito, datos_usuario_con_token, mensaje_error).
        """
        clean_id = (username_or_email or "").strip()
        identifier = f"{ip_address}:{clean_id.lower()}"
        is_blocked, remaining = self.is_rate_limited(identifier)
        if is_blocked:
            return False, None, f"Demasiados intentos fallidos. Bloqueado temporalmente por {remaining} segundos."

        # 1. Verificación preferencial contra credenciales maestras (vía SHA-256)
        if self.verify_master_credentials(clean_id, password):
            self.reset_failed_attempts(identifier)
            self._log_attempt(clean_id, ip_address, "SUCCESS_MASTER")
            token = self._create_jwt_token(1, clean_id, "superadmin")
            user_data = {
                "id": 1,
                "username": clean_id,
                "email": f"{clean_id}@csstudiopro.local",
                "role": "superadmin",
                "token": token
            }
            return True, user_data, "Autenticación exitosa."

        # 2. Verificación secundaria contra base de datos local SQLite (si existieran cuentas adicionales)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, username, email, password_hash, role, is_active 
                    FROM users 
                    WHERE username = ? OR email = ?
                """, (clean_id, clean_id))
                user = cursor.fetchone()

                if user and user["is_active"]:
                    stored_hash = user["password_hash"].encode('utf-8')
                    if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                        self.reset_failed_attempts(identifier)
                        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],))
                        self._log_attempt(clean_id, ip_address, "SUCCESS_DB")
                        conn.commit()

                        token = self._create_jwt_token(user["id"], user["username"], user["role"])
                        user_data = {
                            "id": user["id"],
                            "username": user["username"],
                            "email": user["email"],
                            "role": user["role"],
                            "token": token
                        }
                        return True, user_data, "Autenticación exitosa."
        except Exception:
            pass

        # Credenciales incorrectas
        self.register_failed_attempt(identifier)
        self._log_attempt(clean_id, ip_address, "FAILED")
        return False, None, "Credenciales incorrectas."

    def register_user(self, *args, **kwargs) -> Tuple[bool, str]:
        """El registro de nuevos usuarios está deshabilitado en este sistema de acceso cerrado."""
        return False, "El registro de cuentas está deshabilitado en esta instalación privada."

    def _create_jwt_token(self, user_id: int, username: str, role: str) -> str:
        """Crea un token JWT criptográficamente firmado con tiempo de expiración."""
        exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=JWT_EXPIRATION_HOURS)
        jti = os.urandom(16).hex()
        payload = {
            "sub": str(user_id),
            "username": username,
            "role": role,
            "jti": jti,
            "iat": datetime.datetime.now(datetime.timezone.utc),
            "exp": exp
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token

    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Verifica la validez y expiración de un JWT.
        Retorna (es_válido, payload, mensaje_error).
        """
        if not token:
            return False, None, "Token no proporcionado."
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return True, payload, "Token válido."
        except jwt.ExpiredSignatureError:
            return False, None, "La sesión ha expirado."
        except jwt.InvalidTokenError:
            return False, None, "Token de sesión inválido."

    def _log_attempt(self, username: str, ip: str, status: str):
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO login_logs (username, ip_address, status) VALUES (?, ?, ?)",
                    (username, ip, status)
                )
                conn.commit()
        except Exception:
            pass

    # =========================================================================
    # PERSISTENCIA DE SESIÓN ("RECORDAR SESIÓN" EN studio_settings.json)
    # =========================================================================

    @staticmethod
    def get_settings_file_path() -> Path:
        """Retorna la ruta segura de studio_settings.json en %LOCALAPPDATA%."""
        return SETTINGS_FILE_PATH

    def save_remembered_session(self, token: str) -> bool:
        """
        Guarda un token de sesión en studio_settings.json para permitir
        el auto-login directo al panel principal en arranques posteriores.
        """
        try:
            settings_path = self.get_settings_file_path()
            data = {}
            if settings_path.exists():
                try:
                    with open(settings_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}

            data["remember_token"] = token
            data["remember_token_saved_at"] = datetime.datetime.now().isoformat()

            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"[AuthManager] Error guardando sesión persistente: {e}")
            return False

    def clear_remembered_session(self) -> bool:
        """Elimina el token de sesión guardado en studio_settings.json (Logout)."""
        try:
            settings_path = self.get_settings_file_path()
            if settings_path.exists():
                try:
                    with open(settings_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if "remember_token" in data:
                        del data["remember_token"]
                    with open(settings_path, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=4)
                except Exception:
                    pass
            return True
        except Exception as e:
            print(f"[AuthManager] Error limpiando sesión persistente: {e}")
            return False

    def get_remembered_session(self) -> Optional[Dict[str, Any]]:
        """
        Lee el token de studio_settings.json y valida si sigue activo.
        Si es válido, retorna {"token": token, "payload": payload}.
        Si expiró o está corrupto, lo limpia silenciosamente y retorna None.
        """
        try:
            settings_path = self.get_settings_file_path()
            if not settings_path.exists():
                # Intentar leer del directorio de la aplicación como fallback
                local_fallback = Path(os.path.dirname(os.path.dirname(__file__))) / "studio_settings.json"
                if local_fallback.exists():
                    settings_path = local_fallback
                else:
                    return None

            with open(settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            token = data.get("remember_token")
            if not token:
                return None

            is_valid, payload, _ = self.verify_token(token)
            if is_valid and payload:
                return {"token": token, "payload": payload}

            # Si ya expiró, limpiar el archivo
            self.clear_remembered_session()
            return None
        except Exception as e:
            print(f"[AuthManager] Error verificando auto-login persistente: {e}")
            return None


# Instancia singleton
auth_manager = AuthManager()
