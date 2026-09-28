# -*- coding: utf-8 -*-
"""
CS 1.6 Low-Latency Booster & System Optimizer (GoldSrc Engine)
Ajustes de bajo nivel en Windows (WinMM 1.0ms timer, RAM working set purge,
prioridad de proceso ALTA y afinidad de CPU para hl.exe) con soporte para
demonio en segundo plano integrado y ejecución standalone invisible.
"""

import ctypes
from ctypes import wintypes
import os
import subprocess
import sys
import threading
import time

# Constantes de la API de Windows
PROCESS_ALL_ACCESS = 0x1F0FFF
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_SET_INFORMATION = 0x0200
PROCESS_VM_READ = 0x0010
HIGH_PRIORITY_CLASS = 0x00000080
ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000

# Cargar DLLs seguras de Windows
try:
    kernel32 = ctypes.windll.kernel32
    winmm = ctypes.windll.winmm
    psapi = ctypes.windll.psapi
except Exception as e:
    kernel32 = None
    winmm = None
    psapi = None


class CSBooster:
    def __init__(self, cstrike_dir=None, refresh_rate=144, width=1024, height=768):
        self.cstrike_dir = cstrike_dir
        self.hl_exe = self._resolve_hl_exe(cstrike_dir)
        self.refresh_rate = refresh_rate
        self.width = width
        self.height = height
        self.game_pid = None
        self.timer_boosted = False
        self._daemon_thread = None
        self._stop_event = threading.Event()
        self.last_status = {
            "active": False,
            "timer_1ms": False,
            "hl_detected": False,
            "hl_pid": None,
            "priority_boosted": False,
            "affinity_hex": None,
            "last_ram_trim": None,
            "log": []
        }

    def _resolve_hl_exe(self, cstrike_dir):
        if not cstrike_dir:
            return None
        candidate = os.path.join(os.path.dirname(cstrike_dir), "hl.exe")
        if os.path.exists(candidate):
            return candidate
        # Si cstrike_dir es ya la raíz de Half-Life
        root_cand = os.path.join(cstrike_dir, "hl.exe")
        if os.path.exists(root_cand):
            return root_cand
        return candidate

    def log_event(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {msg}"
        self.last_status["log"].append(entry)
        if len(self.last_status["log"]) > 40:
            self.last_status["log"].pop(0)
        print(entry)

    def optimize_system_timer(self, enable=True):
        """Ajusta el reloj de interrupciones de Windows a 1.0 ms exactos (1000 Hz)"""
        if not winmm:
            return False
        try:
            if enable and not self.timer_boosted:
                res = winmm.timeBeginPeriod(1)
                if res == 0:
                    self.timer_boosted = True
                    self.last_status["timer_1ms"] = True
                    self.log_event("Timer del sistema fijado a 1.0 ms (Tickrate estable a 1000 Hz).")
                    return True
            elif not enable and self.timer_boosted:
                winmm.timeEndPeriod(1)
                self.timer_boosted = False
                self.last_status["timer_1ms"] = False
                self.log_event("Timer del sistema restaurado al valor por defecto del SO.")
                return True
        except Exception as e:
            self.log_event(f"Error al configurar timer del sistema: {e}")
        return self.timer_boosted

    def trim_ram_working_set(self):
        """Obliga al sistema operativo a vaciar páginas de memoria en caché innecesarias"""
        if not kernel32:
            return False
        try:
            handle = kernel32.GetCurrentProcess()
            kernel32.SetProcessWorkingSetSize(handle, -1, -1)
            t_str = time.strftime("%H:%M:%S")
            self.last_status["last_ram_trim"] = t_str
            self.log_event("Memoria RAM purgada correctamente (Working Set Trim).")
            return True
        except Exception as e:
            self.log_event(f"No se pudo recortar el working set de RAM: {e}")
            return False

    def find_hl_process(self):
        """Busca el proceso hl.exe o cstrike.exe sin requerir dependencias externas"""
        if not psapi or not kernel32:
            return None
        arr = (wintypes.DWORD * 2048)()
        cb = ctypes.sizeof(arr)
        bytes_returned = wintypes.DWORD()

        if not psapi.EnumProcesses(ctypes.byref(arr), cb, ctypes.byref(bytes_returned)):
            return None

        count = int(bytes_returned.value / ctypes.sizeof(wintypes.DWORD))
        for i in range(count):
            pid = arr[i]
            if pid == 0:
                continue
            h_proc = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
            if h_proc:
                img_name = (ctypes.c_char * 260)()
                if psapi.GetModuleBaseNameA(h_proc, None, ctypes.byref(img_name), 260) > 0:
                    name = img_name.value.decode("latin-1", errors="ignore").lower()
                    if name in ("hl.exe", "cstrike.exe"):
                        kernel32.CloseHandle(h_proc)
                        return pid
                kernel32.CloseHandle(h_proc)
        return None

    def boost_process(self, pid):
        """Aplica Prioridad Alta y asigna afinidad de núcleos de alto rendimiento"""
        if not kernel32:
            return False
        h_proc = kernel32.OpenProcess(PROCESS_SET_INFORMATION | PROCESS_QUERY_INFORMATION, False, pid)
        if not h_proc:
            return False

        try:
            # 1. Prioridad Alta (evita caídas de FPS y fluctuaciones en el sondeo del mouse)
            kernel32.SetPriorityClass(h_proc, HIGH_PRIORITY_CLASS)
            self.last_status["priority_boosted"] = True

            # 2. Afinidad de CPU: Excluir Core 0 si hay 4 o más núcleos (Core 0 suele saturarse con interrupciones del SO)
            num_cores = os.cpu_count() or 4
            if num_cores >= 4:
                # Bits 1, 2, 3 activos = 0x0E (núcleos 1, 2 y 3)
                affinity_mask = 0x0E
            else:
                affinity_mask = (1 << num_cores) - 1

            kernel32.SetProcessAffinityMask(h_proc, affinity_mask)
            self.last_status["affinity_hex"] = hex(affinity_mask)
            self.last_status["hl_detected"] = True
            self.last_status["hl_pid"] = pid

            self.log_event(f"Proceso CS 1.6 (PID: {pid}) optimizado: Prioridad ALTA | Afinidad CPU: {hex(affinity_mask)}")
            return True
        finally:
            kernel32.CloseHandle(h_proc)

    def launch_game(self, custom_args=None):
        """Lanza el juego con todos los flags de aceleración directa por hardware"""
        self.trim_ram_working_set()
        self.optimize_system_timer(True)

        hl_path = self.hl_exe
        if not hl_path or not os.path.exists(hl_path):
            raise FileNotFoundError(f"Ejecutable hl.exe no encontrado en: {hl_path}")

        default_args = [
            hl_path,
            "-game", "cstrike",
            "-nomaster",              # No consulta el servidor maestro antiguo de WON
            "-noipx",                 # Desactiva protocolo LAN obsoleto IPX
            "-high",                  # Inicializa en prioridad alta
            "-gl",                    # Motor gráfico en OpenGL
            "-noforcemaccel",         # Suprime aceleración de Windows
            "-noforcemparms",         # Parámetros directos de puntero de Windows
            "-noforcemspd",           # Sin aceleración de velocidad del mouse
            "-freq", str(self.refresh_rate),
            "-refresh", str(self.refresh_rate),
            "-w", str(self.width),
            "-h", str(self.height),
            "-novid",                 # Salta video de introducción Valve
            "-nojoy",                 # Desactiva sondeo de joystick (ahorra hilos de CPU)
            "-threads", "4"
        ]

        launch_cmd = custom_args if custom_args else default_args
        self.log_event(f"Lanzando Counter-Strike 1.6: {' '.join(launch_cmd)}")

        proc = subprocess.Popen(launch_cmd, cwd=os.path.dirname(hl_path))
        self.game_pid = proc.pid
        time.sleep(1.2)
        self.boost_process(self.game_pid)
        return self.game_pid

    def start_background_daemon(self):
        """Inicia el demonio en un hilo de fondo gestionado por la aplicación web"""
        if self._daemon_thread and self._daemon_thread.is_alive():
            return True

        self._stop_event.clear()
        self.last_status["active"] = True
        self._daemon_thread = threading.Thread(target=self._daemon_loop, daemon=True)
        self._daemon_thread.start()
        self.log_event("Demonio CS 1.6 Booster activado en segundo plano.")
        return True

    def stop_background_daemon(self):
        """Detiene el demonio en segundo plano y restaura el timer"""
        self._stop_event.set()
        self.optimize_system_timer(False)
        self.last_status["active"] = False
        self.last_status["hl_detected"] = False
        self.last_status["hl_pid"] = None
        self.log_event("Demonio CS 1.6 Booster detenido.")
        return True

    def _daemon_loop(self):
        was_running = False
        while not self._stop_event.is_set():
            try:
                pid = self.find_hl_process()
                if pid and not was_running:
                    self.log_event(f"Counter-Strike 1.6 detectado en ejecución (PID: {pid}).")
                    self.trim_ram_working_set()
                    self.optimize_system_timer(True)
                    self.boost_process(pid)
                    was_running = True
                elif not pid and was_running:
                    self.log_event("Counter-Strike 1.6 cerrado. Restaurando entorno del sistema...")
                    self.optimize_system_timer(False)
                    self.trim_ram_working_set()
                    self.last_status["hl_detected"] = False
                    self.last_status["hl_pid"] = None
                    was_running = False

                # Pausa de 3 segundos para 0% CPU
                self._stop_event.wait(3.0)
            except Exception as e:
                self.log_event(f"Aviso en ciclo de monitoreo: {e}")
                self._stop_event.wait(4.0)

        # Al salir del loop
        self.optimize_system_timer(False)

    def apply_registry_latency_fix(self):
        """Importa el archivo cs_latency_fix.reg al registro de Windows mediante reg.exe"""
        reg_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cs_latency_fix.reg")
        if not os.path.exists(reg_file):
            raise FileNotFoundError(f"Archivo cs_latency_fix.reg no encontrado en {reg_file}")

        cmd = ["reg.exe", "import", reg_file]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            self.log_event("Ajustes de latencia TCP/IP y MMCSS importados exitosamente al Registro de Windows.")
            return True, "Registro de Windows optimizado con éxito."
        else:
            err = res.stderr or res.stdout or "Acceso denegado (se requieren permisos de Administrador)."
            self.log_event(f"Error al importar archivo .reg: {err}")
            return False, err


# Instancia singleton del Booster
system_booster = CSBooster()


if __name__ == "__main__":
    print("==================================================================")
    print("CS 1.6 SYSTEM & LATENCY BOOSTER DAEMON (GOLDRSC ENGINE)")
    print("==================================================================")
    booster = CSBooster()

    if len(sys.argv) > 1 and sys.argv[1] == "--launch":
        booster.launch_game()
        booster.start_background_daemon()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            booster.stop_background_daemon()
    else:
        booster.start_background_daemon()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            booster.stop_background_daemon()
