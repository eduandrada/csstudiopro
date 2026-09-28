# -*- coding: utf-8 -*-
"""
Módulo Compilador de Grafitis WAD3 (tempdecal.wad / pldecal.wad)
Ajuste a 11.200 px, cuantización con slot 255 azul transparente, mipmaps Miptex,
e inyección de atributo de sistema Solo Lectura (FILE_ATTRIBUTE_READONLY).
"""

import ctypes
import io
import math
import os
import struct
import sys
from PIL import Image
from core.backup_manager import backup_manager


def find_best_dimensions(orig_w, orig_h, max_pixels=11200):
    """Calcula las dimensiones óptimas (múltiplos de 16, <= 11200 px) conservando la proporción."""
    aspect = orig_w / orig_h
    best_w, best_h = 96, 96
    best_cost = float('inf')

    for i in range(1, 44):
        for j in range(1, 44):
            pw = i * 16
            ph = j * 16
            area = pw * ph
            if area > max_pixels:
                continue

            ratio = pw / ph
            ratio_diff = abs(ratio - aspect) / aspect
            area_penalty = (max_pixels - area) / max_pixels
            cost = ratio_diff * 4.0 + area_penalty

            if cost < best_cost:
                best_cost = cost
                best_w, best_h = pw, ph

    return best_w, best_h


