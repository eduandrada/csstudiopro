# CS 1.6 Modding, Tuning & Audio Studio Pro
### Estación Definitiva de Personalización, Netcode, Demos y Audio para el Motor GoldSrc (Counter-Strike 1.6 / Half-Life)

---

## 👑 Desarrollador Principal & Arquitectura
- **Edu Andrada** ([@eduandrada](https://github.com/eduandrada))

## 👥 Equipo de Investigación & Colaboradores
- **yuyito** — Dirección Técnica & Arquitectura GoldSrc
- **Hidden /A/** — Sistemas, Ciberseguridad & Kernel Tuning
- **KYAMI** — Interfaz Táctica (UI/UX) & Shaders GoldSrc
- **vANS** — Motor Acústico & Netcode Competitivo

## 🌐 Enlaces Oficiales & Despliegue
- **Repositorio Oficial en GitHub**: [https://github.com/eduandrada/csstudiopro.git](https://github.com/eduandrada/csstudiopro.git)
- **Versión Web en Vivo (Render Cloud)**: [https://csstudiopro.onrender.com](https://csstudiopro.onrender.com)
- **ID de Servicio Render**: `srv-dass8sfpn0mc739qp790`

---

## 🚀 Descripción General

**CS 1.6 Modding, Tuning & Audio Studio Pro** es una suite completa diseñada para controlar cada rincón del motor GoldSrc sin romper el juego. Proporciona una interfaz web y de escritorio nativa táctica y moderna (HTML5, CSS3, JavaScript) con backend en Python (Flask + Pillow + motor de audio nativo + FFmpeg + SQLite) y control directo del sistema de archivos local en Windows.

Cuenta con un sistema de autenticación privado de grado ciberseguridad (hashing con bcrypt cost factor 12, JWT en cookies HTTP-only, rate limiting contra fuerza bruta y base de datos SQLite privada).

---

## 🛡️ Seguridad y Autenticación Privada

Para su uso en entornos privados o personales:
- **Usuario por defecto**: `cstrike`
- **Contraseña por defecto**: `pro`
- **Hashing**: `bcrypt` (12 salt rounds, ninguna contraseña en texto plano).
- **Gestión de Sesión**: Cookies HTTP-only, SameSite=Strict y tokens JWT firmados con algoritmo HS256.
- **Protección contra Fuerza Bruta**: Rate Limiting de 5 intentos fallidos máximos con bloqueo temporal de 15 minutos.
- **Configuración mediante `.env`**: Secretos, expiración de tokens y parámetros de seguridad.

---

## ⚡ Módulos Esenciales de la Suite

### 1. 🎨 Conversores & VGUI
- **🎯 Compilador Binario WAD3 (`tempdecal.wad` & `pldecal.wad`)**: Ajuste automático al límite de 11.200 px ($w \times h \le 11200$), slot 255 transparente (#0000FF), 4 mipmaps Miptex e inyección directa con atributo Solo Lectura (+R).
- **🔊 Procesador Acústico estilo GoldWave (`audio_processor.py`)**: Conversión a WAV PCM 16-bit Mono (22.050 Hz / 11.025 Hz) con normalización a 0 dB y prevención de clipping.
- **📋 Editor Visual de VGUI y GameMenu (`resource/GameMenu.res`)**: Edición del menú principal y personalización de colores HUD (`TrackerScheme.res`).
- **🎬 Renderizador y Conversor de Demos (.dem a .mp4)**:
  - **Método 1 (startmovie + FFmpeg)**: Renderiza fotograma por fotograma (`clip*.bmp` y audio `clip.wav`) a 60 o 120 FPS fluidos sin caídas de rendimiento, codificando con H.264/AAC y limpieza automática de fotogramas temporales.
  - **Método 2 (HLAE)**: Asistente para cinemáticas y separación de streams alfa (`mirv_movie_*`).
  - **Método 3 (OBS Studio)**: Guía de captura directa en tiempo real de `hl.exe`.

### 2. ⚙️ Binds & Configuración
- **⌨️ Teclado Visual 100% & Binds**: Renderizado del teclado completo (alfanumérico, F1-F12, navegación, Numpad y mouse) con asignación de acciones por categorías de color y exportador de `binds.cfg`.
- **⚡ Netcode & Rates (`userconfig.cfg`)**: Cálculo exacto de interpolación ($\text{ex\_interp} = 1 / \text{cl\_updaterate}$), `m_rawinput 1`, eliminación de aceleración de Windows y audio de baja latencia (`_snd_mixahead 0.05`).
- **🌲 Compilador de CommandMenu [H] (`commandmenu.txt`)**: Estructura en árbol ergonómica de 9 opciones por nivel.
- **📖 Manual Completo de Comandos y Armas**: Base de datos de más de 45 comandos GoldSrc y catálogo de armas con costos, nombres de compra y descripciones.

### 3. 📦 Gestor de Assets
- **Enrutamiento Heurístico**: Detecta armas (`v_*.mdl` &rarr; `models/`), jugadores (`leet.mdl` &rarr; `models/player/leet/`), sprites (`sprites/`), sonido (`sound/`) y paquetes ZIP completos con snapshot previo.

### 4. 🚀 Lanzador IA (Unificado)
- **Lanzador Steam & No-Steam**: Detección inteligente de ejecutables `hl.exe`, configuración de parámetros (`-noforcemaccel -freq 144 -gl -w 1920 -h 1080 -novid`).
- **Booster & Latencia**: Kernel timer a 1 ms (`timeBeginPeriod(1)`), prioridad de proceso `HIGH_PRIORITY_CLASS`, afinidad multinúcleo y optimizaciones TCP/IP en el Registro de Windows.
- **AI Coach & Telemetría VAC-Safe**: Monitoreo pasivo mediante `con_logfile` y `mp_logdetail 3`. Diagnóstico de K/D, Headshot %, KAST, economía y generación de rutinas de práctica ejecutables (`exec rutina.cfg`).

### 5. 🛡️ Snapshots & Rollback Total
- **Respaldo defensivo automático** en `cstrike/backup_studio/` antes de modificar cualquier archivo, con hash SHA-256 y restauración con 1 clic.

---

## 📦 Instalación y Puesta en Marcha

### Requisitos Previos
1. **Python 3.10+**: [python.org](https://python.org/) (asegúrate de marcar "Add Python to PATH").
2. **FFmpeg** (Opcional, para renderizado de demos a .mp4): [ffmpeg.org](https://ffmpeg.org/download.html).

### Paso 1: Instalación de Dependencias
```bash
pip install -r requirements.txt
```

### Paso 2: Configuración del Entorno (`.env`)
El proyecto incluye un archivo `.env` configurado por defecto. Puedes editarlo o crear uno nuevo a partir de `.env.example`:
```env
PORT=5000
JWT_SECRET_KEY=cs16_studio_pro_ultra_secure_jwt_secret_key_2026_@goldsrc
JWT_EXPIRATION_HOURS=24
AUTH_DB_PATH=data/cs_auth.db
RATE_LIMIT_MAX_ATTEMPTS=5
RATE_LIMIT_LOCKOUT_SECONDS=900
ALLOW_REGISTRATION=true
COOKIE_SECURE=false
DEFAULT_USER=cstrike
DEFAULT_PASSWORD=pro
```

### Paso 3: Ejecución en Modo Web
```bash
python app.py
```
Abre tu navegador en [http://localhost:5000](http://localhost:5000).
Inicia sesión con:
- **Usuario**: `cstrike`
- **Contraseña**: `pro`

### Paso 4: Ejecución como Aplicación de Escritorio Nativa
Para iniciar con ventana nativa de escritorio (sin navegador externo):
```bash
python launcher.py
```

---

## 🛠️ Compilación a Ejecutable Nativo (.exe) e Instalador

### 1. Compilar el .exe con PyInstaller
Ejecuta el script de compilación automatizado:
```bash
python build_exe.py
# o ejecuta directamente:
build_exe.bat
```
El ejecutable compilado en modo carpeta única (`--onedir --windowed`) se generará en:
```
dist/CSStudioPro/CSStudioPro.exe
```

### 2. Generar el Instalador de Windows (Setup.exe) con Inno Setup
1. Descarga e instala [Inno Setup 6](https://jrsoftware.org/isinfo.php).
2. Abre el archivo `installer.iss` con Inno Setup Compiler.
3. Presiona **F9** (o Menú `Build -> Compile`).
4. El instalador final quedará listo en:
```
Output_Installer/CS_Studio_Pro_Setup.exe
```

---

## 🗂️ Estructura de Archivos del Proyecto

```
cs generador spray/
├── .env                       # Variables de entorno y secretos criptográficos
├── .env.example               # Plantilla de variables de entorno
├── app.py                     # Servidor Flask principal y API REST con middleware auth
├── launcher.py                # Lanzador nativo de escritorio (pywebview)
├── build_exe.py               # Pipeline de compilación automatizado a .exe
├── build_exe.bat              # Script batch para compilar con 1 clic
├── installer.iss              # Script de Inno Setup para generar Setup.exe
├── requirements.txt           # Dependencias Python
├── README.md                  # Documentación oficial
├── data/
│   └── cs_auth.db             # Base de datos SQLite privada de usuarios y auditoría
├── core/
│   ├── __init__.py            # Exportación de módulos
│   ├── auth_manager.py        # Ciberseguridad, bcrypt cost 12, JWT y Rate Limiting
│   ├── demo_processor.py      # Conversor de demos (.dem a .mp4) con FFmpeg
│   ├── path_detector.py       # Detección de cstrike (Steam y No-Steam)
│   ├── backup_manager.py      # Motor de Snapshots y Rollback Total
│   ├── audio_processor.py     # Emulador acústico GoldWave (WAV 16-bit Mono)
│   ├── wad_compiler.py        # Compilador binario WAD3 y bloqueo de lectura +R
│   ├── asset_router.py        # Enrutador heurístico de modelos, sprites y ZIPs
│   ├── vgui_editor.py         # Editor de GameMenu.res y TrackerScheme.res
│   ├── config_generator.py    # Generador de userconfig.cfg sin placebos
│   ├── commandmenu_builder.py # Generador de commandmenu.txt
│   ├── steam_launcher.py      # Calculador de launch options
│   ├── system_booster.py      # Booster de kernel (1ms timer) y prioridad
│   ├── telemetry_engine.py    # Motor de telemetría VAC-Safe pasivo
│   └── tactical_coach.py      # Analizador de rendimiento y rutinas
├── templates/
│   ├── login.html             # Interfaz de inicio de sesión y registro táctico
│   └── index.html             # Dashboard táctico con los 5 módulos consolidados
└── static/
    ├── css/style.css          # Estilos CSS tácticos, modo oscuro, layout y teclado
    └── js/app.js              # Controlador frontend en Vanilla JS
```
