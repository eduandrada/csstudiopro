#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
CS 1.6 Modding, Tuning & Audio Studio Pro
=============================================================================
Suite definitiva para Counter-Strike 1.6 / Motor GoldSrc.
Integra 8 módulos esenciales:
 1. Compilador de Grafitis WAD3 (tempdecal.wad con slot 255 transparente y +R)
 2. Procesador y Conversor Acústico estilo GoldWave (PCM 16-bit Mono 22050/11025 Hz)
 3. Enrutador Inteligente de Assets (Modelos, Sprites, Resources y ZIPs)
 4. Editor Visual de VGUI y Esquemas (resource/GameMenu.res, TrackerScheme.res)
 5. Generador de Netcode Competitivo sin Placebo (userconfig.cfg)
 6. Constructor de Binds de Compra Rápida para Teclado Numérico
 7. Compilador de CommandMenu [H] con límite ergonómico de 9 opciones
 8. Calculador de Parámetros de Lanzamiento y Lanzador de Steam
 9. Sistema de Snapshots y Rollback Total
=============================================================================
"""

import io
import json
import os
import sys
from functools import wraps
from flask import Flask, jsonify, render_template, request, send_file, redirect, url_for, make_response

from core.path_detector import path_detector
from core.backup_manager import backup_manager
from core.audio_processor import audio_converter
from core.wad_compiler import (
    process_spray_image,
    compile_wad3,
    install_spray_to_cstrike
)
from core.asset_router import asset_router
from core.vgui_editor import vgui_editor
from core.config_generator import config_generator
from core.commandmenu_builder import commandmenu_builder
from core.steam_launcher import steam_launcher
from core.system_booster import system_booster
from core.telemetry_engine import telemetry_engine
from core.tactical_coach import tactical_coach
from core.auth_manager import auth_manager, COOKIE_NAME, COOKIE_SECURE
from core.demo_processor import demo_processor

from modules.booster import runtime_booster
from modules.cfg_hub import cfg_hub
from modules.cleaner import assets_cleaner
from modules.network import a2s_client, rcon_client
from utils.logger import logger


def get_base_dir():
    """Resuelve la ruta interna de assets tanto en desarrollo como compilado en PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)


def get_client_ip() -> str:
    """Extrae la IP real del cliente considerando proxies o conexiones locales."""
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr or "127.0.0.1"


def get_token_from_request():
    """Obtiene el token de autenticación desde Cookie HTTP-Only o cabecera Authorization."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1].strip()
    return token


def login_required(f):
    """Middleware de autenticación para proteger rutas web y endpoints API con soporte de auto-login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        is_valid, payload, err = auth_manager.verify_token(token)
        if not is_valid:
            # Intentar auto-login desde sesión guardada en studio_settings.json
            remembered = auth_manager.get_remembered_session()
            if remembered and remembered.get("token"):
                request.current_user = remembered["payload"]
                resp = make_response(f(*args, **kwargs))
                resp.set_cookie(
                    COOKIE_NAME,
                    remembered["token"],
                    max_age=30 * 24 * 3600,
                    httponly=True,
                    samesite="Strict",
                    secure=COOKIE_SECURE,
                    path="/"
                )
                return resp

            if request.path.startswith("/api/"):
                return jsonify({
                    "success": False,
                    "error": err or "No autorizado. Inicia sesión.",
                    "authenticated": False
                }), 401
            return redirect(url_for("login"))
        request.current_user = payload
        return f(*args, **kwargs)
    return decorated_function


