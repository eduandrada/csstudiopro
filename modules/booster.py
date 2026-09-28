#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
CSStudioPro - RUNTIME BOOSTER & OPTIMIZADOR EN TIEMPO REAL
=============================================================================
Implementa optimizaciones de bajo nivel para el motor GoldSrc (hl.exe):
 1. Watchdog en segundo plano con psutil y WinAPI ctypes.
 2. Afinidad de CPU inteligente: Descarte del Núcleo 0 (interrupciones DPC/ISR)
    y aislamiento de núcleos físicos reales (evitando hilos SMT/HyperThreading).
 3. Prioridad de proceso HIGH_PRIORITY_CLASS (0x00000080).
 4. Timer Resolution nativo a 0.5 ms / 1.0 ms con auto-rollback garantizado
    mediante atexit y administradores de contexto.
 5. Standby List / Memory Trimming para liberar memoria antes de jugar.
=============================================================================
"""

import os
import sys
import time
import atexit
import threading
import ctypes
from ctypes import wintypes
from typing import Dict, Any, Optional, List, Tuple

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from utils.logger import logger

# =============================================================================
# CONSTANTES WIN32 Y APIS NATIVAS
# =============================================================================
PROCESS_SET_INFORMATION = 0x0200
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_ALL_ACCESS = 0x1F0FFF
HIGH_PRIORITY_CLASS = 0x00000080
NORMAL_PRIORITY_CLASS = 0x00000020

# Funciones de ntdll / winmm / psapi
kernel32 = ctypes.windll.kernel32 if os.name == 'nt' else None
ntdll = ctypes.windll.ntdll if os.name == 'nt' else None
winmm = ctypes.windll.winmm if os.name == 'nt' else None
psapi = ctypes.windll.psapi if os.name == 'nt' else None


class WindowsTimerResolution:
    """
    Administrador de contexto y controlador seguro para Timer Resolution de Windows.
    Fuerza 0.5 ms (o 1.0 ms) y garantiza rollback automático a 15.6 ms al salir.
    """
    def __init__(self, target_ms: float = 0.5):
        self.target_ms = target_ms
        self.is_active = False
        self._using_ntdll = False
        self._using_winmm = False
        atexit.register(self.restore)

    def set_resolution(self, ms: float = 0.5) -> bool:
        """Establece la resolución de temporizador del kernel a 0.5 ms o 1.0 ms."""
        if os.name != 'nt':
            return False

        self.target_ms = ms
        # 1. Intentar ntdll.NtSetTimerResolution (Unidades de 100 ns: 0.5 ms = 5000)
        if ntdll and hasattr(ntdll, 'NtSetTimerResolution'):
            try:
                desired_100ns = int(ms * 10000)
                actual_res = wintypes.ULONG()
                status = ntdll.NtSetTimerResolution(desired_100ns, 1, ctypes.byref(actual_res))
                if status == 0:  # STATUS_SUCCESS
                    self.is_active = True
                    self._using_ntdll = True
                    logger.info(f"[TimerResolution] ntdll forzado a {ms:.2f} ms (actual: {actual_res.value / 10000.0:.2f} ms)")
                    return True
            except Exception as e:
                logger.warning(f"[TimerResolution] ntdll falló: {e}, probando winmm...")

        # 2. Fallback a winmm.timeBeginPeriod(1)
        if winmm and hasattr(winmm, 'timeBeginPeriod'):
            try:
                period = max(1, int(ms))
                if winmm.timeBeginPeriod(period) == 0:
                    self.is_active = True
                    self._using_winmm = True
                    logger.info(f"[TimerResolution] winmm forzado a {period} ms")
                    return True
            except Exception as e:
                logger.error(f"[TimerResolution] winmm falló: {e}")

        return False

    def restore(self):
        """Restaura el temporizador del kernel de Windows al valor estándar (15.6 ms)."""
        if not self.is_active or os.name != 'nt':
            return

        try:
            if self._using_ntdll and ntdll and hasattr(ntdll, 'NtSetTimerResolution'):
                actual_res = wintypes.ULONG()
                ntdll.NtSetTimerResolution(5000, 0, ctypes.byref(actual_res))
                logger.info("[TimerResolution] ntdll restaurado al valor por defecto.")

            if self._using_winmm and winmm and hasattr(winmm, 'timeEndPeriod'):
                winmm.timeEndPeriod(1)
                logger.info("[TimerResolution] winmm restaurado al valor por defecto.")
        except Exception as e:
            logger.error(f"[TimerResolution] Error durante la restauración: {e}")
        finally:
            self.is_active = False
            self._using_ntdll = False
            self._using_winmm = False

    def __enter__(self):
        self.set_resolution(self.target_ms)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore()


class RuntimeBooster:
    """
    Optimizador de rendimiento en tiempo real para Counter-Strike 1.6 / GoldSrc.
    Monitorea hl.exe, fija afinidad a núcleos físicos y eleva prioridad.
    """

    def __init__(self):
        self.timer_manager = WindowsTimerResolution(target_ms=0.5)
        self.monitoring = False
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.last_optimized_pid: Optional[int] = None
        self.target_core: int = 2  # Núcleo físico predeterminado (evitando Núcleo 0)

        # Detectar topología de núcleos CPU
        self.cpu_info = self._detect_cpu_topology()
        logger.info(f"[RuntimeBooster] Topología CPU detectada: {self.cpu_info}")

    def _detect_cpu_topology(self) -> Dict[str, Any]:
        """
        Detecta núcleos físicos vs lógicos para evitar el Núcleo 0 y el HyperThreading.
        """
        logical_count = os.cpu_count() or 4
        physical_count = logical_count
        if HAS_PSUTIL:
            try:
                physical_count = psutil.cpu_count(logical=False) or (logical_count // 2 or 1)
            except Exception:
                pass

        # Generar máscara para núcleos físicos (números pares si hay SMT/HT)
        is_smt = logical_count > physical_count
        physical_cores = []
        for i in range(physical_count):
            core_id = i * 2 if is_smt else i
            if core_id < logical_count:
                physical_cores.append(core_id)

        # Seleccionar núcleo objetivo preferente: Core 2 (o Core 1 si solo hay 2 núcleos)
        preferred_target = 2 if 2 in physical_cores else (physical_cores[1] if len(physical_cores) > 1 else 0)

        return {
            "logical_count": logical_count,
            "physical_count": physical_count,
            "is_smt": is_smt,
            "physical_cores": physical_cores,
            "recommended_core": preferred_target
        }

    def clean_standby_memory(self) -> Tuple[bool, str]:
        """
        Vacía el conjunto de trabajo (Working Set) y memoria en espera previa al juego.
        """
        if os.name != 'nt':
            return False, "Solo disponible en sistemas Windows."

        cleaned_mb = 0
        try:
            if psapi and hasattr(psapi, 'EmptyWorkingSet'):
                # Trim del propio proceso
                handle = kernel32.GetCurrentProcess()
                psapi.EmptyWorkingSet(handle)

            # Si psutil está instalado, intentar vaciar memoria de procesos en espera
            if HAS_PSUTIL:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        p_handle = kernel32.OpenProcess(0x1F0FFF, False, proc.pid)
                        if p_handle:
                            psapi.EmptyWorkingSet(p_handle)
                            kernel32.CloseHandle(p_handle)
                    except Exception:
                        continue

            logger.info("[MemoryCleaner] Conjuntos de trabajo en espera vaciados con éxito.")
            return True, "Memoria RAM optimizada y conjunto de trabajo depurado."
        except Exception as e:
            logger.warning(f"[MemoryCleaner] Limpieza parcial: {e}")
            return False, f"Aviso de permisos: {str(e)}"

    def apply_optimizations_to_pid(self, pid: int) -> Dict[str, Any]:
        """
        Aplica HIGH_PRIORITY_CLASS y afinidad a núcleo físico dedicado sobre el PID de hl.exe.
        """
        results = {"pid": pid, "priority_elevated": False, "affinity_set": False, "core_assigned": None}
        if os.name != 'nt':
            return results

        # 1. Establecer Timer a 0.5 ms
        self.timer_manager.set_resolution(0.5)

        # 2. Abrir proceso con permisos de modificación
        handle = kernel32.OpenProcess(PROCESS_SET_INFORMATION | PROCESS_QUERY_INFORMATION, False, pid)
        if not handle:
            # Reintentar con permisos generales
            handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)

        if not handle:
            logger.error(f"[RuntimeBooster] No se pudo obtener handle para el PID {pid}.")
            return results

        try:
            # 3. Elevar prioridad a HIGH_PRIORITY_CLASS
            if kernel32.SetPriorityClass(handle, HIGH_PRIORITY_CLASS):
                results["priority_elevated"] = True
                logger.info(f"[RuntimeBooster] PID {pid} elevado a HIGH_PRIORITY_CLASS.")

            # 4. Asignar afinidad: Descartar Núcleo 0 (DPC/ISR) y fijar al núcleo físico objetivo
            target = self.target_core
            if target not in self.cpu_info["physical_cores"]:
                target = self.cpu_info["recommended_core"]

            # Máscara de bits: 1 << target
            affinity_mask = 1 << target
            if kernel32.SetProcessAffinityMask(handle, affinity_mask):
                results["affinity_set"] = True
                results["core_assigned"] = target
                logger.info(f"[RuntimeBooster] Afinidad fijada en Núcleo Físico {target} (Máscara 0x{affinity_mask:X}).")

        finally:
            kernel32.CloseHandle(handle)

        self.last_optimized_pid = pid
        return results

    def find_hl_process(self) -> Optional[int]:
        """Localiza el PID de hl.exe o cstrike.exe si está en ejecución."""
        if HAS_PSUTIL:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    name = proc.info['name']
                    if name and name.lower() in ('hl.exe', 'cstrike.exe'):
                        return proc.info['pid']
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        return None

    def start_watchdog(self):
        """Inicia el hilo en segundo plano que monitorea activamente el lanzamiento de hl.exe."""
        if self.monitoring:
            return

        self.monitoring = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._watchdog_loop, daemon=True, name="HLWatchdogThread")
        self._thread.start()
        logger.info("[RuntimeBooster] Watchdog de hl.exe iniciado.")

    def stop_watchdog(self):
        """Detiene el hilo de monitoreo y restaura los temporizadores del sistema."""
        self.monitoring = False
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self.timer_manager.restore()
        logger.info("[RuntimeBooster] Watchdog de hl.exe detenido y temporizadores restaurados.")

    def _watchdog_loop(self):
        """Bucle continuo del hilo vigilante."""
        game_active = False

        while not self._stop_event.is_set():
            pid = self.find_hl_process()

            if pid and not game_active:
                # El juego acaba de iniciarse
                logger.info(f"[RuntimeBooster] hl.exe detectado en ejecución (PID {pid}). Aplicando optimizaciones...")
                self.apply_optimizations_to_pid(pid)
                game_active = True

            elif not pid and game_active:
                # El juego se acaba de cerrar
                logger.info("[RuntimeBooster] hl.exe cerrado. Restaurando Timer Resolution del sistema...")
                self.timer_manager.restore()
                self.last_optimized_pid = None
                game_active = False

            # Intervalo de verificación eficiente (cada 1.5s sin consumo de CPU)
            self._stop_event.wait(1.5)

    def get_status(self) -> Dict[str, Any]:
        """Retorna el estado en tiempo real del booster."""
        active_pid = self.find_hl_process()
        return {
            "monitoring": self.monitoring,
            "hl_running": bool(active_pid),
            "active_pid": active_pid,
            "timer_05ms_active": self.timer_manager.is_active,
            "target_core": self.target_core,
            "cpu_topology": self.cpu_info,
            "psutil_available": HAS_PSUTIL
        }


# Instancia singleton del runtime booster
runtime_booster = RuntimeBooster()
