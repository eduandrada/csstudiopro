# -*- coding: utf-8 -*-
"""
CS 1.6 Tactical Telemetry Engine (Zero-Ban & VAC-Safe)
Monitor asíncrono y parser en tiempo real de logs locales (console_telemetry.log
y mp_logdetail 3) para calcular métricas competitivas avanzadas (Rating, KAST,
ADR, HS%, Duelos de apertura, Heatmap de impactos y radar de habilidades).
"""

import json
import os
import re
import threading
import time


class TelemetryEngine:
    def __init__(self, cstrike_path=None, data_dir=None):
        self.cstrike_path = cstrike_path
        self.data_dir = data_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.db_file = os.path.join(self.data_dir, "telemetry_db.json")

        self.log_filename = "console_telemetry.log"
        self._monitor_thread = None
        self._stop_event = threading.Event()
        self._file_offset = 0

        # Identificador del jugador local (se autocalibra o usa el nombre detectado)
        self.local_player_name = None

        # Estado en memoria de la sesión activa
        self.session_data = self._load_initial_db()

        # Compilación de Expresiones Regulares Oficiales del Motor GoldSrc
        self._init_regexes()

    def _init_regexes(self):
        # 1. Kills: "Killer" killed "Victim" with "weapon" (headshot)
        self.re_kill = re.compile(
            r'\"(?P<killer>[^\"]+)\"\s+killed\s+\"(?P<victim>[^\"]+)\"\s+with\s+\"(?P<weapon>[^\"]+)\"(?:\s+\((?P<headshot>headshot)\))?',
            re.IGNORECASE
        )
        # 2. Suicide / World kill
        self.re_suicide = re.compile(
            r'\"(?P<player>[^\"]+)\"\s+committed\s+suicide\s+with\s+\"(?P<weapon>[^\"]+)\"',
            re.IGNORECASE
        )
        # 3. Ronda Start / End
        self.re_round_start = re.compile(r'World\s+triggered\s+\"Round_Start\"', re.IGNORECASE)
        self.re_round_end = re.compile(r'World\s+triggered\s+\"Round_End\"', re.IGNORECASE)
        # 4. Objetivos C4
        self.re_c4_plant = re.compile(r'\"(?P<player>[^\"]+)\"\s+triggered\s+\"Planted_The_Bomb\"', re.IGNORECASE)
        self.re_c4_defuse = re.compile(r'\"(?P<player>[^\"]+)\"\s+triggered\s+\"Defused_The_Bomb\"', re.IGNORECASE)
        self.re_c4_explode = re.compile(r'Target_Bombed', re.IGNORECASE)
        # 5. mp_logdetail 3 - Impactos por extremidad (Head, Chest, Stomach, Arms, Legs)
        self.re_hit_detail = re.compile(
            r'\"(?P<attacker>[^\"]+)\"\s+hit\s+\"(?P<victim>[^\"]+)\"\s+in\s+\"(?P<hitbox>head|chest|stomach|leftarm|rightarm|left arm|right arm|leftleg|rightleg|left leg|right leg)\"\s+for\s+(?P<damage>\d+)\s+damage',
            re.IGNORECASE
        )
        # 6. Resumen de daño de fin de ronda / consola
        self.re_damage_given = re.compile(
            r'Damage\s+Given\s+to\s+\"(?P<victim>[^\"]+)\"\s+-\s+(?P<damage>\d+)\s+in\s+(?P<hits>\d+)\s+hit',
            re.IGNORECASE
        )
        self.re_damage_taken = re.compile(
            r'Damage\s+Taken\s+from\s+\"(?P<attacker>[^\"]+)\"\s+-\s+(?P<damage>\d+)\s+in\s+(?P<hits>\d+)\s+hit',
            re.IGNORECASE
        )
        # 7. Granadas lanzadas
        self.re_grenade = re.compile(
            r'\"(?P<player>[^\"]+)\"\s+threw\s+(?P<grenade>hegrenade|flashbang|smokegrenade)',
            re.IGNORECASE
        )
        # 8. Compras de armas
        self.re_buy = re.compile(
            r'\"(?P<player>[^\"]+)\"\s+bought\s+\"(?P<item>[^\"]+)\"',
            re.IGNORECASE
        )

    def _load_initial_db(self):
        default_state = {
            "player_name": "Player",
            "matches_count": 1,
            "total_rounds": 0,
            "kills": 0,
            "deaths": 0,
            "assists": 0,
            "headshots": 0,
            "wallbang_kills": 0,
            "total_damage_given": 0,
            "total_damage_taken": 0,
            "opening_duels_won": 0,
            "opening_duels_lost": 0,
            "rounds_kast_qualified": 0,
            "clutches_won": 0,
            "c4_plants": 0,
            "c4_defuses": 0,
            "grenades_thrown": {
                "hegrenade": 0,
                "flashbang": 0,
                "smokegrenade": 0
            },
            "hitbox_given": {
                "head": 0,
                "chest": 0,
                "stomach": 0,
                "arms": 0,
                "legs": 0
            },
            "hitbox_taken": {
                "head": 0,
                "chest": 0,
                "stomach": 0,
                "arms": 0,
                "legs": 0
            },
            "weapon_kills": {},
            "round_history": [],
            "current_round": {
                "round_num": 1,
                "kills": 0,
                "died": False,
                "assisted": False,
                "survived": True,
                "traded": False,
                "death_timestamp": None,
                "damage_given": 0,
                "damage_taken": 0,
                "is_first_duel": False,
                "won_first_duel": False
            }
        }

        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data
            except Exception as e:
                print(f"[TelemetryEngine] Error al leer base de datos, inicializando nueva: {e}")

        return default_state

    def save_db(self):
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(self.session_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[TelemetryEngine] Error al guardar base de datos: {e}")

    def reset_session(self):
        """Reinicia los contadores de la sesión actual"""
        self.session_data = self._load_initial_db()
        self.session_data["total_rounds"] = 0
        self.session_data["kills"] = 0
        self.session_data["deaths"] = 0
        self.session_data["headshots"] = 0
        self.session_data["total_damage_given"] = 0
        self.session_data["total_damage_taken"] = 0
        self.session_data["opening_duels_won"] = 0
        self.session_data["opening_duels_lost"] = 0
        self.session_data["rounds_kast_qualified"] = 0
        self.session_data["hitbox_given"] = {"head": 0, "chest": 0, "stomach": 0, "arms": 0, "legs": 0}
        self.session_data["hitbox_taken"] = {"head": 0, "chest": 0, "stomach": 0, "arms": 0, "legs": 0}
        self.session_data["weapon_kills"] = {}
        self.session_data["round_history"] = []
        self._file_offset = 0
        self.save_db()
        return True

    def set_cstrike_path(self, path):
        self.cstrike_path = path

    def get_log_file_path(self):
        if not self.cstrike_path:
            return None
        return os.path.join(self.cstrike_path, self.log_filename)

    def is_log_active(self):
        p = self.get_log_file_path()
        return bool(p and os.path.exists(p))

    def ensure_client_telemetry_commands(self, userconfig_path):
        """Inyecta de forma transparente 'con_logfile console_telemetry.log' y 'mp_logdetail 3'"""
        if not userconfig_path or not os.path.exists(userconfig_path):
            return False

        try:
            with open(userconfig_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            needed = []
            if 'con_logfile "console_telemetry.log"' not in content and "con_logfile console_telemetry.log" not in content:
                needed.append('con_logfile "console_telemetry.log"')
            if "mp_logdetail 3" not in content:
                needed.append("mp_logdetail 3")

            if needed:
                with open(userconfig_path, "a", encoding="utf-8") as f:
                    f.write("\n// [CS 1.6 Studio Pro] Telemetria y AI Coach\n")
                    for cmd in needed:
                        f.write(f"{cmd}\n")
                return True
        except Exception as e:
            print(f"[TelemetryEngine] No se pudo escribir comandos en userconfig: {e}")
        return False

    def start_monitoring(self):
        """Inicia el observador asíncrono en segundo plano"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return True

        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        print("[TelemetryEngine] Monitor de telemetría activo en segundo plano.")
        return True

    def stop_monitoring(self):
        self._stop_event.set()
        print("[TelemetryEngine] Monitor de telemetría detenido.")
        return True

    def _monitor_loop(self):
        """Loop no invasivo que lee el archivo de log conforme el juego escribe"""
        while not self._stop_event.is_set():
            log_path = self.get_log_file_path()
            if not log_path or not os.path.exists(log_path):
                self._stop_event.wait(3.0)
                continue

            try:
                file_size = os.path.getsize(log_path)
                # Si el archivo fue truncado o reiniciado
                if file_size < self._file_offset:
                    self._file_offset = 0

                if file_size > self._file_offset:
                    with open(log_path, "r", encoding="latin-1", errors="ignore") as f:
                        f.seek(self._file_offset)
                        lines = f.readlines()
                        self._file_offset = f.tell()

                    if lines:
                        for line in lines:
                            self.parse_log_line(line.strip())
                        self.save_db()

            except Exception as e:
                print(f"[TelemetryEngine] Aviso de lectura de log: {e}")

            self._stop_event.wait(1.5)

    def parse_log_line(self, line):
        if not line:
            return

        # 1. Round Start
        if self.re_round_start.search(line):
            self._handle_round_start()
            return

        # 2. Round End
        if self.re_round_end.search(line):
            self._handle_round_end()
            return

        # 3. Kills / Deaths
        m_kill = self.re_kill.search(line)
        if m_kill:
            killer = m_kill.group("killer")
            victim = m_kill.group("victim")
            weapon = m_kill.group("weapon").lower()
            is_hs = bool(m_kill.group("headshot"))

            self._handle_kill_event(killer, victim, weapon, is_hs)
            return

        # 4. mp_logdetail 3 - Impactos anatómicos
        m_hit = self.re_hit_detail.search(line)
        if m_hit:
            attacker = m_hit.group("attacker")
            victim = m_hit.group("victim")
            raw_box = m_hit.group("hitbox").lower().replace(" ", "")
            dmg = int(m_hit.group("damage"))
            self._handle_hit_detail(attacker, victim, raw_box, dmg)
            return

        # 5. Daño recibido / infligido consolidado
        m_dg = self.re_damage_given.search(line)
        if m_dg:
            dmg = int(m_dg.group("damage"))
            self.session_data["total_damage_given"] += dmg
            self.session_data["current_round"]["damage_given"] += dmg
            return

        m_dt = self.re_damage_taken.search(line)
        if m_dt:
            dmg = int(m_dt.group("damage"))
            self.session_data["total_damage_taken"] += dmg
            self.session_data["current_round"]["damage_taken"] += dmg
            return

        # 6. Granadas lanzadas
        m_g = self.re_grenade.search(line)
        if m_g:
            g_type = m_g.group("grenade").lower()
            if g_type in self.session_data["grenades_thrown"]:
                self.session_data["grenades_thrown"][g_type] += 1
            return

        # 7. Objetivos C4
        if self.re_c4_plant.search(line):
            self.session_data["c4_plants"] += 1
        elif self.re_c4_defuse.search(line):
            self.session_data["c4_defuses"] += 1

    def _handle_round_start(self):
        # Cerrar ronda previa si estaba abierta
        self._handle_round_end()
        cur_num = self.session_data.get("total_rounds", 0) + 1
        self.session_data["current_round"] = {
            "round_num": cur_num,
            "kills": 0,
            "died": False,
            "assisted": False,
            "survived": True,
            "traded": False,
            "death_timestamp": None,
            "damage_given": 0,
            "damage_taken": 0,
            "is_first_duel": False,
            "won_first_duel": False
        }

    def _handle_round_end(self):
        cur = self.session_data.get("current_round")
        if not cur or cur.get("round_num") is None:
            return

        # KAST Qualified check: Kill, Assist, Survived, o Traded
        is_kast = (cur["kills"] > 0) or cur["assisted"] or cur["survived"] or cur["traded"]
        if is_kast:
            self.session_data["rounds_kast_qualified"] += 1

        self.session_data["total_rounds"] += 1
        self.session_data["round_history"].append({
            "round": cur["round_num"],
            "kills": cur["kills"],
            "died": cur["died"],
            "damage": cur["damage_given"],
            "kast": is_kast,
            "won_first_duel": cur["won_first_duel"]
        })
        if len(self.session_data["round_history"]) > 30:
            self.session_data["round_history"].pop(0)

        # Reset ronda
        self.session_data["current_round"] = {
            "round_num": self.session_data["total_rounds"] + 1,
            "kills": 0,
            "died": False,
            "assisted": False,
            "survived": True,
            "traded": False,
            "death_timestamp": None,
            "damage_given": 0,
            "damage_taken": 0,
            "is_first_duel": False,
            "won_first_duel": False
        }

    def _handle_kill_event(self, killer, victim, weapon, is_hs):
        # Auto-calibrar jugador local si no está fijado
        if not self.local_player_name:
            self.local_player_name = killer

        is_local_kill = (killer.lower() == self.local_player_name.lower())
        is_local_death = (victim.lower() == self.local_player_name.lower())

        cur = self.session_data["current_round"]

        # Primer enfrentamiento de la ronda (Opening duel)
        if not cur["is_first_duel"] and (is_local_kill or is_local_death):
            cur["is_first_duel"] = True
            if is_local_kill:
                cur["won_first_duel"] = True
                self.session_data["opening_duels_won"] += 1
            else:
                cur["won_first_duel"] = False
                self.session_data["opening_duels_lost"] += 1

        if is_local_kill:
            self.session_data["kills"] += 1
            cur["kills"] += 1
            if is_hs:
                self.session_data["headshots"] += 1

            # Conteo de arma
            w_stats = self.session_data["weapon_kills"].setdefault(weapon, {"kills": 0, "hs": 0})
            w_stats["kills"] += 1
            if is_hs:
                w_stats["hs"] += 1

        elif is_local_death:
            self.session_data["deaths"] += 1
            cur["died"] = True
            cur["survived"] = False
            cur["death_timestamp"] = time.time()

    def _handle_hit_detail(self, attacker, victim, raw_box, dmg):
        # Normalizar hitbox
        norm_box = "chest"
        if "head" in raw_box:
            norm_box = "head"
        elif "stomach" in raw_box:
            norm_box = "stomach"
        elif "arm" in raw_box:
            norm_box = "arms"
        elif "leg" in raw_box:
            norm_box = "legs"

        is_attacker_local = (attacker.lower() == (self.local_player_name or "").lower())
        is_victim_local = (victim.lower() == (self.local_player_name or "").lower())

        if is_attacker_local:
            self.session_data["hitbox_given"][norm_box] += dmg
            self.session_data["total_damage_given"] += dmg
        elif is_victim_local:
            self.session_data["hitbox_taken"][norm_box] += dmg
            self.session_data["total_damage_taken"] += dmg

    def calculate_metrics(self):
        """Calcula todas las métricas profesionales (KAST, ADR, HS%, Combat Score, Radar)"""
        d = self.session_data
        rounds = max(1, d.get("total_rounds", 0))
        kills = d.get("kills", 0)
        deaths = max(1, d.get("deaths", 0))
        hs = d.get("headshots", 0)
        dmg_given = d.get("total_damage_given", 0)
        kast_rounds = d.get("rounds_kast_qualified", 0)
        op_won = d.get("opening_duels_won", 0)
        op_lost = d.get("opening_duels_lost", 0)
        total_openings = max(1, op_won + op_lost)

        # 1. K/D Ratio
        kd_ratio = round(kills / deaths, 2)

        # 2. Headshot Percentage (HS%)
        hs_pct = round((hs / max(1, kills)) * 100, 1)

        # 3. Average Damage per Round (ADR)
        adr = round(dmg_given / rounds, 1)

        # 4. KAST %
        kast_pct = round((kast_rounds / rounds) * 100, 1)

        # 5. Opening Duel Winrate
        opening_winrate = round((op_won / total_openings) * 100, 1)

        # 6. Combat Score Global (0 a 100)
        # Fórmula ponderada: ADR (30%), KAST (25%), K/D (20%), Opening (15%), Utilidad/Obj (10%)
        adr_score = min(100.0, (adr / 100.0) * 100.0)
        kast_score = min(100.0, kast_pct)
        kd_score = min(100.0, (kd_ratio / 2.0) * 100.0)
        op_score = min(100.0, opening_winrate)
        obj_score = min(100.0, ((d.get("c4_plants", 0) + d.get("c4_defuses", 0)) * 20.0))

        combat_score = round(
            (adr_score * 0.30) +
            (kast_score * 0.25) +
            (kd_score * 0.20) +
            (op_score * 0.15) +
            (obj_score * 0.10)
        )
        combat_score = max(5, min(99, combat_score))

        # 7. Radar de Habilidades (5 Ejes: 0-100)
        # Aim: HS% + efectividad en headbox
        total_hits = sum(d["hitbox_given"].values()) or 1
        head_hit_ratio = (d["hitbox_given"]["head"] / total_hits) * 100
        radar_aim = min(100, round((hs_pct * 0.6) + (head_hit_ratio * 1.5)))

        # Supervivencia: Survival rate y KAST
        surv_ratio = ((rounds - d.get("deaths", 0)) / rounds) * 100
        radar_survival = min(100, max(10, round((surv_ratio * 0.5) + (kast_pct * 0.5))))

        # Utilidad: granadas y daño HE
        he_count = d["grenades_thrown"].get("hegrenade", 0)
        fb_count = d["grenades_thrown"].get("flashbang", 0)
        radar_utility = min(100, max(15, round(((he_count * 8) + (fb_count * 5)) / rounds * 40)))

        # Economía: proporción de rondas y C4
        radar_economy = min(100, max(20, round(60 + (d.get("c4_plants", 0) * 5) + (d.get("c4_defuses", 0) * 8))))

        # Posicionamiento: Opening duels y baja exposición a headshots recibidos
        total_hits_taken = sum(d["hitbox_taken"].values()) or 1
        head_taken_ratio = (d["hitbox_taken"]["head"] / total_hits_taken) * 100
        radar_positioning = min(100, max(10, round(opening_winrate * 0.7 + max(0, 50 - head_taken_ratio))))

        return {
            "kd_ratio": kd_ratio,
            "kills": kills,
            "deaths": d.get("deaths", 0),
            "headshots": hs,
            "hs_pct": hs_pct,
            "adr": adr,
            "kast_pct": kast_pct,
            "opening_winrate": opening_winrate,
            "opening_won": op_won,
            "opening_lost": op_lost,
            "combat_score": combat_score,
            "total_rounds": rounds,
            "radar": {
                "aim": radar_aim,
                "survival": radar_survival,
                "utility": radar_utility,
                "economy": radar_economy,
                "positioning": radar_positioning
            },
            "hitbox_given": d["hitbox_given"],
            "hitbox_taken": d["hitbox_taken"],
            "weapon_kills": d["weapon_kills"],
            "round_history": d.get("round_history", [])[-12:]
        }


# Instancia singleton del motor de telemetría
telemetry_engine = TelemetryEngine()
