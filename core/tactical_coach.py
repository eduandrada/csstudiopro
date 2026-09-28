# -*- coding: utf-8 -*-
"""
CS 1.6 AI Tactical Coach & Diagnosis Engine
Analiza las métricas y hábitos recopilados por TelemetryEngine, detecta fallas
tácticas críticas (spray excesivo, over-peeking, KAST bajo, falta de utilidad)
y prescribe rutinas de entrenamiento con scripts ejecutables .cfg para CS 1.6.
"""

import os
import time


class TacticalCoach:
    def __init__(self, cstrike_path=None):
        self.cstrike_path = cstrike_path

    def set_cstrike_path(self, path):
        self.cstrike_path = path

    def diagnose_session(self, metrics):
        """
        Ejecuta el motor de reglas heurísticas sobre las métricas competitivas
        para generar tarjetas de diagnóstico con lenguaje natural directo.
        """
        diagnoses = []
        kd = metrics.get("kd_ratio", 1.0)
        hs_pct = metrics.get("hs_pct", 0.0)
        adr = metrics.get("adr", 0.0)
        kast = metrics.get("kast_pct", 0.0)
        op_winrate = metrics.get("opening_winrate", 50.0)
        op_won = metrics.get("opening_won", 0)
        op_lost = metrics.get("opening_lost", 0)
        rounds = metrics.get("total_rounds", 0)
        radar = metrics.get("radar", {})
        hit_given = metrics.get("hitbox_given", {})
        hit_taken = metrics.get("hitbox_taken", {})

        # 1. Diagnóstico de Puntería y Control de Spray
        if hs_pct < 28.0 and rounds >= 3:
            diagnoses.append({
                "id": "spray_headshot_deficit",
                "severity": "critical",
                "title": "Sobre-Spray y Déficit de Disparos a la Cabeza",
                "badge": "Crítico (Aim)",
                "icon": "🎯",
                "what_happened": f"Tu porcentaje de Headshot es de solo {hs_pct}%. Estás descargando ráfagas continuas (>8 balas) al torso y piernas en lugar de calibrar el primer tiro a la cabeza.",
                "how_to_fix": "Practica el 'Tap Fire' (1 a 2 balas con AK-47) a larga distancia. En distancias medias, dispara ráfagas de 3 balas tirando suavemente el mouse hacia abajo para compensar el retroceso vertical.",
                "recommended_routine": "routine_onetap"
            })
        elif hs_pct >= 50.0:
            diagnoses.append({
                "id": "aim_elite",
                "severity": "positive",
                "title": "Precisión Quirúrgica de Nivel Profesional",
                "badge": "Excelente",
                "icon": "⭐",
                "what_happened": f"Excelente porcentaje de Headshots ({hs_pct}%). Tu crosshair placement está perfectamente alineado a la altura de la cabeza de los rivales.",
                "how_to_fix": "Mantén la memoria muscular con sesiones cortas de 10 minutos de calentamiento antes de jugar partidos competitivos.",
                "recommended_routine": "routine_warmup"
            })

        # 2. Diagnóstico de Apertura de Duelos (Opening Duels)
        if op_winrate < 42.0 and (op_won + op_lost) >= 2:
            diagnoses.append({
                "id": "overpeek_first_death",
                "severity": "critical",
                "title": "Sobre-extensión y Regalo de Primera Baja",
                "badge": "Crítico (Posición)",
                "icon": "⚠️",
                "what_happened": f"Has perdido el {round(100 - op_winrate, 1)}% de tus duelos iniciales ({op_lost} muertes tempranas). Estás asomándote (dry-peeking) sin apoyo de granadas ni info.",
                "how_to_fix": "Nunca asomes un ángulo abierto sin una flashbang de rebote. En bando CT, mantén ángulos defensivos cerrados ('off-angles') obligando al atacante a limpiar tu posición a ciegas.",
                "recommended_routine": "routine_prefire"
            })
        elif op_winrate >= 65.0 and (op_won + op_lost) >= 2:
            diagnoses.append({
                "id": "opening_master",
                "severity": "positive",
                "title": "Entry Fragger Implacable",
                "badge": "Excelente (Entry)",
                "icon": "⚡",
                "what_happened": f"Dominas el {op_winrate}% de los duelos de apertura, asegurando ventaja numérica (5v4) para tu equipo al inicio de ronda.",
                "how_to_fix": "Asegúrate de que un compañero avance detrás de ti para hacer re-frag inmediato si llegas a caer.",
                "recommended_routine": "routine_warmup"
            })

        # 3. Diagnóstico de KAST y Trade-Fragging
        if kast < 62.0 and rounds >= 3:
            diagnoses.append({
                "id": "low_kast_isolation",
                "severity": "warning",
                "title": "Aislamiento Táctico y Falta de Re-Frag (KAST Bajo)",
                "badge": "Advertencia (Teamplay)",
                "icon": "🛡️",
                "what_happened": f"Tu KAST es del {kast}%. En más del 38% de las rondas mueres sin haber asistido, sin matar a nadie y en zonas donde ningún compañero puede vengar tu baja (trade kill).",
                "how_to_fix": "Juega emparejado con un compañero ('buddy system'). Si juegas en pareja a menos de 5 metros de distancia, cualquier rival que te elimine morirá inmediatamente por el disparo de tu compañero.",
                "recommended_routine": "routine_spray"
            })

        # 4. Diagnóstico de Daño y ADR
        if adr < 65.0 and rounds >= 3:
            diagnoses.append({
                "id": "low_adr_impact",
                "severity": "warning",
                "title": "Bajo Impacto en Rondas (ADR Insuficiente)",
                "badge": "Advertencia (Impacto)",
                "icon": "💥",
                "what_happened": f"Tu ADR es de {adr} de daño por ronda. Estás rotando demasiado tarde o manteniéndote demasiado pasivo mientras tus compañeros son eliminados.",
                "how_to_fix": "Aprende los tiempos de llegada (timings) de cada mapa. Cuando escuches contacto en el otro bombsite, rota proactivamente con cuchillo en mano hasta zona segura.",
                "recommended_routine": "routine_spray"
            })

        # 5. Diagnóstico de Utilidad y Granadas
        if radar.get("utility", 50) < 35:
            diagnoses.append({
                "id": "underutilized_nades",
                "severity": "warning",
                "title": "Desperdicio de Utilidad (Pocas Granadas)",
                "badge": "Mejora Sugerida",
                "icon": "💣",
                "what_happened": "Rara vez compras o arrojas granadas HE y Flashbangs. Entras a duelos de rifles al descubierto sin cegar antes el ángulo enemigo.",
                "how_to_fix": "Asigna un bind rápido en el Numpad para 'Full Nades' (hegren; flash; flash; sgren). Arroja una HE a los pasillos comunes (Banana en Inferno, Larga en Dust2) a los 3 segundos de empezar la ronda.",
                "recommended_routine": "routine_prefire"
            })

        # Si todo está en equilibrio positivo o pocas rondas
        if not diagnoses:
            diagnoses.append({
                "id": "session_balanced",
                "severity": "positive",
                "title": "Juego Sólido y Rendimiento Estable",
                "badge": "Rendimiento Bueno",
                "icon": "✅",
                "what_happened": f"Estadísticas consistentes: K/D de {kd}, ADR de {adr} y {kast}% de KAST. Mantienes buena disciplina táctica.",
                "how_to_fix": "Sigue practicando prefire en tus mapas más débiles para mejorar aún más tu ratio de duelos de apertura.",
                "recommended_routine": "routine_warmup"
            })

        return diagnoses

    def get_practice_routines(self):
        """Devuelve el catálogo de rutinas de entrenamiento táctico profesional"""
        return [
            {
                "id": "routine_onetap",
                "title": "Rutina 1: One-Tap y Reacción con AK-47 / Deagle",
                "focus": "Puntería pura, Crosshair Placement y Micro-ajustes",
                "duration": "15 minutos",
                "description": "Configura un servidor local con bots inmóviles para calibrar la mira exactamente a la altura de la cabeza, obligando a disparos limpios de una sola bala.",
                "cfg_name": "practice_onetap.cfg",
                "commands": [
                    "sv_cheats 1",
                    "bot_stop 1",
                    "mp_roundtime 60",
                    "mp_freezetime 0",
                    "mp_startmoney 16000",
                    "sv_restart 1",
                    "give weapon_ak47",
                    "give weapon_deagle",
                    "echo [AI Coach] Rutina de One-Tap cargada con exito"
                ]
            },
            {
                "id": "routine_spray",
                "title": "Rutina 2: Spray Transfer y Control de Retroceso Vertical",
                "focus": "Control de ráfagas de 5 a 10 balas y cambio de blanco rápido",
                "duration": "15 minutos",
                "description": "Entrenamiento contra paredes y siluetas para memorizar el patrón en 'T invertida' del retroceso del AK-47 y M4A1 a distintas distancias.",
                "cfg_name": "practice_spray.cfg",
                "commands": [
                    "sv_cheats 1",
                    "mp_roundtime 60",
                    "mp_freezetime 0",
                    "r_decals 1000",
                    "sv_restart 1",
                    "echo [AI Coach] Rutina de Spray Control cargada. Practica a 10m y 25m de distancia"
                ]
            },
            {
                "id": "routine_prefire",
                "title": "Rutina 3: Prefire, Peek Táctico y Limpieza de Ángulos",
                "focus": "Movimiento, Counter-Strafing y apertura con Flashbang",
                "duration": "20 minutos",
                "description": "Enfocado en detenerse por completo (contra-strafeando en sentido opuesto con A/D) antes de disparar al doblar esquinas críticas.",
                "cfg_name": "practice_prefire.cfg",
                "commands": [
                    "sv_cheats 1",
                    "mp_roundtime 60",
                    "mp_freezetime 0",
                    "mp_startmoney 16000",
                    "sv_restart 1",
                    "echo [AI Coach] Rutina de Prefire iniciada. Recuerda soltar D y presionar A antes de disparar"
                ]
            },
            {
                "id": "routine_warmup",
                "title": "Rutina 4: Calentamiento Rápido Competitivo (Esports Warmup)",
                "focus": "Movilidad global, sonido y sincronización motriz",
                "duration": "10 minutos",
                "description": "Rutina rápida para antes de ingresar a servidores de torneo o partidas de liga.",
                "cfg_name": "practice_warmup.cfg",
                "commands": [
                    "rate 100000",
                    "cl_updaterate 102",
                    "cl_cmdrate 105",
                    "ex_interp 0.0098",
                    "fps_max 99.5",
                    "echo [AI Coach] Calentamiento listo. Sal a la arena con confianza"
                ]
            }
        ]

    def install_routine_cfg(self, routine_id):
        """Crea el archivo .cfg de práctica en la carpeta cstrike/ activa del usuario"""
        if not self.cstrike_path or not os.path.exists(self.cstrike_path):
            raise FileNotFoundError("Ruta de cstrike/ no conectada.")

        routines = self.get_practice_routines()
        routine = next((r for r in routines if r["id"] == routine_id), None)
        if not routine:
            raise ValueError(f"Rutina con ID '{routine_id}' no encontrada.")

        cfg_filename = routine["cfg_name"]
        target_path = os.path.join(self.cstrike_path, cfg_filename)

        lines = [
            f"// ==============================================================================",
            f"// CS 1.6 TACTICAL AI COACH - {routine['title'].upper()}",
            f"// Enfoque: {routine['focus']}",
            f"// Ejecutar en consola con: exec {cfg_filename}",
            f"// ==============================================================================",
            ""
        ] + routine["commands"] + [""]

        with open(target_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return target_path, cfg_filename


# Instancia singleton del Coach
tactical_coach = TacticalCoach()