def process_spray_image(
    image_stream,
    alpha_mode='alpha',
    color_tolerance=30,
    alpha_threshold=128,
    custom_color='#000000',
    target_w=None,
    target_h=None,
    dither=False
):
    """Procesa y cuantiza la imagen a 256 colores dejando el slot 255 para transparencia."""
    img = Image.open(image_stream).convert("RGBA")
    w, h = img.size

    if not target_w or not target_h:
        target_w, target_h = find_best_dimensions(w, h, max_pixels=11200)
    else:
        target_w = max(16, (int(target_w) // 16) * 16)
        target_h = max(16, (int(target_h) // 16) * 16)
        while (target_w * target_h) > 11200:
            if target_w >= target_h and target_w > 16:
                target_w -= 16
            elif target_h > 16:
                target_h -= 16
            else:
                break

    resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    r, g, b, a = resized.split()
    r_bytes = list(r.tobytes())
    g_bytes = list(g.tobytes())
    b_bytes = list(b.tobytes())
    a_bytes = list(a.tobytes())

    tol_ratio = float(color_tolerance) / 100.0

    if alpha_mode == 'white':
        threshold = int(255 * (1.0 - tol_ratio))
        for i in range(len(a_bytes)):
            if r_bytes[i] >= threshold and g_bytes[i] >= threshold and b_bytes[i] >= threshold:
                a_bytes[i] = 0
            else:
                a_bytes[i] = 255
    elif alpha_mode == 'black':
        threshold = int(255 * tol_ratio)
        for i in range(len(a_bytes)):
            if r_bytes[i] <= threshold and g_bytes[i] <= threshold and b_bytes[i] <= threshold:
                a_bytes[i] = 0
            else:
                a_bytes[i] = 255
    elif alpha_mode == 'custom':
        custom_hex = custom_color.lstrip('#')
        if len(custom_hex) == 6:
            kr = int(custom_hex[0:2], 16)
            kg = int(custom_hex[2:4], 16)
            kb = int(custom_hex[4:6], 16)
        else:
            kr, kg, kb = 0, 0, 0
        max_dist = 441.67 * tol_ratio
        for i in range(len(a_bytes)):
            dist = math.sqrt((r_bytes[i] - kr) ** 2 + (g_bytes[i] - kg) ** 2 + (b_bytes[i] - kb) ** 2)
            if dist <= max_dist:
                a_bytes[i] = 0
            else:
                a_bytes[i] = 255
    elif alpha_mode == 'none':
        a_bytes = [255] * len(a_bytes)

    rgb_img = Image.merge("RGB", (r, g, b))
    dither_flag = Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE
    quantized = rgb_img.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=dither_flag)

    raw_palette = list(quantized.getpalette() or [])
    if len(raw_palette) < 765:
        raw_palette.extend([0] * (765 - len(raw_palette)))
    else:
        raw_palette = raw_palette[:765]

    # Slot 255: Azul transparente GoldSrc
    palette = raw_palette + [0, 0, 255]

    pixels = bytearray(quantized.tobytes())
    for i in range(len(pixels)):
        if a_bytes[i] < int(alpha_threshold):
            pixels[i] = 255
        elif pixels[i] == 255:
            pixels[i] = 254

    return pixels, palette, target_w, target_h


def compile_wad3(pixels, palette, target_w, target_h, lump_type=0x40):
    """Compila el archivo WAD3 binario conforme a la especificación de Half-Life / GoldSrc."""
    mip0 = bytes(pixels)
    p_img = Image.frombytes("P", (target_w, target_h), mip0)
    p_img.putpalette(palette)

    mip1 = p_img.resize((target_w // 2, target_h // 2), Image.Resampling.NEAREST).tobytes()
    mip2 = p_img.resize((target_w // 4, target_h // 4), Image.Resampling.NEAREST).tobytes()
    mip3 = p_img.resize((target_w // 8, target_h // 8), Image.Resampling.NEAREST).tobytes()

    texture_name = b"{LOGO\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    offset0 = 40
    offset1 = offset0 + len(mip0)
    offset2 = offset1 + len(mip1)
    offset3 = offset2 + len(mip2)

    miptex_header = struct.pack(
        "<16sIIIIII",
        texture_name,
        target_w,
        target_h,
        offset0,
        offset1,
        offset2,
        offset3
    )

    palette_data = struct.pack("<H", 256) + bytes(palette) + b"\x00\x00"
    lump_data = miptex_header + mip0 + mip1 + mip2 + mip3 + palette_data

    wad_header = struct.pack("<4sII", b"WAD3", 1, 12 + len(lump_data))
    lump_info = struct.pack(
        "<IIIBBH16s",
        12,
        len(lump_data),
        len(lump_data),
        int(lump_type),
        0,
        0,
        texture_name
    )

    out = io.BytesIO()
    out.write(wad_header)
    out.write(lump_data)
    out.write(lump_info)
    out.seek(0)
    return out.getvalue()


def set_windows_readonly(filepath):
    """Aplica el atributo de Solo Lectura en Windows para proteger el archivo."""
    if sys.platform == "win32":
        try:
            FILE_ATTRIBUTE_READONLY = 0x01
            ctypes.windll.kernel32.SetFileAttributesW(filepath, FILE_ATTRIBUTE_READONLY)
            return True
        except Exception:
            pass
    try:
        import stat
        os.chmod(filepath, stat.S_IREAD)
        return True
    except Exception:
        return False


def remove_windows_readonly(filepath):
    """Remueve el atributo de Solo Lectura si se necesita sobreescribir."""
    if sys.platform == "win32":
        try:
            FILE_ATTRIBUTE_NORMAL = 0x80
            ctypes.windll.kernel32.SetFileAttributesW(filepath, FILE_ATTRIBUTE_NORMAL)
            return True
        except Exception:
            pass
    try:
        import stat
        os.chmod(filepath, stat.S_IWRITE | stat.S_IREAD)
        return True
    except Exception:
        return False


def install_spray_to_cstrike(cstrike_path, wad_bytes):
    """
    Instala directamente en tempdecal.wad y pldecal.wad dentro de cstrike/
    creando snapshots y marcando ambos como Solo Lectura.
    """
    targets = ["tempdecal.wad", "pldecal.wad"]
    installed = []

    for rel_target in targets:
        full_path = os.path.join(cstrike_path, rel_target)
        # Snapshot previo
        backup_manager.backup_file(cstrike_path, rel_target, action_desc="Instalación de Spray WAD3")

        # Quitar solo lectura previo si existía para poder escribir
        if os.path.exists(full_path):
            remove_windows_readonly(full_path)

        with open(full_path, "wb") as f:
            f.write(wad_bytes)

        # Aplicar Solo Lectura
        set_windows_readonly(full_path)
        installed.append(full_path)

    return installed
