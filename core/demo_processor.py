#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
CS 1.6 STUDIO PRO - PROCESADOR Y RENDERIZADOR DE DEMOS (.DEM A .MP4)
=============================================================================
Un archivo .dem de Counter-Strike 1.6 es un registro de paquetes de red y
coordenadas del motor GoldSrc. Este módulo implementa el pipeline estándar
para convertir partidas a video MP4 (H.264 + AAC) en 60 o 120 FPS sin tirones:
 1. Método 1: Renderizado por Fotogramas (startmovie + FFmpeg)
 2. Método 2: Asistente para cinemáticas con HLAE (Half-Life Advanced Effects)
 3. Método 3: Guía de captura directa en tiempo real con OBS Studio

Créditos del Proyecto: yuyito, Hidden /A/, KYAMI, vANS.
=============================================================================
"""

import os
import glob
import shutil
import subprocess
from typing import Dict, Any, List, Optional, Tuple


class DemoProcessor:
    """Motor de análisis, captura y renderizado de demos de GoldSrc a video MP4."""

    def __init__(self):
        self._custom_ffmpeg_path: Optional[str] = None

    def set_custom_ffmpeg_path(self, path: str):
        """Permite al usuario especificar una ruta personalizada a ffmpeg.exe."""
        if path and os.path.isfile(path):
            self._custom_ffmpeg_path = path

    def find_ffmpeg(self, custom_path: Optional[str] = None) -> Optional[str]:
        """
        Localiza el binario ejecutable de FFmpeg en el sistema (PATH, ubicaciones comunes o personalizada).
        """
        if custom_path and os.path.isfile(custom_path):
            return custom_path
        if self._custom_ffmpeg_path and os.path.isfile(self._custom_ffmpeg_path):
            return self._custom_ffmpeg_path

        # 1. Buscar en PATH del sistema
        which_ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
        if which_ffmpeg:
            return which_ffmpeg

        # 2. Rutas comunes en Windows
        candidate_paths = [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
            r"D:\ffmpeg\bin\ffmpeg.exe",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "ffmpeg.exe"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ffmpeg.exe")
        ]
        for p in candidate_paths:
            if os.path.isfile(p):
                return os.path.abspath(p)
        return None

    def get_ffmpeg_status(self) -> Dict[str, Any]:
        """Verifica la disponibilidad y versión de FFmpeg."""
        ffmpeg_bin = self.find_ffmpeg()
        if not ffmpeg_bin:
            return {
                "available": False,
                "path": None,
                "version": "No detectado. Instala FFmpeg o especifica su ruta.",
                "download_url": "https://ffmpeg.org/download.html"
            }

        try:
            res = subprocess.run([ffmpeg_bin, "-version"], capture_output=True, text=True, timeout=5)
            first_line = res.stdout.splitlines()[0] if res.stdout else "FFmpeg disponible"
            return {
                "available": True,
                "path": ffmpeg_bin,
                "version": first_line
            }
        except Exception as e:
            return {
                "available": True,
                "path": ffmpeg_bin,
                "version": f"FFmpeg detectado ({str(e)})"
            }

    def list_cstrike_demos(self, cstrike_path: str) -> List[Dict[str, Any]]:
        """Escanea y lista todas las demos (.dem) presentes en cstrike/."""
        demos = []
        if not cstrike_path or not os.path.isdir(cstrike_path):
            return demos

        pattern = os.path.join(cstrike_path, "*.dem")
        for filepath in glob.glob(pattern):
            try:
                stats = os.stat(filepath)
                size_mb = round(stats.st_size / (1024 * 1024), 2)
                import datetime
                mtime = datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M")
                demos.append({
                    "name": os.path.basename(filepath),
                    "path": filepath,
                    "size_mb": size_mb,
                    "modified": mtime
                })
            except Exception:
                continue

        # Ordenar por fecha de modificación descendente
        demos.sort(key=lambda d: d.get("modified", ""), reverse=True)
        return demos

    def scan_recorded_frames(self, cstrike_path: str, prefix: str = "clip") -> Dict[str, Any]:
        """
        Escanea fotogramas generados por startmovie (ej: clip0000.bmp y clip.wav).
        """
        if not cstrike_path or not os.path.isdir(cstrike_path):
            return {"found": False, "error": "Ruta de cstrike no válida."}

        bmp_pattern = os.path.join(cstrike_path, f"{prefix}*.bmp")
        wav_file = os.path.join(cstrike_path, f"{prefix}.wav")
        frames = sorted(glob.glob(bmp_pattern))

        if not frames:
            return {
                "found": False,
                "frames_count": 0,
                "has_audio": os.path.isfile(wav_file),
                "wav_file": wav_file if os.path.isfile(wav_file) else None,
                "total_size_mb": 0,
                "estimated_duration_60fps": 0.0,
                "estimated_duration_120fps": 0.0
            }

        total_bytes = sum(os.path.getsize(f) for f in frames if os.path.exists(f))
        has_audio = os.path.isfile(wav_file)
        if has_audio:
            total_bytes += os.path.getsize(wav_file)

        # Detectar patrón de dígitos (clip0001 vs clip00001)
        first_frame = os.path.basename(frames[0])
        digits_part = first_frame.replace(prefix, "").replace(".bmp", "")
        num_digits = len(digits_part) if digits_part.isdigit() else 4

        return {
            "found": True,
            "prefix": prefix,
            "frames_count": len(frames),
            "first_frame": os.path.basename(frames[0]),
            "last_frame": os.path.basename(frames[-1]),
            "num_digits": num_digits,
            "has_audio": has_audio,
            "wav_file": wav_file if has_audio else None,
            "total_size_mb": round(total_bytes / (1024 * 1024), 2),
            "estimated_duration_60fps": round(len(frames) / 60.0, 2),
            "estimated_duration_120fps": round(len(frames) / 120.0, 2)
        }

    def compile_demo_to_mp4(
        self,
        cstrike_path: str,
        prefix: str = "clip",
        fps: int = 60,
        crf: int = 18,
        preset: str = "slow",
        output_name: str = "jugada.mp4",
        cleanup_bmps: bool = True,
        custom_ffmpeg: Optional[str] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Compila los fotogramas y audio volcados por startmovie en un archivo MP4 con FFmpeg.
        """
        ffmpeg_bin = self.find_ffmpeg(custom_ffmpeg)
        if not ffmpeg_bin:
            return False, {
                "error": "FFmpeg no encontrado. Por favor, instala FFmpeg o especifica su ruta en la configuración."
            }

        scan = self.scan_recorded_frames(cstrike_path, prefix)
        if not scan.get("found"):
            return False, {
                "error": f"No se encontraron fotogramas con el prefijo '{prefix}' en {cstrike_path}."
            }

        num_digits = scan.get("num_digits", 4)
        input_sequence = os.path.join(cstrike_path, f"{prefix}%0{num_digits}d.bmp")
        wav_file = os.path.join(cstrike_path, f"{prefix}.wav")

        if not output_name.lower().endswith(".mp4"):
            output_name += ".mp4"
        output_path = os.path.join(cstrike_path, output_name)

        cmd = [
            ffmpeg_bin,
            "-y",
            "-r", str(fps),
            "-i", input_sequence
        ]

        # Si el audio sincronizado clip.wav existe, agregarlo a la codificación
        has_audio = os.path.isfile(wav_file)
        if has_audio:
            cmd.extend([
                "-i", wav_file,
                "-c:a", "aac",
                "-b:a", "192k"
            ])

        # Parámetros de video H.264 universales
        cmd.extend([
            "-c:v", "libx264",
            "-preset", preset,
            "-crf", str(crf),
            "-pix_fmt", "yuv420p",
            output_path
        ])

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if proc.returncode != 0:
                return False, {
                    "error": f"Error al ejecutar FFmpeg: {proc.stderr[:300]}",
                    "cmd": " ".join(cmd)
                }

            # Limpieza opcional de fotogramas temporales para recuperar espacio en disco
            cleaned_count = 0
            if cleanup_bmps:
                bmp_pattern = os.path.join(cstrike_path, f"{prefix}*.bmp")
                for f in glob.glob(bmp_pattern):
                    try:
                        os.remove(f)
                        cleaned_count += 1
                    except OSError:
                        pass
                if has_audio and os.path.exists(wav_file):
                    try:
                        os.remove(wav_file)
                    except OSError:
                        pass

            output_size_mb = 0
            if os.path.isfile(output_path):
                output_size_mb = round(os.path.getsize(output_path) / (1024 * 1024), 2)

            return True, {
                "message": f"¡Video codificado con éxito a {fps} FPS!",
                "output_path": output_path,
                "output_name": output_name,
                "output_size_mb": output_size_mb,
                "frames_processed": scan.get("frames_count", 0),
                "duration_seconds": round(scan.get("frames_count", 0) / float(fps), 2),
                "cleaned_temp_files": cleaned_count,
                "has_audio": has_audio
            }

        except subprocess.TimeoutExpired:
            return False, {"error": "La codificación excedió el tiempo límite (10 min)."}
        except Exception as e:
            return False, {"error": f"Excepción durante la codificación: {str(e)}"}

    def cleanup_frames(self, cstrike_path: str, prefix: str = "clip") -> Dict[str, Any]:
        """Elimina manualmente fotogramas temporales BMP y audio WAV en cstrike/."""
        if not cstrike_path or not os.path.isdir(cstrike_path):
            return {"success": False, "error": "Ruta de cstrike inválida."}

        bmp_pattern = os.path.join(cstrike_path, f"{prefix}*.bmp")
        wav_file = os.path.join(cstrike_path, f"{prefix}.wav")
        removed_count = 0
        freed_bytes = 0

        for f in glob.glob(bmp_pattern):
            try:
                freed_bytes += os.path.getsize(f)
                os.remove(f)
                removed_count += 1
            except OSError:
                pass

        if os.path.isfile(wav_file):
            try:
                freed_bytes += os.path.getsize(wav_file)
                os.remove(wav_file)
                removed_count += 1
            except OSError:
                pass

        return {
            "success": True,
            "removed_files": removed_count,
            "freed_mb": round(freed_bytes / (1024 * 1024), 2)
        }

    def get_console_commands_guide(self, fps: int = 60, prefix: str = "clip") -> Dict[str, Any]:
        """
        Retorna los comandos listos para copiar y pegar en la consola de CS 1.6
        para iniciar el volcado de fotogramas a máxima calidad visual.
        """
        return {
            "fps": fps,
            "prefix": prefix,
            "setup_commands": [
                "hud_draw 0 // Oculta radar y vida para cinematica (o hud_draw 1 para conservarlo)",
                "crosshair 1 // Mantiene la mira visible",
                "r_detailtextures 1 // Texturas en maxima resolucion",
                "gl_texturemode GL_LINEAR_MIPMAP_LINEAR // Suavizado de texturas trilineal",
                f"bind F9 \"startmovie {prefix} {fps}\" // Inicia volcado fotograma a fotograma",
                "bind F10 \"endmovie\" // Detiene la grabacion"
            ],
            "hlae_commands": [
                f"mirv_movie_filename \"{prefix}\"",
                f"mirv_movie_fps {fps}",
                "mirv_movie_splitstreams 1 // Separa audio del juego, microfono, HUD y modelos con canal alfa"
            ],
            "obs_guide": [
                "1. En OBS Studio, agrega una fuente 'Captura de Juego' apuntando a 'hl.exe'.",
                "2. En CS 1.6, abre la consola y escribe: viewdemo minombre",
                "3. Presiona la barra espaciadora para ocultar los controles de reproduccion.",
                "4. Inicia la grabacion en OBS y reproduce la jugada a velocidad normal."
            ]
        }


# Instancia singleton
demo_processor = DemoProcessor()
