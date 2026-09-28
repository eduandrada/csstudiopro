"""
CS 1.6 SYSTEM & LATENCY BOOSTER (GOLDRSC ENGINE)
Daemon en segundo plano y lanzador de alto rendimiento para Counter-Strike 1.6.
Consumo < 15 MB de RAM y 0% CPU en reposo.

Tareas:
1. Sincronización del Timer de Windows a 1.0 ms (1000 Hz) con winmm.timeBeginPeriod(1).
2. Purga de Memoria RAM (Working Set Trim) al detectar el juego.
3. Prioridad ALTA (HIGH_PRIORITY_CLASS) y Aislamiento de Cores 1, 2 y 3 (Afinidad 0x0E).
4. Parámetros de lanzamiento de hardware acelerado (-nomaster -noipx -high -gl -novid -nojoy).
"""

import os
import sys
from core.system_booster import CSBooster, booster_instance

if __name__ == "__main__":
    # Obtener directorio cstrike configurado si existe
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cstrike_detected = booster_instance.detect_cstrike_dir() or r"C:\Program Files (x86)\Steam\steamapps\common\Half-Life\cstrike"

    booster = CSBooster(cstrike_detected, refresh_rate=144, width=1024, height=768)

    if len(sys.argv) > 1 and sys.argv[1] == "--launch":
        booster.launch_game()
        booster.run_daemon()
    else:
        booster.run_daemon()
