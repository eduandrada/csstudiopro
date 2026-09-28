/**
 * ==============================================================================
 * CS 1.6 MODDING, TUNING & AUDIO STUDIO PRO - FRONTEND CONTROLLER
 * ==============================================================================
 */

// Estado Global
const State = {
    connected: false,
    cstrikePath: null,
    hlRoot: null,
    isSteam: false,
    versionType: "No detectado",
    backupCount: 0,
    spray: {
        file: null,
        image: new Image(),
        loaded: false,
        dims: { w: 96, h: 96 }
    },
    audio: {
        file: null,
        buffer: null,
        wavBlob: null
    },
    netcode: {
        binds: {
            "kp_ins": "vesthelm; vest;",
            "kp_end": "ak47; m4a1;",
            "kp_downarrow": "awp;",
            "kp_pgdn": "deagle;",
            "kp_leftarrow": "hegren;",
            "kp_5": "flash;",
            "kp_rightarrow": "sgren;",
            "kp_home": "defuser;",
            "kp_uparrow": "primammo; secammo;",
            "kp_pgup": "famas; galil;",
            "kp_plus": "shield;",
            "kp_enter": "hegren; flash; flash; sgren; defuser; vesthelm;",
            "kp_del": "usp;"
        }
    },
    buyBindModal: {
        key: null,
        chain: []
    },
    manual: {
        activeCat: 'all',
        searchQuery: ''
    },
    cmdMenu: [],
    booster: {
        active: false,
        timer_1ms: false,
        hl_detected: false,
        pollTimer: null
    },
    telemetry: {
        active: false,
        pollTimer: null,
        metrics: null,
        diagnoses: null
    }
};

// ==============================================================================
// BASE DE DATOS COMPLETA DE ARMAS Y EQUIPAMIENTO DE CS 1.6 (GOLDRSC)
// ==============================================================================
const WEAPONS_DATA = [
    // --- Rifles y Francotiradores ---
    { id: 'ak47', name: 'CV-47 / AK-47', cat: 'rifles', cost: 2500, team: 't', desc: 'Rifle de asalto terrorista. Letal con disparo directo a la cabeza (one-tap).' },
    { id: 'm4a1', name: 'Maverick M4A1 Carabina', cat: 'rifles', cost: 3100, team: 'ct', desc: 'Rifle CT con silenciador opcional. Máxima precisión y control de ráfagas.' },
    { id: 'awp', name: 'Magnum Sniper Rifle (AWP)', cat: 'rifles', cost: 4750, team: 'both', desc: 'El francotirador más temido. Eliminación instantánea de 1 tiro en torso o cabeza.' },
    { id: 'galil', name: 'IDF Defender (Galil)', cat: 'rifles', cost: 2000, team: 't', desc: 'Rifle económico T con cargador de 35 balas. Excelente para rondas semi-compra.' },
    { id: 'famas', name: 'Clarion 5.56 (FAMAS)', cat: 'rifles', cost: 2250, team: 'ct', desc: 'Rifle económico CT con selector de ráfaga de 3 disparos (burst fire).' },
    { id: 'scout', name: 'Schmidt Scout', cat: 'rifles', cost: 2750, team: 'both', desc: 'Francotirador ligero de alta movilidad (260 u/s). Precisión letal en saltos.' },
    { id: 'sg552', name: 'Krieg 552 Commando', cat: 'rifles', cost: 3500, team: 't', desc: 'Rifle con mira óptica telescópica 2x y alta cadencia para Terroristas.' },
    { id: 'aug', name: 'Bullpup (AUG)', cat: 'rifles', cost: 3500, team: 'ct', desc: 'Rifle de asalto CT con zoom 2x y altísima penetración de blindaje.' },
    { id: 'g3sg1', name: 'D3/AU-1 Auto-Sniper', cat: 'rifles', cost: 5000, team: 't', desc: 'Rifle francotirador semiautomático con 20 balas continuas (Terrorista).' },
    { id: 'sg550', name: 'Krieg 550 Auto-Sniper', cat: 'rifles', cost: 4200, team: 'ct', desc: 'Rifle francotirador semiautomático CT con 30 balas continuas.' },

    // --- Pistolas ---
    { id: 'deagle', name: 'Night Hawk .50C (Desert Eagle)', cat: 'pistols', cost: 650, team: 'both', desc: 'Pistola de alto calibre. Baja de 1 tiro a la cabeza incluso con casco.' },
    { id: 'usp', name: 'KM .45 Tactical (USP)', cat: 'pistols', cost: 500, team: 'ct', desc: 'Pistola reglamentaria CT con silenciador desmontable y máxima precisión.' },
    { id: 'glock', name: 'Glock 18 Select Fire', cat: 'pistols', cost: 400, team: 't', desc: 'Pistola reglamentaria T con 20 balas y modo ráfaga secundaria de 3 balas.' },
    { id: 'p228', name: '228 Compact (P228)', cat: 'pistols', cost: 600, team: 'both', desc: 'Pistola con 13 balas, alta cadencia y excelente perforación de chaleco.' },
    { id: 'fn57', name: 'ES Five-Seven', cat: 'pistols', cost: 750, team: 'ct', desc: 'Pistola CT de alta capacidad (20 balas), retroceso suave y penetración.' },
    { id: 'elites', name: '.40 Dual Elites (Berettas)', cat: 'pistols', cost: 800, team: 't', desc: 'Pistolas dobles con 30 balas combinadas. Fuego rápido y recarga acrobática.' },

    // --- Subfusiles (SMG) ---
    { id: 'mp5', name: 'KM Sub-Machine Gun (MP5 Navy)', cat: 'smg', cost: 1500, team: 'both', desc: 'El subfusil clásico más equilibrado para rondas anti-eco y movilidad.' },
    { id: 'p90', name: 'ES C90 (FN P90)', cat: 'smg', cost: 2350, team: 'both', desc: 'Cargador de 50 balas con cadencia salvaje de 900 RPM. Ideal en movimiento.' },
    { id: 'ump45', name: 'KM UMP45', cat: 'smg', cost: 1700, team: 'both', desc: 'Subfusil calibre .45 con alto poder de frenado a corta distancia.' },
    { id: 'mac10', name: 'Ingram MAC-10', cat: 'smg', cost: 1400, team: 't', desc: 'Subfusil ultraligero y económico de alta cadencia para Terroristas.' },
    { id: 'tmp', name: 'Schmidt TMP', cat: 'smg', cost: 1250, team: 'ct', desc: 'Subfusil silenciado de fábrica para CTs. Prácticamente inaudible.' },

    // --- Escopetas y Pesadas ---
    { id: 'm3', name: 'Leone 12 Gauge Super (M3)', cat: 'heavy', cost: 1700, team: 'both', desc: 'Escopeta de bombeo táctico con letalidad devastadora a corta distancia.' },
    { id: 'xm1014', name: 'Leone YG1265 (XM1014 Auto)', cat: 'heavy', cost: 3000, team: 'both', desc: 'Escopeta automática de fuego continuo rápido para emboscadas y pasillos.' },
    { id: 'm249', name: 'M249 SAW Para', cat: 'heavy', cost: 5750, team: 'both', desc: 'Ametralladora ligera de 100 balas en cinta para fuego de cobertura masivo.' },

    // --- Equipamiento y Granadas ---
    { id: 'vesthelm', name: 'Chaleco Kevlar + Casco', cat: 'equipment', cost: 1000, team: 'both', desc: 'Protección integral completa de torso y cabeza contra disparos y metralla.' },
    { id: 'vest', name: 'Solo Chaleco Kevlar', cat: 'equipment', cost: 650, team: 'both', desc: 'Protección para el pecho y cuerpo (sin protección en la cabeza).' },
    { id: 'flash', name: 'Granada Cegadora (Flashbang)', cat: 'equipment', cost: 200, team: 'both', desc: 'Ciega y ensordece a los enemigos. Puedes llevar hasta 2 por ronda.' },
    { id: 'hegren', name: 'Granada Explosiva HE', cat: 'equipment', cost: 300, team: 'both', desc: 'Granada de fragmentación de alto poder destructivo en área.' },
    { id: 'sgren', name: 'Granada de Humo (Smoke)', cat: 'equipment', cost: 300, team: 'both', desc: 'Despliega una densa cortina de humo gris para cortar líneas de visión.' },
    { id: 'defuser', name: 'Kit de Desactivación (Defuse)', cat: 'equipment', cost: 200, team: 'ct', desc: 'Reduce el tiempo de defuse del C4 de 10 segundos a solo 5 segundos.' },
    { id: 'shield', name: 'Escudo Táctico Antidisturbios', cat: 'equipment', cost: 2200, team: 'ct', desc: 'Escudo antibalas de cuerpo entero desplegable para CTs con pistola.' },
    { id: 'nvg', name: 'Visor Nocturno (Nightvision)', cat: 'equipment', cost: 1250, team: 'both', desc: 'Gafas de amplificación de luz residual para zonas oscuras.' },

    // --- Munición ---
    { id: 'primammo', name: 'Munición Primaria Completa', cat: 'ammo', cost: 100, team: 'both', desc: 'Rellena todos los cargadores de reserva de tu rifle o arma principal.' },
    { id: 'secammo', name: 'Munición Secundaria Completa', cat: 'ammo', cost: 50, team: 'both', desc: 'Rellena todos los cargadores de reserva de tu pistola secundaria.' }
];

// ==============================================================================
// BASE DE DATOS COMPLETA DE COMANDOS Y CVARS GOLDRSC (CS 1.6)
// ==============================================================================
const COMMANDS_MANUAL_DATA = [
    // --- Netcode & Conexión ---
    {
        cmd: "rate 100000",
        name: "Tasa de Transferencia (Rate)",
        cat: "netcode",
        recom: "100000 (100k)",
        desc: "Define el límite máximo de bytes por segundo que el cliente solicita al servidor. 100.000 es el valor esports definitivo para conexiones modernas."
    },
    {
        cmd: "cl_updaterate 102",
        name: "Frecuencia de Actualizaciones Recibidas",
        cat: "netcode",
        recom: "102 (servidores 100 tick)",
        desc: "Número de paquetes de estado del mundo que recibes del servidor por segundo. Debe sincronizarse con ex_interp = 1 / updaterate."
    },
    {
        cmd: "cl_cmdrate 105",
        name: "Frecuencia de Comandos Enviados",
        cat: "netcode",
        recom: "105 (o fps_max + 5)",
        desc: "Número de paquetes con tus movimientos y disparos enviados al servidor por segundo. Evita desync entre tu cliente y el servidor."
    },
    {
        cmd: "ex_interp 0.0098",
        name: "Interpolación de Hitbox (ex_interp)",
        cat: "netcode",
        recom: "0.0098 (1 / 102)",
        desc: "Tiempo en segundos para interpolar posiciones de jugadores entre paquetes. Un ex_interp exacto (1/updaterate) alinea la hitbox real con el modelo 3D."
    },
    {
        cmd: "cl_cmdbackup 2",
        name: "Respaldo de Comandos (Backup)",
        cat: "netcode",
        recom: "2",
        desc: "Número de comandos anteriores retransmitidos en cada paquete por si se pierde uno en tránsito (prevención de loss/choke)."
    },
    {
        cmd: "cl_resend 2",
        name: "Delay de Reenvío de Conexión",
        cat: "netcode",
        recom: "2",
        desc: "Tiempo de espera en segundos antes de reenviar el paquete de conexión inicial a un servidor."
    },
    {
        cmd: "cl_dlmax 1024",
        name: "Fragmentación de Descarga",
        cat: "netcode",
        recom: "1024",
        desc: "Tamaño máximo en bytes de los fragmentos de datos descargados del servidor (mapas, sonidos, sprays)."
    },
    {
        cmd: "cl_nosmooth 1",
        name: "Suavizado de Predicción",
        cat: "netcode",
        recom: "1 (Desactivado)",
        desc: "Desactiva el suavizado visual de errores de predicción, mostrando la posición real sin artificios ni 'deslizamientos' falsos."
    },
    {
        cmd: "sys_ticrate 1000",
        name: "Tasa de Ticks del Servidor Local",
        cat: "netcode",
        recom: "1000",
        desc: "Frecuencia de cálculo del servidor dedicado o local. A 1000 ticks, el registro de disparos y físicas es perfecto."
    },

    // --- Armas y Compras ---
    {
        cmd: "buy <alias>",
        name: "Comprar Arma por Alias",
        cat: "weapons",
        recom: "buy ak47 / buy m4a1",
        desc: "Comando nativo de compra en CS 1.6. Soporta aliases directos como 'ak47', 'm4a1', 'awp', 'deagle', 'vesthelm', 'defuser'."
    },
    {
        cmd: "rebuy",
        name: "Recomprar Equipo de la Ronda Anterior",
        cat: "weapons",
        recom: "rebuy (F2 por defecto)",
        desc: "Compra de forma automática exactamente el mismo equipamiento y armas que compraste en la ronda anterior si tienes fondos."
    },
    {
        cmd: "autobuy",
        name: "Compra Automática Inteligente",
        cat: "weapons",
        recom: "autobuy (F1 por defecto)",
        desc: "Compra el combo de rifle prioritario, chaleco con casco y munición según tu dinero disponible configurado en autobuy.txt."
    },
    {
        cmd: "drop",
        name: "Soltar Arma Actual",
        cat: "weapons",
        recom: "bind g drop",
        desc: "Suelta el arma activa en tus manos para pasársela a un compañero o recoger otra del suelo."
    },
    {
        cmd: "lastinv",
        name: "Cambio Rápido a Última Arma (Q Switch)",
        cat: "weapons",
        recom: "bind q lastinv",
        desc: "Alterna instantáneamente entre el arma actual y el último ítem equipado (esencial para quitar zoom del AWP rápido)."
    },

    // --- Mira, HUD y Radar ---
    {
        cmd: "cl_crosshair_color \"0 255 0\"",
        name: "Color de Mira (RGB)",
        cat: "visuals",
        recom: "\"0 255 0\" (Verde Neón)",
        desc: "Define el color de la retícula en valores RGB (Rojo, Verde, Azul de 0 a 255). El verde y el cian '0 255 255' ofrecen el mejor contraste."
    },
    {
        cmd: "cl_crosshair_size small",
        name: "Tamaño de la Mira",
        cat: "visuals",
        recom: "small (o auto / medium / large)",
        desc: "Define las dimensiones de las líneas de la retícula. 'small' permite apuntar con precisión quirúrgica a largas distancias."
    },
    {
        cmd: "cl_dynamiccrosshair 0",
        name: "Mira Dinámica vs Estática",
        cat: "visuals",
        recom: "0 (Estática)",
        desc: "Al ponerlo en 0, la retícula no se expande al caminar o saltar, manteniendo siempre el mismo punto de referencia visual."
    },
    {
        cmd: "cl_crosshair_translucent 0",
        name: "Translucidez de la Mira",
        cat: "visuals",
        recom: "0 (Opaca sólida)",
        desc: "En 0 la mira es 100% sólida y visible contra cualquier fondo claro u oscuro (arena de Dust2, nieve, etc.)."
    },
    {
        cmd: "hud_fastswitch 1",
        name: "Cambio Rápido de Armas",
        cat: "visuals",
        recom: "1 (Activo)",
        desc: "Al presionar 1, 2, 3 o rueda del ratón, equipa el arma de inmediato sin requerir clic de confirmación."
    },
    {
        cmd: "cl_radartype 1",
        name: "Radar Opaco Táctico",
        cat: "visuals",
        recom: "1 (Opaco)",
        desc: "Fondo negro sólido en el radar superior izquierdo, permitiendo ver los puntos de compañeros y bombas con claridad."
    },
    {
        cmd: "net_graph 3",
        name: "Gráfico de Rendimiento y Netcode",
        cat: "visuals",
        recom: "3 (Mínimo estorbo) o 1",
        desc: "Muestra en pantalla FPS reales, ping, loss, choke y ms de interpolación en tiempo real."
    },
    {
        cmd: "net_graphpos 2",
        name: "Posición de Net Graph",
        cat: "visuals",
        recom: "2 (Centro) o 1 (Derecha)",
        desc: "Posición horizontal del monitor de rendimiento en pantalla (1: Derecha, 2: Centro, 3: Izquierda)."
    },

    // --- Rendimiento, Gráficos y FPS ---
    {
        cmd: "fps_max 99.5",
        name: "Límite Máximo de FPS",
        cat: "video",
        recom: "99.5 (o 144 / 240 con override)",
        desc: "Límite de cuadros por segundo del motor. 99.5 evita fluctuaciones físicas en GoldSrc clásico; con fps_override 1 puedes subirlo."
    },
    {
        cmd: "fps_override 1",
        name: "Desbloqueo de 100+ FPS",
        cat: "video",
        recom: "1 (Para monitores 144Hz/240Hz)",
        desc: "Permite superar el límite histórico de 100 FPS del motor Half-Life en versiones modernas de Steam."
    },
    {
        cmd: "gl_vsync 0",
        name: "Sincronización Vertical (V-Sync)",
        cat: "video",
        recom: "0 (Desactivado)",
        desc: "Elimina por completo el retraso de entrada (input lag) del ratón provocado por la sincronización de monitor."
    },
    {
        cmd: "r_decals 300",
        name: "Límite de Decals (Balas y Sprays)",
        cat: "video",
        recom: "300 (Estándar) o 0 para boost",
        desc: "Número máximo de impactos de bala, sangre y grafitis WAD3 visibles simultáneamente en el mapa."
    },
    {
        cmd: "max_shells 0",
        name: "Casquillos de Munición Expulsados",
        cat: "video",
        recom: "0 (Desactivado)",
        desc: "Evita que las armas generen casquillos voladores en 3D al disparar, ganando fluidez en tiroteos intensos."
    },
    {
        cmd: "cl_weather 0",
        name: "Efectos Climáticos (Lluvia/Nieve)",
        cat: "video",
        recom: "0 (Desactivado en de_aztec)",
        desc: "Desactiva la lluvia en mapas como Aztec mejorando visibilidad y rendimiento."
    },
    {
        cmd: "m_rawinput 1",
        name: "Entrada Pura del Ratón (Raw Input)",
        cat: "video",
        recom: "1 (Activo)",
        desc: "Lee directamente los datos del sensor del ratón sin pasar por la aceleración ni filtros de Windows."
    },

    // --- Audio y Micrófono ---
    {
        cmd: "_snd_mixahead 0.05",
        name: "Buffer Acústico de Baja Latencia",
        cat: "audio",
        recom: "0.05 (50 ms)",
        desc: "Reduce el retraso con el que escuchas los pasos y disparos de 100ms a solo 50ms (o 0.06 si se corta)."
    },
    {
        cmd: "hisound 1",
        name: "Calidad de Audio de Alta Fidelidad (22 kHz)",
        cat: "audio",
        recom: "1 (22.050 Hz 16-bit)",
        desc: "Fuerza al motor GoldSrc a reproducir sonido a máxima calidad de 22.050 Hz en lugar del modo comprimido de 11 kHz."
    },
    {
        cmd: "stopsound",
        name: "Detener Sonidos y Bugeos de Audio",
        cat: "audio",
        recom: "bind f1 stopsound",
        desc: "Corta instantáneamente cualquier audio en reproducción (viento, sonido de lluvia o zumbidos trabados)."
    },
    {
        cmd: "voice_enable 1",
        name: "Habilitar Chat de Voz",
        cat: "audio",
        recom: "1 (o 0 para mutear a todos)",
        desc: "Activa o desactiva la recepción y emisión de voz de los jugadores de la partida."
    },
    {
        cmd: "voice_scale 1.0",
        name: "Volumen de Voces de Jugadores",
        cat: "audio",
        recom: "0.75 - 1.0",
        desc: "Ajusta la ganancia del micrófono de los demás jugadores sin afectar los sonidos de pasos ni disparos del juego."
    },
    {
        cmd: "room_type 0",
        name: "Efecto de Reverberación de Sala",
        cat: "audio",
        recom: "0 (Sin eco)",
        desc: "Desactiva el eco irreal de las habitaciones para escuchar pasos con nitidez limpia y posicional."
    },

    // --- Servidor Local y Práctica ---
    {
        cmd: "sv_restart 1",
        name: "Reiniciar Ronda del Servidor",
        cat: "server",
        recom: "sv_restart 1",
        desc: "Reinicia el tiempo, puntuación y posiciones iniciales tras 1 segundo."
    },
    {
        cmd: "mp_startmoney 16000",
        name: "Dinero Inicial de Partida",
        cat: "server",
        recom: "16000 (Máximo en CS 1.6)",
        desc: "Establece el dinero con el que arrancan los jugadores al ingresar o reiniciar la partida."
    },
    {
        cmd: "mp_roundtime 1.75",
        name: "Duración de Ronda en Minutos",
        cat: "server",
        recom: "1.75 (1 min 45s oficial competitivo)",
        desc: "Tiempo límite de cada ronda antes de que ganen los Antiterroristas si no se planta la bomba."
    },
    {
        cmd: "mp_freezetime 0",
        name: "Tiempo Congelado al Inicio de Ronda",
        cat: "server",
        recom: "0 (Práctica) o 3 (Torneo)",
        desc: "Segundos que los jugadores están inmovilizados comprando antes de poder correr."
    },
    {
        cmd: "mp_buytime 0.25",
        name: "Tiempo Habilitado para Comprar",
        cat: "server",
        recom: "0.25 (15 segundos oficial) o 99",
        desc: "Fracción de minuto en la que la zona de compra permanece activa."
    },
    {
        cmd: "mp_c4timer 35",
        name: "Tiempo de Detonación del C4",
        cat: "server",
        recom: "35 (Oficial) o 45 (Clásico)",
        desc: "Segundos exactos que tarda la bomba C4 en detonar desde que es plantada."
    },
    {
        cmd: "sv_gravity 800",
        name: "Gravedad del Servidor",
        cat: "server",
        recom: "800 (Normal) o 400 (Baja)",
        desc: "Modifica la atracción gravitatoria del mapa. 800 es el valor por defecto; 400 permite saltos lunares."
    },
    {
        cmd: "mp_autoteambalance 0",
        name: "Auto-Balance de Equipos",
        cat: "server",
        recom: "0 (Desactivado para scrims/práctica)",
        desc: "Evita que el servidor te cambie de bando automáticamente si un equipo tiene menos jugadores."
    },
    {
        cmd: "bot_add",
        name: "Añadir Bot a la Partida",
        cat: "server",
        recom: "bot_add / bot_add_ct / bot_add_t",
        desc: "Añade un jugador controlado por la inteligencia artificial en servidores locales con soporte ZBot/CS Bot."
    }
];