@app.after_request
def apply_security_headers(response):
    """Aplica cabeceras de ciberseguridad estrictas a todas las respuestas HTTP."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


def get_active_cstrike():
    """Obtiene la ruta activa de cstrike/."""
    status = path_detector.get_status()
    if status.get("connected") and status.get("path"):
        return status["path"]
    return None


# =============================================================================
# RUTAS DE AUTENTICACIÓN Y SEGURIDAD (LOGIN / SESIONES PERSISTENTES)
# =============================================================================

@app.route("/login")
def login():
    """Renderiza el portal de autenticación o redirige automáticamente si hay sesión activa o recordada."""
    token = get_token_from_request()
    is_valid, _, _ = auth_manager.verify_token(token)
    if is_valid:
        return redirect(url_for("index"))

    # Auto-login si existe token válido guardado en studio_settings.json
    remembered = auth_manager.get_remembered_session()
    if remembered and remembered.get("token"):
        resp = make_response(redirect(url_for("index")))
        resp.set_cookie(
            COOKIE_NAME,
            remembered["token"],
            max_age=30 * 24 * 3600,
            httponly=True,
            samesite="Strict",
            secure=COOKIE_SECURE,
            path="/"
        )
        return resp

    return render_template("login.html")


@app.route("/api/auth/login", methods=["POST"])
def api_auth_login():
    """Autentica al usuario mediante hashing seguro, previene fuerza bruta y gestiona persistencia."""
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    remember_me = bool(data.get("remember_me", True))
    ip = get_client_ip()

    if not username or not password:
        return jsonify({"success": False, "error": "Usuario y contraseña requeridos."}), 400

    ok, user_data, msg = auth_manager.authenticate_user(username, password, ip)
    if not ok:
        return jsonify({"success": False, "error": msg}), 401

    # Persistencia en studio_settings.json si 'remember_me' está activado
    if remember_me:
        auth_manager.save_remembered_session(user_data["token"])
    else:
        auth_manager.clear_remembered_session()

    resp = make_response(jsonify({
        "success": True,
        "message": msg,
        "user": {
            "id": user_data["id"],
            "username": user_data["username"],
            "email": user_data["email"],
            "role": user_data["role"]
        }
    }))

    # Fijar cookie segura HTTP-only y SameSite=Strict
    max_age_seconds = 30 * 24 * 3600 if remember_me else 24 * 3600
    resp.set_cookie(
        COOKIE_NAME,
        user_data["token"],
        max_age=max_age_seconds,
        httponly=True,
        samesite="Strict",
        secure=COOKIE_SECURE,
        path="/"
    )
    return resp


@app.route("/api/auth/register", methods=["POST"])
def api_auth_register():
    """El registro público está desactivado en esta versión cerrada."""
    return jsonify({
        "success": False, 
        "error": "El registro de cuentas está deshabilitado en este sistema cerrado."
    }), 403


@app.route("/api/auth/logout", methods=["POST", "GET"])
def api_auth_logout():
    """Cierra la sesión revocando la cookie HTTP-Only y limpiando la persistencia."""
    auth_manager.clear_remembered_session()
    resp = make_response(redirect(url_for("login")) if request.method == "GET" else jsonify({"success": True, "message": "Sesión cerrada."}))
    resp.set_cookie(COOKIE_NAME, "", expires=0, path="/", httponly=True, samesite="Strict")
    return resp


@app.route("/api/auth/me", methods=["GET"])
def api_auth_me():
    """Retorna información del usuario actualmente autenticado o de la sesión recordada."""
    token = get_token_from_request()
    is_valid, payload, _ = auth_manager.verify_token(token)
    if not is_valid:
        remembered = auth_manager.get_remembered_session()
        if remembered:
            is_valid, payload = True, remembered["payload"]

    if not is_valid or not payload:
        return jsonify({"authenticated": False, "user": None})
    return jsonify({
        "authenticated": True,
        "user": {
            "username": payload.get("username"),
            "role": payload.get("role"),
            "sub": payload.get("sub")
        }
    })


@app.route("/api/credits", methods=["GET"])
def api_credits():
    """Retorna los créditos oficiales y la información del proyecto."""
    return jsonify({
        "project": "CS 1.6 Modding, Tuning & Audio Studio Pro",
        "version": "4.0",
        "lead_developer": "Edu Andrada (eduandrada)",
        "collaborators": ["yuyito", "Hidden /A/", "KYAMI", "vANS"],
        "github": "https://github.com/eduandrada/csstudiopro.git",
        "render_url": "https://csstudiopro.onrender.com",
        "render_service_id": "srv-dass8sfpn0mc739qp790",
        "description": "Suite integral definitiva de personalización, optimización y telemetría para Counter-Strike 1.6 GoldSrc."
    })


# =============================================================================
# RUTAS PRINCIPALES Y DE ESTADO
# =============================================================================

@app.route("/")
@login_required
def index():
    return render_template("index.html")



@app.route("/api/status")
def api_status():
    status = path_detector.get_status()
    cstrike_p = status.get("path")
    backups_count = 0
    if cstrike_p and os.path.isdir(cstrike_p):
        backups_count = len(backup_manager.list_backups(cstrike_p))
    status["backups_count"] = backups_count
    return jsonify(status)


@app.route("/api/set_path", methods=["POST"])
def api_set_path():
    data = request.get_json(silent=True) or {}
    path = data.get("path", "").strip()
    if not path:
        return jsonify({"success": False, "error": "Ruta vacía"}), 400

    if path_detector.save_path(path):
        return jsonify({"success": True, "status": path_detector.get_status()})
    else:
        return jsonify({"success": False, "error": "La ruta proporcionada no contiene una instalación válida de Counter-Strike 1.6 (cstrike/)."}), 400


# =============================================================================
# MÓDULO 1: SPRAYS WAD3
# =============================================================================

@app.route("/api/spray/preview", methods=["POST"])
def api_spray_preview():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]

    try:
        alpha_mode = request.form.get("alpha_mode", "alpha")
        color_tolerance = int(request.form.get("color_tolerance", 30))
        alpha_threshold = int(request.form.get("alpha_threshold", 128))
        custom_color = request.form.get("custom_color", "#000000")
        target_w = request.form.get("target_w")
        target_h = request.form.get("target_h")
        dither = request.form.get("dither") == "1"

        pixels, palette, tw, th = process_spray_image(
            file.stream,
            alpha_mode=alpha_mode,
            color_tolerance=color_tolerance,
            alpha_threshold=alpha_threshold,
            custom_color=custom_color,
            target_w=int(target_w) if target_w else None,
            target_h=int(target_h) if target_h else None,
            dither=dither
        )

        palette_list = [[palette[i * 3], palette[i * 3 + 1], palette[i * 3 + 2]] for i in range(256)]

        return jsonify({
            "success": True,
            "width": tw,
            "height": th,
            "total_pixels": tw * th,
            "palette": palette_list
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/spray/convert", methods=["POST"])
def api_spray_convert():
    if "file" not in request.files:
        return "No file uploaded", 400
    file = request.files["file"]

    try:
        alpha_mode = request.form.get("alpha_mode", "alpha")
        color_tolerance = int(request.form.get("color_tolerance", 30))
        alpha_threshold = int(request.form.get("alpha_threshold", 128))
        custom_color = request.form.get("custom_color", "#000000")
        target_w = request.form.get("target_w")
        target_h = request.form.get("target_h")
        dither = request.form.get("dither") == "1"
        lump_type_str = request.form.get("lump_type", "0x40")
        lump_type = int(lump_type_str, 16) if lump_type_str.startswith("0x") else int(lump_type_str)

        pixels, palette, tw, th = process_spray_image(
            file.stream,
            alpha_mode=alpha_mode,
            color_tolerance=color_tolerance,
            alpha_threshold=alpha_threshold,
            custom_color=custom_color,
            target_w=int(target_w) if target_w else None,
            target_h=int(target_h) if target_h else None,
            dither=dither
        )

        wad_bytes = compile_wad3(pixels, palette, tw, th, lump_type=lump_type)

        return send_file(
            io.BytesIO(wad_bytes),
            as_attachment=True,
            download_name="tempdecal.wad",
            mimetype="application/octet-stream"
        )
    except Exception as e:
        return f"Error: {str(e)}", 400


@app.route("/api/spray/install", methods=["POST"])
def api_spray_install():
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de Counter-Strike 1.6 no conectada."}), 400

    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
    file = request.files["file"]

    try:
        alpha_mode = request.form.get("alpha_mode", "alpha")
        color_tolerance = int(request.form.get("color_tolerance", 30))
        alpha_threshold = int(request.form.get("alpha_threshold", 128))
        custom_color = request.form.get("custom_color", "#000000")
        target_w = request.form.get("target_w")
        target_h = request.form.get("target_h")
        dither = request.form.get("dither") == "1"
        lump_type_str = request.form.get("lump_type", "0x40")
        lump_type = int(lump_type_str, 16) if lump_type_str.startswith("0x") else int(lump_type_str)

        pixels, palette, tw, th = process_spray_image(
            file.stream,
            alpha_mode=alpha_mode,
            color_tolerance=color_tolerance,
            alpha_threshold=alpha_threshold,
            custom_color=custom_color,
            target_w=int(target_w) if target_w else None,
            target_h=int(target_h) if target_h else None,
            dither=dither
        )

        wad_bytes = compile_wad3(pixels, palette, tw, th, lump_type=lump_type)
        installed = install_spray_to_cstrike(cstrike_p, wad_bytes)

        return jsonify({
            "success": True,
            "installed_paths": installed,
            "message": "tempdecal.wad y pldecal.wad instalados y marcados como Solo Lectura (+R)"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# =============================================================================
# MÓDULO 2: AUDIO GOLDWAVE
# =============================================================================

@app.route("/api/audio/convert", methods=["POST"])
def api_audio_convert():
    if "file" not in request.files:
        return "No file uploaded", 400
    file = request.files["file"]

    try:
        profile = request.form.get("profile", "weapons")
        vol_boost = float(request.form.get("volume_boost", 1.0))
        normalize = request.form.get("normalize") == "1"

        target_rate = 22050
        if profile in ("radio", "voice"):
            target_rate = 11025

        raw_bytes = file.read()
        try:
            out_wav = audio_converter.resample_and_mono(
                raw_bytes,
                target_rate=target_rate,
                normalize=normalize,
                volume_boost=vol_boost
            )
        except Exception as e:
            if raw_bytes.startswith(b"RIFF") and len(raw_bytes) > 44:
                out_wav = raw_bytes
            else:
                raise e

        download_name = file.filename.rsplit(".", 1)[0] + "_goldsrc.wav"
        return send_file(
            io.BytesIO(out_wav),
            as_attachment=True,
            download_name=download_name,
            mimetype="audio/wav"
        )
    except Exception as e:
        return f"Error en procesamiento de audio: {str(e)}", 400


@app.route("/api/audio/install", methods=["POST"])
def api_audio_install():
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de cstrike no conectada."}), 400

    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
    file = request.files["file"]

    try:
        profile = request.form.get("profile", "weapons")
        custom_dest = request.form.get("custom_dest", "").strip()
        vol_boost = float(request.form.get("volume_boost", 1.0))
        normalize = request.form.get("normalize") == "1"

        base_clean_name = file.filename.rsplit(".", 1)[0]
        # Resolver destino según perfil
        if profile == "weapons":
            dest = custom_dest or f"sound/weapons/{base_clean_name}.wav"
            target_rate = 22050
        elif profile == "radio":
            dest = custom_dest or f"sound/radio/{base_clean_name}.wav"
            target_rate = 11025
        elif profile == "voice":
            dest = "voice_input.wav"
            target_rate = 11025
        elif profile == "music":
            dest = "media/gamestartup.mp3"
            target_rate = 44100
        else:
            dest = custom_dest or f"sound/weapons/{base_clean_name}.wav"
            target_rate = 22050

        # Asegurar extensión válida
        if not dest.lower().endswith(".mp3") and not dest.lower().endswith(".wav"):
            dest += ".wav"

        # Si es gamestartup.mp3 directo
        if dest.endswith(".mp3"):
            audio_bytes = file.read()
        else:
            raw_bytes = file.read()
            try:
                audio_bytes = audio_converter.resample_and_mono(
                    raw_bytes,
                    target_rate=target_rate,
                    normalize=normalize,
                    volume_boost=vol_boost
                )
            except Exception as e:
                if raw_bytes.startswith(b"RIFF") and len(raw_bytes) > 44:
                    audio_bytes = raw_bytes
                else:
                    raise e

        installed_path = audio_converter.install_to_cstrike(
            cstrike_p,
            audio_bytes,
            dest,
            action_desc=f"Audio: {os.path.basename(dest)}"
        )

        return jsonify({
            "success": True,
            "installed_to": dest,
            "full_path": installed_path
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# =============================================================================
# MÓDULO 3: GESTOR DE ASSETS
# =============================================================================

@app.route("/api/assets/install", methods=["POST"])
def api_assets_install():
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de cstrike no conectada."}), 400

    files = request.files.getlist("files")
    if not files or files[0].filename == "":
        return jsonify({"success": False, "error": "No se recibieron archivos."}), 400

    installed_results = []
    try:
        for f in files:
            fname = f.filename
            if fname.lower().endswith(".zip"):
                zip_items = asset_router.install_zip_archive(cstrike_p, f.stream)
                installed_results.extend(zip_items)
            else:
                res = asset_router.install_single_file(cstrike_p, f.stream, fname)
                installed_results.append(res)

        return jsonify({
            "success": True,
            "installed": installed_results
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# =============================================================================
# MÓDULO 4: VGUI & GAMEMENU
# =============================================================================

@app.route("/api/vgui/gamemenu", methods=["GET"])
def api_vgui_gamemenu_get():
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"items": vgui_editor.load_game_menu("")})
    items = vgui_editor.load_game_menu(cstrike_p)
    return jsonify({"items": items})


@app.route("/api/vgui/gamemenu", methods=["POST"])
def api_vgui_gamemenu_post():
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de cstrike no conectada."}), 400

    data = request.get_json(silent=True) or {}
    items = data.get("items", [])
    try:
        vgui_editor.save_game_menu(cstrike_p, items)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/vgui/scheme", methods=["POST"])
def api_vgui_scheme():
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de cstrike no conectada."}), 400

    data = request.get_json(silent=True) or {}
    r = int(data.get("r", 245))
    g = int(data.get("g", 166))
    b = int(data.get("b", 35))

    try:
        vgui_editor.generate_tracker_scheme_colors(cstrike_p, (r, g, b))
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# =============================================================================
# MÓDULO 5 & 6: NETCODE & USERCONFIG.CFG
# =============================================================================

@app.route("/api/config/preview", methods=["POST"])
def api_config_preview():
    data = request.get_json(silent=True) or {}
    cfg_text = config_generator.generate_userconfig_text(
        rate=int(data.get("rate", 100000)),
        cl_updaterate=int(data.get("cl_updaterate", 102)),
        cl_cmdrate=int(data.get("cl_cmdrate", 105)),
        fps_max=float(data.get("fps_max", 99.5)),
        raw_input=bool(data.get("raw_input", True)),
        crosshair_color=data.get("crosshair_color", "0 255 0"),
        crosshair_dynamic=bool(data.get("crosshair_dynamic", False)),
        numpad_binds=data.get("numpad_binds")
    )
    return jsonify({"success": True, "cfg_text": cfg_text})


@app.route("/api/config/install", methods=["POST"])
def api_config_install():
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de cstrike no conectada."}), 400

    data = request.get_json(silent=True) or {}
    cfg_text = data.get("cfg_text", "")
    if not cfg_text:
        return jsonify({"success": False, "error": "Configuración vacía."}), 400

    try:
        config_generator.install_userconfig(cstrike_p, cfg_text)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# =============================================================================
# MÓDULO 7: COMMANDMENU [H]
# =============================================================================

@app.route("/api/commandmenu/preview", methods=["POST"])
def api_cmdmenu_preview():
    data = request.get_json(silent=True) or {}
    tree = data.get("tree", [])
    text = commandmenu_builder.serialize_tree(tree)
    return jsonify({"success": True, "text": text})


@app.route("/api/commandmenu/install", methods=["POST"])
def api_cmdmenu_install():
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de cstrike no conectada."}), 400

    data = request.get_json(silent=True) or {}
    tree = data.get("tree", [])
    try:
        commandmenu_builder.install_commandmenu(cstrike_p, tree)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# =============================================================================
# MÓDULO 8: STEAM LAUNCHER
# =============================================================================

@app.route("/api/steam/generate_args", methods=["POST"])
def api_steam_generate_args():
    data = request.get_json(silent=True) or {}
    args = steam_launcher.build_launch_options(
        width=int(data.get("width", 1024)),
        height=int(data.get("height", 768)),
        freq=int(data.get("freq", 144)),
        noforce=bool(data.get("noforce", True)),
        novid=bool(data.get("novid", True)),
        nojoy=bool(data.get("nojoy", True)),
        opengl=bool(data.get("opengl", True))
    )
    return jsonify({"success": True, "args": args})


@app.route("/api/steam/launch", methods=["POST"])
def api_steam_launch():
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de cstrike no conectada."}), 400

    data = request.get_json(silent=True) or {}
    launch_args = data.get("args", "-noforcemaccel -noforcemparms -novid")
    mode = data.get("mode", "auto")
    connect_server = data.get("connect_server", "").strip()

    ok, msg = steam_launcher.launch_game(cstrike_p, launch_options=launch_args, mode=mode, connect_server=connect_server)
    return jsonify({"success": ok, "message": msg})


@app.route("/api/launcher/fix_masterservers", methods=["POST"])
def api_launcher_fix_masterservers():
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de cstrike no conectada."}), 400

    ok, msg = steam_launcher.fix_masterservers(cstrike_p)
    return jsonify({"success": ok, "message": msg})


# =============================================================================
# MÓDULO 9: SNAPSHOTS & ROLLBACK
# =============================================================================

@app.route("/api/backups", methods=["GET"])
def api_backups_list():
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"backups": []})
    backups = backup_manager.list_backups(cstrike_p)
    return jsonify({"backups": backups})


@app.route("/api/rollback", methods=["POST"])
def api_rollback():
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de cstrike no conectada."}), 400

    data = request.get_json(silent=True) or {}
    entry_id = data.get("entry_id")
    if not entry_id:
        return jsonify({"success": False, "error": "ID de snapshot requerido."}), 400

    ok, msg = backup_manager.rollback(cstrike_p, entry_id)
    return jsonify({"success": ok, "message": msg})


@app.route("/api/rollback_all", methods=["POST"])
def api_rollback_all():
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de cstrike no conectada."}), 400

    res = backup_manager.rollback_all(cstrike_p)
    return jsonify(res)


@app.route("/api/binds/install", methods=["POST"])
def api_binds_install():
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de cstrike no conectada."}), 400

    data = request.get_json(silent=True) or {}
    cfg_text = data.get("content", "")
    if not cfg_text.strip():
        return jsonify({"success": False, "error": "El contenido de binds.cfg está vacío."}), 400

    try:
        binds_file = os.path.join(cstrike_p, "binds.cfg")
        backup_manager.backup_file(cstrike_p, "binds.cfg", "Instalación de binds.cfg")
        with open(binds_file, "w", encoding="latin-1", errors="ignore") as f:
            f.write(cfg_text)

        # Vincular a userconfig.cfg
        userconfig_file = os.path.join(cstrike_p, "userconfig.cfg")
        exec_line = "exec binds.cfg\n"
        existing = ""
        if os.path.exists(userconfig_file):
            with open(userconfig_file, "r", encoding="latin-1", errors="ignore") as f:
                existing = f.read()

        if "exec binds.cfg" not in existing:
            backup_manager.backup_file(cstrike_p, "userconfig.cfg", "Vincular binds.cfg en userconfig.cfg")
            with open(userconfig_file, "a", encoding="latin-1", errors="ignore") as f:
                f.write(f"\n// Carga automática de binds personalizados\n{exec_line}")

        return jsonify({
            "success": True,
            "message": "¡Binds instalados con éxito en cstrike/binds.cfg y vinculados a userconfig.cfg!"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500




# =============================================================================
# MÓDULO 10: CS 1.6 SYSTEM & LATENCY BOOSTER (KERNEL & WINMM)
# =============================================================================

@app.route("/api/booster/status", methods=["GET"])
def api_booster_status():
    cstrike_p = get_active_cstrike()
    if cstrike_p:
        system_booster.cstrike_dir = cstrike_p
    hl_pid = system_booster.find_hl_process()
    st = dict(system_booster.last_status)
    st["hl_detected"] = bool(hl_pid)
    st["hl_pid"] = hl_pid
    st["timer_1ms"] = system_booster.timer_boosted
    return jsonify(st)


@app.route("/api/booster/toggle", methods=["POST"])
def api_booster_toggle():
    cstrike_p = get_active_cstrike()
    if cstrike_p:
        system_booster.cstrike_dir = cstrike_p
    data = request.get_json(silent=True) or {}
    enable = data.get("enable")
    if enable is None:
        enable = not system_booster.last_status.get("active", False)

    if enable:
        system_booster.start_background_daemon()
    else:
        system_booster.stop_background_daemon()

    return jsonify({"success": True, "active": system_booster.last_status.get("active", False)})


@app.route("/api/booster/trim_ram", methods=["POST"])
def api_booster_trim_ram():
    ok = system_booster.trim_ram_working_set()
    return jsonify({"success": ok, "message": "Memoria RAM purgada y liberada." if ok else "No se pudo purgar la memoria."})


@app.route("/api/booster/timer", methods=["POST"])
def api_booster_timer():
    data = request.get_json(silent=True) or {}
    enable = bool(data.get("enable", True))
    ok = system_booster.optimize_system_timer(enable)
    return jsonify({"success": ok, "timer_1ms": system_booster.timer_boosted})


@app.route("/api/booster/download_reg", methods=["GET"])
def api_booster_download_reg():
    reg_path = os.path.join(os.path.dirname(__file__), "cs_latency_fix.reg")
    if not os.path.exists(reg_path):
        return "cs_latency_fix.reg no encontrado", 404
    return send_file(reg_path, as_attachment=True, download_name="cs_latency_fix.reg", mimetype="application/octet-stream")


@app.route("/api/booster/apply_reg", methods=["POST"])
def api_booster_apply_reg():
    try:
        ok, msg = system_booster.apply_registry_latency_fix()
        return jsonify({"success": ok, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# =============================================================================
# MÓDULO 11: TELEMETRÍA TÁCTICA & COACH DE IA (NON-INTRUSIVE & VAC-SAFE)
# =============================================================================

@app.route("/api/telemetry/status", methods=["GET"])
def api_telemetry_status():
    cstrike_p = get_active_cstrike()
    if cstrike_p:
        telemetry_engine.set_cstrike_path(cstrike_p)
        tactical_coach.set_cstrike_path(cstrike_p)

    active = telemetry_engine.is_log_active()
    metrics = telemetry_engine.calculate_metrics()
    return jsonify({
        "log_active": active,
        "log_file": telemetry_engine.get_log_file_path(),
        "total_rounds": metrics.get("total_rounds", 0),
        "combat_score": metrics.get("combat_score", 0),
        "monitoring": bool(telemetry_engine._monitor_thread and telemetry_engine._monitor_thread.is_alive())
    })


@app.route("/api/telemetry/start", methods=["POST"])
def api_telemetry_start():
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de cstrike no conectada."}), 400

    telemetry_engine.set_cstrike_path(cstrike_p)
    tactical_coach.set_cstrike_path(cstrike_p)

    # Inyectar comandos con_logfile y mp_logdetail 3 en userconfig.cfg
    userconfig_p = os.path.join(cstrike_p, "userconfig.cfg")
    injected = telemetry_engine.ensure_client_telemetry_commands(userconfig_p)
    telemetry_engine.start_monitoring()

    return jsonify({
        "success": True,
        "injected": injected,
        "message": "Monitoreo de telemetría VAC-Safe activado. Registrando partidas en tiempo real."
    })


@app.route("/api/telemetry/reset", methods=["POST"])
def api_telemetry_reset():
    telemetry_engine.reset_session()
    return jsonify({"success": True, "message": "Estadísticas y telemetría de la sesión reiniciadas."})


@app.route("/api/telemetry/stats", methods=["GET"])
def api_telemetry_stats():
    cstrike_p = get_active_cstrike()
    if cstrike_p:
        telemetry_engine.set_cstrike_path(cstrike_p)
        tactical_coach.set_cstrike_path(cstrike_p)

    metrics = telemetry_engine.calculate_metrics()
    return jsonify({"success": True, "metrics": metrics})


@app.route("/api/telemetry/coach", methods=["GET"])
def api_telemetry_coach():
    cstrike_p = get_active_cstrike()
    if cstrike_p:
        telemetry_engine.set_cstrike_path(cstrike_p)
        tactical_coach.set_cstrike_path(cstrike_p)

    metrics = telemetry_engine.calculate_metrics()
    diagnoses = tactical_coach.diagnose_session(metrics)
    routines = tactical_coach.get_practice_routines()

    return jsonify({
        "success": True,
        "diagnoses": diagnoses,
        "routines": routines,
        "metrics_summary": {
            "combat_score": metrics.get("combat_score", 0),
            "kd": metrics.get("kd_ratio", 1.0),
            "hs_pct": metrics.get("hs_pct", 0.0),
            "adr": metrics.get("adr", 0.0),
            "kast": metrics.get("kast_pct", 0.0)
        }
    })


@app.route("/api/telemetry/install_routine", methods=["POST"])
def api_telemetry_install_routine():
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de cstrike no conectada."}), 400

    tactical_coach.set_cstrike_path(cstrike_p)
    data = request.get_json(silent=True) or {}
    routine_id = data.get("routine_id")
    if not routine_id:
        return jsonify({"success": False, "error": "ID de rutina requerido."}), 400

    try:
        path, filename = tactical_coach.install_routine_cfg(routine_id)
        return jsonify({
            "success": True,
            "filename": filename,
            "path": path,
            "message": f"¡Rutina instalada! En el juego escribe: exec {filename}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400




# =============================================================================
# MÓDULO 10: RENDERIZADOR Y CONVERSOR DE DEMOS (.DEM A .MP4) CON FFMPEG
# =============================================================================

@app.route("/api/demo/status", methods=["GET"])
@login_required
def api_demo_status():
    """Retorna el estado de FFmpeg, demos .dem en cstrike/ y fotogramas detectados."""
    cstrike_p = get_active_cstrike()
    prefix = request.args.get("prefix", "clip").strip() or "clip"
    ffmpeg_info = demo_processor.get_ffmpeg_status()
    demos = demo_processor.list_cstrike_demos(cstrike_p) if cstrike_p else []
    frames_scan = demo_processor.scan_recorded_frames(cstrike_p, prefix) if cstrike_p else {"found": False}

    return jsonify({
        "success": True,
        "ffmpeg": ffmpeg_info,
        "cstrike_connected": bool(cstrike_p),
        "cstrike_path": cstrike_p,
        "demos": demos,
        "frames_scan": frames_scan
    })


@app.route("/api/demo/compile", methods=["POST"])
@login_required
def api_demo_compile():
    """Ejecuta la compilación de fotogramas volcados con startmovie a video MP4 con FFmpeg."""
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de cstrike no conectada."}), 400

    data = request.get_json(silent=True) or {}
    prefix = data.get("prefix", "clip").strip() or "clip"
    fps = int(data.get("fps", 60))
    crf = int(data.get("crf", 18))
    preset = data.get("preset", "slow")
    output_name = data.get("output_name", "jugada.mp4").strip() or "jugada.mp4"
    cleanup_bmps = bool(data.get("cleanup_bmps", True))
    custom_ffmpeg = data.get("custom_ffmpeg", "").strip() or None

    ok, result = demo_processor.compile_demo_to_mp4(
        cstrike_path=cstrike_p,
        prefix=prefix,
        fps=fps,
        crf=crf,
        preset=preset,
        output_name=output_name,
        cleanup_bmps=cleanup_bmps,
        custom_ffmpeg=custom_ffmpeg
    )

    if ok:
        return jsonify({"success": True, "result": result})
    else:
        return jsonify({"success": False, "error": result.get("error", "Error al codificar con FFmpeg.")}), 400


@app.route("/api/demo/cleanup", methods=["POST"])
@login_required
def api_demo_cleanup():
    """Elimina manualmente fotogramas temporales BMP y audio WAV en cstrike/."""
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de cstrike no conectada."}), 400

    data = request.get_json(silent=True) or {}
    prefix = data.get("prefix", "clip").strip() or "clip"
    res = demo_processor.cleanup_frames(cstrike_p, prefix)
    return jsonify(res)


@app.route("/api/demo/guide", methods=["GET"])
def api_demo_guide():
    """Obtiene los comandos de consola para CS 1.6, HLAE y OBS."""
    fps = int(request.args.get("fps", 60))
    prefix = request.args.get("prefix", "clip").strip() or "clip"
    return jsonify(demo_processor.get_console_commands_guide(fps, prefix))


@app.route("/api/demo/set_custom_ffmpeg", methods=["POST"])
@login_required
def api_demo_set_custom_ffmpeg():
    """Configura una ruta personalizada a ffmpeg.exe."""
    data = request.get_json(silent=True) or {}
    path = data.get("path", "").strip()
    demo_processor.set_custom_ffmpeg_path(path)
    return jsonify({"success": True, "ffmpeg": demo_processor.get_ffmpeg_status()})


# =============================================================================
# ARQUITECTURA V2: PILARES MODULARES DE ALTO RENDIMIENTO
# =============================================================================

# --- PILAR 1: RUNTIME BOOSTER EN TIEMPO REAL ---
@app.route("/api/v2/booster/status", methods=["GET"])
@login_required
def api_v2_booster_status():
    """Retorna el estado del watchdog de hl.exe, timer 0.5ms y afinidad de CPU."""
    return jsonify({"success": True, "status": runtime_booster.get_status()})


@app.route("/api/v2/booster/toggle_watchdog", methods=["POST"])
@login_required
def api_v2_booster_toggle():
    """Inicia o detiene el hilo vigilante de hl.exe."""
    if runtime_booster.monitoring:
        runtime_booster.stop_watchdog()
    else:
        runtime_booster.start_watchdog()
    return jsonify({"success": True, "status": runtime_booster.get_status()})


@app.route("/api/v2/booster/clean_memory", methods=["POST"])
@login_required
def api_v2_booster_clean_memory():
    """Limpia el conjunto de trabajo y memoria en espera previo al juego."""
    ok, msg = runtime_booster.clean_standby_memory()
    return jsonify({"success": ok, "message": msg})


@app.route("/api/v2/booster/set_core", methods=["POST"])
@login_required
def api_v2_booster_set_core():
    """Configura el núcleo físico dedicado para el proceso hl.exe."""
    data = request.get_json(silent=True) or {}
    core = int(data.get("core", 2))
    runtime_booster.target_core = core
    return jsonify({"success": True, "target_core": core})


# --- PILAR 2: CFG HUB & CALCULADORA MATEMÁTICA DE NETCODE ---
@app.route("/api/v2/cfg/calculate", methods=["POST"])
@login_required
def api_v2_cfg_calculate():
    """Calcula matemáticamente las cvars oficiales de GoldSrc basadas en ping y Mbps."""
    data = request.get_json(silent=True) or {}
    ping = float(data.get("ping_ms", 30.0))
    bw = float(data.get("bandwidth_mbps", 50.0))
    fps = int(data.get("target_fps", 100))
    calc = cfg_hub.calculate_rates(ping_ms=ping, bandwidth_mbps=bw, target_fps=fps)
    return jsonify({"success": True, "calculated": calc})


@app.route("/api/v2/cfg/inject", methods=["POST"])
@login_required
def api_v2_cfg_inject():
    """Inyecta de forma no destructiva las cvars calculadas con snapshot automático previo."""
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de cstrike no conectada."}), 400

    data = request.get_json(silent=True) or {}
    calc = data.get("calculated")
    if not calc:
        ping = float(data.get("ping_ms", 30.0))
        bw = float(data.get("bandwidth_mbps", 50.0))
        fps = int(data.get("target_fps", 100))
        calc = cfg_hub.calculate_rates(ping_ms=ping, bandwidth_mbps=bw, target_fps=fps)

    ok, msg = cfg_hub.inject_non_destructive(cstrike_p, calc)
    return jsonify({"success": ok, "message": msg})


@app.route("/api/v2/cfg/presets", methods=["GET"])
def api_v2_cfg_presets():
    """Retorna los perfiles competitivos oficiales."""
    return jsonify({"success": True, "presets": cfg_hub.PRESETS})


@app.route("/api/v2/cfg/snapshots", methods=["GET"])
@login_required
def api_v2_cfg_snapshots():
    """Lista las instantáneas de respaldo de .cfg."""
    cstrike_p = get_active_cstrike()
    snaps = cfg_hub.list_snapshots(cstrike_p) if cstrike_p else []
    return jsonify({"success": True, "snapshots": snaps})


@app.route("/api/v2/cfg/rollback", methods=["POST"])
@login_required
def api_v2_cfg_rollback():
    """Restaura una instantánea de configuración."""
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de cstrike no conectada."}), 400
    data = request.get_json(silent=True) or {}
    snapshot_id = data.get("snapshot_id")
    ok, msg = cfg_hub.rollback_snapshot(cstrike_p, snapshot_id)
    return jsonify({"success": ok, "message": msg})


# --- PILAR 3: ASSETS & CACHE CLEANER CON WHITELIST VANILLA ---
@app.route("/api/v2/cleaner/scan", methods=["GET"])
@login_required
def api_v2_cleaner_scan():
    """Escanea descargas acumuladas y custom.hpk excluyendo assets nativos."""
    cstrike_p = get_active_cstrike()
    scan = assets_cleaner.scan_cstrike_cache(cstrike_p) if cstrike_p else {}
    return jsonify({"success": True, "scan": scan})


@app.route("/api/v2/cleaner/clean", methods=["POST"])
@login_required
def api_v2_cleaner_clean():
    """Ejecuta la depuración selectiva de caché de servidores."""
    cstrike_p = get_active_cstrike()
    if not cstrike_p:
        return jsonify({"success": False, "error": "Ruta de cstrike no conectada."}), 400

    data = request.get_json(silent=True) or {}
    clean_hpk = bool(data.get("clean_hpk", True))
    clean_dl = bool(data.get("clean_downloads", True))
    clean_maps = bool(data.get("clean_custom_maps", False))
    clean_models = bool(data.get("clean_custom_models", False))

    res = assets_cleaner.clean_cache(
        cstrike_path=cstrike_p,
        clean_hpk=clean_hpk,
        clean_downloads=clean_dl,
        clean_custom_maps=clean_maps,
        clean_custom_models=clean_models
    )
    return jsonify(res)


# --- PILAR 4: MONITOR DE SERVIDORES (A2S QUERY) Y RCON NATIVO ---
@app.route("/api/v2/network/a2s_query", methods=["GET"])
@login_required
def api_v2_network_a2s_query():
    """Consulta directa vía socket UDP a un servidor de CS 1.6."""
    host = request.args.get("host", "127.0.0.1").strip()
    port = int(request.args.get("port", 27015))
    res = a2s_client.query_server(host, port)
    return jsonify(res)


@app.route("/api/v2/network/rcon_command", methods=["POST"])
@login_required
def api_v2_network_rcon():
    """Ejecuta un comando RCON remoto vía UDP contra un servidor GoldSrc."""
    data = request.get_json(silent=True) or {}
    host = data.get("host", "127.0.0.1").strip()
    port = int(data.get("port", 27015))
    pwd = data.get("password", "")
    cmd = data.get("command", "status").strip()
    if not pwd:
        return jsonify({"success": False, "error": "Contraseña RCON requerida."}), 400

    res = rcon_client.send_command(host, port, pwd, cmd)
    return jsonify(res)


# =============================================================================
# MODO DE LÍNEA DE COMANDOS (CLI) Y SERVIDOR PRINCIPAL
# =============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print("====================================================================")
    print("  CS 1.6 MODDING, TUNING & AUDIO STUDIO PRO")
    print(f"  Servidor iniciado en: http://localhost:{port}")
    print("====================================================================")
    app.run(host="0.0.0.0", port=port, debug=False)
