# =============================================================================
# CS 1.6 MODDING & TUNING STUDIO PRO - NATIVE DESKTOP LAUNCHER
# Desarrollado por: yuyito, Hidden /A/, KYAMI, vANS
# =============================================================================
# Lanzador de escritorio nativo (Desktop GUI) usando pywebview sobre Flask.
# Empaquetable a ejecutable nativo (.exe) mediante PyInstaller.
# =============================================================================

import os
import sys
import threading
import time
import webbrowser
import logging
import urllib.request
import urllib.error

def get_base_path():
    """Resuelve la ruta interna de archivos temporales al compilar con PyInstaller"""
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.abspath(os.path.dirname(__file__))

# Asegurar que la ruta base esté en sys.path
base_path = get_base_path()
if base_path not in sys.path:
    sys.path.insert(0, base_path)

from app import app

def run_flask():
    """Inicia el servidor Flask en segundo plano sin logs verbosos"""
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    os.environ['WERKZEUG_RUN_MAIN'] = 'true'
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)

def wait_for_server(url="http://127.0.0.1:5000/login", timeout=12.0):
    """Espera a que el servidor Flask responda antes de abrir la ventana"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'CSStudioLauncher'})
            with urllib.request.urlopen(req, timeout=0.8) as response:
                if response.status in (200, 302):
                    return True
        except urllib.error.HTTPError as e:
            if e.code in (200, 302):
                return True
        except Exception:
            time.sleep(0.15)
    return False

def main():
    # 1. Iniciar servidor Flask en hilo secundario daemon
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # 2. Esperar a que el servidor esté listo
    wait_for_server()

    # 3. Abrir ventana nativa de escritorio con pywebview
    try:
        import webview
        window = webview.create_window(
            title="CS 1.6 Modding & Tuning Studio Pro",
            url="http://127.0.0.1:5000",
            width=1180,
            height=820,
            resizable=True,
            min_size=(980, 680),
            background_color="#0c0f12"
        )
        webview.start()
    except Exception as e:
        # Fallback elegante a navegador si pywebview no dispone de entorno gráfico directo
        print(f"[!] pywebview fallback: {e}. Abriendo en navegador predeterminado...")
        webbrowser.open("http://127.0.0.1:5000")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    sys.exit(0)

if __name__ == "__main__":
    main()