// ==============================================================================
// CONTROLADOR DE PANTALLA DE CARGA TÁCTICA (GOLD AK-47 & RADAR)
// ==============================================================================
const LoadingOverlay = {
    get el() { return document.getElementById('tacticalLoadingOverlay'); },
    get titleEl() { return document.getElementById('loadingTitle'); },
    get stepEl() { return document.getElementById('loadingStep'); },
    get fillEl() { return document.getElementById('loadingProgressFill'); },
    get pctEl() { return document.getElementById('loadingProgressPercent'); },
    get tagEl() { return document.getElementById('loadingEngineTag'); },
    get tickerEl() { return document.getElementById('loadingDetailText'); },
    _timer: null,

    show({ 
        title = "PROCESANDO OPERACIÓN TÁCTICA", 
        step = "Inicializando motor de renderizado GoldSrc...", 
        percent = 0, 
        engineTag = "GOLDRSC ENGINE • 11.200 PX MAX", 
        detail = "[STATUS: ACTIVO] • [CALIBRACIÓN BINARIA]" 
    } = {}) {
        if (this._timer) clearInterval(this._timer);
        const overlay = this.el;
        if (!overlay) return;

        if (this.titleEl) this.titleEl.textContent = title;
        if (this.stepEl) this.stepEl.textContent = step;
        if (this.tagEl) this.tagEl.textContent = engineTag;
        if (this.tickerEl) this.tickerEl.textContent = detail;
        this.setProgress(percent);

        overlay.style.display = 'flex';
        // Forzar reflow para disparo fluido de la transición CSS
        void overlay.offsetWidth;
        overlay.classList.add('active');
    },

    setProgress(percent, stepText = null, detailText = null) {
        const p = Math.max(0, Math.min(100, Math.round(percent)));
        if (this.fillEl) this.fillEl.style.width = p + '%';
        if (this.pctEl) this.pctEl.textContent = p + '%';
        if (stepText && this.stepEl) this.stepEl.textContent = stepText;
        if (detailText && this.tickerEl) this.tickerEl.textContent = detailText;
    },

    setTitle(title) {
        if (this.titleEl) this.titleEl.textContent = title;
    },

    setDetail(detail) {
        if (this.tickerEl) this.tickerEl.textContent = detail;
    },

    hide(delayMs = 400) {
        if (this._timer) {
            clearInterval(this._timer);
            this._timer = null;
        }
        setTimeout(() => {
            const overlay = this.el;
            if (!overlay) return;
            overlay.classList.remove('active');
            setTimeout(() => {
                if (!overlay.classList.contains('active')) {
                    overlay.style.display = 'none';
                }
            }, 300);
        }, delayMs);
    },

    // Demostración interactiva táctica en 5 fases continuas
    async simulateDemo() {
        const phases = [
            { pct: 15, step: "Escaneando firmas binarias y límites del motor GoldSrc...", detail: "[FASE 1/5] • [RESOLUCIÓN BASE 112x96 • 10.752 PX]", tag: "MODO DEMO • GOLDRSC SUITE" },
            { pct: 40, step: "Generando paleta 256 colores y aislando slot 255 (Blue Key)...", detail: "[FASE 2/5] • [PALETA: {0,0,255} TRANSPARENTE]", tag: "QUANTIZACIÓN CUÁNTICA" },
            { pct: 68, step: "Compilando texturas Miptex con 4 niveles de sub-resolución...", detail: "[FASE 3/5] • [MIPTEX 0/1/2/3 • LUMP {LOGO]", tag: "WAD3 COMPILER PRO" },
            { pct: 88, step: "Ajustando permisos NTFS y aplicando atributo Solo Lectura (+R)...", detail: "[FASE 4/5] • [WINDOWS API: FILE_ATTRIBUTE_READONLY]", tag: "SECURITY LOCK (+R)" },
            { pct: 100, step: "¡Operación táctica completada con éxito!", detail: "[FASE 5/5] • [ESTADO: SINCRONIZADO CON CSTRIKE/]", tag: "GOLDRSC ENGINE • LISTO" }
        ];

        this.show({
            title: "DEMOSTRACIÓN DE CARGA TÁCTICA",
            step: phases[0].step,
            percent: phases[0].pct,
            engineTag: phases[0].tag,
            detail: phases[0].detail
        });

        for (let i = 1; i < phases.length; i++) {
            await new Promise(r => setTimeout(r, 650));
            this.setProgress(phases[i].pct, phases[i].step, phases[i].detail);
            if (this.tagEl) this.tagEl.textContent = phases[i].tag;
        }

        await new Promise(r => setTimeout(r, 900));
        this.hide(100);
    }
};

// ==============================================================================
// 1. INICIALIZACIÓN Y NAVEGACIÓN
// ==============================================================================
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    initPathStatus();
    initAuthUser();
    initDemoModule();
    initSprayModule();
    initAudioModule();
    initAssetModule();
    initVGUIModule();
    initNetcodeModule();
    initFullKeyboardModule();
    initCommandMenuModule();
    initSteamLauncherModule();
    initManualModule();
    initBoosterModule();
    initTelemetryModule();
    initV2Pillars();
    loadBackups();
});

function initNavigation() {
    document.querySelectorAll('.tab-link').forEach(btn => {
        btn.addEventListener('click', () => {
            switchTab(btn.dataset.tab);
        });
    });

    document.querySelectorAll('.subtab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const bar = e.target.parentElement;
            bar.querySelectorAll('.subtab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');

            const targetId = 'subpane-' + e.target.dataset.subtab;
            const container = bar.parentElement;
            container.querySelectorAll('.subtab-pane').forEach(p => p.classList.remove('active'));
            const pane = document.getElementById(targetId);
            if (pane) pane.classList.add('active');
        });
    });

    // Subpestañas modulares unificadas
    document.querySelectorAll('.mod-subtab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            switchModuleSubtab(btn.dataset.modtab);
        });
    });
}

function switchModuleSubtab(subtabId) {
    const targetSubpane = document.getElementById('modpane-' + subtabId);
    if (!targetSubpane) return;

    const parentPane = targetSubpane.closest('.tab-pane');
    if (parentPane) {
        parentPane.querySelectorAll('.mod-subpane').forEach(p => p.classList.remove('active'));
        parentPane.querySelectorAll('.mod-subtab-btn').forEach(b => b.classList.remove('active'));
    }

    targetSubpane.classList.add('active');
    const btn = document.querySelector(`.mod-subtab-btn[data-modtab="${subtabId}"]`);
    if (btn) btn.classList.add('active');

    if (subtabId === 'cfg-manual') filterManualCommands();
    if (subtabId === 'conv-vgui') loadGameMenu();
    if (subtabId === 'cfg-binds') {
        if (typeof updateCfgOutput === 'function') updateCfgOutput();
    }
    if (subtabId === 'lia-booster') fetchBoosterStatus();
    if (subtabId === 'lia-telemetry') loadTelemetryDashboard();
    if (subtabId === 'conv-demomp4') scanDemosAndFrames();
}

function switchTab(tabId, subtabId) {
    document.querySelectorAll('.tab-link').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    const link = document.querySelector(`.tab-link[data-tab="${tabId}"]`);
    if (link) link.classList.add('active');

    const pane = document.getElementById(`tab-${tabId}`);
    if (pane) pane.classList.add('active');

    if (subtabId) {
        switchModuleSubtab(subtabId);
    }

    if (tabId === 'snapshots') loadBackups();
    if (tabId === 'converters') loadGameMenu();
    if (tabId === 'configsuite') {
        filterManualCommands();
        if (typeof updateCfgOutput === 'function') updateCfgOutput();
    }
    if (tabId === 'launcher-ia' || tabId === 'booster' || tabId === 'telemetry') {
        fetchBoosterStatus();
        loadTelemetryDashboard();
    }
}



// ==============================================================================
// 2. CONEXIÓN Y DETECCIÓN DE RUTAS
// ==============================================================================
async function initPathStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        updatePathUI(data);
    } catch (err) {
        console.error("Error al consultar estado:", err);
    }
}

function updatePathUI(data) {
    State.connected = data.connected;
    State.cstrikePath = data.path;
    State.hlRoot = data.hl_root;
    State.isSteam = data.is_steam;
    State.versionType = data.version_type;

    const led = document.getElementById('statusLed');
    const text = document.getElementById('statusText');
    const preview = document.getElementById('pathPreview');
    const versionBadge = document.getElementById('statusVersionBadge');

    if (data.connected && data.path) {
        led.className = "status-led online";
        text.textContent = "Conectado a CS 1.6";
        preview.textContent = data.path;
        preview.title = data.path;

        if (versionBadge && data.version_type) {
            versionBadge.style.display = 'inline-flex';
            versionBadge.className = 'version-badge ' + (data.is_steam ? 'steam' : 'nosteam');
            versionBadge.textContent = data.version_type.toUpperCase();
        }
    } else {
        led.className = "status-led";
        text.textContent = "No conectado";
        preview.textContent = "Haz clic para seleccionar ruta";
        if (versionBadge) versionBadge.style.display = 'none';
    }

    // Modal candidates con badges descriptivos Steam / No-Steam
    const candList = document.getElementById('candidatesList');
    if (candList) {
        candList.innerHTML = '';
        const list = data.candidates_info || (data.available_candidates || []).map(c => ({
            path: c,
            version_type: (c.toLowerCase().includes('steamapps') ? 'Steam' : 'No-Steam'),
            is_steam: c.toLowerCase().includes('steamapps')
        }));

        if (!list.length) {
            candList.innerHTML = '<div style="color:var(--text-muted); font-size:0.82rem; padding:8px;">No se encontraron instalaciones automáticas. Introduce la ruta manual abajo.</div>';
        }

        list.forEach(cand => {
            const item = document.createElement('div');
            item.className = 'candidate-item' + (cand.path === data.path ? ' selected' : '');
            
            const badgeType = cand.is_steam ? 'steam' : 'nosteam';
            const badgeLabel = cand.version_type ? cand.version_type.toUpperCase() : (cand.is_steam ? 'STEAM' : 'NO-STEAM');
            
            item.innerHTML = `
                <div style="display:flex; align-items:center; gap:8px; width:100%; justify-content:space-between;">
                    <span style="font-weight:600; color:var(--text-main); font-family:monospace; word-break:break-all;">${cand.path}</span>
                    <span class="version-badge ${badgeType}" style="margin-left:auto; flex-shrink:0;">${badgeLabel}</span>
                </div>
            `;
            item.onclick = () => {
                document.getElementById('manualPathInput').value = cand.path;
                document.querySelectorAll('.candidate-item').forEach(c => c.classList.remove('selected'));
                item.classList.add('selected');
            };
            candList.appendChild(item);
        });
    }

    if (data.path && document.getElementById('manualPathInput')) {
        document.getElementById('manualPathInput').value = data.path;
    }
}

function openPathModal() {
    document.getElementById('pathModal').classList.add('active');
}

function closePathModal() {
    document.getElementById('pathModal').classList.remove('active');
}

async function saveManualPath() {
    const path = document.getElementById('manualPathInput').value.trim();
    if (!path) return;

    try {
        const res = await fetch('/api/set_path', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: path })
        });
        const data = await res.json();
        if (data.success) {
            updatePathUI(data.status);
            closePathModal();
            showToast("¡Ruta de Counter-Strike 1.6 guardada con éxito!");
        } else {
            alert(data.error || "Ruta no válida. Asegúrate de seleccionar la carpeta cstrike/ o la raíz de Half-Life.");
        }
    } catch (err) {
        alert("Error de conexión: " + err.message);
    }
}

// ==============================================================================
// 3. MÓDULO 1: SPRAYS WAD3 (tempdecal.wad)
// ==============================================================================
function initSprayModule() {
    const dropzone = document.getElementById('sprayDropzone');
    const fileInput = document.getElementById('sprayFileInput');

    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length) handleSprayFile(e.dataTransfer.files[0]);
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) handleSprayFile(fileInput.files[0]);
    });

    // Ctrl+V Paste
    window.addEventListener('paste', (e) => {
        const items = (e.clipboardData || e.originalEvent.clipboardData).items;
        for (let item of items) {
            if (item.kind === 'file' && item.type.startsWith('image/')) {
                handleSprayFile(item.getAsFile());
                showToast("¡Imagen pegada desde el portapapeles!");
                break;
            }
        }
    });

    // Control Listeners
    document.getElementById('sprayPreset').addEventListener('change', () => {
        const isCustom = document.getElementById('sprayPreset').value === 'custom';
        document.getElementById('sprayCustomDimRow').style.display = isCustom ? 'grid' : 'none';
        updateSprayPipeline();
    });

    document.getElementById('sprayCustomW').addEventListener('input', updateSprayPipeline);
    document.getElementById('sprayCustomH').addEventListener('input', updateSprayPipeline);

    document.getElementById('sprayAlphaMode').addEventListener('change', () => {
        const mode = document.getElementById('sprayAlphaMode').value;
        document.getElementById('sprayCustomColorRow').style.display = (mode === 'custom') ? 'block' : 'none';
        document.getElementById('sprayTolRow').style.display = (mode === 'white' || mode === 'black' || mode === 'custom') ? 'block' : 'none';
        document.getElementById('sprayAlphaThreshRow').style.display = (mode === 'alpha') ? 'block' : 'none';
        updateSprayPipeline();
    });

    document.getElementById('sprayTolSlider').addEventListener('input', (e) => {
        document.getElementById('sprayTolVal').textContent = e.target.value + '%';
        updateSprayPipeline();
    });

    document.getElementById('sprayAlphaThreshSlider').addEventListener('input', (e) => {
        document.getElementById('sprayAlphaThreshVal').textContent = e.target.value;
        updateSprayPipeline();
    });

    document.getElementById('sprayKeyColor').addEventListener('input', updateSprayPipeline);
    document.getElementById('sprayDither').addEventListener('change', updateSprayPipeline);
    document.getElementById('sprayLumpType').addEventListener('change', updateSprayPipeline);

    // Color picker clicking on canvas
    document.getElementById('sprayPreviewCanvas').addEventListener('click', (e) => {
        const canvas = e.target;
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const x = Math.floor((e.clientX - rect.left) * scaleX);
        const y = Math.floor((e.clientY - rect.top) * scaleY);

        const ctx = canvas.getContext('2d');
        const p = ctx.getImageData(x, y, 1, 1).data;
        const hex = "#" + ((1 << 24) + (p[0] << 16) + (p[1] << 8) + p[2]).toString(16).slice(1);
        
        document.getElementById('sprayAlphaMode').value = 'custom';
        document.getElementById('sprayAlphaMode').dispatchEvent(new Event('change'));
        document.getElementById('sprayKeyColor').value = hex;
        updateSprayPipeline();
        showToast(`Color de fondo fijado en ${hex.toUpperCase()}`);
    });
}

function handleSprayFile(file) {
    if (!file.type.startsWith('image/')) {
        showToast("Por favor selecciona una imagen válida.");
        return;
    }
    State.spray.file = file;
    document.getElementById('sprayDropText').innerHTML = `<b>${file.name}</b> (${Math.round(file.size / 1024)} KB)`;

    const reader = new FileReader();
    reader.onload = (e) => {
        State.spray.image.onload = () => {
            State.spray.loaded = true;
            document.getElementById('sprayInstallBtn').disabled = false;
            document.getElementById('sprayDownloadBtn').disabled = false;
            updateSprayPipeline();
        };
        State.spray.image.src = e.target.result;
    };
    reader.readAsDataURL(file);
}

function computeBestSprayDimensions(w, h, maxPixels = 11200) {
    const aspect = w / h;
    let bestW = 96, bestH = 96;
    let bestCost = Infinity;

    for (let i = 1; i <= 43; i++) {
        for (let j = 1; j <= 43; j++) {
            const pw = i * 16;
            const ph = j * 16;
            const area = pw * ph;
            if (area > maxPixels) continue;

            const ratio = pw / ph;
            const ratioDiff = Math.abs(ratio - aspect) / aspect;
            const areaPenalty = (maxPixels - area) / maxPixels;
            const cost = ratioDiff * 4.0 + areaPenalty;

            if (cost < bestCost) {
                bestCost = cost;
                bestW = pw;
                bestH = ph;
            }
        }
    }
    return { w: bestW, h: bestH };
}

let sprayDebounceTimer = null;
function updateSprayPipeline() {
    if (!State.spray.loaded) return;

    const preset = document.getElementById('sprayPreset').value;
    if (preset === 'auto') {
        State.spray.dims = computeBestSprayDimensions(State.spray.image.width, State.spray.image.height);
    } else if (preset === 'custom') {
        let cw = parseInt(document.getElementById('sprayCustomW').value) || 96;
        let ch = parseInt(document.getElementById('sprayCustomH').value) || 96;
        cw = Math.max(16, Math.round(cw / 16) * 16);
        ch = Math.max(16, Math.round(ch / 16) * 16);
        State.spray.dims = { w: cw, h: ch };
    } else {
        const parts = preset.split('x');
        State.spray.dims = { w: parseInt(parts[0]), h: parseInt(parts[1]) };
    }

    const totalPx = State.spray.dims.w * State.spray.dims.h;
    const pct = ((totalPx / 11200) * 100).toFixed(1);
    document.getElementById('sprayPixelCounter').textContent = `${totalPx.toLocaleString()} / 11.200 px (${pct}%)`;
    const bar = document.getElementById('sprayProgressBar');
    bar.style.width = Math.min(100, pct) + '%';

    if (totalPx > 11200) {
        bar.classList.add('overflow');
        document.getElementById('sprayInstallBtn').disabled = true;
        document.getElementById('sprayDownloadBtn').disabled = true;
    } else {
        bar.classList.remove('overflow');
        document.getElementById('sprayInstallBtn').disabled = false;
        document.getElementById('sprayDownloadBtn').disabled = false;
    }

    document.getElementById('sprayResLabel').textContent = `${State.spray.dims.w} × ${State.spray.dims.h}`;

    renderSprayCanvases();

    clearTimeout(sprayDebounceTimer);
    sprayDebounceTimer = setTimeout(fetchSprayServerPalette, 300);
}

