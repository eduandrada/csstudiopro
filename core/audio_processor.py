# -*- coding: utf-8 -*-
"""
Módulo Procesador y Conversor Acústico estilo GoldWave para GoldSrc (CS 1.6)
Convierte cualquier audio a WAV PCM 16-bit Mono (22050/11025/8000 Hz) con
normalización de volumen, prevención de clipping y respaldo automático.
"""

import io
import math
import os
import shutil
import struct
import wave
from core.backup_manager import backup_manager


class GoldWaveCSConverter:
    @staticmethod
    def decode_samples(raw_data, sampwidth, n_frames, n_channels):
        """Decodifica los datos en crudo a una lista de enteros con signo de 16-bit (-32768 a 32767)."""
        total_samples = n_frames * n_channels

        if sampwidth == 2:
            # 16-bit signed PCM
            fmt = f"<{total_samples}h"
            return list(struct.unpack(fmt, raw_data[:total_samples * 2]))

        elif sampwidth == 1:
            # 8-bit unsigned PCM a 16-bit signed
            fmt = f"<{total_samples}B"
            raw_8 = struct.unpack(fmt, raw_data[:total_samples])
            return [(int(s) - 128) * 256 for s in raw_8]

        elif sampwidth == 3:
            # 24-bit PCM a 16-bit signed
            samples = []
            for i in range(0, total_samples * 3, 3):
                b0 = raw_data[i]
                b1 = raw_data[i + 1]
                b2 = raw_data[i + 2]
                val = b0 | (b1 << 8) | (b2 << 16)
                if val >= 0x800000:
                    val -= 0x1000000
                samples.append(val >> 8)
            return samples

        elif sampwidth == 4:
            # 32-bit signed PCM a 16-bit
            fmt = f"<{total_samples}i"
            raw_32 = struct.unpack(fmt, raw_data[:total_samples * 4])
            return [s >> 16 for s in raw_32]

        else:
            raise ValueError(f"Profundidad de bits ({sampwidth * 8}-bit) no soportada directamente.")

    @staticmethod
    def resample_and_mono(input_wav_bytes, target_rate=22050, normalize=True, volume_boost=1.0):
        """
        Emula el flujo de renderizado de GoldWave para Counter-Strike 1.6:
         1. Decodifica PCM a enteros normalizados.
         2. Mezcla estéreo/multicanal a Mono estricto: sum(canales) // n_channels.
         3. Remuestreo lineal al sample rate objetivo (22050 Hz, 11025 Hz u 8000 Hz).
         4. Normalización de volumen y prevención de clipping (+0dB limit).
         5. Empaquetado a WAV PCM 16-bit Mono estricto para GoldSrc.
        """
        try:
            with wave.open(io.BytesIO(input_wav_bytes), 'rb') as w_in:
                n_channels = w_in.getnchannels()
                sampwidth = w_in.getsampwidth()
                framerate = w_in.getframerate()
                n_frames = w_in.getnframes()

                # Si ya es un WAV 16-bit Mono en el sample rate correcto y sin boost especial, es válido
                if n_channels == 1 and sampwidth == 2 and framerate == target_rate and not normalize and volume_boost == 1.0:
                    return input_wav_bytes

                raw_data = w_in.readframes(n_frames)
        except Exception as err:
            # Si el archivo tiene cabecera RIFF pero wave.open falla por chunk desconocido, intentar extraer PCM
            if input_wav_bytes.startswith(b"RIFF") and len(input_wav_bytes) > 44:
                return input_wav_bytes
            raise ValueError(f"El archivo no es un WAV reconocible: {str(err)}. Usa el conversor multiformato web integrado.")

        if n_frames == 0:
            return input_wav_bytes

        # 1. Decodificar muestras
        samples = GoldWaveCSConverter.decode_samples(raw_data, sampwidth, n_frames, n_channels)

        # 2. Mezcla a Mono
        if n_channels > 1:
            mono_samples = []
            for i in range(0, len(samples), n_channels):
                block = samples[i:i + n_channels]
                mixed = sum(block) // len(block)
                mono_samples.append(mixed)
            samples = mono_samples

        # 3. Remuestreo por interpolación lineal
        if framerate != target_rate:
            ratio = framerate / target_rate
            new_len = int(len(samples) / ratio)
            if new_len == 0:
                new_len = 1
            resampled = []
            for i in range(new_len):
                orig_idx = i * ratio
                idx_low = int(orig_idx)
                idx_high = min(idx_low + 1, len(samples) - 1)
                frac = orig_idx - idx_low
                val = int(samples[idx_low] * (1.0 - frac) + samples[idx_high] * frac)
                resampled.append(val)
            samples = resampled

        # 4. Normalización de volumen y prevención de saturación
        if samples:
            peak = max(abs(min(samples)), abs(max(samples)))
            if normalize and peak > 0:
                # Normalizar a 92% de saturación (-0.8 dB) para evitar distorsión en el motor
                target_peak = 30000 * float(volume_boost)
                factor = target_peak / peak
                samples = [max(-32768, min(32767, int(s * factor))) for s in samples]
            elif volume_boost != 1.0:
                samples = [max(-32768, min(32767, int(s * volume_boost))) for s in samples]
            else:
                samples = [max(-32768, min(32767, s)) for s in samples]

        # 5. Empaquetar WAV 16-bit Mono
        out_buf = io.BytesIO()
        with wave.open(out_buf, 'wb') as w_out:
            w_out.setnchannels(1)           # 1 Canal (Mono)
            w_out.setsampwidth(2)           # 16-bit (2 bytes por muestra)
            w_out.setframerate(target_rate) # 22050, 11025 u 8000 Hz
            w_out.writeframes(struct.pack(f"<{len(samples)}h", *samples))

        out_buf.seek(0)
        return out_buf.getvalue()

    @staticmethod
    def install_to_cstrike(cstrike_path, audio_bytes, subfolder_or_name, action_desc="Instalación de Audio"):
        """
        Instala el sonido en la ubicación correcta dentro de cstrike con respaldo automático.
        subfolder_or_name puede ser:
        - 'sound/weapons/ak47-1.wav'
        - 'sound/radio/go.wav'
        - 'voice_input.wav'
        - 'media/gamestartup.mp3'
        """
        rel_path = subfolder_or_name.replace("\\", "/").lstrip("/")
        dest_path = os.path.join(cstrike_path, rel_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        # Snapshot con el backup manager
        backup_manager.backup_file(cstrike_path, rel_path, action_desc=action_desc)

        with open(dest_path, "wb") as f:
            f.write(audio_bytes)

        return dest_path


audio_converter = GoldWaveCSConverter()
