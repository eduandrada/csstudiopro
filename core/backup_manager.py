# -*- coding: utf-8 -*-
"""
Módulo de Gestión de Snapshots y Rollback Automático para CS 1.6
Garantiza que cualquier archivo modificado pueda revertirse con un solo clic.
"""

import datetime
import hashlib
import json
import os
import shutil


class BackupManager:
    def __init__(self):
        pass

    def _get_backup_dir(self, cstrike_path):
        bdir = os.path.join(cstrike_path, "backup_studio")
        os.makedirs(bdir, exist_ok=True)
        return bdir

    def _get_manifest_path(self, cstrike_path):
        return os.path.join(self._get_backup_dir(cstrike_path), "backup_manifest.json")

    def _load_manifest(self, cstrike_path):
        mpath = self._get_manifest_path(cstrike_path)
        if os.path.exists(mpath):
            try:
                with open(mpath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_manifest(self, cstrike_path, manifest):
        mpath = self._get_manifest_path(cstrike_path)
        with open(mpath, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=4, ensure_ascii=False)

    def backup_file(self, cstrike_path, rel_target_path, action_desc="Instalación de Mod"):
        """
        Crea un snapshot del archivo de destino antes de sobreescribirlo.
        rel_target_path: ruta relativa dentro de cstrike (ej: 'models/v_ak47.mdl')
        """
        full_target = os.path.join(cstrike_path, rel_target_path)
        bdir = self._get_backup_dir(cstrike_path)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        manifest = self._load_manifest(cstrike_path)
        entry_id = f"{timestamp}_{os.path.basename(rel_target_path)}"

        backup_sub = os.path.join(bdir, entry_id)

        file_existed = os.path.exists(full_target)
        file_size = 0
        sha256 = ""

        if file_existed:
            file_size = os.path.getsize(full_target)
            shutil.copy2(full_target, backup_sub)
            try:
                with open(full_target, "rb") as f:
                    sha256 = hashlib.sha256(f.read()).hexdigest()
            except Exception:
                pass
        else:
            backup_sub = None

        entry = {
            "id": entry_id,
            "rel_path": rel_target_path.replace("\\", "/"),
            "backup_filename": entry_id if file_existed else None,
            "timestamp": datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "action": action_desc,
            "existed_before": file_existed,
            "size_bytes": file_size,
            "sha256": sha256
        }

        manifest.insert(0, entry)
        self._save_manifest(cstrike_path, manifest)
        return entry

    def rollback(self, cstrike_path, entry_id):
        """Restaura un archivo específico a su snapshot anterior."""
        manifest = self._load_manifest(cstrike_path)
        target_entry = None
        for e in manifest:
            if e["id"] == entry_id:
                target_entry = e
                break

        if not target_entry:
            return False, "Snapshot no encontrado en el manifiesto."

        rel_path = target_entry["rel_path"]
        full_dest = os.path.join(cstrike_path, rel_path)
        bdir = self._get_backup_dir(cstrike_path)

        try:
            if target_entry["existed_before"] and target_entry["backup_filename"]:
                backup_file = os.path.join(bdir, target_entry["backup_filename"])
                if os.path.exists(backup_file):
                    os.makedirs(os.path.dirname(full_dest), exist_ok=True)
                    # Quitar solo lectura si estuviera bloqueado
                    if os.path.exists(full_dest):
                        try:
                            import ctypes
                            ctypes.windll.kernel32.SetFileAttributesW(full_dest, 0x80)
                        except Exception:
                            pass
                    shutil.copy2(backup_file, full_dest)
                else:
                    return False, f"El archivo físico de respaldo no existe: {backup_file}"
            else:
                # Si no existía antes, eliminar el archivo instalado
                if os.path.exists(full_dest):
                    try:
                        import ctypes
                        ctypes.windll.kernel32.SetFileAttributesW(full_dest, 0x80)
                    except Exception:
                        pass
                    os.remove(full_dest)

            # Actualizar manifiesto
            manifest = [e for e in manifest if e["id"] != entry_id]
            self._save_manifest(cstrike_path, manifest)
            return True, f"Restaura exitosa para: {rel_path}"
        except Exception as err:
            return False, f"Error durante rollback: {str(err)}"

    def rollback_all(self, cstrike_path):
        """Restaura todos los snapshots en orden cronológico inverso."""
        manifest = self._load_manifest(cstrike_path)
        success_count = 0
        errors = []

        for entry in list(manifest):
            ok, msg = self.rollback(cstrike_path, entry["id"])
            if ok:
                success_count += 1
            else:
                errors.append(msg)

        return {
            "success": len(errors) == 0,
            "restored_count": success_count,
            "errors": errors
        }

    def list_backups(self, cstrike_path):
        """Retorna la lista de todos los backups disponibles."""
        return self._load_manifest(cstrike_path)

    def delete_backup_entry(self, cstrike_path, entry_id):
        """Elimina una entrada de snapshot sin restaurarla."""
        manifest = self._load_manifest(cstrike_path)
        bdir = self._get_backup_dir(cstrike_path)

        for e in manifest:
            if e["id"] == entry_id:
                if e.get("backup_filename"):
                    bfile = os.path.join(bdir, e["backup_filename"])
                    if os.path.exists(bfile):
                        try:
                            os.remove(bfile)
                        except Exception:
                            pass
                break

        manifest = [e for e in manifest if e["id"] != entry_id]
        self._save_manifest(cstrike_path, manifest)
        return True


backup_manager = BackupManager()
