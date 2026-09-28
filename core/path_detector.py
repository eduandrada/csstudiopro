# -*- coding: utf-8 -*-
"""
Módulo de Detección de Rutas de CS 1.6 y Half-Life (GoldSrc)
Escanea el registro de Windows, librerías secundarias de Steam y rutas comunes.
"""

import json
import os
import re
import string
import sys

def get_settings_file_path() -> str:
    r"""
    Retorna la ruta segura de studio_settings.json en %LOCALAPPDATA%.
    Si el archivo no existe en AppData pero existe en el directorio de la aplicación,
    migra o lee los datos iniciales de allí sin fallar por permisos en C:\Program Files.
    """
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        app_dir = os.path.join(local_app_data, "CSStudioPro")
    else:
        app_dir = os.path.join(os.path.expanduser("~"), ".csstudiopro")
    os.makedirs(app_dir, exist_ok=True)
    user_settings = os.path.join(app_dir, "studio_settings.json")

    # Si aún no existe en AppData, verificar si hay uno empaquetado en el directorio base
    if not os.path.exists(user_settings):
        base_fallback = os.path.join(os.path.dirname(os.path.dirname(__file__)), "studio_settings.json")
        if os.path.isfile(base_fallback):
            try:
                import shutil
                shutil.copy2(base_fallback, user_settings)
            except Exception:
                pass
    return user_settings

SETTINGS_FILE = get_settings_file_path()