function renderSprayCanvases() {
    const tw = State.spray.dims.w;
    const th = State.spray.dims.h;

    const pCanvas = document.getElementById('sprayPreviewCanvas');
    const pCtx = pCanvas.getContext('2d');
    pCanvas.width = tw;
    pCanvas.height = th;
    pCtx.clearRect(0, 0, tw, th);
    pCtx.drawImage(State.spray.image, 0, 0, tw, th);

    const imgData = pCtx.getImageData(0, 0, tw, th);
    const d = imgData.data;
    const mode = document.getElementById('sprayAlphaMode').value;
    const tol = parseInt(document.getElementById('sprayTolSlider').value) / 100;
    const alphaThresh = parseInt(document.getElementById('sprayAlphaThreshSlider').value);

    let hex = document.getElementById('sprayKeyColor').value;
    let kr = parseInt(hex.substr(1, 2), 16);
    let kg = parseInt(hex.substr(3, 2), 16);
    let kb = parseInt(hex.substr(5, 2), 16);

    let vis = 0, transp = 0;
    for (let i = 0; i < d.length; i += 4) {
        let r = d[i], g = d[i+1], b = d[i+2], a = d[i+3];
        let isT = false;

        if (mode === 'alpha') {
            if (a < alphaThresh) isT = true;
        } else if (mode === 'white') {
            let thresh = 255 * (1.0 - tol);
            if (r >= thresh && g >= thresh && b >= thresh) isT = true;
        } else if (mode === 'black') {
            let thresh = 255 * tol;
            if (r <= thresh && g <= thresh && b <= thresh) isT = true;
        } else if (mode === 'custom') {
            let dist = Math.sqrt(Math.pow(r - kr, 2) + Math.pow(g - kg, 2) + Math.pow(b - kb, 2));
            if (dist <= 441.67 * tol) isT = true;
        }

        if (isT) {
            d[i+3] = 0;
            transp++;
        } else {
            d[i+3] = 255;
            vis++;
        }
    }

    pCtx.putImageData(imgData, 0, 0);
    document.getElementById('sprayVisLabel').textContent = vis.toLocaleString();
    document.getElementById('sprayTranspLabel').textContent = transp.toLocaleString();

    renderDust2Wall(pCanvas, tw, th);
}

function renderDust2Wall(previewCanvas, tw, th) {
    const wCanvas = document.getElementById('sprayWallCanvas');
    const ctx = wCanvas.getContext('2d');
    const w = wCanvas.width;
    const h = wCanvas.height;

    // Fondo arena Dust 2
    ctx.fillStyle = '#bda078';
    ctx.fillRect(0, 0, w, h);

    // Mortero
    ctx.fillStyle = '#8f7756';
    for (let y = 0; y < h; y += 40) {
        ctx.fillRect(0, y, w, 2);
        const offset = (Math.floor(y / 40) % 2) * 60;
        for (let x = offset; x < w; x += 120) {
            ctx.fillRect(x, y, 2, 40);
        }
    }

    // Sombra y grunge
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, 'rgba(0,0,0,0.12)');
    grad.addColorStop(1, 'rgba(0,0,0,0.4)');
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);

    // Spray centrado
    const scale = Math.min(2.0, Math.min((w * 0.7) / tw, (h * 0.7) / th));
    const sw = tw * scale;
    const sh = th * scale;
    const sx = (w - sw) / 2;
    const sy = (h - sh) / 2;

    ctx.save();
    ctx.imageSmoothingEnabled = false;
    ctx.shadowColor = 'rgba(0, 0, 0, 0.5)';
    ctx.shadowBlur = 5;
    ctx.shadowOffsetX = 1;
    ctx.shadowOffsetY = 2;
    ctx.drawImage(previewCanvas, sx, sy, sw, sh);
    ctx.restore();

    // Crosshair verde
    const cx = w / 2;
    const cy = h / 2;
    ctx.strokeStyle = '#00ff00';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(cx - 14, cy); ctx.lineTo(cx - 4, cy);
    ctx.moveTo(cx + 4, cy); ctx.lineTo(cx + 14, cy);
    ctx.moveTo(cx, cy - 14); ctx.lineTo(cx, cy - 4);
    ctx.moveTo(cx, cy + 4); ctx.lineTo(cx, cy + 14);
    ctx.stroke();
}

async function fetchSprayServerPalette() {
    if (!State.spray.file) return;

    const fd = buildSprayFormData();
    try {
        const res = await fetch('/api/spray/preview', { method: 'POST', body: fd });
        if (!res.ok) return;
        const data = await res.json();
        if (data.palette) renderSprayPalette(data.palette);
    } catch (err) {
        console.error("Error al obtener paleta:", err);
    }
}

function renderSprayPalette(palette) {
    const grid = document.getElementById('sprayPaletteGrid');
    grid.innerHTML = '';
    for (let i = 0; i < 256; i++) {
        const cell = document.createElement('div');
        cell.className = 'pal-cell' + (i === 255 ? ' slot-255' : '');
        const rgb = palette[i] || [0, 0, 0];
        cell.style.backgroundColor = `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
        cell.title = (i === 255) 
            ? `Slot 255: Transparente (GoldSrc Key RGB: ${rgb.join(',')})`
            : `Slot ${i}: RGB(${rgb.join(',')})`;
        grid.appendChild(cell);
    }
}

function buildSprayFormData() {
    const fd = new FormData();
    fd.append('file', State.spray.file);
    fd.append('alpha_mode', document.getElementById('sprayAlphaMode').value);
    fd.append('color_tolerance', document.getElementById('sprayTolSlider').value);
    fd.append('alpha_threshold', document.getElementById('sprayAlphaThreshSlider').value);
    fd.append('custom_color', document.getElementById('sprayKeyColor').value);
    fd.append('target_w', State.spray.dims.w);
    fd.append('target_h', State.spray.dims.h);
    fd.append('dither', document.getElementById('sprayDither').checked ? '1' : '0');
    fd.append('lump_type', document.getElementById('sprayLumpType').value);
    return fd;
}

async function installSprayDirect() {
    if (!State.spray.file) return;
    const btn = document.getElementById('sprayInstallBtn');
    btn.disabled = true;
    btn.textContent = "Compilando e instalando (+R)...";

    LoadingOverlay.show({
        title: "COMPILANDO SPRAY WAD3",
        step: "Calibrando dimensiones a múltiplos de 16 (límite 11.200 px)...",
        percent: 15,
        engineTag: `GOLDRSC • ${State.spray.dims.w}×${State.spray.dims.h} PX`,
        detail: "[STATUS: PROCESANDO] • [QUANTIZACIÓN DE PALETA 256]"
    });

    const fd = buildSprayFormData();
    let simPct = 25;
    const progressTimer = setInterval(() => {
        if (simPct < 85) {
            simPct += 12;
            const steps = [
                "Indexando paleta de 256 colores y máscara Slot 255 {0,0,255}...",
                "Construyendo Lump {LOGO y calculando offsets binarios...",
                "Generando 4 sub-niveles de textura Miptex (1/2, 1/4, 1/8)...",
                "Escribiendo cabecera WAD3 y bloqueando con SetFileAttributes (+R)..."
            ];
            const stepIdx = Math.min(steps.length - 1, Math.floor((simPct - 25) / 18));
            LoadingOverlay.setProgress(simPct, steps[stepIdx], `[ESTRUCTURA WAD3: ${simPct}%] • [SOLO LECTURA]`);
        }
    }, 130);

    try {
        const res = await fetch('/api/spray/install', { method: 'POST', body: fd });
        clearInterval(progressTimer);
        const data = await res.json();
        if (data.success) {
            LoadingOverlay.setProgress(100, "¡tempdecal.wad y pldecal.wad instalados en Solo Lectura (+R)!", "[STATUS: COMPLETADO CON ÉXITO]");
            showToast("¡tempdecal.wad y pldecal.wad instalados y bloqueados como Solo Lectura!");
            loadBackups();
            LoadingOverlay.hide(650);
        } else {
            LoadingOverlay.hide(0);
            alert(data.error || "Error al instalar spray.");
        }
    } catch (err) {
        clearInterval(progressTimer);
        LoadingOverlay.hide(0);
        alert("Error de conexión: " + err.message);
    } finally {
        btn.disabled = false;
        btn.textContent = "INSTALAR DIRECTO EN CS 1.6 (+R)";
    }
}

async function downloadSprayWad() {
    if (!State.spray.file) return;
    LoadingOverlay.show({
        title: "COMPILANDO TEMPDECAL.WAD",
        step: "Indexando paleta 256 y empaquetando texturas Miptex...",
        percent: 30,
        engineTag: `GOLDRSC • ${State.spray.dims.w}×${State.spray.dims.h} PX`,
        detail: "[WAD3 BINARY] • [MÁSCARA AZUL SLOT 255]"
    });

    const fd = buildSprayFormData();
    try {
        LoadingOverlay.setProgress(65, "Calculando cabecera WAD3 y offsets binarios...", "[ESTRUCTURA LUMP {LOGO]");
        const res = await fetch('/api/spray/convert', { method: 'POST', body: fd });
        if (!res.ok) throw new Error("Error en compilación");
        const blob = await res.blob();
        LoadingOverlay.setProgress(100, "¡Descargando archivo binario tempdecal.wad!", "[STATUS: DESCARGA LISTA]");
        downloadBlob(blob, "tempdecal.wad");
        showToast("¡tempdecal.wad descargado! Recuerda marcarlo como Solo Lectura.");
        LoadingOverlay.hide(500);
    } catch (err) {
        LoadingOverlay.hide(0);
        alert("Error al descargar: " + err.message);
    }
}

// ==============================================================================
// 4. MÓDULO 2: AUDIO GOLDWAVE
// ==============================================================================
function initAudioModule() {
    const dropzone = document.getElementById('audioDropzone');
    const fileInput = document.getElementById('audioFileInput');

    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length) handleAudioFile(e.dataTransfer.files[0]);
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) handleAudioFile(fileInput.files[0]);
    });

    document.getElementById('audioProfile').addEventListener('change', () => {
        const prof = document.getElementById('audioProfile').value;
        const subRow = document.getElementById('audioSubpathRow');
        const customInput = document.getElementById('audioCustomDest');
        subRow.style.display = (prof === 'custom') ? 'block' : 'none';

        if (prof === 'weapons') {
            document.getElementById('specRate').textContent = "22.050 Hz";
            document.getElementById('specChannels').textContent = "1 (Mono)";
            customInput.value = "sound/weapons/ak47-1.wav";
        } else if (prof === 'radio') {
            document.getElementById('specRate').textContent = "11.025 Hz";
            document.getElementById('specChannels').textContent = "1 (Mono)";
            customInput.value = "sound/radio/go.wav";
        } else if (prof === 'voice') {
            document.getElementById('specRate').textContent = "11.025 Hz";
            document.getElementById('specChannels').textContent = "1 (Mono)";
            customInput.value = "voice_input.wav";
        } else if (prof === 'music') {
            document.getElementById('specRate').textContent = "44.100 Hz";
            document.getElementById('specChannels').textContent = "2 (Estéreo)";
            customInput.value = "media/gamestartup.mp3";
        }
    });

    document.getElementById('audioVolSlider').addEventListener('input', (e) => {
        document.getElementById('audioVolVal').textContent = e.target.value + '%';
    });
}

async function handleAudioFile(file) {
    State.audio.file = file;
    State.audio.buffer = null;
    State.audio.decodingPromise = null;

    document.getElementById('audioDropText').innerHTML = `<b>${file.name}</b> (${Math.round(file.size / 1024)} KB)`;
    document.getElementById('audioFileInfo').textContent = `Archivo: ${file.name} | Tipo: ${file.type || 'multimedia'}`;

    // Reproductor local
    const audioUrl = URL.createObjectURL(file);
    const player = document.getElementById('audioPreviewPlayer');
    player.src = audioUrl;
    player.style.display = 'block';

    document.getElementById('audioSpecsBox').style.display = 'grid';
    document.getElementById('specDuration').textContent = "Decodificando...";
    document.getElementById('audioInstallBtn').disabled = false;
    document.getElementById('audioDownloadBtn').disabled = false;

    // Iniciar decodificación asíncrona preventiva
    ensureAudioDecoded().then(audioBuf => {
        if (audioBuf && isFinite(audioBuf.duration)) {
            document.getElementById('specDuration').textContent = audioBuf.duration.toFixed(2) + 's';
        }
    }).catch(err => {
        console.warn("Aviso decodificación preventiva:", err);
        document.getElementById('specDuration').textContent = "Listo para convertir";
    });
}

async function ensureAudioDecoded() {
    if (State.audio.buffer) return State.audio.buffer;
    if (State.audio.decodingPromise) return await State.audio.decodingPromise;
    if (!State.audio.file) throw new Error("No hay ningún archivo de audio o video seleccionado.");

    State.audio.decodingPromise = (async () => {
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const arrayBuf = await State.audio.file.arrayBuffer();
        const decoded = await audioCtx.decodeAudioData(arrayBuf);
        State.audio.buffer = decoded;
        return decoded;
    })();

    return await State.audio.decodingPromise;
}

function buildAudioFormData() {
    const fd = new FormData();
    fd.append('file', State.audio.file);
    fd.append('profile', document.getElementById('audioProfile').value);
    fd.append('custom_dest', document.getElementById('audioCustomDest').value);
    fd.append('volume_boost', (parseInt(document.getElementById('audioVolSlider').value) / 100).toString());
    fd.append('normalize', document.getElementById('audioNormalize').checked ? '1' : '0');
    return fd;
}

function writeAsciiString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
        view.setUint8(offset + i, string.charCodeAt(i));
    }
}

function encodeAudioBufferToWav(audioBuf, targetRate, normalize = true, volumeBoost = 1.0) {
    const numChannels = audioBuf.numberOfChannels;
    const length = audioBuf.length;
    const srcRate = audioBuf.sampleRate;

    // 1. Downmix de canales estéreo a mono puro Float32
    const mono = new Float32Array(length);
    for (let c = 0; c < numChannels; c++) {
        const ch = audioBuf.getChannelData(c);
        for (let i = 0; i < length; i++) {
            mono[i] += ch[i] / numChannels;
        }
    }

    // 2. Remuestreo lineal al sample rate objetivo de GoldSrc (22050, 11025 u 8000 Hz)
    let resampled = mono;
    if (srcRate !== targetRate) {
        const ratio = srcRate / targetRate;
        const newLen = Math.max(1, Math.round(length / ratio));
        resampled = new Float32Array(newLen);
        for (let i = 0; i < newLen; i++) {
            const origIdx = i * ratio;
            const idxLow = Math.floor(origIdx);
            const idxHigh = Math.min(idxLow + 1, length - 1);
            const frac = origIdx - idxLow;
            resampled[i] = mono[idxLow] * (1.0 - frac) + mono[idxHigh] * frac;
        }
    }

    // 3. Normalización y control de pico (-0.8 dB para prevenir saturación en GoldSrc)
    let peak = 0;
    for (let i = 0; i < resampled.length; i++) {
        const a = Math.abs(resampled[i]);
        if (a > peak) peak = a;
    }

    let multiplier = volumeBoost;
    if (normalize && peak > 0) {
        multiplier = (0.92 / peak) * volumeBoost;
    }

    // 4. Empaquetado binario RIFF/WAVE PCM 16-bit Mono
    const numSamples = resampled.length;
    const byteRate = targetRate * 2; // 1 canal * 2 bytes por muestra
    const blockAlign = 2;            // 1 canal * 2 bytes
    const buffer = new ArrayBuffer(44 + numSamples * 2);
    const view = new DataView(buffer);

    // Cabecera RIFF
    writeAsciiString(view, 0, 'RIFF');
    view.setUint32(4, 36 + numSamples * 2, true);
    writeAsciiString(view, 8, 'WAVE');

    // Subchunk "fmt "
    writeAsciiString(view, 12, 'fmt ');
    view.setUint32(16, 16, true);           // Subchunk1Size (16 para PCM)
    view.setUint16(20, 1, true);            // Formato de Audio (1 = PCM lineal)
    view.setUint16(22, 1, true);            // Canales (1 = Mono)
    view.setUint32(24, targetRate, true);   // Frecuencia de Muestreo (Hz)
    view.setUint32(28, byteRate, true);     // Tasa de bytes
    view.setUint16(32, blockAlign, true);   // Alineación de bloque
    view.setUint16(34, 16, true);           // Profundidad de bits (16-bit)

    // Subchunk "data"
    writeAsciiString(view, 36, 'data');
    view.setUint32(40, numSamples * 2, true);

    // Muestras PCM con signo (-32768 a 32767)
    let offset = 44;
    for (let i = 0; i < numSamples; i++) {
        let s = resampled[i] * multiplier;
        s = Math.max(-1.0, Math.min(1.0, s));
        const sample16 = s < 0 ? Math.round(s * 0x8000) : Math.round(s * 0x7FFF);
        view.setInt16(offset, sample16, true);
        offset += 2;
    }

    return new Blob([buffer], { type: 'audio/wav' });
}

async function installAudioDirect() {
    if (!State.audio.file) return;
    const btn = document.getElementById('audioInstallBtn');
    btn.disabled = true;
    btn.textContent = "Procesando audio GoldWave e instalando...";

    const prof = document.getElementById('audioProfile').value;
    const targetRate = (prof === 'radio' || prof === 'voice') ? 11025 : (prof === 'music' ? 44100 : 22050);
    const rateText = prof === 'music' ? '44.100 Hz Estéreo' : `${targetRate.toLocaleString()} Hz Mono`;
    const volBoost = parseFloat(document.getElementById('audioVolSlider').value) / 100;
    const normalize = document.getElementById('audioNormalize').checked;

    LoadingOverlay.show({
        title: "CONVERSIÓN DE AUDIO MULTIFORMATO",
        step: `Re-muestreando audio a ${rateText} (PCM 16-bit)...`,
        percent: 20,
        engineTag: `AUDIO GOLDRSC • ${rateText}`,
        detail: "[COMPATIBLE: MP4 / MP3 / WAV / OGG / FLAC / M4A]"
    });

    try {
        LoadingOverlay.setProgress(45, "Decodificando pistas y sintetizando WAV 16-bit Mono...", "[DOWNMIX & NORMALIZACIÓN]");
        const audioBuf = await ensureAudioDecoded();

        LoadingOverlay.setProgress(70, "Construyendo cabecera RIFF/WAVE calibrada para GoldSrc...", "[16-BIT MONO]");
        const wavBlob = encodeAudioBufferToWav(audioBuf, targetRate, normalize, volBoost);
        const cleanBaseName = State.audio.file.name.replace(/\.[^/.]+$/, "");
        const fileToSend = new File([wavBlob], `${cleanBaseName}.wav`, { type: 'audio/wav' });

        const fd = new FormData();
        fd.append('file', fileToSend);
        fd.append('profile', prof);
        fd.append('custom_dest', document.getElementById('audioCustomDest').value);
        fd.append('volume_boost', volBoost.toString());
        fd.append('normalize', normalize ? '1' : '0');

        LoadingOverlay.setProgress(85, "Instalando en directorio cstrike/ y respaldando...", "[SNAPSHOT]");
        const res = await fetch('/api/audio/install', { method: 'POST', body: fd });
        const data = await res.json();
        if (data.success) {
            LoadingOverlay.setProgress(100, `¡Audio instalado en ${data.installed_to}!`, "[STATUS: INSTALADO + BACKUP]");
            showToast(`¡Audio instalado en ${data.installed_to} con respaldo automático!`);
            loadBackups();
            LoadingOverlay.hide(650);
        } else {
            LoadingOverlay.hide(0);
            alert(data.error || "Error al instalar audio.");
        }
    } catch (err) {
        LoadingOverlay.hide(0);
        alert("Error de procesamiento acústico: " + err.message);
    } finally {
        btn.disabled = false;
        btn.textContent = "CONVERTIR E INSTALAR EN CSTRIKE";
    }
}

async function downloadAudioWav() {
    if (!State.audio.file) return;

    const prof = document.getElementById('audioProfile').value;
    const targetRate = (prof === 'radio' || prof === 'voice') ? 11025 : (prof === 'music' ? 44100 : 22050);
    const volBoost = parseFloat(document.getElementById('audioVolSlider').value) / 100;
    const normalize = document.getElementById('audioNormalize').checked;

    LoadingOverlay.show({
        title: "PROCESANDO WAV GOLDRSC",
        step: `Convirtiendo pistas y codificando PCM 16-bit Mono (${targetRate} Hz)...`,
        percent: 25,
        engineTag: `AUDIO ENGINE • ${targetRate} HZ`,
        detail: "[CONVERSIÓN MULTIFORMATO: MP4 / MP3 / OGG / WAV / FLAC]"
    });

    try {
        LoadingOverlay.setProgress(55, "Decodificando pistas y aplicando filtros acústicos...", "[WEB AUDIO ENGINE]");
        const audioBuf = await ensureAudioDecoded();

        LoadingOverlay.setProgress(85, "Construyendo cabecera RIFF/WAVE calibrada para Half-Life...", "[16-BIT MONO]");
        const wavBlob = encodeAudioBufferToWav(audioBuf, targetRate, normalize, volBoost);

        const cleanBaseName = State.audio.file.name.replace(/\.[^/.]+$/, "");
        LoadingOverlay.setProgress(100, "¡Archivo de audio listo para descargar!", "[STATUS: DESCARGA]");
        downloadBlob(wavBlob, `${cleanBaseName}_goldsrc.wav`);
        showToast("¡WAV 16-bit Mono (GoldSrc) generado y descargado con éxito!");
        LoadingOverlay.hide(450);
    } catch (err) {
        LoadingOverlay.hide(0);
        alert("Error al descargar audio: " + err.message);
    }
}

// ==============================================================================
// 5. MÓDULO 3: GESTOR DE ASSETS
// ==============================================================================
function initAssetModule() {
    const dropzone = document.getElementById('assetDropzone');
    const fileInput = document.getElementById('assetFileInput');

    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length) uploadAssets(e.dataTransfer.files);
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length) uploadAssets(fileInput.files);
    });
}

async function uploadAssets(fileList) {
    const fd = new FormData();
    for (let f of fileList) {
        fd.append('files', f);
    }

    document.getElementById('assetDropTitle').textContent = `Instalando ${fileList.length} archivo(s)...`;

    LoadingOverlay.show({
        title: "ENRUTADOR INTELIGENTE DE ASSETS",
        step: `Analizando ${fileList.length} archivo(s) y jerarquía GoldSrc...`,
        percent: 25,
        engineTag: "GOLDRSC ASSET MANAGER",
        detail: "[INSPECCIÓN DE FIRMAS Y FORMATOS]"
    });

    try {
        LoadingOverlay.setProgress(60, "Extrayendo paquetes y enrutando modelos, sprites y sonidos...", "[ENRUTANDO A CSTRIKE/]");
        const res = await fetch('/api/assets/install', { method: 'POST', body: fd });
        const data = await res.json();
        if (data.success && data.installed) {
            LoadingOverlay.setProgress(100, `¡${data.installed.length} asset(s) instalados correctamente!`, "[SNAPSHOTS REGISTRADOS]");
            renderAssetLogs(data.installed);
            showToast(`¡${data.installed.length} asset(s) enrutado(s) e instalado(s) con éxito!`);
            loadBackups();
            LoadingOverlay.hide(650);
        } else {
            LoadingOverlay.hide(0);
            alert(data.error || "Error al procesar assets.");
        }
    } catch (err) {
        LoadingOverlay.hide(0);
        alert("Error de conexión: " + err.message);
    } finally {
        document.getElementById('assetDropTitle').textContent = "Arrastra modelos, sprites o paquetes ZIP aquí";
    }
}

function renderAssetLogs(items) {
    const container = document.getElementById('assetsLogContainer');
    const tbody = document.getElementById('assetsLogTable');
    container.style.display = 'block';
    tbody.innerHTML = '';

    items.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><b>${item.filename}</b></td>
            <td><span class="badge cyan">${item.category}</span></td>
            <td><code>${item.installed_to}</code></td>
            <td>${Math.round(item.size / 1024)} KB</td>
            <td><span class="badge green">Instalado</span></td>
        `;
        tbody.appendChild(tr);
    });
}

