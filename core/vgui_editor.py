# -*- coding: utf-8 -*-
"""
Módulo Editor de VGUI y Esquemas (resource/GameMenu.res, TrackerScheme.res)
Permite modificar los botones del menú de inicio, atajos de conexión rápida,
fuentes y colores de la interfaz con respaldo automático.
"""

import json
import os
import re
from core.backup_manager import backup_manager

DEFAULT_GAME_MENU = [
    {"label": "#GameUI_GameMenu_ResumeGame", "command": "ResumeGame", "OnlyInGame": "1"},
    {"label": "#GameUI_GameMenu_Disconnect", "command": "Disconnect", "OnlyInGame": "1"},
    {"label": "#GameUI_GameMenu_PlayerList", "command": "OpenPlayerListDialog", "OnlyInGame": "1"},
    {"label": "★ RECONECTAR AL SERVIDOR (RETRY) ★", "command": "engine retry", "OnlyInGame": "1"},
    {"label": "🔊 LIMPIAR SONIDO (STOPSOUND)", "command": "engine stopsound", "OnlyInGame": "1"},
    {"label": "", "command": "", "notmapped": "1"},  # Separador
    {"label": "#GameUI_GameMenu_FindServers", "command": "OpenServerBrowser"},
    {"label": "#GameUI_GameMenu_CreateServer", "command": "OpenCreateMultiplayerGameDialog"},
    {"label": "📺 REPRODUCTOR DE DEMOS", "command": "engine viewdemo"},
    {"label": "💻 ABRIR CONSOLA", "command": "engine toggleconsole"},
    {"label": "#GameUI_GameMenu_Options", "command": "OpenOptionsDialog"},
    {"label": "#GameUI_GameMenu_Quit", "command": "Quit"},
]


class VGUIEditor:
    @staticmethod
    def load_game_menu(cstrike_path):
        """Carga y parsea GameMenu.res desde cstrike/resource/GameMenu.res."""
        menu_path = os.path.join(cstrike_path, "resource", "GameMenu.res")
        if not os.path.exists(menu_path):
            return DEFAULT_GAME_MENU

        items = []
        try:
            with open(menu_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Extraer bloques {"label" ... "command" ...}
            blocks = re.findall(r'\"(\d+)\"\s*\{([^}]+)\}', content)
            for idx_str, block in blocks:
                item = {}
                labels = re.findall(r'\"label\"\s*\"([^\"]*)\"', block, re.I)
                commands = re.findall(r'\"command\"\s*\"([^\"]*)\"', block, re.I)
                only_ingame = re.findall(r'\"OnlyInGame\"\s*\"([^\"]*)\"', block, re.I)
                not_ingame = re.findall(r'\"notingame\"\s*\"([^\"]*)\"', block, re.I)

                item["label"] = labels[0] if labels else ""
                item["command"] = commands[0] if commands else ""
                if only_ingame:
                    item["OnlyInGame"] = only_ingame[0]
                if not_ingame:
                    item["notingame"] = not_ingame[0]
                items.append(item)

            return items if items else DEFAULT_GAME_MENU
        except Exception:
            return DEFAULT_GAME_MENU

    @staticmethod
    def save_game_menu(cstrike_path, items):
        """Genera y guarda el archivo KeyValues GameMenu.res en cstrike/resource/."""
        dest_path = os.path.join(cstrike_path, "resource", "GameMenu.res")
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        # Snapshot previo
        backup_manager.backup_file(cstrike_path, "resource/GameMenu.res", action_desc="Editor de GameMenu.res")

        lines = ['"GameMenu"\n{']
        counter = 1
        for item in items:
            lbl = item.get("label", "").strip()
            cmd = item.get("command", "").strip()
            lines.append(f'\t"{counter}"')
            lines.append('\t{')
            lines.append(f'\t\t"label" "{lbl}"')
            lines.append(f'\t\t"command" "{cmd}"')
            if item.get("OnlyInGame") == "1":
                lines.append('\t\t"OnlyInGame" "1"')
            if item.get("notingame") == "1":
                lines.append('\t\t"notingame" "1"')
            lines.append('\t}')
            counter += 1

        lines.append('}\n')
        content = "\n".join(lines)

        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True

    @staticmethod
    def generate_tracker_scheme_colors(cstrike_path, hud_color_rgb, chat_font_size=14):
        """
        Personaliza los colores del HUD en resource/TrackerScheme.res y ClientScheme.res.
        hud_color_rgb: tupla o lista (R, G, B) ej (245, 166, 35)
        """
        r, g, b = hud_color_rgb
        scheme_path = os.path.join(cstrike_path, "resource", "TrackerScheme.res")
        os.makedirs(os.path.dirname(scheme_path), exist_ok=True)

        backup_manager.backup_file(cstrike_path, "resource/TrackerScheme.res", action_desc="Esquema TrackerScheme.res")

        content = f"""// Esquema de Colores Personalizado CS 1.6 Studio Pro
Scheme
{{
\tColors
\t{{
\t\t"BaseText" "{r} {g} {b} 255"
\t\t"BrightBaseText" "{min(255, r+30)} {min(255, g+30)} {min(255, b+30)} 255"
\t\t"SelectedText" "255 255 255 255"
\t\t"DimBaseText" "{max(0, r-50)} {max(0, g-50)} {max(0, b-50)} 200"
\t\t"LabelDimText" "{max(0, r-60)} {max(0, g-60)} {max(0, b-60)} 255"
\t\t"ControlText" "{r} {g} {b} 255"
\t}}
}}
"""
        with open(scheme_path, "w", encoding="utf-8") as f:
            f.write(content)

        return True


vgui_editor = VGUIEditor()