class PathDetector:
    def __init__(self):
        self.cached_path = None
        self._load_saved_path()

    def _load_saved_path(self):
        path_to_read = SETTINGS_FILE if os.path.exists(SETTINGS_FILE) else os.path.join(os.path.dirname(os.path.dirname(__file__)), "studio_settings.json")
        if os.path.exists(path_to_read):
            try:
                with open(path_to_read, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    saved = data.get("cstrike_path")
                    if saved and self.is_valid_cstrike(saved):
                        self.cached_path = os.path.abspath(saved)
            except Exception:
                pass

    def save_path(self, path):
        if self.is_valid_cstrike(path):
            self.cached_path = os.path.abspath(path)
            try:
                data = {}
                if os.path.exists(SETTINGS_FILE):
                    try:
                        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                            data = json.load(f)
                    except Exception:
                        data = {}
                data["cstrike_path"] = self.cached_path
                with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                return True
            except Exception:
                return False
        return False

    def is_valid_cstrike(self, path):
        """Verifica si la ruta dada es un directorio cstrike válido o la raíz de Half-Life."""
        if not path or not os.path.isdir(path):
            return False

        norm = os.path.abspath(path)
        base = os.path.basename(norm).lower()

        # Si apuntó a la raíz de Half-Life
        if base in ("half-life", "counter-strike", "counter-strike 1.6", "cs 1.6"):
            cstrike_sub = os.path.join(norm, "cstrike")
            if os.path.isdir(cstrike_sub):
                return True

        # Si apuntó directamente a cstrike o cstrike_spanish
        if "cstrike" in base:
            # Comprobar indicadores típicos de cstrike (subcarpetas o archivos)
            indicators = ["models", "sound", "sprites", "resource", "cl_dlls", "maps", "tempdecal.wad", "gameinfo.txt"]
            score = sum(1 for ind in indicators if os.path.exists(os.path.join(norm, ind)))
            hl_exe_near = os.path.exists(os.path.join(os.path.dirname(norm), "hl.exe"))
            if score >= 2 or hl_exe_near:
                return True

        return False

    def get_actual_cstrike(self, path):
        """Resuelve la ruta definitiva a la carpeta cstrike/."""
        if not path:
            return None
        norm = os.path.abspath(path)
        if os.path.isdir(os.path.join(norm, "cstrike")):
            return os.path.join(norm, "cstrike")
        if os.path.isdir(os.path.join(norm, "cstrike_spanish")):
            return os.path.join(norm, "cstrike_spanish")
        return norm

    def scan_windows_registry(self):
        """Lee el registro de Windows buscando rutas de Steam y No-Steam (Half-Life / Counter-Strike)."""
        detected_paths = []
        if sys.platform != "win32":
            return detected_paths

        import winreg
        hives = [
            # Steam
            (winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam", "SteamPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Steam", "InstallPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Steam", "InstallPath"),
            # Valve / Half-Life (Común en No-Steam y Retail)
            (winreg.HKEY_CURRENT_USER, r"Software\Valve\Half-Life", "InstallPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\Half-Life", "InstallPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\Half-Life", "InstallPath"),
            # Counter-Strike No-Steam builds (Warzone, WAStrikers, etc.)
            (winreg.HKEY_CURRENT_USER, r"Software\Counter-Strike", "InstallPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Counter-Strike", "InstallPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Counter-Strike", "InstallPath"),
            (winreg.HKEY_CURRENT_USER, r"Software\Valve\CounterStrike", "InstallPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\CounterStrike", "InstallPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Valve\CounterStrike", "InstallPath"),
            (winreg.HKEY_CURRENT_USER, r"Software\Valve\CS16", "InstallPath"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Valve\CS16", "InstallPath"),
        ]

        for hive, subkey, val_name in hives:
            try:
                with winreg.OpenKey(hive, subkey) as key:
                    val, _ = winreg.QueryValueEx(key, val_name)
                    if val and os.path.isdir(val):
                        norm = os.path.normpath(val)
                        if norm not in detected_paths:
                            detected_paths.append(norm)
            except Exception:
                pass

        return detected_paths

    def parse_steam_libraries(self, steam_root):
        """Parsea steamapps/libraryfolders.vdf para encontrar todas las bibliotecas de Steam."""
        libraries = [steam_root]
        vdf_path = os.path.join(steam_root, "steamapps", "libraryfolders.vdf")
        if os.path.exists(vdf_path):
            try:
                with open(vdf_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    # Buscar rutas entre comillas "path" "D:\\SteamLibrary"
                    matches = re.findall(r'"path"\s+"([^"]+)"', content)
                    for m in matches:
                        cleaned = m.replace("\\\\", "\\")
                        if os.path.isdir(cleaned) and cleaned not in libraries:
                            libraries.append(cleaned)
            except Exception:
                pass
        return libraries

    def find_all_candidates(self):
        """Busca todas las posibles ubicaciones de CS 1.6 en el sistema."""
        candidates = []

        # 1. Si hay una ruta guardada válida, tiene prioridad
        if self.cached_path and self.is_valid_cstrike(self.cached_path):
            candidates.append(self.cached_path)

        # 2. Rutas desde el registro de Windows (Steam y No-Steam)
        registry_roots = self.scan_windows_registry()
        all_steam_libs = []
        for r_root in registry_roots:
            all_steam_libs.extend(self.parse_steam_libraries(r_root))
            # Comprobar si la ruta del registro apunta directamente a una instalación No-Steam
            if self.is_valid_cstrike(r_root):
                real_cstrike = self.get_actual_cstrike(r_root)
                if real_cstrike and real_cstrike not in candidates:
                    candidates.append(real_cstrike)

        for lib in all_steam_libs:
            hl_dirs = [
                os.path.join(lib, "steamapps", "common", "Half-Life", "cstrike"),
                os.path.join(lib, "steamapps", "common", "Half-Life", "cstrike_spanish"),
                os.path.join(lib, "steamapps", "common", "Half-Life"),
                os.path.join(lib, "cstrike"),
                os.path.join(lib, "Counter-Strike 1.6", "cstrike"),
            ]
            for d in hl_dirs:
                if os.path.isdir(d):
                    real_cstrike = self.get_actual_cstrike(d)
                    if real_cstrike and real_cstrike not in candidates:
                        candidates.append(real_cstrike)

        # 3. Escaneo exhaustivo en todas las letras de unidad disponibles en Windows (Steam y No-Steam)
        if sys.platform == "win32":
            drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
        else:
            drives = ["/"]

        common_patterns = [
            # Steam
            os.path.join("SteamLibrary", "steamapps", "common", "Half-Life", "cstrike"),
            os.path.join("SteamLibrary", "steamapps", "common", "Half-Life", "cstrike_spanish"),
            os.path.join("Program Files (x86)", "Steam", "steamapps", "common", "Half-Life", "cstrike"),
            os.path.join("Program Files", "Steam", "steamapps", "common", "Half-Life", "cstrike"),
            
            # No-Steam / Standalone comunes (Warzone, Portable, WAStrikers, etc.)
            os.path.join("Counter-Strike 1.6", "cstrike"),
            os.path.join("Counter-Strike 1.6", "cstrike_spanish"),
            os.path.join("Counter-Strike 1.6"),
            os.path.join("CS 1.6", "cstrike"),
            os.path.join("CS 1.6"),
            os.path.join("CS16", "cstrike"),
            os.path.join("Counter-Strike", "cstrike"),
            os.path.join("Half-Life", "cstrike"),
            os.path.join("Games", "Counter-Strike 1.6", "cstrike"),
            os.path.join("Games", "Counter-Strike 1.6"),
            os.path.join("Games", "CS 1.6", "cstrike"),
            os.path.join("Juegos", "Counter-Strike 1.6", "cstrike"),
            os.path.join("Juegos", "Counter-Strike 1.6"),
            os.path.join("Juegos", "CS 1.6", "cstrike"),
            os.path.join("Archivos de programa", "Counter-Strike 1.6", "cstrike"),
            os.path.join("Archivos de programa", "Counter-Strike 1.6"),
            os.path.join("Archivos de programa (x86)", "Counter-Strike 1.6", "cstrike"),
            os.path.join("Archivos de programa", "Valve", "cstrike"),
            os.path.join("Program Files (x86)", "Counter-Strike 1.6", "cstrike"),
            os.path.join("Program Files (x86)", "Counter-Strike 1.6"),
            os.path.join("Program Files", "Counter-Strike 1.6", "cstrike"),
            os.path.join("Program Files", "Counter-Strike 1.6"),
            os.path.join("Program Files (x86)", "Valve", "Counter-Strike 1.6", "cstrike"),
            os.path.join("Program Files", "Valve", "Counter-Strike 1.6", "cstrike"),
            os.path.join("Program Files (x86)", "Valve", "Half-Life", "cstrike"),
            os.path.join("Program Files", "Valve", "Half-Life", "cstrike"),
            os.path.join("CS 1.6 Warzone", "cstrike"),
            os.path.join("Counter-Strike Warzone", "cstrike"),
            os.path.join("cstrike"),
        ]

        for drive in drives:
            for pat in common_patterns:
                full_p = os.path.join(drive, pat)
                if os.path.isdir(full_p):
                    real_cstrike = self.get_actual_cstrike(full_p)
                    if real_cstrike and real_cstrike not in candidates:
                        candidates.append(real_cstrike)

        return candidates

    def detect_version_type(self, path):
        """Determina si la instalación es Steam o No-Steam."""
        if not path:
            return "Desconocido", False

        norm = os.path.abspath(path).lower()
        hl_root = os.path.dirname(path) if os.path.basename(path).lower().startswith("cstrike") else path

        # RevEmu o emuladores No-Steam típicos
        if os.path.isfile(os.path.join(hl_root, "rev.ini")) or os.path.isfile(os.path.join(path, "rev.ini")):
            return "No-Steam", False

        # Steam oficial suele estar en steamapps o contener steam.dll original
        has_steam_dll = os.path.isfile(os.path.join(hl_root, "steam.dll")) or os.path.isfile(os.path.join(hl_root, "steam_api.dll"))
        in_steamapps = "steamapps" in norm

        if in_steamapps and has_steam_dll:
            return "Steam", True
        elif in_steamapps:
            return "Steam", True
        else:
            return "No-Steam", False

    def get_status(self):
        """Retorna el estado de conexión con CS 1.6 (Steam o No-Steam)."""
        candidates = self.find_all_candidates()
        active = None

        if self.cached_path and self.is_valid_cstrike(self.cached_path):
            active = self.get_actual_cstrike(self.cached_path)
        elif candidates:
            active = candidates[0]
            self.cached_path = active

        if active and os.path.isdir(active):
            hl_root = os.path.dirname(active) if os.path.basename(active).lower().startswith("cstrike") else active
            hl_exe = os.path.join(hl_root, "hl.exe")
            has_exe = os.path.isfile(hl_exe)
            version_type, is_steam = self.detect_version_type(active)

            # Información de carpetas internas
            subfolders = {}
            for sub in ["models", "sound", "sprites", "resource", "maps"]:
                sub_path = os.path.join(active, sub)
                subfolders[sub] = os.path.isdir(sub_path)

            # Detalle enriquecido para cada candidato
            candidates_info = [
                {
                    "path": c,
                    "version_type": self.detect_version_type(c)[0],
                    "is_steam": self.detect_version_type(c)[1]
                }
                for c in candidates
            ]

            return {
                "connected": True,
                "path": active,
                "hl_root": hl_root,
                "has_hl_exe": has_exe,
                "direct_exe": hl_exe if has_exe else None,
                "version_type": version_type,
                "is_steam": is_steam,
                "is_spanish": "spanish" in os.path.basename(active).lower(),
                "subfolders": subfolders,
                "available_candidates": candidates,
                "candidates_info": candidates_info
            }
        else:
            candidates_info = [
                {
                    "path": c,
                    "version_type": self.detect_version_type(c)[0],
                    "is_steam": self.detect_version_type(c)[1]
                }
                for c in candidates
            ]
            return {
                "connected": False,
                "path": None,
                "hl_root": None,
                "has_hl_exe": False,
                "direct_exe": None,
                "version_type": "No detectado",
                "is_steam": False,
                "is_spanish": False,
                "subfolders": {},
                "available_candidates": candidates,
                "candidates_info": candidates_info
            }


path_detector = PathDetector()