// ==============================================================================
// 6. MÓDULO 4: VGUI & GAMEMENU
// ==============================================================================
function initVGUIModule() {
    loadGameMenu();
}

async function loadGameMenu() {
    try {
        const res = await fetch('/api/vgui/gamemenu');
        const data = await res.json();
        if (data.items) {
            renderGameMenuItems(data.items);
        }
    } catch (err) {
        console.error("Error al cargar GameMenu:", err);
    }
}

function renderGameMenuItems(items) {
    const list = document.getElementById('gameMenuList');
    const mockup = document.getElementById('gameMenuMockup');
    list.innerHTML = '';
    mockup.innerHTML = '';

    items.forEach((item, idx) => {
        // Fila editable
        const row = document.createElement('div');
        row.className = 'gamemenu-item-row';
        row.innerHTML = `
            <input type="text" class="gm-lbl" value="${item.label}" placeholder="Etiqueta del botón" style="flex:1;">
            <input type="text" class="gm-cmd" value="${item.command}" placeholder="Comando (ej: engine retry)" style="flex:1.2;">
            <button class="btn-danger" onclick="removeGameMenuItem(${idx})">✖</button>
        `;
        row.querySelector('.gm-lbl').addEventListener('input', updateMockupFromInputs);
        row.querySelector('.gm-cmd').addEventListener('input', updateMockupFromInputs);
        list.appendChild(row);

        // Mockup
        if (item.label) {
            const mBtn = document.createElement('div');
            mBtn.className = 'mockup-btn';
            mBtn.textContent = item.label.startsWith('#') ? item.label.replace('#GameUI_GameMenu_', '') : item.label;
            mockup.appendChild(mBtn);
        }
    });
}

function updateMockupFromInputs() {
    const rows = document.querySelectorAll('.gamemenu-item-row');
    const mockup = document.getElementById('gameMenuMockup');
    mockup.innerHTML = '';
    rows.forEach(r => {
        const lbl = r.querySelector('.gm-lbl').value.trim();
        if (lbl) {
            const mBtn = document.createElement('div');
            mBtn.className = 'mockup-btn';
            mBtn.textContent = lbl.startsWith('#') ? lbl.replace('#GameUI_GameMenu_', '') : lbl;
            mockup.appendChild(mBtn);
        }
    });
}

function addGameMenuItem() {
    const list = document.getElementById('gameMenuList');
    const idx = list.children.length;
    const row = document.createElement('div');
    row.className = 'gamemenu-item-row';
    row.innerHTML = `
        <input type="text" class="gm-lbl" value="★ CONECTAR A MI SERVIDOR ★" style="flex:1;">
        <input type="text" class="gm-cmd" value="engine connect 192.168.1.100:27015" style="flex:1.2;">
        <button class="btn-danger" onclick="removeGameMenuItem(${idx})">✖</button>
    `;
    row.querySelector('.gm-lbl').addEventListener('input', updateMockupFromInputs);
    row.querySelector('.gm-cmd').addEventListener('input', updateMockupFromInputs);
    list.appendChild(row);
    updateMockupFromInputs();
}

function removeGameMenuItem(index) {
    const list = document.getElementById('gameMenuList');
    if (list.children[index]) {
        list.children[index].remove();
        updateMockupFromInputs();
    }
}

async function saveGameMenu() {
    const rows = document.querySelectorAll('.gamemenu-item-row');
    const items = [];
    rows.forEach(r => {
        const lbl = r.querySelector('.gm-lbl').value;
        const cmd = r.querySelector('.gm-cmd').value;
        if (lbl || cmd) {
            const item = { label: lbl, command: cmd };
            if (cmd === 'ResumeGame' || cmd === 'Disconnect' || cmd.includes('retry') || cmd.includes('stopsound')) {
                item.OnlyInGame = "1";
            }
            items.push(item);
        }
    });

    LoadingOverlay.show({
        title: "COMPILANDO GAMEMENU.RES",
        step: "Serializando esquema Valve KeyValues...",
        percent: 30,
        engineTag: "VGUI RES COMPILER",
        detail: "[cstrike/resource/GameMenu.res]"
    });

    try {
        LoadingOverlay.setProgress(70, "Escribiendo estructura de menú y creando respaldo previo...", "[RESOURCE PIPELINE]");
        const res = await fetch('/api/vgui/gamemenu', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ items: items })
        });
        const data = await res.json();
        if (data.success) {
            LoadingOverlay.setProgress(100, "¡GameMenu.res actualizado correctamente!", "[STATUS: GUARDADO]");
            showToast("¡cstrike/resource/GameMenu.res guardado con respaldo previo!");
            loadBackups();
            LoadingOverlay.hide(600);
        } else {
            LoadingOverlay.hide(0);
            alert(data.error || "Error al guardar GameMenu.");
        }
    } catch (err) {
        LoadingOverlay.hide(0);
        alert("Error: " + err.message);
    }
}

async function applyHudColor() {
    const hex = document.getElementById('hudSchemeColor').value;
    const r = parseInt(hex.substr(1, 2), 16);
    const g = parseInt(hex.substr(3, 2), 16);
    const b = parseInt(hex.substr(5, 2), 16);

    LoadingOverlay.show({
        title: "APLICANDO COLORES VGUI",
        step: `Inyectando RGB(${r}, ${g}, ${b}) en TrackerScheme.res...`,
        percent: 45,
        engineTag: "TRACKERSCHEME.RES",
        detail: "[PALETA HUD PERSONALIZADA]"
    });

    try {
        const res = await fetch('/api/vgui/scheme', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ r: r, g: g, b: b })
        });
        const data = await res.json();
        if (data.success) {
            LoadingOverlay.setProgress(100, "¡TrackerScheme.res actualizado con éxito!", "[STATUS: HUD CONFIGURADO]");
            showToast("¡Colores de TrackerScheme.res actualizados con éxito!");
            loadBackups();
            LoadingOverlay.hide(600);
        } else {
            LoadingOverlay.hide(0);
        }
    } catch (err) {
        LoadingOverlay.hide(0);
        alert("Error: " + err.message);
    }
}

// ==============================================================================
// 7. MÓDULO 5 & 6: NETCODE, USERCONFIG.CFG & NUMPAD BINDS
// ==============================================================================
function initNetcodeModule() {
    updateCfgPreview();
}

function onNetcodePresetChange() {
    const p = document.getElementById('netcodePreset').value;
    if (p === 'fiber_100k') {
        document.getElementById('cfgRate').value = 100000;
        document.getElementById('cfgUpdate').value = 102;
        document.getElementById('cfgCmd').value = 105;
    } else if (p === 'dsl_50k') {
        document.getElementById('cfgRate').value = 50000;
        document.getElementById('cfgUpdate').value = 80;
        document.getElementById('cfgCmd').value = 80;
    } else if (p === 'classic_25k') {
        document.getElementById('cfgRate').value = 25000;
        document.getElementById('cfgUpdate').value = 60;
        document.getElementById('cfgCmd').value = 60;
    }
    updateCfgPreview();
}

async function updateCfgPreview() {
    const rate = parseInt(document.getElementById('cfgRate').value) || 100000;
    const update = parseInt(document.getElementById('cfgUpdate').value) || 102;
    const cmd = parseInt(document.getElementById('cfgCmd').value) || 105;
    const fps = parseFloat(document.getElementById('cfgFpsMax').value) || 99.5;
    const color = document.getElementById('cfgCrosshairColor').value;
    const raw = document.getElementById('cfgRawInput').checked;
    const dyn = document.getElementById('cfgDynamicCrosshair').checked;

    // Calcular ex_interp = 1 / cl_updaterate
    const interp = (1.0 / update).toFixed(4);
    document.getElementById('cfgInterp').value = interp;

    try {
        const res = await fetch('/api/config/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                rate: rate,
                cl_updaterate: update,
                cl_cmdrate: cmd,
                fps_max: fps,
                crosshair_color: color,
                raw_input: raw,
                crosshair_dynamic: dyn,
                numpad_binds: State.netcode.binds
            })
        });
        const data = await res.json();
        if (data.cfg_text) {
            document.getElementById('cfgCodePreview').value = data.cfg_text;
        }
    } catch (err) {
        console.error("Error al generar vista previa CFG:", err);
    }
}

async function installUserconfig() {
    const text = document.getElementById('cfgCodePreview').value;

    LoadingOverlay.show({
        title: "CONFIGURANDO NETCODE TÁCTICO",
        step: "Calculando ex_interp exacto y vinculando autoexec.cfg...",
        percent: 35,
        engineTag: "NETCODE CALIBRATOR",
        detail: "[EX_INTERP = 1 / CL_UPDATERATE] • [M_RAWINPUT 1]"
    });

    try {
        LoadingOverlay.setProgress(70, "Escribiendo userconfig.cfg y asegurando ejecución con autoexec...", "[INYECCIÓN CSTRIKE/]");
        const res = await fetch('/api/config/install', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cfg_text: text })
        });
        const data = await res.json();
        if (data.success) {
            LoadingOverlay.setProgress(100, "¡userconfig.cfg instalado y respaldado con éxito!", "[STATUS: EJECUCIÓN VINCULADA]");
            showToast("¡userconfig.cfg instalado y vinculado a autoexec.cfg!");
            loadBackups();
            LoadingOverlay.hide(600);
        } else {
            LoadingOverlay.hide(0);
            alert(data.error || "Error al instalar config.");
        }
    } catch (err) {
        LoadingOverlay.hide(0);
        alert("Error: " + err.message);
    }
}

function downloadUserconfig() {
    const text = document.getElementById('cfgCodePreview').value;
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    downloadBlob(blob, "userconfig.cfg");
    showToast("¡userconfig.cfg descargado!");
}

// ==============================================================================
// 7. MÓDULO 6: VISUAL KEYBIND STUDIO (TECLADO 100% INTERACTIVO CS 1.6)
// ==============================================================================
const KEY_BINDS = {};
let currentKeyId = 'w';

const COMPETITIVE_PRESET = {
    "ESCAPE": { cmd: "cancelselect", cat: "c-util" },
    "TAB": { cmd: "+showscores", cat: "c-util" },
    "SPACE": { cmd: "+jump", cat: "c-movement" },
    "CTRL": { cmd: "+duck", cat: "c-movement" },
    "SHIFT": { cmd: "+speed", cat: "c-movement" },
    "`": { cmd: "toggleconsole", cat: "c-util" },
    "w": { cmd: "+forward", cat: "c-movement" },
    "s": { cmd: "+back", cat: "c-movement" },
    "a": { cmd: "+moveleft", cat: "c-movement" },
    "d": { cmd: "+moveright", cat: "c-movement" },
    "q": { cmd: "lastinv", cat: "c-combat" },
    "r": { cmd: "+reload", cat: "c-combat" },
    "e": { cmd: "+use", cat: "c-combat" },
    "g": { cmd: "drop", cat: "c-combat" },
    "f": { cmd: "impulse 100", cat: "c-combat" },
    "t": { cmd: "impulse 201", cat: "c-combat" },
    "b": { cmd: "buy", cat: "c-buy" },
    "h": { cmd: "+commandmenu", cat: "c-util" },
    "1": { cmd: "slot1", cat: "c-combat" },
    "2": { cmd: "slot2", cat: "c-combat" },
    "3": { cmd: "slot3", cat: "c-combat" },
    "4": { cmd: "slot4", cat: "c-combat" },
    "5": { cmd: "slot5", cat: "c-combat" },
    "y": { cmd: "messagemode", cat: "c-comm" },
    "u": { cmd: "messagemode2", cat: "c-comm" },
    "v": { cmd: "+voicerecord", cat: "c-comm" },
    "k": { cmd: "+voicerecord", cat: "c-comm" },
    "z": { cmd: "radio1", cat: "c-comm" },
    "x": { cmd: "radio2", cat: "c-comm" },
    "c": { cmd: "radio3", cat: "c-comm" },
    "F5": { cmd: "snapshot", cat: "c-util" },
    "PAUSE": { cmd: "pause", cat: "c-util" },
    "MOUSE1": { cmd: "+attack", cat: "c-combat" },
    "MOUSE2": { cmd: "+attack2", cat: "c-combat" },
    "MOUSE3": { cmd: "lastinv", cat: "c-combat" },
    "MWHEELUP": { cmd: "+duck", cat: "c-movement" },
    "MWHEELDOWN": { cmd: "+jump", cat: "c-movement" },
    "MOUSE4": { cmd: "+voicerecord", cat: "c-comm" },
    "MOUSE5": { cmd: "drop", cat: "c-combat" },
    // Numpad Compras
    "KP_INS": { cmd: "mp5; primammo", cat: "c-buy" },
    "KP_END": { cmd: "m4a1; ak47; primammo", cat: "c-buy" },
    "KP_DOWNARROW": { cmd: "deagle; secammo", cat: "c-buy" },
    "KP_PGDN": { cmd: "awp; primammo", cat: "c-buy" },
    "KP_LEFTARROW": { cmd: "vesthelm; vest; defuser", cat: "c-buy" },
    "KP_5": { cmd: "famas; galil; primammo", cat: "c-buy" },
    "KP_RIGHTARROW": { cmd: "scout; primammo", cat: "c-buy" },
    "KP_HOME": { cmd: "hegren", cat: "c-buy" },
    "KP_UPARROW": { cmd: "flash", cat: "c-buy" },
    "KP_PGUP": { cmd: "sgren", cat: "c-buy" },
    "KP_ENTER": { cmd: "m4a1; ak47; primammo; defuser; vest", cat: "c-buy" },
    "KP_DEL": { cmd: "vest", cat: "c-buy" },
    "KP_SLASH": { cmd: "defuser", cat: "c-buy" }
};

function initFullKeyboardModule() {
    loadCompetitivePreset();
    updateNumpadLabels();
    renderWeaponsCatalog();
}

function selectKey(keyName) {
    document.querySelectorAll('.key').forEach(el => el.classList.remove('selected'));
    currentKeyId = keyName;

    const el = document.getElementById('k_' + keyName);
    if (el) el.classList.add('selected');

    const titleEl = document.getElementById('editorTitle');
    if (titleEl) titleEl.textContent = `Configurando tecla: [ ${keyName} ]`;
    
    const current = KEY_BINDS[keyName];
    const cmdInput = document.getElementById('customCommandInput');
    const catSelect = document.getElementById('keyCategorySelect');
    const quickSelect = document.getElementById('quickActionSelect');

    if (cmdInput) cmdInput.value = current ? current.cmd : "";
    if (catSelect) catSelect.value = current && current.cat ? current.cat : "";
    if (quickSelect) quickSelect.value = "";
}

function applyPresetAction() {
    const quickSelect = document.getElementById('quickActionSelect');
    if (!quickSelect || !quickSelect.value) return;
    const [cmd, cat] = quickSelect.value.split('|');
    const cmdInput = document.getElementById('customCommandInput');
    const catSelect = document.getElementById('keyCategorySelect');
    if (cmdInput) cmdInput.value = cmd;
    if (catSelect) catSelect.value = cat || "";
}

function saveCurrentKey() {
    if (!currentKeyId) {
        showToast("Primero haz clic en una tecla del teclado visual.");
        return;
    }

    const cmdInput = document.getElementById('customCommandInput');
    const catSelect = document.getElementById('keyCategorySelect');
    const cmd = cmdInput ? cmdInput.value.trim() : "";
    const cat = catSelect ? catSelect.value : "";

    if (!cmd) {
        unbindCurrentKey();
        return;
    }

    KEY_BINDS[currentKeyId] = { cmd, cat };
    renderKeyUI(currentKeyId);
    updateCfgOutput();
    showToast(`Tecla [${currentKeyId}] asignada a: ${cmd}`);
}

function unbindCurrentKey() {
    if (!currentKeyId) return;
    delete KEY_BINDS[currentKeyId];
    renderKeyUI(currentKeyId);
    const cmdInput = document.getElementById('customCommandInput');
    const catSelect = document.getElementById('keyCategorySelect');
    if (cmdInput) cmdInput.value = "";
    if (catSelect) catSelect.value = "";
    updateCfgOutput();
    showToast(`Tecla [${currentKeyId}] desvinculada (unbind).`);
}

function clearAllBinds() {
    if (!confirm("¿Deseas desvincular todas las teclas del teclado visual?")) return;
    for (const key in KEY_BINDS) delete KEY_BINDS[key];
    document.querySelectorAll('.key').forEach(el => {
        const keyName = el.id.replace('k_', '');
        renderKeyUI(keyName);
    });
    const cmdInput = document.getElementById('customCommandInput');
    const catSelect = document.getElementById('keyCategorySelect');
    if (cmdInput) cmdInput.value = "";
    if (catSelect) catSelect.value = "";
    updateCfgOutput();
    showToast("Todos los binds han sido limpiados.");
}

