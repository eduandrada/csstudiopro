# -*- coding: utf-8 -*-
"""
Módulo Generador de Netcode Competitivo, Binds y userconfig.cfg para CS 1.6
Ajuste matemático entre cl_updaterate y ex_interp (1 / updaterate),
eliminación de comandos placebo, optimización de mouse puro y compras rápidas.
"""

import os
from core.backup_manager import backup_manager

NETCODE_PRESETS = {
    "fiber_100k": {
        "name": "Fibra Óptica / LAN Competitiva (100k)",
        "rate": 100000,
        "cl_updaterate": 102,
        "cl_cmdrate": 105,
        "cl_cmdbackup": 2,
        "fps_max": 99.5,
        "ex_interp": 0.0098,  # 1 / 102
        "desc": "Máxima tasa de muestreo y mínimo delay para conexiones modernas estables."
    },
    "dsl_50k": {
        "name": "Banda Ancha Estándar / DSL (50k)",
        "rate": 50000,
        "cl_updaterate": 80,
        "cl_cmdrate": 80,
        "cl_cmdbackup": 2,
        "fps_max": 99.5,
        "ex_interp": 0.0125,  # 1 / 80
        "desc": "Balance óptimo para conexiones con jitter moderado o servidores lejanos."
    },
    "classic_25k": {
        "name": "Servidores Clásicos / Estándar Valve (25k)",
        "rate": 25000,
        "cl_updaterate": 60,
        "cl_cmdrate": 60,
        "cl_cmdbackup": 3,
        "fps_max": 99.5,
        "ex_interp": 0.0167,  # 1 / 60
        "desc": "Compatibilidad absoluta con servidores antiguos con sv_maxrate 25000."
    }
}

DEFAULT_NUMPAD_BINDS = {
    "kp_ins": "vesthelm; vest;",
    "kp_end": "ak47; m4a1;",
    "kp_downarrow": "awp;",
    "kp_pgdn": "deagle;",
    "kp_leftarrow": "hegren;",
    "kp_5": "flash;",
    "kp_rightarrow": "sgren;",
    "kp_home": "defuser;",
    "kp_uparrow": "primammo; secammo;",
    "kp_pgup": "famas; galil;",
    "kp_plus": "shield;",
    "kp_enter": "hegren; flash; flash; sgren; defuser; vesthelm;",
}


class ConfigGenerator:
    @staticmethod
    def calculate_ex_interp(updaterate):
        """Calcula el ex_interp matemáticamente exacto: 1 / cl_updaterate."""
        u = max(10, min(105, float(updaterate)))
        return round(1.0 / u, 4)

    @staticmethod
    def generate_userconfig_text(
        rate=100000,
        cl_updaterate=102,
        cl_cmdrate=105,
        cl_cmdbackup=2,
        fps_max=99.5,
        fps_override=False,
        raw_input=True,
        crosshair_color="0 255 0",
        crosshair_size="small",
        crosshair_dynamic=False,
        snd_mixahead=0.05,
        numpad_binds=None
    ):
        """Genera el contenido de userconfig.cfg sin comandos placebo."""
        ex_interp = ConfigGenerator.calculate_ex_interp(cl_updaterate)
        binds = numpad_binds if numpad_binds is not None else DEFAULT_NUMPAD_BINDS

        cfg_lines = [
            "// ====================================================================",
            "// CS 1.6 MODDING & TUNING STUDIO PRO - USERCONFIG.CFG OPTIMIZADO",
            "// Generado con sincronización matemática de Netcode e Input Puro",
            "// ====================================================================",
            "",
            "// --- [1. SINCRONIZACIÓN DE NETCODE REAL (CERO PLACEBO)] ---",
            f"rate \"{rate}\"",
            f"cl_updaterate \"{cl_updaterate}\"",
            f"cl_cmdrate \"{cl_cmdrate}\"",
            f"cl_cmdbackup \"{cl_cmdbackup}\"",
            f"ex_interp \"{ex_interp}\" // Sincronizado matemáticamente a 1 / {cl_updaterate}",
            "cl_resend \"2\"",
            "cl_dlmax \"1024\"",
            "cl_nosmooth \"1\"",
            "cl_smoothtime \"0\"",
            "",
            "// --- [2. RENDIMIENTO Y FPS] ---",
            f"fps_max \"{fps_max}\"",
            f"fps_override \"{'1' if fps_override else '0'}\"",
            "gl_vsync \"0\"",
            "gl_ansio \"0\"",
            "r_dynamic \"0\"",
            "",
            "// --- [3. INPUT Y RATÓN PURO (SIN ACELERACIÓN DE WINDOWS)] ---",
            f"m_rawinput \"{'1' if raw_input else '0'}\" // Lectura directa del sensor del ratón",
            "m_customaccel \"0\"",
            "m_customaccel_exponent \"1\"",
            "m_customaccel_max \"0\"",
            "m_customaccel_scale \"0\"",
            "m_filter \"0\"",
            "m_yaw \"0.022\" // Ejes simétricos",
            "m_pitch \"0.022\"",
            "",
            "// --- [4. AUDIO DE BAJA LATENCIA (BUFFER ACELERADO)] ---",
            f"_snd_mixahead \"{snd_mixahead}\" // Reduce el retraso de sonido a 50ms",
            "hisound \"1\"",
            "suitvolume \"0\"",
            "",
            "// --- [5. MIRA Y VISUALES COMPETITIVOS] ---",
            f"cl_crosshair_color \"{crosshair_color}\"",
            f"cl_crosshair_size \"{crosshair_size}\"",
            f"cl_dynamiccrosshair \"{'1' if crosshair_dynamic else '0'}\"",
            "cl_crosshair_translucent \"0\"",
            "cl_radartype \"1\"",
            "cl_minmodels \"1\"",
            "",
            "// --- [6. BINDS DE COMPRA RÁPIDA (TECLADO NUMÉRICO)] ---",
        ]

        for key, cmd in binds.items():
            cfg_lines.append(f"bind \"{key.upper()}\" \"{cmd}\"")

        cfg_lines.extend([
            "",
            "// Confirmación en consola de carga exitosa",
            "echo \"[STUDIO PRO] userconfig.cfg cargado con éxito. Netcode sincronizado.\"",
            ""
        ])

        return "\n".join(cfg_lines)

    @staticmethod
    def install_userconfig(cstrike_path, cfg_text):
        """Instala el userconfig.cfg en cstrike/ y asegura la ejecución en autoexec.cfg."""
        dest_path = os.path.join(cstrike_path, "userconfig.cfg")
        backup_manager.backup_file(cstrike_path, "userconfig.cfg", action_desc="Configuración userconfig.cfg")

        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(cfg_text)

        # Asegurar 'exec userconfig.cfg' en autoexec.cfg
        autoexec_path = os.path.join(cstrike_path, "autoexec.cfg")
        exec_cmd = "exec userconfig.cfg"
        already_has = False
        if os.path.exists(autoexec_path):
            try:
                with open(autoexec_path, "r", encoding="utf-8", errors="ignore") as f:
                    if exec_cmd in f.read():
                        already_has = True
            except Exception:
                pass

        if not already_has:
            backup_manager.backup_file(cstrike_path, "autoexec.cfg", action_desc="Inyección autoexec.cfg")
            with open(autoexec_path, "a", encoding="utf-8") as f:
                f.write(f"\n{exec_cmd}\n")

        return dest_path


config_generator = ConfigGenerator()
