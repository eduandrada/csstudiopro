# -*- coding: utf-8 -*-
"""
Módulo Calculador de Parámetros de Lanzamiento y Ejecutor de Steam para CS 1.6
Genera parámetros optimizados de rendimiento (-noforcemaccel -noforcemparms -freq -gl -novid)
y permite lanzar el juego mediante el protocolo de Steam (steam://run/10/).
"""

import os
import subprocess
import sys
import urllib.parse


class SteamLauncher:
    @staticmethod
    def build_launch_options(
        width=1024,
        height=768,
        freq=144,
        noforce=True,
        novid=True,
        nojoy=True,
        opengl=True,
        bpp32=True,
        heapsize=None,
        extra_args=""
    ):
        """Construye la cadena de comandos de lanzamiento para Steam."""
        args = []

        # Gráficos y Resolución
        if opengl:
            args.append("-gl")
        if bpp32:
            args.append("-32bpp")

        args.extend([f"-w {width}", f"-h {height}"])

        # Tasa de refresco del monitor
        if freq and int(freq) > 0:
            args.append(f"-freq {freq}")

        # Sin aceleración de ratón
        if noforce:
            args.extend(["-noforcemaccel", "-noforcemparms", "-noforcemspd"])

        # Optimizaciones de inicio
        if novid:
            args.append("-novid")
        if nojoy:
            args.append("-nojoy")

        if heapsize:
            args.append(f"-heapsize {heapsize}")

        if extra_args.strip():
            args.append(extra_args.strip())

        return " ".join(args)

    @staticmethod
    def launch_game(cstrike_path, launch_options="", mode="auto", connect_server=None):
        """
        Lanza Counter-Strike 1.6 en modo Steam o No-Steam:
         - mode='auto': detecta automáticamente si es Steam o No-Steam.
         - mode='nosteam': ejecuta directamente hl.exe -game cstrike.
         - mode='steam': utiliza el protocolo oficial steam://run/10/.
         - connect_server: IP:Puerto opcional para conectarse directamente al servidor.
        """
        hl_root = os.path.dirname(cstrike_path) if os.path.basename(cstrike_path).lower().startswith("cstrike") else cstrike_path
        
        # Posibles nombres de ejecutables para No-Steam y Steam
        exe_candidates = ["hl.exe", "Counter-Strike.exe", "cstrike.exe", "cs.exe"]
        hl_exe = None
        for candidate in exe_candidates:
            cand_path = os.path.join(hl_root, candidate)
            if os.path.isfile(cand_path):
                hl_exe = cand_path
                break

        # Incorporar conexión directa a servidor si fue especificada
        full_args = launch_options.strip()
        if connect_server and connect_server.strip():
            srv = connect_server.strip()
            if not srv.startswith("+connect") and not srv.startswith("connect"):
                full_args += f" +connect {srv}"
            elif srv.startswith("connect"):
                full_args += f" +{srv}"

        # Detectar versión
        is_steam_path = "steamapps" in cstrike_path.lower()

        # 1. MODO NO-STEAM DIRECTO O AUTO DETECTADO NO-STEAM
        if mode == "nosteam" or (mode == "auto" and not is_steam_path):
            if hl_exe and os.path.isfile(hl_exe):
                cmd = f'"{hl_exe}" -game cstrike {full_args}'.strip()
                try:
                    subprocess.Popen(cmd, cwd=hl_root, shell=True)
                    srv_msg = f" con auto-conexión a {connect_server}" if connect_server else ""
                    return True, f"CS 1.6 No-Steam lanzado directamente vía {os.path.basename(hl_exe)}{srv_msg}"
                except Exception as e:
                    return False, f"Error al ejecutar No-Steam ({hl_exe}): {str(e)}"
            else:
                return False, f"No se encontró hl.exe en la carpeta No-Steam: {hl_root}"

        # 2. MODO STEAM OFICIAL O AUTO DETECTADO STEAM
        if sys.platform == "win32" and (mode == "steam" or is_steam_path):
            try:
                encoded_args = urllib.parse.quote(full_args)
                steam_uri = f"steam://run/10//{encoded_args}"
                os.startfile(steam_uri)
                srv_msg = f" (conectando a {connect_server})" if connect_server else ""
                return True, f"CS 1.6 lanzado vía protocolo oficial de Steam{srv_msg}: {steam_uri}"
            except Exception as e:
                # Si falla el protocolo de Steam, intentar fallback con hl.exe si existe
                if hl_exe and os.path.isfile(hl_exe):
                    cmd = f'"{hl_exe}" -game cstrike {full_args}'.strip()
                    subprocess.Popen(cmd, cwd=hl_root, shell=True)
                    return True, f"Steam inaccesible, lanzado directamente con hl.exe: {hl_exe}"
                return False, f"No se pudo invocar Steam: {str(e)}"

        # Fallback general
        if hl_exe and os.path.isfile(hl_exe):
            cmd = f'"{hl_exe}" -game cstrike {full_args}'.strip()
            try:
                subprocess.Popen(cmd, cwd=hl_root, shell=True)
                return True, f"Juego iniciado directamente desde: {hl_exe}"
            except Exception as e:
                return False, f"Error al ejecutar: {str(e)}"

        return False, "No se encontró ningún ejecutable (hl.exe) ni el protocolo de Steam."

    @staticmethod
    def fix_masterservers(cstrike_path):
        """
        Repara y actualiza MasterServers.vdf para instalaciones No-Steam.
        Restaura la lista de servidores de Internet en la pestaña Buscar Servidores (Find Servers).
        """
        hl_root = os.path.dirname(cstrike_path) if os.path.basename(cstrike_path).lower().startswith("cstrike") else cstrike_path
        
        target_dirs = [
            os.path.join(hl_root, "platform", "config"),
            os.path.join(hl_root, "config"),
            os.path.join(cstrike_path, "resource")
        ]

        masterservers_content = '''"MasterServers"
{
	"hl1"
	{
		"0"
		{
			"addr"		"hl1master.steampowered.com:27011"
		}
		"1"
		{
			"addr"		"hl1master.steampowered.com:27010"
		}
		"2"
		{
			"addr"		"ms.cs-monitoring.ru:27010"
		}
		"3"
		{
			"addr"		"master.css.setti.info:27015"
		}
		"4"
		{
			"addr"		"hl1master.counter-strike.net:27010"
		}
	}
}
'''
        repaired_paths = []
        for d in target_dirs:
            try:
                os.makedirs(d, exist_ok=True)
                target_file = os.path.join(d, "MasterServers.vdf")
                # Quitar read-only si ya existía para sobrescribir
                if sys.platform == "win32" and os.path.exists(target_file):
                    import ctypes
                    ctypes.windll.kernel32.SetFileAttributesW(target_file, 0x80)  # FILE_ATTRIBUTE_NORMAL
                
                with open(target_file, "w", encoding="utf-8") as f:
                    f.write(masterservers_content)
                
                # Bloquear en solo lectura (+R) para evitar que servidores maliciosos lo borren
                if sys.platform == "win32":
                    import ctypes
                    ctypes.windll.kernel32.SetFileAttributesW(target_file, 0x01)
                
                repaired_paths.append(target_file)
            except Exception:
                pass

        if repaired_paths:
            return True, f"MasterServers.vdf actualizado en {len(repaired_paths)} ubicaciones y protegido como Solo Lectura."
        return False, "No se pudo actualizar MasterServers.vdf."


steam_launcher = SteamLauncher()