function renderKeyUI(keyName) {
    const el = document.getElementById('k_' + keyName);
    if (!el) return;

    el.className = 'key' + (currentKeyId === keyName ? ' selected' : '');
    const bindSpan = el.querySelector('.key-bind');
    
    if (KEY_BINDS[keyName]) {
        const { cmd, cat } = KEY_BINDS[keyName];
        if (cat) el.classList.add(cat);
        if (bindSpan) {
            bindSpan.textContent = cmd;
            bindSpan.title = cmd;
        }
    } else {
        if (bindSpan) {
            bindSpan.textContent = "";
            bindSpan.title = "";
        }
    }
}

function updateCfgOutput() {
    const outputEl = document.getElementById('cfgOutput');
    if (!outputEl) return;

    let text = "// ====================================================\n";
    text += "// Counter-Strike 1.6 - Binds Configurados (Visual Studio)\n";
    text += "// ====================================================\n\n";
    text += "unbindall\n\n";

    for (const [key, val] of Object.entries(KEY_BINDS)) {
        text += `bind "${key}" "${val.cmd}"\n`;
    }

    outputEl.value = text;
}

function loadCompetitivePreset() {
    for (const key in KEY_BINDS) delete KEY_BINDS[key];
    for (const [k, v] of Object.entries(COMPETITIVE_PRESET)) {
        KEY_BINDS[k] = { ...v };
    }

    document.querySelectorAll('.key').forEach(el => {
        const keyName = el.id.replace('k_', '');
        renderKeyUI(keyName);
    });

    updateCfgOutput();
    selectKey('w');
}

function downloadBindsConfig() {
    const text = document.getElementById('cfgOutput').value;
    const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
    downloadBlob(blob, "binds.cfg");
    showToast("¡binds.cfg descargado con éxito!");
}

async function installBindsToGame() {
    const text = document.getElementById('cfgOutput').value;
    if (!text.trim()) {
        showToast("No hay binds para instalar.");
        return;
    }

    try {
        const res = await fetch('/api/binds/install', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: text })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message || "¡binds.cfg instalado en cstrike/ y vinculado!");
        } else {
            alert(data.error || "No se pudo instalar binds.cfg");
        }
    } catch (err) {
        alert("Error de conexión al instalar binds: " + err.message);
    }
}

function initBuyBindsModule() {
    initFullKeyboardModule();
}


function updateNumpadLabels() {
    Object.keys(State.netcode.binds).forEach(key => {
        const lbl = document.getElementById('lbl_' + key);
        if (lbl) {
            lbl.textContent = State.netcode.binds[key] || "(Vacío)";
            lbl.title = State.netcode.binds[key] || "";
        }
    });
}

function renderWeaponsCatalog(category = 'all', searchQuery = '') {
    const list = document.getElementById('weaponsCatalogList');
    if (!list) return;

    let items = WEAPONS_DATA;
    if (category !== 'all') {
        items = items.filter(w => w.cat === category);
    }
    if (searchQuery && searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        items = items.filter(w => 
            w.name.toLowerCase().includes(q) || 
            w.id.toLowerCase().includes(q) || 
            w.desc.toLowerCase().includes(q)
        );
    }

    if (!items.length) {
        list.innerHTML = `<div style="grid-column:1/-1; text-align:center; color:var(--text-muted); padding:20px; font-size:0.8rem;">No se encontraron armas que coincidan con la búsqueda.</div>`;
        return;
    }

    list.innerHTML = items.map(w => {
        const teamBadge = w.team === 't' ? '<span class="weapon-card-team t">Terroristas</span>' :
                         (w.team === 'ct' ? '<span class="weapon-card-team ct">Antiterroristas</span>' :
                         '<span class="weapon-card-team both">T / CT</span>');
        
        return `
            <div class="weapon-card-item" onclick="onCatalogWeaponClick('${w.id}')" title="Clic para copiar comando o añadir a la tecla activa">
                <div class="weapon-card-header">
                    <span class="weapon-card-name">${w.name}</span>
                    <span class="weapon-card-cost">$${w.cost.toLocaleString()}</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:2px;">
                    <span class="weapon-card-alias"><code>${w.id}</code></span>
                    ${teamBadge}
                </div>
                <div style="font-size:0.72rem; color:var(--text-muted); margin-top:3px; line-height:1.3;">${w.desc}</div>
            </div>
        `;
    }).join('');
}

function filterWeaponsCatalog(category, btn) {
    if (btn) {
        btn.parentElement.querySelectorAll('.cat-pill').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    }
    const q = document.getElementById('weaponCatalogSearch') ? document.getElementById('weaponCatalogSearch').value : '';
    renderWeaponsCatalog(category, q);
}

function searchWeaponsCatalog(query) {
    const activePill = document.querySelector('.weapon-filter-tabs .cat-pill.active');
    const cat = activePill ? (activePill.getAttribute('onclick').match(/'([^']+)'/) || ['','all'])[1] : 'all';
    renderWeaponsCatalog(cat, query);
}

function onCatalogWeaponClick(alias) {
    const buyModal = document.getElementById('buyBindsModal');
    if (buyModal && buyModal.classList.contains('active')) {
        toggleWeaponInModal(alias);
    } else {
        navigator.clipboard.writeText(alias).then(() => {
            showToast(`¡Comando "${alias}" copiado al portapapeles!`);
        });
    }
}

// --- MODAL DE ASIGNACIÓN TÁCTICA PARA TECLAS NUMPAD ---
function openBuyBindModal(key) {
    State.buyBindModal.key = key;

    const raw = State.netcode.binds[key] || "";
    // Separar cadena por ';' y filtrar vacíos
    State.buyBindModal.chain = raw.split(';')
        .map(s => s.trim().replace(/^buy\s+/, ''))
        .filter(Boolean);

    const titleEl = document.getElementById('buyBindsModalTitle');
    const subEl = document.getElementById('buyBindsModalSubtitle');
    const keyNiceName = key.replace('kp_', '').toUpperCase();

    if (titleEl) titleEl.textContent = `Configurar Tecla [${keyNiceName}] del Numpad`;
    if (subEl) subEl.textContent = `Personaliza las armas, granadas y munición para vincular a esta tecla`;

    const rawInput = document.getElementById('buyBindRawInput');
    if (rawInput) rawInput.value = raw;

    renderModalChain();
    renderModalWeapons('all');

    const modal = document.getElementById('buyBindsModal');
    if (modal) modal.classList.add('active');
}

function closeBuyBindModal() {
    const modal = document.getElementById('buyBindsModal');
    if (modal) modal.classList.remove('active');
    State.buyBindModal.key = null;
}

function renderModalChain() {
    const container = document.getElementById('buyBindChainDisplay');
    const costEl = document.getElementById('buyBindTotalCost');
    if (!container) return;

    if (!State.buyBindModal.chain.length) {
        container.innerHTML = `<span style="color:var(--text-muted); font-size:0.78rem;">Ninguna arma seleccionada. Haz clic en las armas abajo o presiona un preset.</span>`;
        if (costEl) costEl.textContent = "Costo Estimado: $0";
        return;
    }

    let totalCost = 0;
    container.innerHTML = State.buyBindModal.chain.map((item, idx) => {
        const weapon = WEAPONS_DATA.find(w => w.id === item.toLowerCase());
        const cost = weapon ? weapon.cost : 0;
        totalCost += cost;
        const name = weapon ? weapon.name : item;

        return `
            <div class="chain-chip">
                <span>${name} <code>(${item})</code></span>
                <span class="remove-chip" onclick="removeChipFromChain(${idx})" title="Quitar">&times;</span>
            </div>
        `;
    }).join('');

    if (costEl) {
        costEl.textContent = `Costo Estimado: $${totalCost.toLocaleString()}`;
    }
}

function removeChipFromChain(index) {
    State.buyBindModal.chain.splice(index, 1);
    updateModalRawInputFromChain();
    renderModalChain();
}

function toggleWeaponInModal(alias) {
    State.buyBindModal.chain.push(alias);
    updateModalRawInputFromChain();
    renderModalChain();
}

function applyPresetToModal(presetCmd) {
    State.buyBindModal.chain = presetCmd.split(';')
        .map(s => s.trim().replace(/^buy\s+/, ''))
        .filter(Boolean);
    updateModalRawInputFromChain();
    renderModalChain();
}

function clearModalBindChain() {
    State.buyBindModal.chain = [];
    updateModalRawInputFromChain();
    renderModalChain();
}

function updateModalRawInputFromChain() {
    const rawInput = document.getElementById('buyBindRawInput');
    if (rawInput) {
        rawInput.value = State.buyBindModal.chain.length ? State.buyBindModal.chain.join('; ') + ';' : '';
    }
}

function syncBuyBindRawInput(text) {
    State.buyBindModal.chain = text.split(';')
        .map(s => s.trim().replace(/^buy\s+/, ''))
        .filter(Boolean);
    renderModalChain();
}

function filterModalWeapons(category, btn) {
    if (btn) {
        btn.parentElement.querySelectorAll('.cat-pill').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    }
    renderModalWeapons(category);
}

function renderModalWeapons(category = 'all') {
    const grid = document.getElementById('modalWeaponsGrid');
    if (!grid) return;

    let items = WEAPONS_DATA;
    if (category !== 'all') {
        items = items.filter(w => w.cat === category);
    }

    grid.innerHTML = items.map(w => {
        const inChain = State.buyBindModal.chain.includes(w.id);
        const teamBadge = w.team === 't' ? '<span class="weapon-card-team t" style="font-size:0.6rem;">T</span>' :
                         (w.team === 'ct' ? '<span class="weapon-card-team ct" style="font-size:0.6rem;">CT</span>' :
                         '<span class="weapon-card-team both" style="font-size:0.6rem;">T/CT</span>');

        return `
            <div class="modal-weapon-card ${inChain ? 'in-chain' : ''}" onclick="toggleWeaponInModal('${w.id}')" title="Añadir ${w.name} a la secuencia">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <b style="font-size:0.75rem; color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${w.name}</b>
                    ${teamBadge}
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:2px;">
                    <code style="color:var(--accent-cyan); font-size:0.7rem;">${w.id}</code>
                    <span style="color:#22c55e; font-weight:800; font-size:0.7rem;">$${w.cost}</span>
                </div>
            </div>
        `;
    }).join('');
}

function saveBuyBindModal() {
    const key = State.buyBindModal.key;
    if (!key) return;

    const rawInput = document.getElementById('buyBindRawInput');
    const finalCmd = rawInput ? rawInput.value.trim() : State.buyBindModal.chain.join('; ') + ';';

    State.netcode.binds[key] = finalCmd;
    const lbl = document.getElementById('lbl_' + key);
    if (lbl) {
        lbl.textContent = finalCmd || "(Vacío)";
        lbl.title = finalCmd;
    }

    updateCfgPreview();
    closeBuyBindModal();
    showToast(`¡Tecla [${key.replace('kp_', '').toUpperCase()}] configurada con éxito!`);
}

function restoreDefaultNumpadBinds() {
    if (!confirm("¿Deseas restaurar la configuración clásica de binds de compra para el Numpad?")) return;

    State.netcode.binds = {
        "kp_ins": "vesthelm; vest;",
        "kp_end": "ak47; m4a1;",
        "kp_downarrow": "awp;",
        "kp_pgdn": "deagle;",
        "kp_leftarrow": "hegren;",
        "kp_5": "flash;",
        "kp_rightarrow": "sgren;",
        "kp_home": "defuser;",
        "kp_uparrow": "primammo; secammo;",
        "kp_pgup": "famas; galil;",
        "kp_plus": "shield;",
        "kp_enter": "hegren; flash; flash; sgren; defuser; vesthelm;",
        "kp_del": "usp;"
    };

    updateNumpadLabels();
    updateCfgPreview();
    showToast("¡Binds numpad restaurados al perfil competitivo oficial!");
}

function applyNumpadBindsToConfig() {
    updateCfgPreview();
    switchTab('netcode');
    showToast("¡Binds de compra aplicados a la configuración userconfig.cfg!");
}

// ==============================================================================
// 8. MÓDULO 10: MANUAL & ENCICLOPEDIA DE COMANDOS GOLDRSC
// ==============================================================================
function initManualModule() {
    filterManualCommands();
}

function setManualCategory(category, btn) {
    State.manual.activeCat = category;
    if (btn) {
        btn.parentElement.querySelectorAll('.cat-pill').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    }
    filterManualCommands();
}

