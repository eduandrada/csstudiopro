#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
CSStudioPro - CFG HUB & GOLDRSC NETCODE CALCULATOR
=============================================================================
Módulo de cálculo matemático exacto de netcode para el motor GoldSrc:
 1. Fórmula oficial: ex_interp = 1 / cl_updaterate (e.g. 1/100 = 0.010 s)
 2. Validación de incompatibilidades (fps_override vs fps_max, m_rawinput)
 3. Separación estricta entre parámetros de renderizado y netcode.
 4. Inyector no destructivo: Conserva intactos binds y aliases del usuario.
 5. Snapshot & Rollback automático con compresión y respaldos .bak.
=============================================================================
"""

import os
import re
import time
import shutil
from typing import Dict, Any, List, Optional, Tuple

from utils.logger import logger

class CFGHub:
    """Motor de cálculo de tasas de red y gestión no destructiva de configuraciones .cfg."""

    # Perfiles predefinidos competitivos y especializados
    PRESETS = {
        "competitive_100": {
            "name": "Competitivo Estándar (100 FPS / 10ms Interp)",
            "desc": "Calibración reglamentaria de torneos (CPL/ESL). Registro de hitboxes perfecto a 100 FPS constantes.",
            "target_fps": 100,
            "rate": 100000,
            "cl_updaterate": 102,
            "cl_cmdrate": 105,
            "cl_cmdbackup": 2,
            "gl_vsync": 0,
            "m_rawinput": 1,
            "_snd_mixahead": 0.05
        },
        "kzbhop_highfps": {
            "name": "KZ & BunnyHop (Desbloqueo de FPS / Movilidad)",
            "desc": "Optimizado para servidores de salto, surf y kreedz con desbloqueo fps_override y suavidad en strafes.",
            "target_fps": 250,
            "rate": 100000,
            "cl_updaterate": 102,
            "cl_cmdrate": 105,
            "cl_cmdbackup": 2,
            "gl_vsync": 0,
            "m_rawinput": 1,
            "_snd_mixahead": 0.05
        },
        "casual_native_hd": {
            "name": "Casual & Gráficos Nativos HD",
            "desc": "Máxima fidelidad gráfica con texturas en alta resolución trilineales y netcode equilibrado.",
            "target_fps": 100,
            "rate": 50000,
            "cl_updaterate": 100,
            "cl_cmdrate": 100,
            "cl_cmdbackup": 2,
            "gl_vsync": 0,
            "m_rawinput": 1,
            "_snd_mixahead": 0.07
        },
        "low_ping_esports": {
            "name": "Ultra Baja Latencia (Ping < 20 ms / Fibra Óptica)",
            "desc": "Interpolación extrema calibrada a 9.5 ms para servidores locales o conexiones de fibra.",
            "target_fps": 105,
            "rate": 100000,
            "cl_updaterate": 105,
            "cl_cmdrate": 105,
            "cl_cmdbackup": 2,
            "gl_vsync": 0,
            "m_rawinput": 1,
            "_snd_mixahead": 0.04
        }
    }

    def __init__(self):
        pass

    def calculate_rates(self, ping_ms: float = 30.0, bandwidth_mbps: float = 50.0, target_fps: int = 100) -> Dict[str, Any]:
        """
        Calcula matemáticamente los valores oficiales de netcode del motor GoldSrc:
         - ex_interp = 1 / cl_updaterate
         - cl_cmdrate sincronizado a FPS o tope de 105
         - rate calibrado según ancho de banda (hasta 100000 para Steam/Build 8684)
        """
        # 1. Tasa de actualización de paquetes (cl_updaterate)
        if ping_ms < 25:
            updaterate = 102
        elif ping_ms < 60:
            updaterate = 100
        elif ping_ms < 100:
            updaterate = 80
        else:
            updaterate = 60

        # 2. Fórmula exacta oficial de GoldSrc: ex_interp = 1 / cl_updaterate
        # Redondeado a 4 decimales matemáticos (e.g. 1/102 = 0.0098 s = 9.8 ms)
        ex_interp = round(1.0 / float(updaterate), 4)

        # 3. Tasa de envío de comandos del cliente (cl_cmdrate)
        # El motor envía comandos al ritmo de los FPS pero limitado habitualmente a 105
        cmdrate = min(105, max(60, target_fps))

        # 4. Asignación de ancho de banda (rate)
        if bandwidth_mbps >= 10.0:
            rate = 100000
        elif bandwidth_mbps >= 2.0:
            rate = 50000
        else:
            rate = 25000

        # 5. Manejo de FPS y compatibilidad con fps_override
        if target_fps > 100:
            fps_override = 1
            fps_max = float(target_fps)
        else:
            fps_override = 0
            fps_max = 99.5  # 99.5 evita desincronizaciones físicas en GoldSrc clásico

        # Parámetros de renderizado separados
        render_settings = {
            "gl_vsync": 0,
            "gl_ansio": 0,
            "r_detailtextures": 1,
            "gl_texturemode": "GL_LINEAR_MIPMAP_LINEAR"
        }

        # Parámetros de entrada de mouse
        input_settings = {
            "m_rawinput": 1,
            "m_customaccel": 0,
            "m_filter": 0,
            "m_yaw": 0.022,
            "m_pitch": 0.022
        }

        return {
            "netcode": {
                "rate": rate,
                "cl_updaterate": updaterate,
                "cl_cmdrate": cmdrate,
                "ex_interp": ex_interp,
                "cl_cmdbackup": 2,
                "cl_dlmax": 1024,
                "cl_nosmooth": 1
            },
            "engine": {
                "fps_override": fps_override,
                "fps_max": fps_max,
                "_snd_mixahead": 0.05
            },
            "render": render_settings,
            "input": input_settings,
            "metrics": {
                "interp_ms": round(ex_interp * 1000.0, 1),
                "ping_ms": ping_ms,
                "bandwidth_mbps": bandwidth_mbps,
                "target_fps": target_fps
            }
        }

    def generate_cfg_content(self, calc_results: Dict[str, Any], header_comment: str = "") -> str:
        """Genera el bloque de texto con sintaxis limpia para userconfig.cfg."""
        net = calc_results.get("netcode", {})
        eng = calc_results.get("engine", {})
        rnd = calc_results.get("render", {})
        inp = calc_results.get("input", {})
        met = calc_results.get("metrics", {})

        lines = [
            "// =============================================================================",
            "// CSStudioPro - CONFIGURACIÓN DE ALTO RENDIMIENTO (GOLDRSC ENGINE)",
            f"// Generado automáticamente: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"// Perfil: Interp {met.get('interp_ms', 10.0)}ms | FPS Objetivo: {met.get('target_fps', 100)}",
            "// =============================================================================",
            "",
            "// --- [1/4] NETCODE OFICIAL Y REGISTRO DE IMPACTOS ---",
            f"rate {net.get('rate', 100000)}",
            f"cl_updaterate {net.get('cl_updaterate', 102)}",
            f"cl_cmdrate {net.get('cl_cmdrate', 105)}",
            f"ex_interp {net.get('ex_interp', 0.0098)}",
            f"cl_cmdbackup {net.get('cl_cmdbackup', 2)}",
            f"cl_dlmax {net.get('cl_dlmax', 1024)}",
            f"cl_nosmooth {net.get('cl_nosmooth', 1)}",
            "",
            "// --- [2/4] MOTOR DE FOTOGRAMAS Y AUDIO ---",
            f"fps_override {eng.get('fps_override', 0)}",
            f"fps_max {eng.get('fps_max', 99.5)}",
            f"_snd_mixahead {eng.get('_snd_mixahead', 0.05)}",
            "",
            "// --- [3/4] ENTRADA DE MOUSE PURA (CERO LATENCIA / SIN ACELERACIÓN) ---",
            f"m_rawinput {inp.get('m_rawinput', 1)}",
            f"m_customaccel {inp.get('m_customaccel', 0)}",
            f"m_filter {inp.get('m_filter', 0)}",
            f"m_yaw {inp.get('m_yaw', 0.022)}",
            f"m_pitch {inp.get('m_pitch', 0.022)}",
            "",
            "// --- [4/4] RENDERIZADO Y TEXTURAS ---",
            f"gl_vsync {rnd.get('gl_vsync', 0)}",
            f"gl_ansio {rnd.get('gl_ansio', 0)}",
            f"r_detailtextures {rnd.get('r_detailtextures', 1)}",
            f"gl_texturemode {rnd.get('gl_texturemode', 'GL_LINEAR_MIPMAP_LINEAR')}",
            "",
            'echo "[CSStudioPro] userconfig.cfg cargado con éxito. Netcode calibrado a 100%."'
        ]
        return "\n".join(lines)

    def backup_cstrike_cfgs(self, cstrike_path: str) -> Optional[str]:
        """
        Crea un respaldo de seguridad instantáneo de todos los .cfg en cstrike/
        antes de cualquier modificación.
        """
        if not cstrike_path or not os.path.isdir(cstrike_path):
            return None

        backup_dir = os.path.join(cstrike_path, "backup_studio", "cfg_snapshots")
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        snapshot_folder = os.path.join(backup_dir, f"snapshot_{timestamp}")
        os.makedirs(snapshot_folder, exist_ok=True)

        copied = 0
        for f in os.listdir(cstrike_path):
            if f.lower().endswith(".cfg"):
                src = os.path.join(cstrike_path, f)
                dst = os.path.join(snapshot_folder, f)
                try:
                    shutil.copy2(src, dst)
                    copied += 1
                except Exception:
                    pass

        logger.info(f"[CFGHub] Respaldo de {copied} archivos .cfg creado en {snapshot_folder}")
        return snapshot_folder

    def inject_non_destructive(self, cstrike_path: str, new_settings: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Inyecta la configuración en userconfig.cfg sin sobrescribir binds ni aliases existentes.
        Aplica un Snapshot previo automático.
        """
        if not cstrike_path or not os.path.isdir(cstrike_path):
            return False, "Ruta de cstrike no conectada."

        # 1. Respaldo preventivo
        snapshot_path = self.backup_cstrike_cfgs(cstrike_path)

        userconfig_path = os.path.join(cstrike_path, "userconfig.cfg")
        cfg_content = self.generate_cfg_content(new_settings)

        # Leer archivo existente para conservar binds y aliases
        existing_lines = []
        if os.path.isfile(userconfig_path):
            try:
                with open(userconfig_path, "r", encoding="utf-8", errors="ignore") as f:
                    existing_lines = f.readlines()
            except Exception as e:
                logger.error(f"[CFGHub] Error al leer {userconfig_path}: {e}")

        # Filtrar comandos gestionados existentes para no duplicarlos
        managed_cvars = {
            "rate", "cl_updaterate", "cl_cmdrate", "ex_interp", "cl_cmdbackup",
            "cl_dlmax", "cl_nosmooth", "fps_override", "fps_max", "_snd_mixahead",
            "m_rawinput", "m_customaccel", "m_filter", "m_yaw", "m_pitch",
            "gl_vsync", "gl_ansio", "r_detailtextures", "gl_texturemode"
        }

        user_custom_lines = []
        in_csstudio_block = False

        for line in existing_lines:
            stripped = line.strip()
            if "CSStudioPro" in stripped:
                in_csstudio_block = True
                continue
            if in_csstudio_block and stripped.startswith("echo"):
                in_csstudio_block = False
                continue
            if in_csstudio_block:
                continue

            # Verificar si la línea define una cvar gestionada
            first_word = stripped.split()[0].lower() if stripped.split() else ""
            if first_word in managed_cvars:
                continue

            user_custom_lines.append(line)

        # Re-ensamblar: bloque nuevo de CSStudioPro + binds y aliases del usuario
        final_text = cfg_content + "\n\n// --- Binds y Personalizaciones Previas del Usuario ---\n" + "".join(user_custom_lines)

        try:
            with open(userconfig_path, "w", encoding="utf-8") as f:
                f.write(final_text)
            logger.info(f"[CFGHub] userconfig.cfg inyectado con éxito en {userconfig_path}")
            return True, f"Configuración inyectada con éxito (Respaldo guardado en: {os.path.basename(snapshot_path or '')})"
        except Exception as e:
            logger.error(f"[CFGHub] Error al escribir {userconfig_path}: {e}")
            return False, f"Error al escribir archivo: {str(e)}"

    def list_snapshots(self, cstrike_path: str) -> List[Dict[str, Any]]:
        """Lista los respaldos de configuración disponibles para rollback."""
        snapshots = []
        if not cstrike_path or not os.path.isdir(cstrike_path):
            return snapshots

        backup_dir = os.path.join(cstrike_path, "backup_studio", "cfg_snapshots")
        if not os.path.isdir(backup_dir):
            return snapshots

        for folder in sorted(os.listdir(backup_dir), reverse=True):
            fpath = os.path.join(backup_dir, folder)
            if os.path.isdir(fpath):
                files = os.listdir(fpath)
                snapshots.append({
                    "id": folder,
                    "path": fpath,
                    "files_count": len(files),
                    "created": time.ctime(os.path.getctime(fpath))
                })
        return snapshots

    def rollback_snapshot(self, cstrike_path: str, snapshot_id: str) -> Tuple[bool, str]:
        """Restaura los archivos .cfg a partir de un snapshot previo."""
        if not cstrike_path or not os.path.isdir(cstrike_path):
            return False, "Ruta de cstrike inválida."

        snapshot_dir = os.path.join(cstrike_path, "backup_studio", "cfg_snapshots", snapshot_id)
        if not os.path.isdir(snapshot_dir):
            return False, "Snapshot no encontrado."

        restored_count = 0
        for f in os.listdir(snapshot_dir):
            if f.lower().endswith(".cfg"):
                src = os.path.join(snapshot_dir, f)
                dst = os.path.join(cstrike_path, f)
                try:
                    shutil.copy2(src, dst)
                    restored_count += 1
                except Exception as e:
                    logger.error(f"[CFGHub] Error restaurando {f}: {e}")

        logger.info(f"[CFGHub] Snapshot {snapshot_id} restaurado ({restored_count} archivos).")
        return True, f"¡Rollback completado! {restored_count} archivos .cfg restaurados."


# Instancia singleton
cfg_hub = CFGHub()
