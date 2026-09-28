#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
CS 1.6 MODDING & TUNING STUDIO PRO - AUTOMATED BUILD PIPELINE (PYINSTALLER)
=============================================================================
Compila el proyecto a ejecutable nativo (.exe) en dist/CSStudioPro/CSStudioPro.exe
Incluye templates HTML, assets estáticos CSS/JS e imágenes.
"""

import os
import sys
import subprocess
import shutil

def build_executable():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)

    print("=" * 70)
    print(" [1/3] Preparando compilación de CS 1.6 Studio Pro a ejecutable (.exe)")
    print("=" * 70)

    # Comando PyInstaller con soporte de templates, assets estáticos, UAC Admin y módulos v2
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "CSStudioPro",
        "--collect-all", "bcrypt",
        "--collect-all", "jwt",
        "--collect-all", "psutil",
        "--add-data", f"{os.path.join(root_dir, 'templates')};templates",
        "--add-data", f"{os.path.join(root_dir, 'static')};static",
        "--add-data", f"{os.path.join(root_dir, 'modules')};modules",
        "--add-data", f"{os.path.join(root_dir, 'utils')};utils",
        "--add-data", f"{os.path.join(root_dir, 'cs_latency_fix.reg')};.",
    ]
    if os.path.isfile(os.path.join(root_dir, ".env")):
        cmd.extend(["--add-data", f"{os.path.join(root_dir, '.env')};."])
    if os.path.isfile(os.path.join(root_dir, "studio_settings.json")):
        cmd.extend(["--add-data", f"{os.path.join(root_dir, 'studio_settings.json')};."])
    cmd.append(os.path.join(root_dir, "launcher.py"))

    print(f"[*] Ejecutando: {' '.join(cmd)}")
    res = subprocess.run(cmd)

    if res.returncode == 0:
        exe_path = os.path.join(root_dir, "dist", "CSStudioPro", "CSStudioPro.exe")
        print("\n" + "=" * 70)
        print(" [OK] Compilacion finalizada con exito!")
        print(f" [OK] Ejecutable generado en: {exe_path}")
        print("=" * 70)
        # Buscar Inno Setup para compilar instalador automáticamente si existe
        inno_compiler_candidates = [
            r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
            r"C:\Program Files\Inno Setup 6\ISCC.exe",
            r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
            r"C:\Program Files\Inno Setup 5\ISCC.exe",
            shutil.which("ISCC.exe") or ""
        ]
        iscc_path = next((p for p in inno_compiler_candidates if p and os.path.exists(p)), None)

        if iscc_path:
            print("\n" + "=" * 70)
            print(f" [2/3] Inno Setup detectado en: {iscc_path}")
            print(" [*] Compilando instalador Setup.exe a Output_Installer/...")
            print("=" * 70)
            inno_res = subprocess.run([iscc_path, os.path.join(root_dir, "installer.iss")])
            if inno_res.returncode == 0:
                print("\n" + "=" * 70)
                print(" [OK] Instalador compilado: Output_Installer/CS_Studio_Pro_Setup.exe")
                print("=" * 70)
            else:
                print("\n[!] Inno Setup devolvio un error.")
        else:
            print("\nPara empaquetarlo en Setup.exe:")
            print("1. Abre 'installer.iss' con Inno Setup Compiler.")
            print("2. Presiona F9 (Build -> Compile).")
            print("3. Tu instalador final estara en 'Output_Installer/CS_Studio_Pro_Setup.exe'\n")
        return True


    else:
        print("\n[!] Error durante la compilación con PyInstaller.")
        return False

if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)