function filterManualCommands() {
    const input = document.getElementById('manualSearchInput');
    const query = input ? input.value.toLowerCase().trim() : '';
    const cat = State.manual.activeCat || 'all';

    let list = COMMANDS_MANUAL_DATA;
    if (cat !== 'all') {
        list = list.filter(c => c.cat === cat);
    }
    if (query) {
        list = list.filter(c => 
            c.cmd.toLowerCase().includes(query) || 
            c.name.toLowerCase().includes(query) || 
            c.desc.toLowerCase().includes(query) ||
            (c.recom && c.recom.toLowerCase().includes(query))
        );
    }

    const badge = document.getElementById('manualStatsBadge');
    if (badge) {
        badge.textContent = `Mostrando ${list.length} de ${COMMANDS_MANUAL_DATA.length} comandos`;
    }

    const grid = document.getElementById('manualCommandsGrid');
    if (!grid) return;

    if (!list.length) {
        grid.innerHTML = `<div style="grid-column:1/-1; text-align:center; color:var(--text-muted); padding:30px; font-size:0.85rem;">No se encontraron comandos para la búsqueda "${query}".</div>`;
        return;
    }

    grid.innerHTML = list.map(item => {
        const catMap = {
            'netcode': { label: 'Netcode', cls: 'netcode' },
            'weapons': { label: 'Armas y Compra', cls: 'weapons' },
            'visuals': { label: 'Mira y HUD', cls: 'visuals' },
            'video': { label: 'Gráficos y FPS', cls: 'video' },
            'audio': { label: 'Audio y Mic', cls: 'audio' },
            'server': { label: 'Servidor y Bots', cls: 'server' }
        };
        const cInfo = catMap[item.cat] || { label: item.cat, cls: 'netcode' };

        return `
            <div class="manual-cmd-card">
                <div class="cmd-card-header">
                    <div>
                        <div class="cmd-code-title">${item.cmd}</div>
                        <div style="font-size:0.75rem; font-weight:700; color:#fff; margin-top:2px;">${item.name}</div>
                    </div>
                    <span class="cmd-badge ${cInfo.cls}">${cInfo.label}</span>
                </div>

                <div class="cmd-recom-box">
                    💡 Valor Recomendado: <span>${item.recom}</span>
                </div>

                <div class="cmd-description">
                    ${item.desc}
                </div>

                <div class="cmd-actions-row">
                    <button class="btn-secondary" style="padding:4px 10px; font-size:0.72rem;" onclick="copyCommand('${item.cmd.replace(/"/g, '&quot;')}')">
                        📋 Copiar
                    </button>
                    <button class="btn-primary" style="width:auto; padding:4px 12px; font-size:0.72rem;" onclick="addCommandToUserconfig('${item.cmd.replace(/"/g, '&quot;')}')">
                        ➕ Añadir a CFG
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function copyCommand(cmdText) {
    navigator.clipboard.writeText(cmdText).then(() => {
        showToast(`¡Comando "${cmdText}" copiado al portapapeles!`);
    });
}

function addCommandToUserconfig(cmdText) {
    const editor = document.getElementById('cfgCodePreview');
    if (!editor) return;

    editor.value += `\n${cmdText}`;
    switchTab('netcode');
    showToast(`¡Comando "${cmdText}" añadido al editor de userconfig.cfg!`);
}

// ==============================================================================
// 8. MÓDULO 7: COMMANDMENU [H]
// ==============================================================================
function initCommandMenuModule() {
    loadDefaultCommandMenu();
}

function loadDefaultCommandMenu() {
    State.cmdMenu = [
        {
            title: "⚡ Rates y Netcode",
            children: [
                { title: "100k Fibra Óptica / LAN", cmd: "rate 100000; cl_updaterate 102; cl_cmdrate 105; ex_interp 0.0098; echo [Rates] 100k aplicado" },
                { title: "50k Banda Ancha / DSL", cmd: "rate 50000; cl_updaterate 80; cl_cmdrate 80; ex_interp 0.0125; echo [Rates] 50k aplicado" },
                { title: "25k Servidores Clásicos", cmd: "rate 25000; cl_updaterate 60; cl_cmdrate 60; ex_interp 0.0167; echo [Rates] 25k aplicado" },
            ]
        },
        {
            title: "🎯 Ajustes de Mira",
            children: [
                { title: "Verde Neón (Estándar)", cmd: "cl_crosshair_color 0 255 0" },
                { title: "Amarillo Ámbar", cmd: "cl_crosshair_color 255 200 0" },
                { title: "Azul Eléctrico", cmd: "cl_crosshair_color 0 180 255" },
                { title: "Rojo Táctico", cmd: "cl_crosshair_color 255 0 0" },
                { title: "Mira Pequeña (Small)", cmd: "cl_crosshair_size small" },
                { title: "Mira Estática", cmd: "cl_dynamiccrosshair 0" },
                { title: "Mira Dinámica", cmd: "cl_dynamiccrosshair 1" },
            ]
        },
        {
            title: "🔊 Audio y Utilidades",
            children: [
                { title: "Silenciar Bugeos (stopsound)", cmd: "stopsound; echo [Audio] Sonidos detenidos" },
                { title: "Volumen 100%", cmd: "volume 1.0" },
                { title: "Volumen 50%", cmd: "volume 0.5" },
                { title: "Reiniciar Sonido (snd_restart)", cmd: "snd_restart" },
                { title: "Limpiar Sangre/Decals", cmd: "r_decals 0; r_decals 300" },
            ]
        },
        {
            title: "🛠️ Servidor Local y Práctica",
            children: [
                { title: "Reiniciar Ronda (sv_restart 1)", cmd: "sv_restart 1" },
                { title: "Dinero al Máximo ($16.000)", cmd: "mp_startmoney 16000; sv_restart 1" },
                { title: "Gravedad Baja (400)", cmd: "sv_gravity 400" },
                { title: "Gravedad Normal (800)", cmd: "sv_gravity 800" },
            ]
        },
        {
            title: "🤖 Control de Bots",
            children: [
                { title: "Añadir Bot Terrorista", cmd: "bot_add_t" },
                { title: "Añadir Bot CT", cmd: "bot_add_ct" },
                { title: "Matar Todos los Bots", cmd: "bot_kill" },
                { title: "Expulsar Bots", cmd: "bot_kick" },
            ]
        }
    ];
    renderCommandMenuTree();
}

function renderCommandMenuTree() {
    const container = document.getElementById('cmdMenuTreeView');
    container.innerHTML = '';

    State.cmdMenu.slice(0, 9).forEach((cat, catIdx) => {
        const catBox = document.createElement('div');
        catBox.className = 'card';
        catBox.style.padding = '12px';
        catBox.style.background = '#0e121a';

        catBox.innerHTML = `
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <b>${catIdx + 1}. ${cat.title}</b>
                <div>
                    <button class="btn-secondary" style="padding:2px 8px; font-size:0.7rem;" onclick="addCommandMenuSubItem(${catIdx})">➕ Opción</button>
                    <button class="btn-danger" style="padding:2px 6px; font-size:0.7rem;" onclick="removeCommandMenuCat(${catIdx})">✖</button>
                </div>
            </div>
            <div class="subitems-list" style="margin-top:8px; display:flex; flex-direction:column; gap:4px; margin-left:14px;">
                ${cat.children.slice(0, 9).map((sub, subIdx) => `
                    <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#cbd5e1; background:#141822; padding:4px 8px; border-radius:4px;">
                        <span>${subIdx + 1}. ${sub.title} <i>(${sub.cmd})</i></span>
                        <span style="color:#ef4444; cursor:pointer;" onclick="removeCommandMenuSub(${catIdx}, ${subIdx})">&times;</span>
                    </div>
                `).join('')}
            </div>
        `;
        container.appendChild(catBox);
    });

    updateCommandMenuPreview();
}

function addCommandMenuCategory() {
    if (State.cmdMenu.length >= 9) {
        alert("Límite ergonómico alcanzado: máximo 9 categorías por nivel para evitar paginación numérica en CS 1.6.");
        return;
    }
    const title = prompt("Título de la nueva categoría (Nivel 1):", "Utilidades Extra");
    if (title) {
        State.cmdMenu.push({ title: title, children: [] });
        renderCommandMenuTree();
    }
}

function removeCommandMenuCat(index) {
    State.cmdMenu.splice(index, 1);
    renderCommandMenuTree();
}

function addCommandMenuSubItem(catIdx) {
    if (State.cmdMenu[catIdx].children.length >= 9) {
        alert("Límite ergonómico alcanzado: máximo 9 opciones por sub-menú.");
        return;
    }
    const title = prompt("Nombre de la opción:", "Mi Opción");
    if (!title) return;
    const cmd = prompt("Comando de consola a ejecutar:", "say Hola mundo");
    if (cmd) {
        State.cmdMenu[catIdx].children.push({ title: title, cmd: cmd });
        renderCommandMenuTree();
    }
}

function removeCommandMenuSub(catIdx, subIdx) {
    State.cmdMenu[catIdx].children.splice(subIdx, 1);
    renderCommandMenuTree();
}

async function updateCommandMenuPreview() {
    try {
        const res = await fetch('/api/commandmenu/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tree: State.cmdMenu })
        });
        const data = await res.json();
        if (data.text) {
            document.getElementById('cmdMenuPreviewText').value = data.text;
        }
    } catch (err) {
        console.error("Error al generar preview de commandmenu:", err);
    }
}

async function installCommandMenu() {
    LoadingOverlay.show({
        title: "COMPILANDO COMMANDMENU [H]",
        step: "Construyendo estructura jerárquica ergonómica...",
        percent: 30,
        engineTag: "COMMANDMENU ENGINE",
        detail: "[ÁRBOL DE COMANDOS: MÁX 9 POR NIVEL]"
    });

    try {
        LoadingOverlay.setProgress(70, "Escribiendo commandmenu.txt en cstrike/ y respaldando...", "[INYECCIÓN CSTRIKE/]");
        const res = await fetch('/api/commandmenu/install', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tree: State.cmdMenu })
        });
        const data = await res.json();
        if (data.success) {
            LoadingOverlay.setProgress(100, "¡commandmenu.txt instalado correctamente!", "[STATUS: EN-GAME LISTO [H]]");
            showToast("¡commandmenu.txt instalado en cstrike/ con éxito!");
            loadBackups();
            LoadingOverlay.hide(600);
        } else {
            LoadingOverlay.hide(0);
            alert(data.error || "Error al instalar commandmenu.");
        }
    } catch (err) {
        LoadingOverlay.hide(0);
        alert("Error: " + err.message);
    }
}

function downloadCommandMenu() {
    const text = document.getElementById('cmdMenuPreviewText').value;
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    downloadBlob(blob, "commandmenu.txt");
    showToast("¡commandmenu.txt descargado!");
}

// ==============================================================================
// 9. MÓDULO 8: STEAM LAUNCHER
// ==============================================================================
function initSteamLauncherModule() {
    updateLaunchArgs();
}

async function updateLaunchArgs() {
    const freq = document.getElementById('launchFreq').value;
    const res = document.getElementById('launchRes').value.split('x');
    const noforce = document.getElementById('launchNoforce').checked;
    const novid = document.getElementById('launchNovid').checked;
    const nojoy = document.getElementById('launchNojoy').checked;
    const opengl = document.getElementById('launchGl').checked;

    try {
        const r = await fetch('/api/steam/generate_args', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                width: parseInt(res[0]),
                height: parseInt(res[1]),
                freq: parseInt(freq),
                noforce: noforce,
                novid: novid,
                nojoy: nojoy,
                opengl: opengl
            })
        });
        const data = await r.json();
        if (data.args) {
            document.getElementById('launchArgsDisplay').textContent = data.args;
        }
    } catch (err) {
        console.error("Error al calcular launch options:", err);
    }
}

function copyLaunchArgs() {
    const args = document.getElementById('launchArgsDisplay').textContent;
    navigator.clipboard.writeText(args).then(() => {
        showToast("¡Parámetros copiados al portapapeles!");
    });
}

async function launchGameDirect() {
    const argsEl = document.getElementById('launchArgsDisplay');
    const args = argsEl ? argsEl.textContent.trim() : '';
    const modeSelect = document.getElementById('launchModeSelect');
    const mode = modeSelect ? modeSelect.value : 'auto';
    const serverInput = document.getElementById('launchServerInput');
    const connect_server = serverInput ? serverInput.value.trim() : '';

    const isNoSteam = mode === 'nosteam' || (mode === 'auto' && !State.isSteam);
    const modeLabel = isNoSteam ? "NO-STEAM DIRECTO" : "STEAM OFICIAL";

    LoadingOverlay.show({
        title: `LANZANDO COUNTER-STRIKE 1.6`,
        step: isNoSteam ? "Iniciando hl.exe -game cstrike en modo No-Steam..." : "Verificando Steam y despachando argumentos...",
        percent: 35,
        engineTag: `MODO: ${modeLabel}`,
        detail: connect_server ? `[CONECTANDO AUTOMÁTICAMENTE A: ${connect_server}]` : "[SINCRONIZANDO GOLDRSC ENGINE]"
    });

    try {
        LoadingOverlay.setProgress(70, "Inyectando parámetros de vídeo y refresco...", "[PARÁMETROS APLICADOS]");
        const res = await fetch('/api/steam/launch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                args: args,
                mode: mode,
                connect_server: connect_server
            })
        });
        const data = await res.json();
        if (data.success) {
            LoadingOverlay.setProgress(100, `¡CS 1.6 ejecutado en modo ${data.mode || modeLabel}!`, "[PROCESO ACTIVO]");
            showToast(data.message || `¡Counter-Strike 1.6 lanzado con éxito (${data.mode})!`);
            LoadingOverlay.hide(700);
        } else {
            LoadingOverlay.hide(0);
            alert(data.error || "No se pudo lanzar el juego.");
        }
    } catch (err) {
        LoadingOverlay.hide(0);
        alert("Error de conexión al lanzar: " + err.message);
    }
}

function launchGameQuick() {
    launchGameDirect();
}

async function fixMasterServers() {
    LoadingOverlay.show({
        title: "REPARANDO LISTA DE SERVIDORES DE INTERNET",
        step: "Descargando e inyectando MasterServers.vdf actualizado...",
        percent: 30,
        engineTag: "NO-STEAM SERVER FIXER",
        detail: "[CONFIGURANDO MASTERSERVERS]"
    });

    try {
        LoadingOverlay.setProgress(70, "Aplicando atributo Solo Lectura (+R) para evitar corrupción...", "[BLOQUEANDO ARCHIVO]");
        const res = await fetch('/api/launcher/fix_masterservers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (data.success) {
            LoadingOverlay.setProgress(100, "¡MasterServers.vdf reparado y bloqueado con éxito!", "[STATUS: SERVIDORES ACTIVOS]");
            showToast(data.message || "¡Lista de servidores de Internet reparada con éxito!");
            LoadingOverlay.hide(600);
        } else {
            LoadingOverlay.hide(0);
            alert(data.error || "No se pudo reparar MasterServers.vdf.");
        }
    } catch (err) {
        LoadingOverlay.hide(0);
        alert("Error al reparar servidores: " + err.message);
    }
}

// ==============================================================================
// 10. MÓDULO 9: SNAPSHOTS & ROLLBACK
// ==============================================================================
async function loadBackups() {
    try {
        const res = await fetch('/api/backups');
        const data = await res.json();
        if (data.backups) {
            renderBackups(data.backups);
            document.getElementById('backupCount').textContent = data.backups.length;
        }
    } catch (err) {
        console.error("Error al cargar respaldos:", err);
    }
}

function renderBackups(backups) {
    const tbody = document.getElementById('snapshotsTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    if (!backups.length) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-muted); padding:20px;">No hay snapshots aún. El estudio creará uno automáticamente cada vez que instales un mod o config.</td></tr>`;
        return;
    }

    backups.forEach(b => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><code>${b.timestamp}</code></td>
            <td><span class="badge cyan">${b.action}</span></td>
            <td><b>${b.rel_path}</b></td>
            <td>${b.size_bytes ? Math.round(b.size_bytes / 1024) + ' KB' : 'Nuevo (no existía)'}</td>
            <td>
                <button class="btn-danger" style="padding:4px 10px;" onclick="rollbackSingle('${b.id}')">
                    ⏪ Revertir
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function rollbackSingle(entryId) {
    if (!confirm("¿Deseas revertir este archivo a su estado original anterior?")) return;

    LoadingOverlay.show({
        title: "ROLLBACK DE SNAPSHOT",
        step: "Extrayendo archivo original desde cstrike/backup_studio/...",
        percent: 45,
        engineTag: "ROLLBACK ENGINE",
        detail: "[RESTAURACIÓN DE ARCHIVO]"
    });

    try {
        LoadingOverlay.setProgress(75, "Restaurando bytes y sincronizando atributos...", "[SOBRESCRIBIENDO ESTADO]");
        const res = await fetch('/api/rollback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ entry_id: entryId })
        });
        const data = await res.json();
        if (data.success) {
            LoadingOverlay.setProgress(100, "¡Archivo restaurado al estado original!", "[STATUS: ROLLBACK EXITOSO]");
            showToast("¡Archivo restaurado al estado original!");
            loadBackups();
            LoadingOverlay.hide(600);
        } else {
            LoadingOverlay.hide(0);
            alert(data.error || "Error al revertir.");
        }
    } catch (err) {
        LoadingOverlay.hide(0);
        alert("Error: " + err.message);
    }
}

async function rollbackAllSnapshots() {
    if (!confirm("⚠️ ¿Estás seguro de que deseas revertir TODOS los archivos modificados a su estado original?")) return;

    LoadingOverlay.show({
        title: "REVERSIÓN TOTAL DE SNAPSHOTS",
        step: "Restaurando todos los archivos modificados al estado original de Valve...",
        percent: 30,
        engineTag: "MASS ROLLBACK ENGINE",
        detail: "[RESTAURACIÓN COLECTIVA]"
    });

    try {
        LoadingOverlay.setProgress(70, "Copiando versiones respaldadas y limpiando temporales...", "[PROCESANDO LOTE]");
        const res = await fetch('/api/rollback_all', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            LoadingOverlay.setProgress(100, `¡Se revirtieron ${data.restored_count} archivos con éxito!`, "[STATUS: SISTEMA RESTAURADO]");
            showToast(`¡Se revirtieron ${data.restored_count} archivos con éxito!`);
            loadBackups();
            LoadingOverlay.hide(600);
        } else {
            LoadingOverlay.hide(0);
            alert("Errores durante la reversión: " + (data.errors || []).join(", "));
        }
    } catch (err) {
        LoadingOverlay.hide(0);
        alert("Error: " + err.message);
    }
}

// ==============================================================================
// 9. MÓDULO 11: BOOSTER DE LATENCIA Y DEMONIO DE RENDIMIENTO
// ==============================================================================
function initBoosterModule() {
    fetchBoosterStatus();
    // Sondeo de estado cada 4 segundos si la pestaña o subpestaña está activa
    setInterval(() => {
        const boosterSub = document.getElementById('modpane-lia-booster');
        const boosterPane = document.getElementById('tab-booster');
        const liaPane = document.getElementById('tab-launcher-ia');
        if ((boosterSub && boosterSub.classList.contains('active') && liaPane && liaPane.classList.contains('active')) ||
            (boosterPane && boosterPane.classList.contains('active'))) {
            fetchBoosterStatus();
        }
    }, 4000);
}


async function fetchBoosterStatus() {
    try {
        const res = await fetch('/api/booster/status');
        if (!res.ok) return;
        const data = await res.json();
        updateBoosterUI(data);
    } catch (err) {
        console.warn("Aviso al consultar estado del booster:", err);
    }
}

function updateBoosterUI(data) {
    State.booster.active = data.active;
    State.booster.timer_1ms = data.timer_1ms;
    State.booster.hl_detected = data.hl_detected;

    const led = document.getElementById('boosterLed');
    const title = document.getElementById('boosterStatusTitle');
    const desc = document.getElementById('boosterStatusDesc');
    const toggleBtn = document.getElementById('boosterToggleBtn');

    if (led && title && desc && toggleBtn) {
        if (data.hl_detected) {
            led.className = 'booster-led detected';
            title.textContent = `¡Counter-Strike 1.6 Activo! (PID: ${data.hl_pid})`;
            desc.textContent = "Prioridad ALTA y Afinidad de Cores 1, 2 y 3 inyectadas.";
        } else if (data.active) {
            led.className = 'booster-led active';
            title.textContent = "Demonio Activo en Segundo Plano";
            desc.textContent = "Monitoreando hl.exe a 0% de uso de CPU (Sondeo cada 3s).";
        } else {
            led.className = 'booster-led';
            title.textContent = "Demonio en Reposo (Inactivo)";
            desc.textContent = "Presiona 'Iniciar Demonio' o ejecuta iniciar_booster.vbs.";
        }

        toggleBtn.textContent = data.active ? "⏹️ DETENER DEMONIO" : "▶️ INICIAR DEMONIO";
        toggleBtn.className = data.active ? "btn-danger" : "btn-primary";
    }

    // Timer WinMM
    const timerVal = document.getElementById('boosterTimerVal');
    const btnToggleTimer = document.getElementById('btnToggleTimer');
    if (timerVal) {
        timerVal.textContent = data.timer_1ms ? "1.0 ms (Tickrate Estable)" : "15.6 ms (Por defecto SO)";
        timerVal.style.color = data.timer_1ms ? "var(--accent-gold)" : "#94a3b8";
    }
    if (btnToggleTimer) {
        btnToggleTimer.textContent = data.timer_1ms ? "Restaurar a 15.6ms" : "Fijar a 1.0 ms";
    }

    // hl.exe process & priority
    const procVal = document.getElementById('boosterProcessVal');
    const pidVal = document.getElementById('boosterPidVal');
    const prioVal = document.getElementById('boosterPriorityVal');
    const affVal = document.getElementById('boosterAffinityVal');

    if (procVal) procVal.textContent = data.hl_detected ? "Ejecutándose" : "No detectado";
    if (pidVal) pidVal.textContent = data.hl_pid ? `PID: ${data.hl_pid}` : "Esperando juego...";
    if (prioVal) {
        prioVal.textContent = data.priority_boosted ? "ALTA (HIGH_PRIORITY_CLASS)" : "NORMAL";
        prioVal.style.color = data.priority_boosted ? "#22c55e" : "#94a3b8";
    }
    if (affVal) affVal.textContent = data.affinity_hex ? `Máscara ${data.affinity_hex} (Cores 1, 2, 3)` : "Cores sin aislar";

    // Log terminal
    const terminal = document.getElementById('boosterLogTerminal');
    if (terminal && data.log && data.log.length) {
        terminal.textContent = data.log.join('\n');
        terminal.scrollTop = terminal.scrollHeight;
    }
}

async function toggleBoosterDaemon() {
    try {
        const nextState = !State.booster.active;
        const res = await fetch('/api/booster/toggle', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enable: nextState })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.active ? "¡Demonio CS 1.6 Booster activado!" : "Demonio Booster detenido.");
            fetchBoosterStatus();
        }
    } catch (err) {
        alert("Error al alternar demonio: " + err.message);
    }
}

async function toggleSystemTimer() {
    try {
        const nextTimer = !State.booster.timer_1ms;
        const res = await fetch('/api/booster/timer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enable: nextTimer })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.timer_1ms ? "¡Reloj WinMM fijado a 1.0 ms exactos (1000 Hz)!" : "Reloj WinMM restaurado al valor estándar.");
            fetchBoosterStatus();
        }
    } catch (err) {
        alert("Error de timer: " + err.message);
    }
}

async function purgeRamWorkingSet() {
    try {
        const res = await fetch('/api/booster/trim_ram', { method: 'POST' });
        const data = await res.json();
        showToast(data.message || "¡Memoria RAM purgada!");
        const ramVal = document.getElementById('boosterRamVal');
        if (ramVal) ramVal.textContent = "Purgada (" + new Date().toLocaleTimeString() + ")";
    } catch (err) {
        alert("Error al purgar memoria: " + err.message);
    }
}

async function applyWindowsRegistryFix() {
    if (!confirm("¿Deseas aplicar las optimizaciones de baja latencia al Registro de Windows (desactivar Nagle, Delayed ACK y Throttling)?")) return;
    try {
        const res = await fetch('/api/booster/apply_reg', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast("¡Registro de Windows optimizado con éxito!");
            fetchBoosterStatus();
        } else {
            alert("Aviso: " + (data.error || data.message || "Requiere permisos de Administrador"));
        }
    } catch (err) {
        alert("Error al aplicar registro: " + err.message);
    }
}


// ==============================================================================
// 10. MÓDULO 12: AI TACTICAL COACH & TELEMETRÍA (ZERO-BAN / VAC-SAFE)
// ==============================================================================
function initTelemetryModule() {
    loadTelemetryDashboard();
    // Polling regular cuando la pestaña o subpestaña de telemetría está abierta
    setInterval(() => {
        const telemetrySub = document.getElementById('modpane-lia-telemetry');
        const telemetryPane = document.getElementById('tab-telemetry');
        const liaPane = document.getElementById('tab-launcher-ia');
        if ((telemetrySub && telemetrySub.classList.contains('active') && liaPane && liaPane.classList.contains('active')) ||
            (telemetryPane && telemetryPane.classList.contains('active'))) {
            loadTelemetryDashboard(true);
        }
    }, 5000);
}


async function loadTelemetryDashboard(silent = false) {
    try {
        const [statsRes, coachRes] = await Promise.all([
            fetch('/api/telemetry/stats'),
            fetch('/api/telemetry/coach')
        ]);

        if (statsRes.ok) {
            const statsData = await statsRes.json();
            if (statsData.success && statsData.metrics) {
                State.telemetry.metrics = statsData.metrics;
                renderTelemetryRibbon(statsData.metrics);
                drawSkillsRadar(statsData.metrics.radar || {});
                renderHitmap(statsData.metrics.hitbox_given || {}, statsData.metrics.hitbox_taken || {});
                renderRoundTimeline(statsData.metrics.round_history || []);
            }
        }

        if (coachRes.ok) {
            const coachData = await coachRes.json();
            if (coachData.success) {
                renderCoachDiagnoses(coachData.diagnoses || []);
                renderPracticeRoutines(coachData.routines || []);
            }
        }
    } catch (err) {
        if (!silent) console.warn("Aviso al cargar telemetría:", err);
    }
}

function renderTelemetryRibbon(m) {
    const cs = document.getElementById('tCombatScore');
    const kd = document.getElementById('tKdRatio');
    const kdSub = document.getElementById('tKillsDeaths');
    const hs = document.getElementById('tHsPct');
    const hsSub = document.getElementById('tHsCount');
    const adr = document.getElementById('tAdr');
    const kast = document.getElementById('tKastPct');
    const opWin = document.getElementById('tOpeningWinrate');
    const opSub = document.getElementById('tOpeningCount');

    if (cs) cs.textContent = m.combat_score || 0;
    if (kd) kd.textContent = (m.kd_ratio || 0).toFixed(2);
    if (kdSub) kdSub.textContent = `${m.kills || 0} K / ${m.deaths || 0} D`;
    if (hs) hs.textContent = `${m.hs_pct || 0}%`;
    if (hsSub) hsSub.textContent = `${m.headshots || 0} Headshots`;
    if (adr) adr.textContent = m.adr || 0;
    if (kast) kast.textContent = `${m.kast_pct || 0}%`;
    if (opWin) opWin.textContent = `${m.opening_winrate || 0}%`;
    if (opSub) opSub.textContent = `${m.opening_won || 0} Gan / ${m.opening_lost || 0} Per`;
}

