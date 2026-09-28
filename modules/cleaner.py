#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
CSStudioPro - ASSETS & CACHE CLEANER CON WHITELIST VANILLA ESTRICTA
=============================================================================
Depura de forma segura y selectiva los gigabytes de archivos acumulados por
servidores comunitarios (descargas automáticas, sprays de terceros, etc.):
 1. Whitelist Vanilla estricta para proteger mapas, texturas y modelos originales.
 2. Depuración de custom.hpk (caché de grafitis de servidores que satura el juego).
 3. Limpieza de cstrike/download/ (modelos, sonidos y mapas huérfanos).
 4. Reporte detallado de espacio en disco liberado antes y después.
=============================================================================
"""

import os
import glob
from typing import Dict, Any, List, Set, Tuple

from utils.logger import logger

class AssetsCleaner:
    """Motor de análisis y depuración de caché y descargas de servidores."""

    # LISTA BLANCA ESTRICTA DE ARCHIVOS VANILLA NATIVOS DE VALVE / CS 1.6
    VANILLA_MAPS: Set[str] = {
        "as_oilrig.bsp", "cs_747.bsp", "cs_assault.bsp", "cs_backalley.bsp",
        "cs_estate.bsp", "cs_havana.bsp", "cs_italy.bsp", "cs_militia.bsp",
        "cs_office.bsp", "cs_siege.bsp", "de_airstrip.bsp", "de_aztec.bsp",
        "de_cbble.bsp", "de_chateau.bsp", "de_dust.bsp", "de_dust2.bsp",
        "de_inferno.bsp", "de_nuke.bsp", "de_piranesi.bsp", "de_prodigy.bsp",
        "de_storm.bsp", "de_survivor.bsp", "de_torn.bsp", "de_train.bsp",
        "de_vertigo.bsp"
    }

    VANILLA_WADS: Set[str] = {
        "cstrike.wad", "halflife.wad", "decals.wad", "fonts.wad", "gfx.wad",
        "liquids.wad", "cached.wad", "chache.wad", "tswad.wad"
    }

    VANILLA_PLAYER_MODELS: Set[str] = {
        "arctic", "gign", "gsg9", "guerilla", "leet", "sas", "terror", "urban", "vip"
    }

    VANILLA_ROOT_MODELS: Set[str] = {
        "backpack.mdl", "chick.mdl", "feather.mdl", "hostage.mdl", "player.mdl",
        "rpgrocket.mdl", "scientist.mdl", "shield.mdl", "w_antidote.mdl",
        "w_battery.mdl", "w_c4.mdl", "w_isotopebox.mdl", "w_longjump.mdl",
        "w_medkit.mdl", "w_oxygen.mdl", "w_rad.mdl", "w_security.mdl",
        "w_suit.mdl", "w_weaponbox.mdl"
    }

    def __init__(self):
        pass

    def scan_cstrike_cache(self, cstrike_path: str) -> Dict[str, Any]:
        """
        Escanea la carpeta cstrike/ en busca de descargas y cachés de servidores,
        clasificándolos por categoría y respetando la lista blanca vanilla.
        """
        results = {
            "cstrike_path": cstrike_path,
            "custom_hpk": {"found": False, "size_mb": 0.0, "path": None},
            "downloads_folder": {"files_count": 0, "size_mb": 0.0, "files": []},
            "custom_maps": {"files_count": 0, "size_mb": 0.0, "files": []},
            "custom_models": {"files_count": 0, "size_mb": 0.0, "files": []},
            "custom_sounds": {"files_count": 0, "size_mb": 0.0, "files": []},
            "total_cleanable_mb": 0.0,
            "total_cleanable_files": 0
        }

        if not cstrike_path or not os.path.isdir(cstrike_path):
            return results

        total_bytes = 0
        total_files = 0

        # 1. Analizar custom.hpk (caché acumulada de sprays)
        hpk_path = os.path.join(cstrike_path, "custom.hpk")
        if os.path.isfile(hpk_path):
            sz = os.path.getsize(hpk_path)
            sz_mb = round(sz / (1024 * 1024), 2)
            results["custom_hpk"] = {
                "found": True,
                "size_mb": sz_mb,
                "path": hpk_path
            }
            total_bytes += sz
            total_files += 1

        # 2. Analizar cstrike/download/ (descargas directas de servidores)
        download_dir = os.path.join(cstrike_path, "download")
        if os.path.isdir(download_dir):
            dl_bytes = 0
            dl_files = []
            for root, _, files in os.walk(download_dir):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        fsz = os.path.getsize(fp)
                        dl_bytes += fsz
                        dl_files.append({
                            "name": f,
                            "path": fp,
                            "rel_path": os.path.relpath(fp, cstrike_path),
                            "size_kb": round(fsz / 1024, 1)
                        })
                    except Exception:
                        pass
            results["downloads_folder"] = {
                "files_count": len(dl_files),
                "size_mb": round(dl_bytes / (1024 * 1024), 2),
                "files": dl_files[:100]  # Limitar vista previa a 100 archivos
            }
            total_bytes += dl_bytes
            total_files += len(dl_files)

        # 3. Analizar mapas (.bsp) no oficiales en cstrike/maps/
        maps_dir = os.path.join(cstrike_path, "maps")
        if os.path.isdir(maps_dir):
            map_bytes = 0
            custom_maps = []
            for f in os.listdir(maps_dir):
                f_lower = f.lower()
                if f_lower.endswith(".bsp") and f_lower not in self.VANILLA_MAPS:
                    fp = os.path.join(maps_dir, f)
                    try:
                        fsz = os.path.getsize(fp)
                        map_bytes += fsz
                        custom_maps.append({
                            "name": f,
                            "path": fp,
                            "size_mb": round(fsz / (1024 * 1024), 2)
                        })
                    except Exception:
                        pass
            results["custom_maps"] = {
                "files_count": len(custom_maps),
                "size_mb": round(map_bytes / (1024 * 1024), 2),
                "files": custom_maps
            }
            total_bytes += map_bytes
            total_files += len(custom_maps)

        # 4. Analizar modelos personalizados de jugador en cstrike/models/player/
        player_models_dir = os.path.join(cstrike_path, "models", "player")
        if os.path.isdir(player_models_dir):
            m_bytes = 0
            custom_models = []
            for folder in os.listdir(player_models_dir):
                if folder.lower() not in self.VANILLA_PLAYER_MODELS:
                    full_p = os.path.join(player_models_dir, folder)
                    if os.path.isdir(full_p):
                        folder_sz = sum(os.path.getsize(os.path.join(full_p, x)) for x in os.listdir(full_p) if os.path.isfile(os.path.join(full_p, x)))
                        m_bytes += folder_sz
                        custom_models.append({
                            "name": folder,
                            "path": full_p,
                            "size_mb": round(folder_sz / (1024 * 1024), 2)
                        })
            results["custom_models"] = {
                "files_count": len(custom_models),
                "size_mb": round(m_bytes / (1024 * 1024), 2),
                "files": custom_models
            }
            total_bytes += m_bytes
            total_files += len(custom_models)

        results["total_cleanable_mb"] = round(total_bytes / (1024 * 1024), 2)
        results["total_cleanable_files"] = total_files
        return results

    def clean_cache(
        self,
        cstrike_path: str,
        clean_hpk: bool = True,
        clean_downloads: bool = True,
        clean_custom_maps: bool = False,
        clean_custom_models: bool = False
    ) -> Dict[str, Any]:
        """
        Ejecuta la depuración selectiva garantizando la preservación estricta de la lista blanca.
        """
        if not cstrike_path or not os.path.isdir(cstrike_path):
            return {"success": False, "error": "Ruta de cstrike no conectada."}

        deleted_files = 0
        freed_bytes = 0

        # 1. Limpiar custom.hpk
        if clean_hpk:
            hpk_p = os.path.join(cstrike_path, "custom.hpk")
            if os.path.isfile(hpk_p):
                try:
                    freed_bytes += os.path.getsize(hpk_p)
                    os.remove(hpk_p)
                    deleted_files += 1
                    logger.info("[AssetsCleaner] custom.hpk eliminado con éxito.")
                except Exception as e:
                    logger.error(f"[AssetsCleaner] Error al eliminar custom.hpk: {e}")

        # 2. Limpiar carpeta download/
        if clean_downloads:
            dl_dir = os.path.join(cstrike_path, "download")
            if os.path.isdir(dl_dir):
                for root, dirs, files in os.walk(dl_dir, topdown=False):
                    for f in files:
                        fp = os.path.join(root, f)
                        try:
                            freed_bytes += os.path.getsize(fp)
                            os.remove(fp)
                            deleted_files += 1
                        except Exception:
                            pass
                    for d in dirs:
                        dp = os.path.join(root, d)
                        try:
                            os.rmdir(dp)
                        except Exception:
                            pass
                logger.info("[AssetsCleaner] Carpeta cstrike/download/ vaciada.")

        # 3. Limpiar mapas no oficiales seleccionados
        if clean_custom_maps:
            maps_dir = os.path.join(cstrike_path, "maps")
            if os.path.isdir(maps_dir):
                for f in os.listdir(maps_dir):
                    f_lower = f.lower()
                    if f_lower.endswith(".bsp") and f_lower not in self.VANILLA_MAPS:
                        fp = os.path.join(maps_dir, f)
                        try:
                            freed_bytes += os.path.getsize(fp)
                            os.remove(fp)
                            deleted_files += 1
                            # Borrar archivos asociados (.txt, .res, .nav)
                            base_name = f_lower[:-4]
                            for ext in [".txt", ".res", ".nav"]:
                                assoc_f = os.path.join(maps_dir, base_name + ext)
                                if os.path.isfile(assoc_f):
                                    os.remove(assoc_f)
                                    deleted_files += 1
                        except Exception as e:
                            logger.error(f"[AssetsCleaner] Error eliminando mapa {f}: {e}")

        # 4. Limpiar modelos personalizados de jugador
        if clean_custom_models:
            import shutil
            player_models_dir = os.path.join(cstrike_path, "models", "player")
            if os.path.isdir(player_models_dir):
                for folder in os.listdir(player_models_dir):
                    if folder.lower() not in self.VANILLA_PLAYER_MODELS:
                        full_p = os.path.join(player_models_dir, folder)
                        if os.path.isdir(full_p):
                            try:
                                folder_sz = sum(os.path.getsize(os.path.join(full_p, x)) for x in os.listdir(full_p) if os.path.isfile(os.path.join(full_p, x)))
                                freed_bytes += folder_sz
                                shutil.rmtree(full_p)
                                deleted_files += 1
                            except Exception as e:
                                logger.error(f"[AssetsCleaner] Error al eliminar modelo {folder}: {e}")

        freed_mb = round(freed_bytes / (1024 * 1024), 2)
        logger.info(f"[AssetsCleaner] Limpieza finalizada: {deleted_files} archivos eliminados ({freed_mb} MB liberados).")

        return {
            "success": True,
            "deleted_files_count": deleted_files,
            "freed_mb": freed_mb,
            "message": f"Se liberaron exitosamente {freed_mb} MB ({deleted_files} archivos eliminados)."
        }


# Instancia singleton
assets_cleaner = AssetsCleaner()
