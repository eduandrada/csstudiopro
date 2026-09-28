# -*- coding: utf-8 -*-
"""
Módulo de Enrutamiento Inteligente de Assets para CS 1.6
Detecta la jerarquía de modelos (armas vs jugadores), sprites, descriptores de HUD,
sonidos y paquetes ZIP con respaldo defensivo automático.
"""

import io
import os
import re
import shutil
import zipfile
from core.backup_manager import backup_manager

# Modelos clásicos de jugadores de CS 1.6
PLAYER_MODEL_NAMES = {
    # Terroristas
    "leet", "terror", "guerilla", "arctic",
    # Counter-Terroristas
    "urban", "gsg9", "sas", "gign", "vip"
}


class AssetRouter:
    @staticmethod
    def classify_file(filename, subpath_in_archive=""):
        """
        Clasifica cualquier archivo de asset y retorna su ruta relativa recomendada dentro de cstrike/.
        """
        fn_lower = filename.lower()
        sub_lower = subpath_in_archive.lower().replace("\\", "/")
        name_no_ext, ext = os.path.splitext(fn_lower)

        # 1. Modelos (.mdl)
        if ext == ".mdl":
            # Si el archivo está dentro de una carpeta player/ en el zip
            if "player/" in sub_lower:
                parts = sub_lower.split("player/")[-1].split("/")
                player_folder = parts[0] if parts[0] else name_no_ext
                return f"models/player/{player_folder}/{filename}", "Modelo de Jugador"

            # Si el nombre coincide con un modelo de jugador estándar
            if name_no_ext in PLAYER_MODEL_NAMES:
                return f"models/player/{name_no_ext}/{filename}", "Modelo de Jugador Estándar"

            # Modelos de armas en primera, tercera persona o en suelo
            if fn_lower.startswith(("v_", "p_", "w_", "shield_")):
                return f"models/{filename}", "Modelo de Arma / Equipamiento"

            # Casquillos, bombas y mochilas
            if name_no_ext in ("shell", "shotgunshell", "backpack", "w_backpack", "v_hands"):
                return f"models/{filename}", "Modelo de Sistema / Efecto"

            # Por defecto modelos van a models/
            return f"models/{filename}", "Modelo General"

        # 2. Sprites (.spr)
        elif ext == ".spr":
            return f"sprites/{filename}", "Sprite de HUD / Mirilla / Efecto"

        # 3. Descriptores de sprites (.txt)
        elif ext == ".txt":
            if fn_lower == "hud.txt" or fn_lower.startswith("weapon_"):
                return f"sprites/{filename}", "Descriptor de Sprites HUD"
            elif fn_lower == "commandmenu.txt":
                return filename, "Menú de Comandos (H)"
            else:
                return f"sprites/{filename}", "Archivo de Configuración Sprite"

        # 4. Sonidos (.wav)
        elif ext == ".wav":
            if "weapons" in sub_lower:
                return f"sound/weapons/{filename}", "Efecto de Disparo / Arma"
            elif "radio" in sub_lower:
                return f"sound/radio/{filename}", "Mensaje de Radio"
            elif "hostage" in sub_lower:
                return f"sound/hostage/{filename}", "Sonido de Rehén"
            elif "player" in sub_lower:
                return f"sound/player/{filename}", "Paso / Daño de Jugador"
            elif "ambience" in sub_lower:
                return f"sound/ambience/{filename}", "Sonido Ambiental"
            elif fn_lower == "voice_input.wav":
                return filename, "Micrófono HLDJ / Mic Spam"
            else:
                return f"sound/weapons/{filename}", "Sonido de Juego"

        # 5. Música (.mp3)
        elif ext == ".mp3":
            if fn_lower == "gamestartup.mp3" or "media" in sub_lower:
                return "media/gamestartup.mp3", "Música de Menú Principal"
            return f"mp3/{filename}", "Pista MP3"

        # 6. Archivos de interfaz y esquemas (.res)
        elif ext == ".res":
            if fn_lower in ("gamemenu.res", "trackerscheme.res", "clientscheme.res"):
                return f"resource/{filename}", "Esquema VGUI / Menú"
            return f"resource/{filename}", "Recurso de Interfaz VGUI"

        # 7. Texturas y paquetes WAD (.wad)
        elif ext == ".wad":
            return filename, "Paquete de Texturas WAD3"

        # 8. Configuraciones (.cfg)
        elif ext == ".cfg":
            return filename, "Script de Configuración GoldSrc"

        # 9. Mapas (.bsp, .nav, .res)
        elif ext in (".bsp", ".nav"):
            return f"maps/{filename}", "Mapa de Juego"

        # Otros
        return filename, "Archivo Desconocido"

    @staticmethod
    def install_single_file(cstrike_path, file_stream_or_bytes, filename, custom_rel_path=None):
        """
        Instala un archivo individual en cstrike con snapshot previo.
        """
        if isinstance(file_stream_or_bytes, bytes):
            data = file_stream_or_bytes
        else:
            data = file_stream_or_bytes.read()

        if custom_rel_path:
            rel_path = custom_rel_path.replace("\\", "/").lstrip("/")
            desc = "Instalación Manual"
        else:
            rel_path, desc = AssetRouter.classify_file(filename)

        full_dest = os.path.join(cstrike_path, rel_path)
        os.makedirs(os.path.dirname(full_dest), exist_ok=True)

        # Snapshot
        backup_manager.backup_file(cstrike_path, rel_path, action_desc=f"Asset: {desc}")

        # Quitar solo lectura previo si existía
        if os.path.exists(full_dest):
            try:
                import ctypes
                ctypes.windll.kernel32.SetFileAttributesW(full_dest, 0x80)
            except Exception:
                pass

        with open(full_dest, "wb") as f:
            f.write(data)

        # Si es un sprite y hay descriptor que sincronizar
        if rel_path.endswith(".spr"):
            AssetRouter.sync_sprite_descriptor(cstrike_path, rel_path)

        return {
            "filename": filename,
            "installed_to": rel_path,
            "category": desc,
            "size": len(data),
            "status": "success"
        }

    @staticmethod
    def install_zip_archive(cstrike_path, zip_stream_or_bytes):
        """
        Extrae y enruta inteligentemente todos los assets contenidos en un archivo ZIP.
        """
        if isinstance(zip_stream_or_bytes, bytes):
            zip_buf = io.BytesIO(zip_stream_or_bytes)
        else:
            zip_buf = zip_stream_or_bytes

        results = []
        with zipfile.ZipFile(zip_buf, 'r') as zf:
            for item in zf.infolist():
                if item.is_dir():
                    continue

                filename = os.path.basename(item.filename)
                if not filename or filename.startswith("."):
                    continue

                # Normalizar ruta dentro del zip
                subpath = os.path.dirname(item.filename).replace("\\", "/")
                # Quitar prefijos típicos como cstrike/, Half-Life/cstrike/
                cleaned_sub = re.sub(r'^(cstrike/|half-life/cstrike/|cs 1\.6/cstrike/)', '', subpath, flags=re.I)

                # Si ya venía bien estructurado dentro del zip (ej: models/v_ak47.mdl)
                if any(cleaned_sub.startswith(p) for p in ("models", "sound", "sprites", "resource", "maps", "media")):
                    rel_target = f"{cleaned_sub}/{filename}".lstrip("/")
                    _, desc = AssetRouter.classify_file(filename, subpath)
                else:
                    rel_target, desc = AssetRouter.classify_file(filename, subpath)

                data = zf.read(item.filename)
                full_dest = os.path.join(cstrike_path, rel_target)
                os.makedirs(os.path.dirname(full_dest), exist_ok=True)

                # Snapshot
                backup_manager.backup_file(cstrike_path, rel_target, action_desc=f"ZIP Mod: {desc}")

                if os.path.exists(full_dest):
                    try:
                        import ctypes
                        ctypes.windll.kernel32.SetFileAttributesW(full_dest, 0x80)
                    except Exception:
                        pass

                with open(full_dest, "wb") as f:
                    f.write(data)

                results.append({
                    "filename": filename,
                    "installed_to": rel_target,
                    "category": desc,
                    "size": len(data)
                })

        return results

    @staticmethod
    def sync_sprite_descriptor(cstrike_path, sprite_rel_path):
        """
        Verifica si el sprite tiene descriptor en hud.txt y asegura consistencia.
        """
        hud_txt = os.path.join(cstrike_path, "sprites", "hud.txt")
        if not os.path.exists(hud_txt):
            return

        sprite_base = os.path.splitext(os.path.basename(sprite_rel_path))[0]
        try:
            with open(hud_txt, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Si ya está mencionado en hud.txt, no duplicar
            if sprite_base.lower() in content.lower():
                return

            # Agregar entrada básica genérica al final si es una mirilla o icono
            if sprite_base.startswith(("ch_", "crosshair", "sniper_", "wp_")):
                new_entry = f"\n{sprite_base} 640 {sprite_base} 0 0 32 32\n"
                backup_manager.backup_file(cstrike_path, "sprites/hud.txt", action_desc="Sincronización de HUD.txt")
                with open(hud_txt, "a", encoding="utf-8") as f:
                    f.write(new_entry)
        except Exception:
            pass


asset_router = AssetRouter()
