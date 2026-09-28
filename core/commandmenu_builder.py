# -*- coding: utf-8 -*-
"""
Módulo Compilador de CommandMenu (commandmenu.txt) para CS 1.6
Organiza las opciones del menú [H] con límite ergonómico de máximo 9 opciones por nivel
para evitar incómodas paginaciones numéricas dentro del juego.
"""

import os
from core.backup_manager import backup_manager

DEFAULT_COMMANDMENU_TREE = [
    {
        "title": "⚡ Rates y Netcode",
        "children": [
            {"title": "100k Fibra Óptica / LAN", "cmd": "rate 100000; cl_updaterate 102; cl_cmdrate 105; ex_interp 0.0098; echo [Rates] 100k aplicado"},
            {"title": "50k Banda Ancha / DSL", "cmd": "rate 50000; cl_updaterate 80; cl_cmdrate 80; ex_interp 0.0125; echo [Rates] 50k aplicado"},
            {"title": "25k Servidores Clásicos", "cmd": "rate 25000; cl_updaterate 60; cl_cmdrate 60; ex_interp 0.0167; echo [Rates] 25k aplicado"},
        ]
    },
    {
        "title": "🎯 Ajustes de Mira",
        "children": [
            {"title": "Verde Neón (Estándar)", "cmd": "cl_crosshair_color 0 255 0"},
            {"title": "Amarillo Ámbar", "cmd": "cl_crosshair_color 255 200 0"},
            {"title": "Azul Eléctrico", "cmd": "cl_crosshair_color 0 180 255"},
            {"title": "Rojo Táctico", "cmd": "cl_crosshair_color 255 0 0"},
            {"title": "Blanco Puro", "cmd": "cl_crosshair_color 255 255 255"},
            {"title": "Tamaño: Pequeña (Small)", "cmd": "cl_crosshair_size small"},
            {"title": "Tamaño: Mediana (Medium)", "cmd": "cl_crosshair_size medium"},
            {"title": "Mira Estática (Sin expansión)", "cmd": "cl_dynamiccrosshair 0"},
            {"title": "Mira Dinámica (Con expansión)", "cmd": "cl_dynamiccrosshair 1"},
        ]
    },
    {
        "title": "🔊 Audio y Utilidades",
        "children": [
            {"title": "Silenciar Bugeos (stopsound)", "cmd": "stopsound; echo [Audio] Sonidos detenidos"},
            {"title": "Volumen 100%", "cmd": "volume 1.0"},
            {"title": "Volumen 50%", "cmd": "volume 0.5"},
            {"title": "Volumen 20%", "cmd": "volume 0.2"},
            {"title": "Reiniciar Sonido (snd_restart)", "cmd": "snd_restart"},
            {"title": "Abrir Consola", "cmd": "toggleconsole"},
            {"title": "Limpiar Sangre y Decals (r_cleardecals)", "cmd": "r_decals 0; r_decals 300"},
        ]
    },
    {
        "title": "🛠️ Servidor Local y Práctica",
        "children": [
            {"title": "Reiniciar Ronda (sv_restart 1)", "cmd": "sv_restart 1"},
            {"title": "Dinero al Máximo ($16.000)", "cmd": "mp_startmoney 16000; sv_restart 1"},
            {"title": "Rondas Infinitas (99 min)", "cmd": "mp_roundtime 9; sv_restart 1"},
            {"title": "Pausar Partida", "cmd": "pause"},
            {"title": "Gravedad Baja (400)", "cmd": "sv_gravity 400"},
            {"title": "Gravedad Normal (800)", "cmd": "sv_gravity 800"},
        ]
    },
    {
        "title": "🤖 Control de Bots",
        "children": [
            {"title": "Añadir Bot Terrorista", "cmd": "bot_add_t"},
            {"title": "Añadir Bot Contra-Terrorista", "cmd": "bot_add_ct"},
            {"title": "Matar Todos los Bots", "cmd": "bot_kill"},
            {"title": "Expulsar Todos los Bots", "cmd": "bot_kick"},
            {"title": "Pausar Bots", "cmd": "bot_stop 1"},
            {"title": "Reanudar Bots", "cmd": "bot_stop 0"},
            {"title": "Solo Cuchillo Bots", "cmd": "bot_knives_only"},
            {"title": "Todas las Armas Bots", "cmd": "bot_all_weapons"},
        ]
    },
    {
        "title": "📹 Grabación de Demos",
        "children": [
            {"title": "Iniciar Demo Rápida (demo_studio)", "cmd": "record demo_studio; echo [Demo] Grabando demo_studio.dem"},
            {"title": "Detener Grabación (stop)", "cmd": "stop; echo [Demo] Grabacion finalizada"},
            {"title": "Reproducir Demo", "cmd": "viewdemo demo_studio"},
        ]
    }
]


class CommandMenuBuilder:
    @staticmethod
    def serialize_tree(tree_items):
        """
        Serializa la estructura de árbol al formato estándar de commandmenu.txt de Valve.
        Valida que ningún nivel exceda las 9 opciones.
        """
        lines = [
            "// ====================================================================",
            "// CS 1.6 MODDING STUDIO PRO - COMMANDMENU.TXT",
            "// Menú en pantalla de la tecla [H] sin paginación molesta (Máx 9 por nivel)",
            "// ====================================================================",
            ""
        ]

        # Nivel 1: máximo 9 categorías
        root_items = tree_items[:9]
        for idx, item in enumerate(root_items, start=1):
            title = item.get("title", f"Opción {idx}")
            children = item.get("children", [])
            cmd = item.get("cmd", "")

            if children:
                lines.append(f'"{idx}" "{title}"')
                lines.append('{')
                # Nivel 2: máximo 9 sub-opciones
                for sub_idx, sub_item in enumerate(children[:9], start=1):
                    sub_title = sub_item.get("title", f"Sub-opción {sub_idx}")
                    sub_cmd = sub_item.get("cmd", "")
                    lines.append(f'\t"{sub_idx}" "{sub_title}" "{sub_cmd}"')
                lines.append('}')
            else:
                lines.append(f'"{idx}" "{title}" "{cmd}"')

        return "\n".join(lines)

    @staticmethod
    def install_commandmenu(cstrike_path, tree_items=None):
        """Genera e instala commandmenu.txt en cstrike/ con snapshot previo."""
        items = tree_items if tree_items is not None else DEFAULT_COMMANDMENU_TREE
        dest_path = os.path.join(cstrike_path, "commandmenu.txt")
        backup_manager.backup_file(cstrike_path, "commandmenu.txt", action_desc="Menú CommandMenu (H)")

        content = CommandMenuBuilder.serialize_tree(items)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)

        return dest_path


commandmenu_builder = CommandMenuBuilder()