function drawSkillsRadar(radar) {
    const canvas = document.getElementById('skillsRadarCanvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const cx = w / 2;
    const cy = h / 2;
    const radius = Math.min(cx, cy) - 38;

    const axes = [
        { key: 'aim', label: 'Puntería', val: radar.aim || 50, color: '#f5a623' },
        { key: 'survival', label: 'Supervivencia', val: radar.survival || 50, color: '#22c55e' },
        { key: 'utility', label: 'Utilidad', val: radar.utility || 50, color: '#38bdf8' },
        { key: 'economy', label: 'Economía', val: radar.economy || 50, color: '#c084fc' },
        { key: 'positioning', label: 'Posición', val: radar.positioning || 50, color: '#ff6a00' }
    ];

    // Actualizar leyenda
    const elAim = document.getElementById('rAimVal');
    const elSurv = document.getElementById('rSurvVal');
    const elUtil = document.getElementById('rUtilVal');
    const elEcon = document.getElementById('rEconVal');
    const elPos = document.getElementById('rPosVal');
    if (elAim) elAim.textContent = axes[0].val;
    if (elSurv) elSurv.textContent = axes[1].val;
    if (elUtil) elUtil.textContent = axes[2].val;
    if (elEcon) elEcon.textContent = axes[3].val;
    if (elPos) elPos.textContent = axes[4].val;

    const numAxes = axes.length;
    const angleStep = (Math.PI * 2) / numAxes;

    // 1. Dibujar círculos concéntricos de referencia (25%, 50%, 75%, 100%)
    const levels = [0.25, 0.5, 0.75, 1.0];
    levels.forEach(lvl => {
        ctx.beginPath();
        for (let i = 0; i < numAxes; i++) {
            const angle = i * angleStep - Math.PI / 2;
            const x = cx + Math.cos(angle) * (radius * lvl);
            const y = cy + Math.sin(angle) * (radius * lvl);
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.closePath();
        ctx.strokeStyle = lvl === 1.0 ? 'rgba(255, 255, 255, 0.18)' : 'rgba(255, 255, 255, 0.07)';
        ctx.lineWidth = 1;
        ctx.stroke();
    });

    // 2. Líneas radiales de cada eje
    for (let i = 0; i < numAxes; i++) {
        const angle = i * angleStep - Math.PI / 2;
        const x = cx + Math.cos(angle) * radius;
        const y = cy + Math.sin(angle) * radius;
        ctx.beginPath();
        ctx.moveTo(cx, cy);
        ctx.lineTo(x, y);
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
        ctx.stroke();

        // Etiquetas
        const lx = cx + Math.cos(angle) * (radius + 20);
        const ly = cy + Math.sin(angle) * (radius + 18);
        ctx.font = 'bold 11px sans-serif';
        ctx.fillStyle = axes[i].color;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(axes[i].label, lx, ly);
    }

    // 3. Polígono de estadísticas del jugador
    ctx.beginPath();
    for (let i = 0; i < numAxes; i++) {
        const angle = i * angleStep - Math.PI / 2;
        const r = (axes[i].val / 100.0) * radius;
        const x = cx + Math.cos(angle) * r;
        const y = cy + Math.sin(angle) * r;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    }
    ctx.closePath();

    // Relleno gradiente con resplandor
    ctx.fillStyle = 'rgba(245, 166, 35, 0.25)';
    ctx.fill();
    ctx.strokeStyle = '#f5a623';
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // 4. Vértices en cada punto de habilidad
    for (let i = 0; i < numAxes; i++) {
        const angle = i * angleStep - Math.PI / 2;
        const r = (axes[i].val / 100.0) * radius;
        const x = cx + Math.cos(angle) * r;
        const y = cy + Math.sin(angle) * r;
        ctx.beginPath();
        ctx.arc(x, y, 4.5, 0, Math.PI * 2);
        ctx.fillStyle = '#fff';
        ctx.fill();
        ctx.strokeStyle = axes[i].color;
        ctx.lineWidth = 2;
        ctx.stroke();
    }
}

function renderHitmap(given, taken) {
    const zgHead = document.getElementById('zgHeadVal');
    const zgChest = document.getElementById('zgChestVal');
    const zgStomach = document.getElementById('zgStomachVal');
    const zgArms = document.getElementById('zgArmsVal');
    const zgLegs = document.getElementById('zgLegsVal');

    if (zgHead) zgHead.textContent = (given.head || 0) + ' dmg';
    if (zgChest) zgChest.textContent = (given.chest || 0) + ' dmg';
    if (zgStomach) zgStomach.textContent = (given.stomach || 0) + ' dmg';
    if (zgArms) zgArms.textContent = (given.arms || 0) + ' dmg';
    if (zgLegs) zgLegs.textContent = (given.legs || 0) + ' dmg';

    const ztHead = document.getElementById('ztHeadVal');
    const ztChest = document.getElementById('ztChestVal');
    const ztStomach = document.getElementById('ztStomachVal');
    const ztArms = document.getElementById('ztArmsVal');
    const ztLegs = document.getElementById('ztLegsVal');

    if (ztHead) ztHead.textContent = (taken.head || 0) + ' dmg';
    if (ztChest) ztChest.textContent = (taken.chest || 0) + ' dmg';
    if (ztStomach) ztStomach.textContent = (taken.stomach || 0) + ' dmg';
    if (ztArms) ztArms.textContent = (taken.arms || 0) + ' dmg';
    if (ztLegs) ztLegs.textContent = (taken.legs || 0) + ' dmg';
}

function renderRoundTimeline(rounds) {
    const list = document.getElementById('roundHistoryList');
    if (!list) return;

    if (!rounds || !rounds.length) {
        list.innerHTML = `<div style="text-align:center; color:var(--text-muted); padding:20px; font-size:0.8rem;">Ninguna ronda registrada en esta sesión todavía.</div>`;
        return;
    }

    list.innerHTML = rounds.map(r => {
        const isWin = !r.died || (r.kills >= 2);
        const winCls = isWin ? 'win' : 'loss';
        const statusText = isWin ? '👑 Ronda Positiva' : '💀 Ronda Difícil';
        const kastBadge = r.kast ? '<span style="color:#22c55e; font-weight:800;">[KAST ✔]</span>' : '<span style="color:#94a3b8;">[-]</span>';

        return `
            <div class="round-history-row ${winCls}">
                <div>
                    <b>Ronda ${r.round}:</b> <span>${statusText}</span>
                </div>
                <div style="display:flex; gap:12px; align-items:center;">
                    <span><b>${r.kills}</b> Kills</span>
                    <span><b>${r.damage}</b> Daño</span>
                    ${kastBadge}
                </div>
            </div>
        `;
    }).join('');
}

function renderCoachDiagnoses(diagnoses) {
    const list = document.getElementById('coachDiagnosesList');
    if (!list) return;

    if (!diagnoses || !diagnoses.length) {
        list.innerHTML = `<div style="text-align:center; color:var(--text-muted); padding:20px; font-size:0.8rem;">Todo en orden. No hay debilidades críticas registradas.</div>`;
        return;
    }

    list.innerHTML = diagnoses.map(d => {
        return `
            <div class="diagnosis-card ${d.severity || 'warning'}">
                <div class="diag-header">
                    <span class="diag-title">${d.icon || '⚠️'} ${d.title}</span>
                    <span class="diag-badge ${d.severity}">${d.badge || 'Análisis'}</span>
                </div>
                <div class="diag-body">
                    <b>Qué ocurrió:</b> ${d.what_happened}
                </div>
                <div class="diag-fix">
                    💡 <b>Cómo corregirlo:</b> ${d.how_to_fix}
                </div>
            </div>
        `;
    }).join('');
}

function renderPracticeRoutines(routines) {
    const grid = document.getElementById('routinesGrid');
    if (!grid) return;

    if (!routines || !routines.length) return;

    grid.innerHTML = routines.map(r => {
        return `
            <div class="routine-card">
                <div class="routine-card-title">${r.title}</div>
                <div class="routine-card-focus">🎯 Enfoque: ${r.focus} (${r.duration})</div>
                <div class="routine-card-desc">${r.description}</div>
                <button class="btn-primary" style="margin-top:6px; font-size:0.72rem; padding:4px 10px;" onclick="installPracticeRoutine('${r.id}')">
                    💾 Instalar en cstrike/ (${r.cfg_name})
                </button>
            </div>
        `;
    }).join('');
}

async function installPracticeRoutine(routineId) {
    try {
        const res = await fetch('/api/telemetry/install_routine', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ routine_id: routineId })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message || "¡Rutina de entrenamiento instalada!");
        } else {
            alert(data.error || "No se pudo instalar la rutina.");
        }
    } catch (err) {
        alert("Error al instalar rutina: " + err.message);
    }
}

async function activateTelemetryLogging() {
    try {
        const res = await fetch('/api/telemetry/start', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast("¡Telemetría VAC-Safe activada y vinculada a userconfig.cfg!");
            loadTelemetryDashboard();
        } else {
            alert(data.error || "Error al activar telemetría.");
        }
    } catch (err) {
        alert("Error: " + err.message);
    }
}

async function resetTelemetrySession() {
    if (!confirm("¿Deseas reiniciar todas las estadísticas de la sesión actual de telemetría?")) return;
    try {
        const res = await fetch('/api/telemetry/reset', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            showToast("¡Estadísticas de sesión reiniciadas a cero!");
            loadTelemetryDashboard();
        }
    } catch (err) {
        alert("Error: " + err.message);
    }
}

// ==============================================================================
// UTILIDADES
// ==============================================================================
function showToast(msg) {
    const toast = document.getElementById('toast');
    if (!toast) return;
    toast.textContent = msg;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 3500);
}

function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
}

// ==============================================================================
// GESTIÓN DE USUARIO Y CRÉDITOS OFICIALES DEL PROYECTO
// Desarrollado por: yuyito, Hidden /A/, KYAMI, vANS
// ==============================================================================
async function initAuthUser() {
    try {
        const res = await fetch('/api/auth/me');
        const data = await res.json();
        if (data.authenticated && data.user) {
            const nameEl = document.getElementById('headerUserName');
            if (nameEl) nameEl.textContent = data.user.username;
        }
    } catch (e) {
        console.error("Error al obtener usuario:", e);
    }
}

function openCreditsModal() {
    const modal = document.getElementById('creditsModal');
    if (modal) {
        modal.style.display = 'flex';
        const onEsc = (e) => {
            if (e.key === 'Escape') {
                closeCreditsModal();
                document.removeEventListener('keydown', onEsc);
            }
        };
        document.addEventListener('keydown', onEsc);
    }
}

function closeCreditsModal() {
    const modal = document.getElementById('creditsModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// ==============================================================================
// MÓDULO DEMO A MP4 (.DEM A .MP4) CON FFMPEG
// ==============================================================================
let demoScanData = null;

function initDemoModule() {
    scanDemosAndFrames();
}

async function scanDemosAndFrames() {
    const prefix = (document.getElementById('demoPrefix')?.value || 'clip').trim();
    try {
        const res = await fetch(`/api/demo/status?prefix=${encodeURIComponent(prefix)}`);
        const data = await res.json();
        demoScanData = data;

        // 1. Actualizar estado de FFmpeg
        const led = document.getElementById('ffmpegLed');
        const title = document.getElementById('ffmpegStatusTitle');
        const badge = document.getElementById('ffmpegBadge');
        const desc = document.getElementById('ffmpegDesc');
        const customPathRow = document.getElementById('ffmpegCustomPathRow');

        if (data.ffmpeg && data.ffmpeg.available) {
            if (led) { led.style.background = '#2ed573'; led.style.boxShadow = '0 0 6px #2ed573'; }
            if (title) title.textContent = 'FFmpeg: Disponible y Operativo';
            if (badge) { badge.className = 'badge success'; badge.textContent = 'OPERATIVO'; }
            if (desc) desc.textContent = data.ffmpeg.version || data.ffmpeg.path;
            if (customPathRow) customPathRow.style.display = 'none';
        } else {
            if (led) { led.style.background = '#ff4757'; led.style.boxShadow = '0 0 6px #ff4757'; }
            if (title) title.textContent = 'FFmpeg: No detectado en PATH';
            if (badge) { badge.className = 'badge danger'; badge.textContent = 'REQUERIDO'; }
            if (desc) desc.innerHTML = 'Descarga gratuita en <a href="https://ffmpeg.org/download.html" target="_blank" style="color:var(--accent); font-weight:600;">ffmpeg.org</a> o indica su ruta completa (.exe) a continuación:';
            if (customPathRow) customPathRow.style.display = 'block';
        }

        // 2. Poblar selector de demos
        const select = document.getElementById('demoFileSelect');
        if (select) {
            if (data.demos && data.demos.length > 0) {
                select.innerHTML = '<option value="">-- Selecciona una demo para reproducir --</option>' +
                    data.demos.map(d => `<option value="${d.name}">${d.name} (${d.size_mb} MB - ${d.modified})</option>`).join('');
            } else {
                select.innerHTML = '<option value="">(No se encontraron demos .dem en cstrike/)</option>';
            }
        }

        // 3. Métricas de fotogramas
        const fCountEl = document.getElementById('demoFramesCount');
        const aStatusEl = document.getElementById('demoAudioStatus');
        const dMbEl = document.getElementById('demoDiskMb');
        const dDurEl = document.getElementById('demoDurationEst');

        const scan = data.frames_scan || {};
        if (scan.found) {
            if (fCountEl) fCountEl.textContent = `${scan.frames_count} fotogramas (${scan.first_frame} ... ${scan.last_frame})`;
            if (aStatusEl) aStatusEl.textContent = scan.has_audio ? '✅ clip.wav sincronizado' : '⚠️ Sin clip.wav (Solo video)';
            if (dMbEl) dMbEl.textContent = `${scan.total_size_mb} MB`;
            updateDemoDuration();
        } else {
            if (fCountEl) fCountEl.textContent = '0 fotogramas detectados';
            if (aStatusEl) aStatusEl.textContent = scan.has_audio ? '✅ clip.wav presente' : 'No detectado';
            if (dMbEl) dMbEl.textContent = '0 MB';
            if (dDurEl) dDurEl.textContent = '0.0 s';
        }
    } catch (err) {
        console.error("Error al escanear demos y fotogramas:", err);
    }
}

function onDemoSelected(demoName) {
    if (!demoName) return;
    const baseName = demoName.replace(/\.dem$/i, '');
    const cmdInput = document.getElementById('demoViewCmd');
    if (cmdInput) cmdInput.value = `viewdemo ${baseName}`;
    const outputInput = document.getElementById('demoOutputName');
    if (outputInput) outputInput.value = `${baseName}.mp4`;
}

function copyDemoCmd(inputId) {
    const input = document.getElementById(inputId);
    if (!input) return;
    navigator.clipboard.writeText(input.value).then(() => {
        showToast("¡Comando copiado al portapapeles!");
    }).catch(() => {
        input.select();
        document.execCommand('copy');
        showToast("¡Comando copiado!");
    });
}

function updateDemoDuration() {
    const scan = demoScanData?.frames_scan;
    const durEl = document.getElementById('demoDurationEst');
    if (!scan || !scan.found || !durEl) return;
    const fps = parseInt(document.getElementById('demoFpsSelect')?.value || '60', 10);
    const dur = (scan.frames_count / fps).toFixed(2);
    durEl.textContent = `${dur} s`;
}

async function saveCustomFfmpeg() {
    const path = document.getElementById('customFfmpegInput')?.value.trim();
    if (!path) return alert("Por favor ingresa la ruta completa a ffmpeg.exe.");
    try {
        const res = await fetch('/api/demo/set_custom_ffmpeg', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path })
        });
        const data = await res.json();
        if (data.success) {
            showToast("Ruta de FFmpeg actualizada.");
            scanDemosAndFrames();
        }
    } catch (e) {
        alert("Error al guardar ruta de FFmpeg: " + e.message);
    }
}

async function compileDemoToMp4() {
    const prefix = (document.getElementById('demoPrefix')?.value || 'clip').trim();
    const fps = parseInt(document.getElementById('demoFpsSelect')?.value || '60', 10);
    const crf = parseInt(document.getElementById('demoCrfSelect')?.value || '18', 10);
    const preset = document.getElementById('demoPresetSelect')?.value || 'slow';
    const output_name = (document.getElementById('demoOutputName')?.value || 'mi_jugada.mp4').trim();
    const cleanup_bmps = document.getElementById('demoCleanupCheck')?.checked ?? true;

    const scan = demoScanData?.frames_scan;
    if (!scan || !scan.found || scan.frames_count === 0) {
        alert("No se han detectado fotogramas con el prefijo '" + prefix + "' en cstrike/.\n\nSigue el Paso 1: En CS 1.6 abre la consola (~), escribe viewdemo y presiona F9 para que el motor guarde los fotogramas antes de compilar.");
        return;
    }

    if (!confirm(`¿Iniciar compilación de ${scan.frames_count} fotogramas a ${fps} FPS en ${output_name}?`)) {
        return;
    }

    LoadingOverlay.show({
        title: "COMPILANDO VIDEO MP4 CON FFMPEG",
        step: `Uniendo ${scan.frames_count} fotogramas a ${fps} FPS (H.264 / AAC)...`,
        percent: 45,
        engineTag: "FFMPEG H.264 • YUV420P",
        detail: `[SALIDA: ${output_name}] • [CRF: ${crf}] • [PRESET: ${preset}]`
    });

    const consoleEl = document.getElementById('demoOutputConsole');
    if (consoleEl) {
        consoleEl.style.display = 'block';
        consoleEl.innerHTML = `<span style="color:var(--accent);">[*] Codificando video MP4 con FFmpeg...</span><br>Frames: ${scan.frames_count} | FPS: ${fps} | CRF: ${crf}<br>`;
    }

    try {
        const res = await fetch('/api/demo/compile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prefix,
                fps,
                crf,
                preset,
                output_name,
                cleanup_bmps
            })
        });
        const data = await res.json();
        LoadingOverlay.hide(100);

        if (data.success && data.result) {
            const r = data.result;
            const logMsg = `
                <br><span style="color:#2ed573; font-weight:bold;">[OK] ¡Video generado con éxito!</span><br>
                <b>Archivo:</b> ${r.output_name} (${r.output_size_mb} MB)<br>
                <b>Duración:</b> ${r.duration_seconds} segundos (${r.frames_processed} cuadros)<br>
                <b>Ruta:</b> ${r.output_path}<br>
                ${r.cleaned_temp_files > 0 ? `<span style="color:#a0aec0;">[Limpieza] ${r.cleaned_temp_files} archivos temporales BMP liberados del disco.</span>` : ''}
            `;
            if (consoleEl) consoleEl.innerHTML += logMsg;
            showToast("¡Video MP4 generado exitosamente!");
            scanDemosAndFrames();
        } else {
            alert(data.error || "Error durante la compilación con FFmpeg.");
            if (consoleEl) consoleEl.innerHTML += `<br><span style="color:#ff4757;">[!] ${data.error || 'Error'}</span>`;
        }
    } catch (err) {
        LoadingOverlay.hide(100);
        alert("Error de conexión durante el renderizado: " + err.message);
    }
}

async function cleanupDemoFramesManual() {
    const prefix = (document.getElementById('demoPrefix')?.value || 'clip').trim();
    if (!confirm(`¿Eliminar todos los fotogramas temporales '${prefix}*.bmp' y '${prefix}.wav' de cstrike/ para liberar espacio en disco?`)) {
        return;
    }

    try {
        const res = await fetch('/api/demo/cleanup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prefix })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`¡Limpieza completada! ${data.removed_files} archivos eliminados (${data.freed_mb} MB liberados).`);
            scanDemosAndFrames();
        } else {
            alert(data.error || "No se pudieron limpiar los fotogramas.");
        }
    } catch (err) {
        alert("Error: " + err.message);
    }
}

// ==============================================================================
// 11. PILARES DE INGENIERÍA V2 (BOOSTER, CFG HUB, CLEANER, NETWORK A2S/RCON)
// ==============================================================================

let currentCalculatedRates = null;
let lastA2SServer = null;

function initV2Pillars() {
    calculateNetcodeRates();
    fetchBoosterStatusV2();
    // Sondeo de estado del booster v2 cada 4 segundos
    setInterval(fetchBoosterStatusV2, 4000);
}

// ------------------------------------------------------------------------------
// PILAR 1: RUNTIME BOOSTER, TIMER 0.5MS Y AFINIDAD INTELIGENTE
// ------------------------------------------------------------------------------

async function fetchBoosterStatusV2() {
    try {
        const res = await fetch('/api/v2/booster/status');
        if (!res.ok) return;
        const data = await res.json();

        // 1. Timer Resolution
        const timerVal = document.getElementById('boosterTimerVal');
        if (timerVal) {
            if (data.timer_05ms_active) {
                timerVal.textContent = "0.5 ms (Kernel Forzado)";
                timerVal.style.color = "var(--accent-gold)";
            } else {
                timerVal.textContent = "15.6 ms (Por defecto SO)";
                timerVal.style.color = "#94a3b8";
            }
        }

        // 2. Proceso hl.exe
        const procVal = document.getElementById('boosterProcessVal');
        const pidVal = document.getElementById('boosterPidVal');
        const prioVal = document.getElementById('boosterPriorityVal');
        if (procVal) procVal.textContent = data.hl_running ? "hl.exe En Ejecución" : "No detectado";
        if (pidVal) pidVal.textContent = data.active_pid ? `PID: ${data.active_pid}` : "Esperando juego...";
        if (prioVal) {
            prioVal.textContent = data.hl_running ? "ALTA (HIGH_PRIORITY_CLASS)" : "NORMAL";
            prioVal.style.color = data.hl_running ? "#22c55e" : "#94a3b8";
        }

        // 3. Topología de CPU y Núcleo Asignado
        const topo = data.cpu_topology;
        const badge = document.getElementById('cpuTopologyBadge');
        if (badge && topo) {
            badge.textContent = `${topo.physical_count} Cores Físicos / ${topo.logical_count} Hilos${topo.is_smt ? ' (SMT/HT Activo)' : ''}`;
        }

        const buttonsBox = document.getElementById('coreSelectorButtons');
        if (buttonsBox && topo && topo.physical_cores && topo.physical_cores.length) {
            buttonsBox.innerHTML = topo.physical_cores.map(c => {
                const isSelected = (c === data.target_core);
                const isAvoided = (c === 0);
                const recText = (c === topo.recommended_core) ? " (Recomendado)" : "";
                const avoidText = isAvoided ? " [Núcleo 0 - DPC/ISR]" : "";
                return `<button class="core-pill-btn ${isSelected ? 'active' : ''}" onclick="setBoosterCore(${c})">
                    Core Físico ${c}${recText}${avoidText}
                </button>`;
            }).join('');
        }
    } catch (e) {
        // Silencioso si aún no está listo el servidor
    }
}

async function setTimerResolution(ms) {
    try {
        const res = await fetch('/api/booster/timer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enable: true, ms: ms })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`¡Timer Resolution del Kernel fijado a ${ms} ms!`);
            fetchBoosterStatusV2();
        }
    } catch (err) {
        alert("Error al fijar Timer Resolution: " + err.message);
    }
}

async function restoreSystemTimer() {
    try {
        const res = await fetch('/api/booster/timer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ enable: false })
        });
        const data = await res.json();
        if (data.success) {
            showToast("Timer del sistema restaurado a 15.6 ms.");
            fetchBoosterStatusV2();
        }
    } catch (err) {
        alert("Error al restaurar temporizador: " + err.message);
    }
}

async function cleanStandbyMemory() {
    LoadingOverlay.show({
        title: "PURGANDO STANDBY LIST",
        step: "Llamando a WinAPI psapi.EmptyWorkingSet...",
        percent: 50,
        engineTag: "MEMORY TRIMMER",
        detail: "[DESCARGANDO CONJUNTOS DE TRABAJO EN ESPERA]"
    });

    try {
        const res = await fetch('/api/v2/booster/clean_memory', { method: 'POST' });
        const data = await res.json();
        LoadingOverlay.hide(100);
        if (data.success) {
            showToast(data.message || "¡Memoria RAM en espera purgada con éxito!");
        } else {
            showToast(data.message || "Aviso de limpieza de memoria.");
        }
    } catch (err) {
        LoadingOverlay.hide(100);
        alert("Error: " + err.message);
    }
}

async function setBoosterCore(coreId) {
    try {
        const res = await fetch('/api/v2/booster/set_core', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ core: coreId })
        });
        const data = await res.json();
        if (data.success) {
            showToast(`¡Afinidad fijada al Núcleo Físico ${coreId}!`);
            fetchBoosterStatusV2();
        }
    } catch (err) {
        alert("Error al asignar núcleo: " + err.message);
    }
}

// ------------------------------------------------------------------------------
// PILAR 2: CFG HUB & CALCULADORA MATEMÁTICA GOLDRSC (ex_interp = 1 / cl_updaterate)
// ------------------------------------------------------------------------------

async function calculateNetcodeRates() {
    const ping = parseFloat(document.getElementById('calcPingMs')?.value || 25);
    const bw = parseFloat(document.getElementById('calcBandwidthMbps')?.value || 50);
    const fps = parseInt(document.getElementById('calcTargetFps')?.value || 100);

    try {
        const res = await fetch('/api/v2/cfg/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ping_ms: ping,
                bandwidth_mbps: bw,
                target_fps: fps
            })
        });
        const data = await res.json();
        if (data.success && data.calculated) {
            currentCalculatedRates = data.calculated;
            const net = data.calculated.netcode;
            const eng = data.calculated.engine;
            const inp = data.calculated.input;
            const met = data.calculated.metrics;

            // Actualizar campos
            const rEl = document.getElementById('cfgRate');
            const uEl = document.getElementById('cfgUpdate');
            const cEl = document.getElementById('cfgCmd');
            const iEl = document.getElementById('cfgInterp');
            const fEl = document.getElementById('cfgFpsDisplay');
            const mEl = document.getElementById('cfgRawInputDisplay');

            if (rEl) rEl.value = net.rate;
            if (uEl) uEl.value = net.cl_updaterate;
            if (cEl) cEl.value = net.cl_cmdrate;
            if (iEl) iEl.value = net.ex_interp + ` (${met.interp_ms} ms)`;
            if (fEl) fEl.value = `fps_max ${eng.fps_max} (override ${eng.fps_override})`;
            if (mEl) mEl.value = `${inp.m_rawinput} (Cero aceleración / RAW)`;

            // Generar vista previa
            renderCalculatedCfgPreview(data.calculated);
        }
    } catch (err) {
        console.error("Error al calcular rates:", err);
    }
}

function onCfgHubPresetChange(presetKey) {
    const pingEl = document.getElementById('calcPingMs');
    const bwEl = document.getElementById('calcBandwidthMbps');
    const fpsEl = document.getElementById('calcTargetFps');

    if (presetKey === 'competitive_100') {
        if (pingEl) pingEl.value = 25;
        if (bwEl) bwEl.value = 50;
        if (fpsEl) fpsEl.value = 100;
    } else if (presetKey === 'low_ping_esports') {
        if (pingEl) pingEl.value = 15;
        if (bwEl) bwEl.value = 100;
        if (fpsEl) fpsEl.value = 105;
    } else if (presetKey === 'kzbhop_highfps') {
        if (pingEl) pingEl.value = 30;
        if (bwEl) bwEl.value = 50;
        if (fpsEl) fpsEl.value = 250;
    } else if (presetKey === 'casual_native_hd') {
        if (pingEl) pingEl.value = 40;
        if (bwEl) bwEl.value = 20;
        if (fpsEl) fpsEl.value = 100;
    }
    calculateNetcodeRates();
}

function renderCalculatedCfgPreview(calc) {
    const editor = document.getElementById('cfgCodePreview');
    if (!editor) return;

    const net = calc.netcode || {};
    const eng = calc.engine || {};
    const rnd = calc.render || {};
    const inp = calc.input || {};
    const met = calc.metrics || {};

    const text = `// =============================================================================
// CSStudioPro - CONFIGURACIÓN DE ALTO RENDIMIENTO (GOLDRSC ENGINE)
// Perfil: Interp ${met.interp_ms}ms | FPS: ${met.target_fps} | Ping: ${met.ping_ms}ms
// =============================================================================

// --- [1/4] NETCODE OFICIAL (ECUACIÓN: ex_interp = 1 / cl_updaterate) ---
rate ${net.rate}
cl_updaterate ${net.cl_updaterate}
cl_cmdrate ${net.cl_cmdrate}
ex_interp ${net.ex_interp}
cl_cmdbackup ${net.cl_cmdbackup}
cl_dlmax ${net.cl_dlmax}
cl_nosmooth ${net.cl_nosmooth}

// --- [2/4] MOTOR DE FOTOGRAMAS Y AUDIO ---
fps_override ${eng.fps_override}
fps_max ${eng.fps_max}
_snd_mixahead ${eng._snd_mixahead}

// --- [3/4] ENTRADA DE MOUSE PURA (CERO LATENCIA / SIN ACELERACIÓN) ---
m_rawinput ${inp.m_rawinput}
m_customaccel ${inp.m_customaccel}
m_filter ${inp.m_filter}
m_yaw ${inp.m_yaw}
m_pitch ${inp.m_pitch}

// --- [4/4] RENDERIZADO Y TEXTURAS ---
gl_vsync ${rnd.gl_vsync}
gl_ansio ${rnd.gl_ansio}
r_detailtextures ${rnd.r_detailtextures}
gl_texturemode ${rnd.gl_texturemode}

echo "[CSStudioPro] userconfig.cfg cargado con éxito. Netcode calibrado al 100%."`;

    editor.value = text;
}

async function injectCalculatedCfg() {
    LoadingOverlay.show({
        title: "INYECCIÓN NO DESTRUCTIVA",
        step: "Respaldando cstrike/*.cfg y combinando userconfig...",
        percent: 40,
        engineTag: "CFG HUB ENGINE",
        detail: "[PRESERVANDO BINDS Y ALIASES PERSONALES]"
    });

    try {
        const res = await fetch('/api/v2/cfg/inject', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ calculated: currentCalculatedRates })
        });
        const data = await res.json();
        LoadingOverlay.hide(100);

        if (data.success) {
            showToast(data.message || "¡Configuración inyectada con éxito!");
            loadCfgSnapshots();
        } else {
            alert(data.error || "Error al inyectar configuración.");
        }
    } catch (err) {
        LoadingOverlay.hide(100);
        alert("Error de inyección: " + err.message);
    }
}

function downloadCalculatedCfg() {
    const text = document.getElementById('cfgCodePreview')?.value || '';
    const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    downloadBlob(blob, "userconfig.cfg");
    showToast("¡userconfig.cfg descargado!");
}

async function loadCfgSnapshots() {
    const card = document.getElementById('cfgSnapshotsCard');
    const tbody = document.getElementById('cfgSnapshotsTableBody');
    if (!card || !tbody) return;

    card.style.display = 'block';
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:12px;">Cargando instantáneas...</td></tr>';

    try {
        const res = await fetch('/api/v2/cfg/snapshots');
        const data = await res.json();
        const snaps = data.snapshots || [];

        if (!snaps.length) {
            tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:var(--text-muted); padding:16px;">No hay snapshots aún. Se creará uno automáticamente al realizar cualquier inyección.</td></tr>';
            return;
        }

        tbody.innerHTML = snaps.map(s => `
            <tr>
                <td><code>${s.id}</code></td>
                <td>${s.created}</td>
                <td><b>${s.files_count} archivos .cfg</b></td>
                <td>
                    <button class="btn-secondary mini-btn" onclick="rollbackCfgSnapshot('${s.id}')">
                        🔄 Revertir Snapshot
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:#ff4757;">Error al cargar snapshots: ${err.message}</td></tr>`;
    }
}

async function rollbackCfgSnapshot(snapshotId) {
    if (!confirm(`¿Deseas restaurar todos los archivos .cfg a partir del snapshot '${snapshotId}'?`)) {
        return;
    }

    LoadingOverlay.show({
        title: "ROLLBACK DE CFGS",
        step: `Restaurando snapshot ${snapshotId}...`,
        percent: 60,
        engineTag: "ROLLBACK ENGINE",
        detail: "[RESTAURANDO ESTADO ORIGINAL]"
    });

    try {
        const res = await fetch('/api/v2/cfg/rollback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ snapshot_id: snapshotId })
        });
        const data = await res.json();
        LoadingOverlay.hide(100);

        if (data.success) {
            showToast(data.message || "¡Rollback completado con éxito!");
            loadCfgSnapshots();
        } else {
            alert(data.error || "Error durante el rollback.");
        }
    } catch (err) {
        LoadingOverlay.hide(100);
        alert("Error: " + err.message);
    }
}

// ------------------------------------------------------------------------------
// PILAR 3: ASSETS & CACHE CLEANER (WHITELIST VANILLA ESTRICTA)
// ------------------------------------------------------------------------------

async function scanAssetsCache() {
    LoadingOverlay.show({
        title: "ESCANEANDO CACHÉ DE SERVIDORES",
        step: "Revisando custom.hpk, carpeta download/ y assets huérfanos...",
        percent: 45,
        engineTag: "WHITELIST ENGINE",
        detail: "[COMPROBANDO LISTA BLANCA NATIVA DE VALVE]"
    });

    try {
        const res = await fetch('/api/v2/cleaner/scan');
        const data = await res.json();
        LoadingOverlay.hide(100);

        if (data.success && data.scan) {
            const s = data.scan;
            const tMb = document.getElementById('cleanerTotalMb');
            const tFl = document.getElementById('cleanerTotalFiles');
            const hMb = document.getElementById('cleanerHpkMb');
            const hSt = document.getElementById('cleanerHpkStatus');
            const dMb = document.getElementById('cleanerDlMb');
            const dFl = document.getElementById('cleanerDlFiles');
            const mMb = document.getElementById('cleanerMapsMb');
            const mCt = document.getElementById('cleanerMapsCount');
            const oMb = document.getElementById('cleanerModelsMb');
            const oCt = document.getElementById('cleanerModelsCount');

            if (tMb) tMb.textContent = `${s.total_cleanable_mb} MB`;
            if (tFl) tFl.textContent = `${s.total_cleanable_files} archivos`;
            if (hMb) hMb.textContent = `${s.custom_hpk.size_mb} MB`;
            if (hSt) hSt.textContent = s.custom_hpk.found ? "Detectado en cstrike/" : "No existe";
            if (dMb) dMb.textContent = `${s.downloads_folder.size_mb} MB`;
            if (dFl) dFl.textContent = `${s.downloads_folder.files_count} archivos`;
            if (mMb) mMb.textContent = `${s.custom_maps.size_mb} MB`;
            if (mCt) mCt.textContent = `${s.custom_maps.files_count} mapas`;
            if (oMb) oMb.textContent = `${s.custom_models.size_mb} MB`;
            if (oCt) oCt.textContent = `${s.custom_models.files_count} carpetas`;

            showToast(`Escaneo completado: ${s.total_cleanable_mb} MB liberables.`);
        }
    } catch (err) {
        LoadingOverlay.hide(100);
        alert("Error al escanear caché: " + err.message);
    }
}

async function cleanAssetsCache() {
    const hpk = document.getElementById('cleanHpkOpt')?.checked || false;
    const dl = document.getElementById('cleanDlOpt')?.checked || false;
    const maps = document.getElementById('cleanMapsOpt')?.checked || false;
    const models = document.getElementById('cleanModelsOpt')?.checked || false;

    if (!hpk && !dl && !maps && !models) {
        alert("Selecciona al menos una categoría para depurar.");
        return;
    }

    if (!confirm("¿Deseas depurar de forma segura la caché de servidores seleccionada?\n(Los archivos oficiales de CS 1.6 están protegidos por la whitelist).")) {
        return;
    }

    LoadingOverlay.show({
        title: "DEPURANDO CACHÉ DE SERVIDORES",
        step: "Purgando archivos temporales respetando la Whitelist Vanilla...",
        percent: 50,
        engineTag: "CLEANER PRO",
        detail: "[BORRADO SEGURO EN CURSO]"
    });

    try {
        const res = await fetch('/api/v2/cleaner/clean', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                clean_hpk: hpk,
                clean_downloads: dl,
                clean_custom_maps: maps,
                clean_custom_models: models
            })
        });
        const data = await res.json();
        LoadingOverlay.hide(100);

        const outBox = document.getElementById('cleanerOutputBox');
        if (data.success) {
            if (outBox) {
                outBox.style.display = 'block';
                outBox.innerHTML = `<span style="color:#2ed573; font-weight:bold;">[OK] ${data.message}</span><br>Archivos purgados: ${data.deleted_files_count} | Espacio liberado: ${data.freed_mb} MB`;
            }
            showToast(`¡Se liberaron ${data.freed_mb} MB del disco!`);
            scanAssetsCache();
        } else {
            alert(data.error || "Error al depurar caché.");
        }
    } catch (err) {
        LoadingOverlay.hide(100);
        alert("Error de conexión durante la depuración: " + err.message);
    }
}

// ------------------------------------------------------------------------------
// PILAR 4: MONITOR DE SERVIDORES A2S Y CONSOLA RCON NATIVA (UDP)
// ------------------------------------------------------------------------------

async function queryA2SServer() {
    const host = (document.getElementById('a2sHostInput')?.value || '127.0.0.1').trim();
    const port = parseInt(document.getElementById('a2sPortInput')?.value || 27015);

    LoadingOverlay.show({
        title: "CONSULTA UDP A2S_INFO",
        step: `Enviando paquete Valve 0x54 a ${host}:${port}...`,
        percent: 40,
        engineTag: "A2S UDP PROTOCOL",
        detail: "[HANDSHAKE DE DESAFÍO 0x41]"
    });

    try {
        const res = await fetch(`/api/v2/network/a2s_query?host=${encodeURIComponent(host)}&port=${port}`);
        const data = await res.json();
        LoadingOverlay.hide(100);

        const panel = document.getElementById('a2sDisplayPanel');
        if (panel) panel.style.display = 'block';

        if (data.online) {
            lastA2SServer = { host, port };
            document.getElementById('a2sServerName').textContent = data.name || "(Sin nombre)";
            document.getElementById('a2sMapName').textContent = data.map || "Desconocido";
            document.getElementById('a2sPlayersCount').textContent = `${data.players} / ${data.max_players} (${data.bots} bots)`;
            
            const pBadge = document.getElementById('a2sPingBadge');
            if (pBadge) {
                pBadge.textContent = `${data.ping_ms} ms`;
                pBadge.className = data.ping_ms < 50 ? 'server-ping-badge ping-fast' : (data.ping_ms < 100 ? 'server-ping-badge ping-medium' : 'server-ping-badge ping-slow');
            }

            const vacEl = document.getElementById('a2sVacStatus');
            if (vacEl) {
                vacEl.textContent = data.vac ? "Protegido por Valve Anti-Cheat (VAC)" : "Sin Protección VAC";
                vacEl.style.color = data.vac ? "#22c55e" : "#ff4757";
            }

            const osEl = document.getElementById('a2sOsType');
            if (osEl) osEl.textContent = `${data.server_type || 'Servidor'} en ${data.os || 'Desconocido'}`;

            showToast(`Servidor "${data.name}" responde (${data.ping_ms} ms).`);
        } else {
            alert(data.error || "El servidor no respondió a la consulta A2S.");
        }
    } catch (err) {
        LoadingOverlay.hide(100);
        alert("Error de consulta A2S: " + err.message);
    }
}

function connectToA2SServer() {
    if (!lastA2SServer) return;
    const serverAddr = `${lastA2SServer.host}:${lastA2SServer.port}`;
    const serverInput = document.getElementById('launchServerInput');
    if (serverInput) serverInput.value = serverAddr;
    switchTab('launcher-ia');
    launchGameDirect();
}

async function sendRconCommand() {
    const host = (document.getElementById('a2sHostInput')?.value || '127.0.0.1').trim();
    const port = parseInt(document.getElementById('a2sPortInput')?.value || 27015);
    const pwd = (document.getElementById('rconPasswordInput')?.value || '').trim();
    const cmd = (document.getElementById('rconCommandInput')?.value || 'status').trim();

    if (!pwd) {
        alert("Introduce la contraseña RCON.");
        return;
    }

    const term = document.getElementById('rconTerminalOutput');
    if (term) term.textContent += `\n> rcon ${cmd}...\n`;

    try {
        const res = await fetch('/api/v2/network/rcon_command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ host, port, password: pwd, command: cmd })
        });
        const data = await res.json();
        if (term) {
            if (data.success) {
                term.textContent += `${data.response}\n`;
            } else {
                term.textContent += `[ERROR] ${data.error}\n`;
            }
            term.scrollTop = term.scrollHeight;
        }
    } catch (err) {
        if (term) term.textContent += `[ERROR CONEXIÓN] ${err.message}\n`;
    }
}

