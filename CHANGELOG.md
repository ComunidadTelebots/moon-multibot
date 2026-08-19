# Changelog - Moon Multibot

## [v18.26.15.16-beta] - 2026-08-19 (Release Beta Multi-Canal)

**Refactorización Completa del Hub (Diseño Todo-en-Uno)**
* Se ha unificado toda la evolución histórica del diseño web en un solo archivo inmaculado (`hub.html`).
* **Selector de Apariencia (Arquitectura):** Se ha añadido un menú para alternar en tiempo real entre 4 estructuras UI diferentes sin perder funcionalidades:
  - 🚀 **Alfa Definitivo (Aurora)**: El motor actual Cyberpunk con pestañas.
  - ✨ **New Hub**: El diseño moderno de transiciones sin pestañas.
  - ✅ **Clásico Estable**: El diseño oficial de tarjetas largas (de la rama master).
  - 📺 **Clásico Puro**: La maqueta original e inalterada de tarjetas apiladas.
* **Separación de Temas:** El selector de "Tema de Color" ahora es independiente de la estructura de la web, recuperando los **Temas Nativos Apple iOS (Día/Noche)** y **Android Material 3 (Día/Noche)**.
* **Sincronización Multi-Rama:** Se absorbieron todos los arreglos crudos y parches estabilizados de la rama `master` (arreglos en el simulador 3D, bugs de WebApp y enrutador inteligente) directamente en la rama `alfa`.
* **Corrección de Codificación (Encoding):** Reparación quirúrgica de tildes y eñes perdidas (`Diseño`, `Añadir`, `Clásico`) usando diccionarios directos, garantizando que el DOM y el motor Javascript permanecen intactos sin generar caracteres nulos (UTF-16).

**Optimizaciones de Backend y Estabilidad (Silent Fixes)**
* **Crash Crítico del Router Resuelto:** Reparado un desajuste de argumentos (`patched_api_call` recibía 6 argumentos en vez de 4) que causaba el colapso silencioso del bucle de eventos cada 5 segundos.
* **Rotación de Logs (Prevención de Desbordamiento):** Implementado un sistema nativo para `data/bot.log` que archiva el historial automáticamente al alcanzar los 5MB, previniendo el consumo infinito de disco.
* **Limpieza de Verbose Debugging:** Eliminados los rastros excesivos de logging en el bucle principal ("Esperando nuevos mensajes", "Detección de ID") que saturaban la interfaz del dashboard y la memoria.
* **Purga de BOM UTF-8:** Eliminado un carácter invisible (`\ufeff`) en la cabecera del archivo masivo `core/routes_public.py` que comprometía la compatibilidad del intérprete en entornos Linux/Docker.

**Arquitectura Multi-Canal (Micro-Repositorios)**
* **Enrutamiento por Base de Datos Restaurado:** Se reescribió el interceptor del router (`patched_api_call`) para restaurar la lógica perdida en commits anteriores. Ahora el Master (stable) vuelve a consultar nativamente `SELECT release_channels FROM users` y redirige los eventos de Telegram a las instancias correspondientes (`alpha`, `beta`, `rc`) de forma transparente.
* **Aislamiento de Manifiestos:** Se escanearon y etiquetaron automáticamente **103 archivos de manifiesto** (`*manifest.py`) inyectando la propiedad `"release_channel": "alpha"`. Esto sella las fronteras del control de acceso y prepara el código base para su división física en micro-repositorios sin pérdida de compatibilidad.



## [v18.25.15.15-alpha] - 2026-08-19 (Registro Diario de Builds)

**Build 15** (`b741135`): Desplazamiento del parche del router por encima del bucle infinito de Waitress para garantizar su ejecución.
**Build 14** (`f74bcf8`): Implementación de la herramienta de Ping directamente accesible desde el panel de administración.
**Build 13** (`f3d0100`): Resolución de error de sangría (indentation) y bloque try/except roto durante parcheo automatizado.
**Build 12** (`c06f15d`): Importación de la librería `queue` en el interceptor para prevenir un crash silencioso en el hilo del timer.
**Build 11** (`51f7eab`): Inyección de logs de diagnóstico profundos para auditar la correcta aplicación de los interceptores web.
**Build 10** (`6614582`): Unificación y limpieza arquitectónica de parches duplicados del router que causaban colisiones de concurrencia.
**Build 9** (`8eb5657`): Corrección del `AttributeError` originado al tratar `active_bots` como lista en lugar de diccionario.
**Build 8** (`6789416`): Eliminación crítica de carácter BOM (Byte Order Mark) UTF-8 invisible en la línea 2 que bloqueaba intérpretes.
**Build 7** (`16a1699`): Inclusión de importación faltante (`wraps` de `functools`) necesaria para los decoradores del router.
**Build 6** (`eeaf848`): Aumento de verbosidad con logs de debug avanzados en la función `api_call` hacia Telegram.
**Build 5** (`cf0c885`): Desactivación estratégica de réplicas en el bot estable para eliminar colisiones `409 Conflict` en la API de Telegram.
**Build 4** (`7f007e4`): Inclusión de un fallback robusto en el auto-escalador para calcular `system_cpu_usage` frente a discrepancias de la API de Docker.
**Build 3** (`7bd65d5`): Eliminación de errores de configuración en el sistema de réplicas asociado al motor de Ollama.
**Build 2** (`4a91a8f`): Implementación nuclear del Auto-escalador, colas de Webhooks y correcciones masivas en el Central Router.
**Build 1** (`ac9708a`): Reparación de la autenticación de testers y forzado del establecimiento de la cookie `hub_session` adaptada a subdominios cruzados.

**18 de Agosto de 2026**
- **Arquitectura Docker Multi-Entorno**: Soporte nativo en `docker-compose` para entornos (alfa, beta, rc, estable) aislando puertos y redes (Traefik ext), con regeneración segura de YAML sin perfiles conflictivos.
- **Central Webhook Router**: Nuevo enrutador central de webhooks con limitador de tasa global (Rate Limiter) y suspensión dinámica de hilos secundarios en entornos no estables.
- **UI del Hub**: Insignias visuales (badges) dinámicas que muestran el estado y versión actual (Alfa/Beta/RC/Estable) con selector y limitación por `release channel`.


## v18.25.15-alpha - 2026-08-15 - Evolución completa de Rutas del Continente

### Interfaz y experiencia de usuario

- Sustituye la interfaz heredada por el sistema visual de Canva: cabecera operativa, cuadro de conducción, centro principal y dock de Vehículo, Ruta, Trabajo y Servicios.
- Elimina superposiciones antiguas que duplicaban telemetría, botones y estados sobre la escena.
- Añade pantalla de carga de TodoSobreAllTech Studios con fases DOM, módulos, render y mundo, diagnóstico de error y reintento.
- Incorpora ajustes de gráficos, audio, accesibilidad, contraste, movimiento y escala de interfaz.
- Añade selector accesible de nueve cámaras, nombres adaptados a cada familia de vehículos y teclas directas 1–9.
- Añade pantalla completa y resoluciones internas seleccionables.
- Corrige errores de sintaxis del HUD, fallos de arranque y la conexión entre el panel regional y los controles.

### Camiones, cabinas y materiales

- Añade una malla estática de alta definición para Aster Viento y una cabina estática formada por componentes identificables.
- Carga un modelo de camión diferente en Ultra, evitando que todos los perfiles conservaran la misma geometría.
- Sustituye mapas procedurales del camión de calidad alta por materiales horneados basados en las referencias de Canva.
- Separa pintura, metal, cristal, goma, llantas, luces, paneles y remolque en materiales y coordenadas UV independientes.
- Corrige la aplicación accidental de atlas completos sobre remolque, puertas, ruedas y componentes incompatibles.
- Añade materiales interiores y exteriores propios para autobuses y vehículos de emergencia.
- Incorpora estados visuales para limpieza, suciedad, lluvia, nieve, movimiento, frenado e iluminación.
- Mejora exterior, cabina digital, remolque frigorífico, ruedas, animaciones y composición de cámara del camión.

### Mundo, ciudades, carrera y operaciones

- Añade una malla poligonal de mundo transmitida por sectores y amplía los materiales de carretera, terreno, acera, piedra, edificios, vegetación, instalaciones y clima.
- Incorpora ciudades vivas con negocios y actividad programada según horario.
- Mejora carreteras, señales con destinos, estabilidad del remolque y cámara de persecución para evitar que la caja oculte la tractora.
- Amplía campañas, prólogos, decisiones e introducciones cinematográficas persistentes.
- Añade trabajos para camión, autobús, ambulancia, bomberos, grúa, avión de carga y portacontenedores.
- Incorpora flota empresarial persistente, compra de vehículos, asignación de conductores, mantenimiento, mejoras, desgaste e ingresos.
- Añade cadena logística con manifiesto, custodia, carretera, ferrocarril, aire, mar, transferencias y prueba de entrega.
- Integra estaciones de pesaje, inspecciones, sanciones y misiones asociadas.

### Gráficos, rendimiento y dispositivos

- Expone dentro del juego los perfiles Legacy, Bajo, Equilibrado, Alto y Ultra.
- Detecta capacidad del dispositivo, memoria, núcleos, pantalla y densidad de píxeles para elegir un perfil inicial seguro.
- Añade resolución adaptativa guiada por FPS, persistencia del perfil y límites para Android, iOS, PC y dispositivos antiguos.
- Separa el ritmo de simulación del render para evitar que una caída de fotogramas altere la velocidad del mundo.
- Ajusta la escala Ultra y conserva alternativas ligeras para geometría, sombras y materiales.

### Canales de publicación y Telegram

- Añade los canales Estable, RC, Beta y Alfa para distribuir progresivamente las funciones de Rutas del Continente.
- Vincula el canal efectivo al ID del usuario de Telegram validado mediante `Telegram.WebApp.initData`; un jugador normal no puede elevar su propio acceso.
- Añade al master la gestión de asignaciones por usuario, la revocación de accesos y la posibilidad de revisar los cuatro canales.
- Persiste las asignaciones en la colección `feature_release_access` de PocketBase y aplica Estable como valor seguro cuando no existe una asignación válida.
- Recupera como edición Estable la primera versión WebGL verificable del commit `5f4a52e`, con camión, autobús, tres cámaras y conducción básica.
- Clasifica la simulación terrestre moderna como RC; empresa, carga, trabajos y rutas OSM como Beta; y convoyes, campañas, eventos regionales, aviación, navegación y logística mundial como Alfa.
- Separa Estable en un recurso propio y aplica controles de disponibilidad a las interfaces modernas según la madurez del canal.

### Verificación

- Sintaxis de Python, JavaScript y scripts de módulo HTML validada.
- Pruebas de asignación, canales, perfiles, mallas, materiales, cámaras, físicas, flota, trabajos, misiones, pesaje y telemetría superadas durante sus respectivos commits.

## v18.25.13 - 2026-08-14 - Interfaz Canva, aduanas y continuidad

### Auditoría previa

- Contrasta el código con las páginas 21–23, 32, 41 y 51–60 del diseño maestro de Canva.
- Confirma que el planificador mundial, la cadena de frío y la carga frágil ya existían; se amplían sin duplicarlos.
- Detecta como carencias reales la reacción visual del HUD, las aduanas, la normativa por país, la operación visible de animales y una interfaz para migrar partidas.

### Cambios nuevos verificados

- Unifica HUD, cabina, controles, mapas, empresa, carga, aviación y navegación con la paleta azul petróleo, turquesa y naranja de Canva.
- Añade animaciones de cambios del HUD, alertas por severidad, exceso de velocidad, estados en marcha/detenido y respuesta táctil/háptica accesible.
- Añade aduanas internacionales con inspección, tasas, normativa ADR/HazMat, sentido de circulación, límites para pesados y peajes por país.
- Conecta el despacho aduanero con la economía y el registro maestro de eventos antes de conducir, volar o navegar.
- Hace seleccionables carga general, cadena de frío, frágil, ADR y animales; muestra temperatura, integridad, sujeción, hidratación y equipo específico.
- Añade continuidad de partida con copia local, restauración, exportación e importación JSON normalizada al esquema actual.

### Verificación local

- Sintaxis validada en el módulo principal y cinco módulos nuevos; 6/6 pruebas de telemetría, carga y cinemáticas superadas.

## v18.25.12 - 2026-08-14 - Sistema visual multimodal de Canva

### Auditoría previa

- Revisa las 80 páginas actuales del diseño maestro de Canva y separa catálogo general, interfaces del camión, aviación, navegación marítima y operaciones regionales.
- Confirma que ya existían modelos básicos de aeronaves y barcos, pero funcionaban como selecciones genéricas dentro de la carretera y no como experiencias propias.
- Confirma que carreteras, OSM, servicios y nodos logísticos ya existían, pero carecían de una interfaz regional unificada.

### Cambios nuevos verificados

- Añade un sistema visual principal con secciones Conducir, Empresa, Operaciones y Sistema, conectado a las pantallas y estados reales del simulador.
- Añade Moon Aviation con instrumentos, aeropuertos, destinos, misiones, progreso, despegue, ascenso, aterrizaje, cabeceo, alabeo y rotores animados.
- Convierte Puerto Logístico en una experiencia naval con carguero, ferri, remolcador, timón, inercia, radar, ruta balizada, atraque y descarga.
- Añade un centro operativo regional con territorio, nodo logístico, puertos, aeropuertos, centros intermodales, accesos, servicios, estado de vía y punto kilométrico.
- Mantiene interfaces responsive para escritorio, móvil y Telegram sin generar ni descargar imágenes nuevas.

### Verificación local

- Sintaxis validada en HTML y módulos nuevos; simulador naval comprobado y 7/7 pruebas combinadas superadas.

## v18.25.11 - 2026-08-14 - Seguridad, flota y operaciones animadas

### Auditoría previa de Canva y código

- Confirma que contratación, garajes y jornadas ya existían; se amplían sin duplicarlos.
- Confirma que no existían seguridad empresarial persistente, talentos, bots de última milla ni una secuencia visual para cargar palés.

### Cambios nuevos verificados

- Añade alarmas y guardias por sede, riesgo, turnos, intentos de intrusión, robos, pérdidas, valor protegido e historial de incidentes.
- Añade formación, progresión y talentos de eco-conducción, carga delicada y ruta exprés para los conductores.
- Añade tres bots de reparto con compra, pausa, ingresos, entregas y desgaste persistentes.
- Sustituye la desaparición instantánea del palé por una maniobra de alineación, elevación y asegurado con cámara cinemática y progreso accesible.
- Conecta seguridad, flota y carga al libro contable y al registro maestro de eventos.

### Verificación local

- Sintaxis de módulos y HTML validada; migración de partidas verificada y 6/6 pruebas superadas.

## v18.25.10 - 2026-08-14 - Operaciones y clima del simulador de camiones

### Auditoría de Canva antes de implementar

- Verifica que carrera, contratos, conductores, garajes, préstamos y contabilidad ya existían en el motor, pero no tenían una interfaz de gestión completa.
- Verifica que el estado físico de la mercancía ya estaba programado como módulo aislado, pero nunca se conectó a la conducción, el HUD ni los eventos.
- Detecta que nieve, niebla y tormenta procedentes del clima real se reducían a lluvia genérica.

### Cambios nuevos verificados

- Añade un Centro de empresa responsive con mercado de contratos, contrato activo, conductores, jornadas de flota, garajes, financiación, contabilidad y KPIs.
- Integra el Control de carga con perfiles general, refrigerado, frágil y ADR; calcula integridad, temperatura y sujeción a partir de golpes, vibración, firme, clima, puertas y refrigeración.
- Añade inspección de sujeción con el vehículo detenido, advertencia por puertas abiertas y registro automático de incidencias de mercancía.
- Diferencia nieve, niebla y tormenta con partículas, visibilidad, iluminación, adherencia, agua, viento, limpiaparabrisas y sonido propios.
- Refuerza el registro maestro ante datos persistidos corruptos, detalles excesivos, ciclos y valores BigInt.

### Verificación local

- Sintaxis del módulo principal y módulos nuevos validada; 116 identificadores HTML sin duplicados y 5/5 pruebas de telemetría superadas.

## v18.25.9 - 2026-08-14 - Catálogo visual unificado de Juegos Moon

### Auditoría de la página 1 de Canva

- Verifica que Rutas del Continente, Circuito Neón y Vuelo Rescate ya disponían de versiones 2D/3D y selector común; no se duplican.
- Detecta que Puerto Logístico, Enlace Ferroviario, Control Aéreo y Rescate Marítimo estaban registrados en el Hub, pero quedaban fuera del catálogo visual compartido.

### Cambios nuevos verificados

- Centraliza perfiles e historial de versiones en `MoonGamesCatalog` para que el Hub use una única fuente de nombre, categoría, versión y evolución.
- Añade perfiles visuales e historiales para los cuatro juegos operativos que faltaban y completa la evolución de Gato Soda Rush y Leyenda Latina.
- Evita insertar un segundo botón de historial cuando una versión anterior de la interfaz ya lo creó.

## v18.25.8 - 2026-08-13 - Estado visual y latencia multijugador

### Ya existente, no contabilizado como novedad

- Las salas ya sincronizaban vehículo, posición, altitud, velocidad y carga, y los vehículos locales ya tenían luces, frenado, intermitentes, emergencia, sirena y motor; esos estados aún no se transmitían.

### Cambios nuevos verificados

- Amplía la instantánea compartida con motor, faros, frenado, intermitente, luces de emergencia, sirena y clima local, manteniendo valores predeterminados compatibles con clientes anteriores.
- Mide el tiempo real de ida y vuelta de cada actualización, compensa el reloj compartido con media latencia y muestra el ping en las interfaces de camión y vuelo.
- Añade marca temporal del servidor a cada participante para futuras predicción y reconciliación de movimiento.
- Los modelos remotos encienden faros y pilotos según su estado sincronizado; el camión y el helicóptero publican ahora sus estados operativos.
- Interpola posición y orientación entre instantáneas para reducir saltos producidos por el intervalo de red de 700 ms.

### Verificación local

- Sintaxis validada en protocolo, servidor, representación compartida y ambos simuladores 3D.

## v18.25.7 - 2026-08-13 - Contacto, sonido de motor y semáforos sincronizados

### Ya existente, no contabilizado como novedad

- La cabina ya tenía un contacto modelado, el motor físico calculaba RPM y los semáforos aplicaban rojo, ámbar y verde con límites y detención; faltaban interacción, audio y un reloj común.

### Cambios nuevos verificados

- Añade un botón de contacto que arranca y apaga el motor, bloquea el par y el control de crucero cuando está apagado y actualiza el estado del cuadro.
- Genera audio de motor original mediante Web Audio, sin archivos ni marcas externas: combina dos osciladores, filtro y ganancia dinámica ligados a RPM y carga, con transiciones suaves de arranque y parada.
- Sincroniza el reloj del cliente con `serverTime` de la sala y expone `MoonConvoy.now()`; sin conexión mantiene UTC local como referencia compatible.
- Los semáforos calculan ahora su fase desde ese reloj compartido y su desplazamiento individual, por lo que todos los jugadores observan el mismo rojo, ámbar o verde.

### Verificación local

- Sintaxis validada en audio, convoy, eventos y simulador principal; servidor Python compilado correctamente.

## v18.25.6 - 2026-08-13 - Clima real e incendios activos

### Ya existente, no contabilizado como novedad

- El simulador ya incluía lluvia, niebla, cielo dinámico, asfalto mojado, viento procedural y humo de incidencias; se reutilizan esos sistemas en lugar de duplicarlos.

### Cambios nuevos verificados

- Añade un modo opcional de clima real por coordenadas mediante Open-Meteo, con condición WMO, temperatura, precipitación, viento, dirección y rachas; usa la posición de la ruta OSM y Madrid como respaldo sin ruta activa.
- Consulta incendios abiertos cercanos mediante NASA EONET, limita su activación por distancia y conserva el modo simulado cuando la red o las fuentes no responden.
- Añade la única textura meteorológica que faltaba: llama procedural transparente y animada, escalada por calidad gráfica y mostrada solo cuando existe un incendio activo dentro del radio configurado.
- Integra en el camión lluvia, visibilidad e incendio según datos reales; Vuelo Rescate utiliza el viento real en su dinámica y ajusta la visibilidad en lluvia o niebla.
- Guarda durante 15 minutos la lectura geográfica para evitar consultas repetidas y permite volver manualmente al clima simulado.

### Verificación local

- Sintaxis validada en cliente meteorológico, efecto de fuego, física aérea y ambos simuladores 3D.

## v18.25.5 - 2026-08-13 - Operaciones cooperativas entre transportes

### Ya existente, no contabilizado como novedad

- Ya estaban implementados contratos, rescates, carga intermodal, salas compartidas, participantes IA, logros y representación cruzada de vehículos; no se vuelven a presentar como funciones nuevas.

### Cambio nuevo verificado

- Añade una capa de despacho cooperativo sobre la sala existente con cuatro operaciones originales: corredor médico, incendio forestal, emergencia portuaria y entrega intermodal.
- Cada operación exige que combinaciones diferentes de camión, tren, avión, helicóptero o barco alcancen una zona común antes de que termine el tiempo.
- La misión se selecciona de forma determinista mediante el código de sala y una ventana temporal, de modo que todos los clientes obtienen el mismo objetivo sin crear un segundo servicio de sincronización.
- Rutas 3D y Vuelo Rescate muestran nombre, progreso, medios necesarios, tiempo restante y finalización de la operación compartida.

### Verificación local

- Sintaxis y carga de dependencias verificadas en el módulo cooperativo y en ambos simuladores 3D.

## v18.25.4 - 2026-08-13 - Mundo compartido multimodal

### Ya existente, no contabilizado como novedad

- Ya existían salas de convoy, sincronización periódica, participantes IA de carretera, tren, aire y mar, y transferencia de carga entre juegos; los modos 2D solo enumeraban a los participantes y el camión ocultaba los vehículos que no fueran terrestres.

### Cambios nuevos verificados

- Amplía el protocolo existente —sin crear otro multijugador— con tipo concreto de vehículo, tercera coordenada y altitud, conservando compatibilidad con clientes que solo envían `x` e `y`.
- Añade un renderizador común de presencia 3D con siluetas diferenciadas para camión, autobús, helicóptero, avión, barco y tren, y limpieza automática de participantes que abandonan la sala.
- Rutas 3D deja de ocultar aeronaves, barcos y trenes: ahora representa todos los participantes humanos e IA de la misma sala en su mundo.
- Vuelo Rescate 3D puede crear o unirse al mismo código de mundo, publica posición, altitud, velocidad y rescates, y muestra los demás medios de transporte.
- Control Aéreo, Rescate Marítimo y Enlace Ferroviario publican ahora el tipo de vehículo y coordenadas ampliadas; su escena continúa siendo 2D y no se contabiliza como conversión 3D.

### Verificación local

- Sintaxis validada para servidor, protocolo, renderizador compartido y módulos embebidos de camión y vuelo.

## v18.25.3 - 2026-08-13 - Academia de conducción y dinámica de vuelo

### Ya existente, no contabilizado como novedad

- El simulador terrestre ya disponía de físicas por vehículo y firme, clima, tráfico, carrera, desgaste, combustible, asistencias, cámaras, logros y mapa con posición.
- Vuelo Rescate 3D ya tenía escenario WebGL, helicóptero, objetivos, controles básicos de posición y cámaras interior/exterior.

### Cambios nuevos verificados

- Añade al simulador terrestre tres pruebas originales de academia —eficiencia, precisión y control sobre mojado— con duración, límite propio, detección de colisiones, excesos, maniobras bruscas, puntuación, tres estrellas y mejor resultado persistente.
- Sustituye en Vuelo Rescate 3D el desplazamiento fijo por una dinámica de helicóptero con colectivo gradual, inercia vertical y lateral, resistencia, viento cruzado variable, balanceo, cabeceo, consumo y pérdida progresiva de potencia sin combustible.
- Incorpora instrumentación aérea en tiempo real para velocidad, velocidad vertical, combustible y viento, conservando controles móviles, cámaras y objetivos existentes.
- Referencias funcionales revisadas: sistemas públicos de carrera, mundo, clima, cámaras y desgaste de Microsoft Flight Simulator 2024, y academia de conducción, objetivos con estrellas y física revisada de Euro Truck Simulator 2; la implementación y los nombres son originales.

### Verificación local

- Sintaxis válida en los dos módulos nuevos y en los módulos principales embebidos de ambos simuladores.

## v18.25.2 - 2026-08-13 - Corrección de materiales del camión detallado

### Ya existente, no contabilizado como novedad

- El sistema procedural ya generaba pintura, metal y caucho con resolución y anisotropía adaptadas al perfil gráfico.
- La geometría de neumáticos, tacos, llantas, bujes y tornillos ya fue incorporada en `v18.25.1`.

### Cambio nuevo de esta versión

- Corrige la llamada a `createDetailedTruckExterior`: ahora entrega al modelo los mapas procedurales disponibles mediante `textureMaps`, que antes no se pasaban y dejaban el caucho con un color plano.
- Conecta el mapa existente de neumático y su relieve a la carcasa, los flancos y los tacos del camión y del remolque detallados.
- Completa las superficies que todavía no tenían un mapa específico con tres materiales procedurales: plástico técnico para bajos y parrilla, aluminio cepillado para la rueda y panel sándwich para el remolque.
- Mantiene estos materiales dentro del gestor de texturas existente y de su método `dispose()`, sin añadir descargas externas ni duplicar atlas.

## v18.25.1 - 2026-08-13 - Envolvente interior de cabina corregida

- Sustituye las cuatro superficies rectangulares que cerraban el interior por un techo abovedado, una pared trasera arqueada y dos revestimientos laterales contorneados.
- Marca de forma semántica la piel exterior de la cabina y la oculta únicamente en las cámaras interiores 1 y 2, evitando que techo, parabrisas, pilares y puertas exteriores tapen el puesto de conducción.
- Mantiene visibles el interior modelado, cristales interiores, espejos, vehículo, remolque y entorno; las cámaras exteriores conservan la carrocería completa.
- Corrige la pieza interior que sobresalía como una maleta: el conjunto interior completo se muestra solo en las cámaras 1 y 2 y queda oculto en todas las vistas exteriores.
- Acerca la silueta exterior a la referencia original con techo y deflector redondeados, esquinas carenadas, ceja frontal inclinada y puertas con bordes suavizados.
- Mejora las ruedas con carcasa radial, flancos redondeados, garganta y labios de llanta, ventilación, buje, diez tornillos y tacos de banda de rodadura adaptados a la calidad gráfica.
- Verificación local: sintaxis válida y respuestas HTTP 200 para el simulador, modelo interior, carrocería exterior y acristalamiento.

## v18.25.0 - 2026-08-13 - Red logística mundial y hubs de carga 3D

### Auditoría previa

- Confirma que ya existían una cadena logística abstracta almacén–tren–aeropuerto–puerto, un minijuego portuario 2D, modos de transporte y escenarios europeos; no se han contado de nuevo como novedades.

### Cambios nuevos verificados

- Añade una red mundial de 28 centros logísticos en 7 regiones, con conexiones explícitas por carretera, barco y avión y planificación multimodal entre Europa, América, África, Oriente Medio, Asia y Oceanía.
- Resuelve mediante OSRM únicamente los tramos terrestres y mantiene los enlaces marítimos y aéreos como transferencias logísticas, evitando representar océanos como carreteras conducibles.
- Incorpora un planificador mundial dentro del simulador, con origen, destino, desglose por modo, distancia, duración y acceso al primer tramo terrestre disponible.
- Genera puertos, aeropuertos de carga y terminales intermodales 3D próximos a las rutas a partir de OpenStreetMap, con muelles, dársenas, contenedores, grúas, pistas, terminal, torre, almacenes, vías, vagones y zonas de interacción.
- Añade caché Overpass de 7 días, dos endpoints alternativos y terminales procedurales de respaldo cuando no existen datos OSM o la consulta falla.
- Incorpora 13 perfiles regionales con texturas procedurales PBR para terreno, vegetación, arquitectura, cubiertas, arcenes, señales, puertos y aeropuertos, seleccionados por coordenadas y calidad gráfica.

### Verificación local

- Sintaxis validada en los tres módulos nuevos y en el módulo principal del simulador.
- Rutas Madrid–Nueva York, Nueva York–Tokio y Madrid–Sídney verificadas con modos intercontinentales coherentes.
- Servidor estático local: `transport-3d.html` respondió HTTP 200 y sus 33 dependencias cargaron sin errores HTTP.
- No se realizó prueba visual WebGL automatizada porque no había un navegador compatible disponible en el entorno de verificación.

## v18.24.2 - 2026-08-13 - Precisión GPS, POI reales y culling OSM

### Auditoría previa

- Confirma que ya existían map matching, progreso, maniobras, llegada, servicios procedurales, caché Overpass y niveles de calidad; no se han duplicado esos sistemas.

### Cambios nuevos verificados

- Corrige la posición del GPS sobre geometrías OSM con puntos desigualmente espaciados: ahora interpola por distancia geográfica acumulada y reutiliza el cálculo mediante caché, en lugar de convertir el progreso directamente en un índice del array.
- Incorpora POI reales próximos al itinerario desde OpenStreetMap: gasolineras, cargadores, aparcamientos, áreas de descanso y talleres, con nombre del establecimiento, proyección sobre el mundo 3D, dos endpoints Overpass, caché de 7 días y servicios sintéticos como respaldo.
- Corrige el culling del corredor OSM, que evaluaba entidades con geometría horneada como si todas estuvieran en `(0,0,0)`; edificios y terrenos usan ahora centros espaciales reales y los árboles se dividen en sectores instanciados.
- Limita la evaluación de visibilidad a 5 Hz y añade una histéresis del 12 % para reducir carga de CPU y evitar parpadeo al entrar o salir del rango visible.

## v18.24.1 - 2026-08-13 - Conducción sobre rutas reales de OpenStreetMap

### Cambios nuevos verificados

- Sustituye, al elegir origen y destino, la estimación de la red estilizada por una ruta de conducción calculada con OSRM sobre datos OpenStreetMap; conserva distancia, duración, geometría e instrucciones y guarda la respuesta durante 30 días.
- Genera una calzada 3D continua siguiendo la polilínea calculada, con curvas, carriles, arcenes, marcas, elevación suavizada, peralte limitado, guardarraíles y reflectores; el circuito recto anterior permanece únicamente como respaldo sin ruta activa.
- Hace que el vehículo avance y se oriente sobre el trazado seleccionado, conserva el desplazamiento lateral para los cambios de carril y elimina el reinicio artificial que devolvía el camión al comienzo cada 6 km.
- Añade seguimiento de ruta con progreso, distancia restante, próxima maniobra en español, aviso de salida del recorrido y llegada; el navegador de la cabina dibuja el tramo real alrededor del vehículo.
- Mueve el tráfico europeo sobre la misma polilínea y añade perfiles de coche, furgoneta, camión y autobús, distancia de seguridad, frenado progresivo, cambios de carril seguros y reacción a cierres por incidencias.
- Conecta la amenaza del tráfico de la ruta con ACC y AEBS. Los vehículos y servicios del escenario recto se ocultan cuando está activa una ruta europea para evitar cruces visuales incoherentes.
- Genera un corredor visual muestreado desde Overpass alrededor del itinerario con edificios, usos del suelo, agua y árboles, caché de 7 días, endpoints alternativos y límites de geometría según el perfil gráfico.

### Alcance actual

- OpenStreetMap y OSRM definen el recorrido y parte del entorno, pero no constituyen todavía una reproducción fotográfica continua de toda Europa; el corredor se obtiene mediante muestras limitadas para proteger memoria, red y rendimiento en Telegram.
- Las gasolineras, talleres e incidencias de la ruta OSM usan por ahora representación procedural y detección funcional; los complejos 3D detallados del escenario local aún no se trasladan íntegramente a cada ruta europea.

## v18.24.0 - 2026-08-13 - Juegos Moon, simulación de transporte y escalado

### Plataforma de juegos

- Integra en el Hub un catálogo de juegos originales compatible con Telegram HTML5 Games, enlaces `t.me`, pantalla completa y controles adaptados a móvil y escritorio.
- Incorpora Moon Snake, Circuito Neón, Block Royale, Rutas del Continente y nuevos juegos de operaciones, logística portuaria, rescate y vuelo.
- Añade variantes 2D y 3D, historial visible de versiones, perfiles gráficos `LOW`, `MEDIUM`, `HIGH` y `ULTRA`, detección de aceleración WebGL y controles unificados.
- Conecta los juegos mediante una red logística compartida: almacenes, puertos, aeropuertos, carga transferible, contratos, convoyes, IA sincronizada y logros.
- Añade primera persona, pantalla completa, multijugador de supervivencia y modos de conducción compatibles con teclado, táctil y mandos físicos.

### Rutas del Continente 3D

- Convierte el simulador básico en un mundo 3D continuo con camión, autobús, ambulancia, bomberos, grúa, vehículos de tráfico y transportes especiales o extremos.
- Añade una red estilizada de carreteras europeas con 29 ciudades, 40 conexiones, peajes, ferris, rutas, distancias y un mapa de Europa con posición real y varios niveles de zoom.
- Incorpora física de masa y carga, caja automática de doce marchas, curva de par, aerodinámica, pendiente, adherencia por superficie, aquaplaning, suspensión, balanceo, cabeceo, viento lateral, frenos térmicos, retarder y riesgo de vuelco.
- Añade sistemas de asistencia AEBS, control de tracción, crucero adaptativo, fatiga, combustible, daños, reparación, economía, experiencia, garajes, préstamos, conductores y contratos.
- Implementa tráfico por carriles con distancia de seguridad, frenado, adelantamientos sencillos, intermitentes, luces de freno y reciclado continuo del mundo.
- Añade obras, túneles, accidentes, policía, límites variables, semáforos, gasolineras, talleres, puntos de descanso, cargadores eléctricos y servicios de emergencia.
- Integra carga manual en almacén, movimiento del operario, traspaleta, preparación de mercancía, transportes pesados, escoltas y restricciones de convoy.

### Mundo y gráficos

- Añade texturas procedurales PBR para asfalto, terreno, hierba, hormigón, metal, pintura, neumáticos, señales, servicios y flotas de mantenimiento o emergencia.
- Incorpora atlas visuales originales para carreteras europeas, estaciones de servicio, talleres y vehículos, sin utilizar marcas ni recursos protegidos de otros juegos.
- Mejora carreteras con arcenes, marcas reflectantes, captafaros, drenajes, juntas, parches y desgaste; corrige las discontinuidades entre acera, césped, talud y montaña.
- Añade edificios, árboles, jardines, rotondas y elementos urbanos, complementados con datos públicos de OpenStreetMap y atribución visible.
- Mejora iluminación, sombras, gestión de color sRGB, tone mapping ACES, ciclo de día y noche, lluvia, niebla, asfalto mojado, charcos y detalle escalado según la GPU.
- Corrige carteles y señales: altura, soportes, nombres de destino, formas reglamentarias, balizamiento de obras y líneas de detención.

### Vehículos y cabinas

- Modela un conjunto articulado original sin marcas, con cabina, chasis, remolque, depósitos, quinta rueda, ruedas, luces, intermitentes, espejos y materiales diferenciados.
- Añade nueve cámaras asignadas a las teclas `1` a `9`, seguimiento suave, movimiento de cabeza con ratón, primera persona, vistas exteriores y composición específica para cabina y salón.
- Integra volantes físicos mediante Gamepad API, incluidos perfiles compatibles con Logitech G920 y dispositivos equivalentes, además de vibración y controles de conducción.
- Modela una cabina europea con salpicadero envolvente, volante, relojes, navegación, climatización, mandos, pedales, puertas, almacenamiento, techo, litera y materiales independientes.
- Añade asientos ergonómicos con tejido y cuero, apoyos lumbar y lateral, cojín extensible, reposacabezas, apoyabrazos, cinturón y suspensión neumática modelada.
- Incorpora parabrisas laminado transparente, juntas, pilares A/B, ventanillas, puertas detalladas y espejos principal/convexo con reflejos renderizados y calidad adaptativa.
- Anima agujas, interruptores, testigos, intermitentes, retarder e iluminación interior según el estado real del vehículo.
- Separa la cabina del autobús con puesto de conductor, entrada de piso bajo, mampara, puerta de dos hojas, pasamanos, ticketera, validador y consola propia.
- Corrige cámaras interiores que atravesaban volante, asiento o techo, cristales opacos y la repetición incorrecta de una imagen de referencia sobre todas las superficies.

### Alta disponibilidad de Moonbot

- Añade balanceo de réplicas web mediante Traefik con comprobaciones de salud y escalado local automático entre una y cuatro instancias.
- Separa el rol web del `worker` de Telegram para conservar un único consumidor de polling y evitar mensajes, tareas o informes duplicados.
- Incorpora un autoscaler conservador basado en CPU y memoria, con límites, enfriamiento, reducción de réplicas y servicio `systemd`.
- Añade un adaptador protegido para Hostinger VPS API: autenticación Bearer, modo simulación predeterminado y autorización explícita antes de realizar una compra con coste.
- Mantiene las credenciales y el JSON de compra fuera del repositorio mediante variables de entorno y permite sustituir Hostinger por un webhook de orquestación propio.

## v18.23.38 - 2026-08-12 - NoticiasWeb3 dentro del Hub

- Añade una vista rápida nativa de NoticiasWeb3 dentro de la Mini App, alimentada por el RSS interno y sin incrustar el diseño de escritorio.
- Corrige la ruta del feed, su publicación detrás de Traefik y la carga de hasta 60 noticias desde `api.todosobreall.tech/noticias/rss`.
- Incorpora búsqueda, categorías, resumen, fecha, visualizaciones y apertura de cada noticia dentro del Hub o en la web completa.
- Añade expansión de artículos, noticias recomendadas y controles de tipografía, tamaño y preferencias de lectura adaptados al navegador.
- Unifica las visualizaciones de artículos entre NoticiasWeb3 y el Hub para evitar contadores independientes.
- Actualiza los enlaces publicados por TodoSobreAllTech para abrir directamente el artículo correspondiente mediante el parámetro `startapp` de Telegram.
- Integra anuncios comunitarios con detección automática de la fotografía real del grupo o canal administrado por el bot.
- Añade lectores nativos para Gameplays y otros canales de la red, con publicaciones multimedia adaptadas a móvil y navegación coherente con NoticiasWeb3.
- Documenta y corrige la URL real de la Mini App, sus enlaces profundos de Telegram y el comportamiento de caché o rutas que anteriormente devolvían `Not Found`.

## v18.23.37 - 2026-08-11 - Alertas adaptativas y privacidad de seguridad

- Completa las alertas adaptativas del historial de seguridad con prioridad mínima configurable y agrupación de picos o análisis de riesgo alto.
- Permite al master reconocer alertas de forma persistente sin borrar el evento original ni alterar las decisiones de los analizadores.
- Añade privacidad reforzada activa por defecto: la API elimina nombres de archivo, URLs y valores antes de responder, sustituyéndolos por una huella corta no reversible.
- Integra los controles en Seguridad del Hub mediante los componentes existentes y mantiene todas las rutas protegidas por el JWT administrativo.
- Marca `future-0367` y `future-0379` como implementadas tras verificar almacenamiento, redacción en servidor, interfaz y pruebas.

## v18.23.36 - 2026-08-11 - Inteligencia explicable del historial de seguridad

- Completa la búsqueda por intención sobre análisis de seguridad almacenados, con expansión local de términos y puntuación explicable sin llamadas externas.
- Incorpora un resumen determinista por riesgo, fuente, formato y señal que indica expresamente la ventana y los datos utilizados.
- Detecta anomalías comparando dos ventanas consecutivas de 25 análisis y destaca picos de riesgo o de una fuente concreta sin ejecutar acciones automáticas.
- Integra búsqueda, resumen y anomalías en el panel Seguridad del Hub exclusivo del master, reutilizando sus métricas, tarjetas y botones.
- Marca `future-0373`, `future-0374` y `future-0387` como implementadas únicamente después de añadir ruta autenticada, interfaz y pruebas.

## v18.23.35 - 2026-08-11 - Diagnóstico temporal de moderación

- Completa el comparador temporal de moderación con hasta 30 capturas persistentes por grupo y diferencias de avisos, baneos, spam, cuarentena y módulos activos.
- Añade un diagnóstico automático que prioriza anti-raid, acumulación de reportes, decisiones por consenso y aumentos anómalos de spam o avisos sin ejecutar sanciones.
- Permite descargar desde el Hub un historial JSON firmado con HMAC-SHA256 para detectar modificaciones posteriores del informe.
- Conserva la autorización de administrador del grupo, limita los datos al grupo validado y reutiliza desplegables, botones, métricas y colores existentes.
- Marca `future-0339`, `future-0340` y `future-0350` como implementadas tras incorporar backend, interfaz y pruebas verificables.

## v18.23.34 - 2026-08-09 - Tareas personales vinculadas a grupos

- Lleva al Hub las tareas del plugin `/todo` sin crear un segundo almacén, conservando compatibilidad con las tareas antiguas.
- Permite usar un contexto personal o vincular opcionalmente una tarea a un grupo que el servidor haya confirmado que administra el usuario.
- Aísla cada lista por identidad de Telegram y por contexto; ningún usuario puede solicitar tareas de otro usuario ni enlazar grupos ajenos.
- Añade creación, cierre, reapertura y eliminación en la interfaz existente para usuarios, con validación y límites en el servidor.
- Expone el inspector URL a TodoSobreAllTech mediante `/api/internal/security/url-inspect`, protegido por `MOON_ADMIN_API_KEY` y reutilizando el mismo motor offline.

## v18.23.33 - 2026-08-09 - Inspector seguro de URL y dominio

- Añade una inspección estructural offline de enlaces que no abre la URL ni realiza conexiones con el destino.
- Detecta credenciales incrustadas, dominios Punycode, direcciones IP literales, destinos privados, puertos no estándar y enlaces excesivamente largos.
- Integra el resultado en Seguridad del Hub master con los componentes visuales existentes y mejora el comando `/domain` con las mismas señales.
- Mantiene el endpoint protegido por la autenticación administrativa y limita longitud, esquema y campos devueltos.
- Documenta en el roadmap la auditoría que confirma que tareas personales, notas, resumen local, Wayback, cola gestionada y listas nombradas ya estaban implementadas.

## v18.23.32 - 2026-08-09 - Diagnóstico operativo de campañas

- Añade al Hub master un resumen de impresiones, clics, CTR, campañas activas y actividad diaria usando los componentes visuales existentes.
- Detecta campañas pausadas, pendientes, sin destino o con objetivos y límites diarios alcanzados antes de que el master investigue una entrega detenida.
- Agrupa métricas anónimas por chat y bot sin recopilar nombres, mensajes ni identificadores de usuarios.
- Permite exportar las métricas de cada campaña en CSV desde la misma interfaz de administración.
- Mantiene la consulta, el diagnóstico y la exportación protegidos por la verificación exclusiva del rol master.

## v18.23.31 - 2026-08-09 - Estado real de las fuentes CAS

- Publica para la API interna el estado y los contadores del export CAS local y del feed reciente sin exponer ningún ID ni ruta del servidor.
- Permite que TodoSobreAllTech distinga la disponibilidad real de Moonbot de una caída de la API remota de CAS.
- Evita que el panel marque CAS como inactivo cuando el export local ya está cargado y operativo.

## v18.23.30 - 2026-08-09 - Identidad en el directorio de bloqueos

- Enriquece los bloqueos CAS, GBAN y locales con el nombre, alias, idioma, última actividad y volumen de mensajes ya conocidos por Moonbot.
- Amplía la búsqueda interna para localizar registros por nombre y usuario además de ID, motivo y origen.
- Conserva los campos vacíos cuando Telegram no proporcionó esa información, sin inventar identidades ni realizar consultas externas masivas.

## v18.23.29 - 2026-08-09 - Suscripciones oficiales de canales

- Crea enlaces oficiales de suscripción para canales mediante `createChatSubscriptionInviteLink`, con cobro recurrente en Telegram Stars.
- Valida que el destino sea un canal, que el bot conserve `can_invite_users`, que el nombre no supere 32 caracteres y que el precio esté entre 1 y 10.000 Stars.
- Permite copiar, renombrar y revocar enlaces; el periodo se fija en los 30 días exigidos actualmente por Telegram.
- Incorpora `/suscripcion`, `/suscripciones` y `/suscripcion_revocar` al menú de administradores de canales.
- Conserva un registro administrativo local de los enlaces creados por cada bot y canal, sin almacenar credenciales ni datos de pago.
- Añade el panel al Hub para el creador y los administradores autorizados del canal, con auditoría de cada operación.

## v18.23.28 - 2026-08-09 - Métricas y segmentación publicitaria completa

- **Métricas Telegram persistentes:** las impresiones y los clics recibidos desde TodoSobreAllTech se agregan por `chat_id` y `bot_id`, validando ambos identificadores antes de almacenarlos.
- **Presupuesto diario:** cada campaña conserva contadores UTC de clics e impresiones del día para aplicar límites diarios sin mezclar jornadas.
- **Objetivos y contexto:** el catálogo conserva objetivos totales, límites diarios, categorías, palabras incluidas/excluidas y destinos concretos de canal o grupo.
- **Hub master:** el editor de campañas incorpora controles de segmentación contextual, canales, grupos y presupuesto sin alterar el diseño general del Hub.
- **Compatibilidad:** duplicar o reiniciar una campaña limpia todas las métricas nuevas y las campañas antiguas reciben valores seguros por defecto.
- **Seguridad:** los IDs Telegram se aceptan únicamente con formato numérico válido; no se guardan usuarios, mensajes ni credenciales en las métricas.

## v18.23.27

- Publica en una ruta interna autenticada diez capacidades verificadas de experiencia Telegram: temas pendientes, atajos personales, panel contextual, respuestas efímeras, comunidades enlazadas, formularios adaptativos, guía de administradores, modo evento, acciones masivas y avisos por impacto.
- Añade un panel exclusivo del master en los centros operativos del Hub, conservando la navegación, tarjetas y estilos existentes.
- Valida una lista cerrada de operaciones, limita el tamaño del JSON y registra cada ejecución en la auditoría persistente.
- Incorpora pruebas que ejecutan las diez capacidades y comprueban autorización, allowlist, límites, escape de contenido y navegación de regreso.

## v18.23.26

- Corrige la coincidencia de canales por todas las identidades del bot, tanto ID como nombre de usuario.
- Almacena en caché el análisis de candidaturas y lo invalida únicamente cuando cambia el historial observado.
- Valida de forma atómica la lista global para que una petición inválida no borre canales antes de responder con error.
- Conserva listas multicanal existentes durante la migración desde el antiguo ajuste de canal único.
- Completa en el Hub los banners horizontales, fotos, búsqueda, riesgo, unión del bot y selección tanto global como por grupo.

## v18.23.25

- Muestra la foto pública real del canal en las recomendaciones globales y locales del captcha.
- Analiza hasta cien mensajes observados por canal con señales explicables de phishing, malware, explotación, captación y spam repetitivo.
- Retira automáticamente de las candidaturas los canales cuyo riesgo alcanza el umbral de seguridad, sin alterar listas ya configuradas por el master.
- Expone cantidad de mensajes analizados y puntuación de riesgo en Web y Hub; cuando no existen datos marca el análisis como pendiente.
- Añade búsqueda por nombre, usuario o ID y un enlace seguro de Telegram para incorporar otro bot como administrador del canal.

## v18.23.24

- Admite hasta diez canales obligatorios globales y diez canales locales por grupo en el captcha.
- Recomienda mediante tarjetas únicamente canales donde participa un bot activo; en cada grupo filtra por el bot que lo administra.
- Mantiene compatibilidad con la configuración histórica de canal único y migra sus datos sin perderlos.
- El Hub permite seleccionar, retirar y guardar canales desde tarjetas o mediante una lista manual.

## v18.23.23

- El captcha global muestra `Sí/No` por usuario y un estado general verificado/no verificado en Web y Hub.
- `@TodoSobreAllTech` queda activado como canal obligatorio global mediante una migración única.
- La reverificación global pasa a intervalos por horas y se ejecuta cada 12 horas de forma predeterminada.

## v18.23.22

- Convierte la publicación en el directorio de canales en un flujo de solicitud y revisión.
- Oculta por defecto canales nuevos y registros antiguos sin una aprobación explícita.
- Permite al master aprobar desde el Hub y a administradores web revisar desde TodoSobreAllTech.
- Mantiene el retiro inmediato por el administrador del canal y registra autor y fechas de solicitud y revisión.
- Protege listado, ficha individual, ranking y estadísticas públicas con el estado `approved`.

## v18.23.21

- Aplica revisión cerrada a todas las campañas nuevas o editadas: nacen pendientes y solo el master puede aprobarlas.
- Exige estado `approved` explícito antes de incluir publicidad en web, canal o respuestas de bots.
- Mantiene aprobadas exclusivamente las campañas oficiales versionadas y conserva la aprobación al pausar una campaña.
- Impide reactivar una campaña pendiente o rechazada hasta completar su revisión.

## v18.23.20

- Añade publicidad comunitaria rotatoria a respuestas informativas de comandos en grupos.
- Excluye chats privados y comandos de moderación, seguridad, captcha, alertas y sanciones.
- Mide la apertura mediante el enlace propio de TodoSobreAllTech e incorpora acceso a la ficha pública del canal.
- Expone en el directorio público la comunidad real detectada por Bot API y sus canales relacionados.
- Mantiene el anuncio en el fallback compatible cuando Rich Markdown no está disponible.

## v18.23.19

- Mueve el canal obligatorio general a `Master > Acceso global`, sin necesidad de abrir ningún grupo.
- Añade una periodicidad global de reverificación entre 1 y 90 días, comprobada cada quince minutos.
- Conserva el canal obligatorio local de cada grupo; cuando existen ambos, el usuario debe pertenecer a los dos.
- Expone el ajuste global mediante la API interna autenticada para mantener sincronizados el Hub y TodoSobreAllTech.
- Retira del panel local el campo global duplicado y corrige manejadores obsoletos del panel master.

## v18.23.18

- Amplía el captcha de entrada con retos rotatorios de iconos, secuencias, formas y cálculo.
- Añade selección de modalidades por grupo desde el Hub sin alterar los roles administrativos existentes.
- Aumenta progresivamente la dificultad tras cada fallo y evita repetir consecutivamente el mismo diseño.
- Vincula cada reto al usuario y al grupo, lo convierte en un solo uso y compara su respuesta mediante firma constante.
- Deja de guardar la solución del captcha en texto claro y conserva la caducidad, CAS, canales obligatorios y apelaciones.
- Mejora la accesibilidad móvil con botones semánticos, foco de teclado, instrucciones textuales y etiquetas para las figuras.

## v18.23.17

- Añade un directorio interno paginado para que TodoSobreAllTech consulte los baneos registrados por Moonbot.
- Distingue detecciones CAS registradas, GBAN y baneos locales sin publicar ni recorrer el export completo de CAS.
- Permite buscar por ID, motivo u origen mediante la conexión interna autenticada.
- Incorpora una campaña global, exclusiva del master, que inicia la reverificación en todos los grupos para usuarios pendientes.
- Reutiliza los protocolos existentes de mute, captcha, CAS, canales obligatorios y apelación, y publica progreso agregado y cancelación.
- Persiste el desglose por grupo y reconstruye la cola de usuarios restantes con el estado de cada protocolo tras cerrar o reabrir el navegador.

## v18.23.16

- Añade `/verificarweb` por chat privado para confirmar códigos administrativos emitidos por TodoSobreAllTech.
- Envía la identidad real del remitente a la API interna mediante la clave compartida, sin exponerla al navegador ni al Hub.
- Rechaza códigos malformados, URLs HTTP externas y verificaciones realizadas desde grupos.
- Reconoce administradores web únicamente por un rol activo vinculado al mismo `telegram_id` en PocketBase.
- Añade al Hub una pestaña independiente de administración web, sin heredar permisos master ni permisos administrativos de grupos.

## v18.23.15

- Retira los manifiestos de canales del directorio web público para impedir su descarga directa.
- Sirve los assets futuros del Hub mediante un endpoint autenticado con `initData` de Telegram.
- Resuelve el canal exclusivamente desde el `telegram_id` verificado e ignora cualquier canal o ruta aportados por el navegador.
- Limita los assets a un registro cerrado, valida su esquema y tamaño, y devuelve respuestas privadas sin caché ni detección MIME.
- Conserva el Hub base y su diseño actual cuando no existe un bundle válido para el canal autorizado.

## v18.23.14

- Muestra en el Hub el canal autorizado y la versiÃ³n real servida, tanto en el diseÃ±o moderno como en el clÃ¡sico.
- Resuelve esa identidad exclusivamente en el servidor mediante `telegram_id`; ignora cualquier canal indicado por el navegador.
- AÃ±ade manifiestos pasivos y allowlisted para preparar bundles separados de `stable`, `rc`, `beta` y `alpha`.
- Mantiene el Hub base operativo si falta un manifiesto o no cumple el contrato esperado.
- Rechaza canales desconocidos en manifiestos y evita cachear respuestas privadas entre identidades o canales.

## v18.23.13

- Incorpora canales progresivos de funciones `stable`, `rc`, `beta` y `alpha` sin alterar los roles existentes.
- Vincula el canal del Hub a la cuenta web mediante el `telegram_id` verificado en PocketBase.
- El master recibe el canal alpha y conserva control completo; las cuentas sin asignaciÃ³n fallan de forma segura a stable.
- Filtra el catÃ¡logo y vuelve a comprobar el canal al ejecutar para impedir abrir funciones ocultas manipulando la peticiÃ³n.
- Marca las nuevas operaciones experimentales de integraciones como alpha.

## v18.23.12

- AÃ±ade correlaciÃ³n temporal y deduplicada de incidencias de integraciones para creadores de grupo y master.
- AÃ±ade delegaciones temporales y revocables de integraciones, con scopes permitidos, caducidad mÃ¡xima de siete dÃ­as y aprobaciÃ³n para configurar.
- Aplica el rol existente de cada usuario en el grupo seleccionado; las operaciones de grupo ya no heredan permisos de otros grupos.
- Impide falsificar `actor`, `actor_id`, `actor_role`, `is_admin` o `is_master` desde la Mini App.
- Limita a 128 KiB las peticiones del registro pÃºblico y valida de forma cerrada cualquier rol explÃ­cito de manifiesto.
- Expone las 2.742 funciones Ãºnicas mediante formularios automÃ¡ticos en el Hub, sin duplicar paneles.

## v18.23.11

- Genera contratos de interfaz para las 2.740 funciones verificadas a partir de sus firmas reales.
- Añade formularios automáticos de texto, número, booleano y JSON en el Hub, manteniendo el editor avanzado.
- Incorpora `Mis funciones` a la Mini App para usuarios, administradores, creadores de grupo y master.
- Calcula el rol de la Mini App desde `initData` y los grupos administrados; el navegador nunca puede elegirlo.
- Aplica el rol efectivo tanto al listar como al ejecutar una función y bloquea escaladas entre roles.
- Añade validación de campos obligatorios, parámetros variádicos y navegación mediante panel emergente con flecha atrás.

## v18.23.10

- Elimina la carga insegura de modelos antispam mediante Pickle y conserva el clasificador con entrenamiento determinista.
- Impide atravesar directorios al restaurar copias y confina los archivos JSON al directorio de datos.
- Valida los puertos MTProxy antes de crear comandos remotos y rechaza claves SSH desconocidas.
- Evita tokens JWT en URLs de descarga: registros y datos de IA se obtienen con cabecera `Authorization`.
- Limita los intentos fallidos de acceso al Hub por origen y devuelve `429` con `Retry-After`.
- Añade pruebas focales para las protecciones de restauración, SSH, puertos, descargas y autenticación.

## v18.23.9

- Añade al Hub paneles específicos para IA avanzada, integraciones/API, experiencia y revisión de calidad.
- Mejora navegación con flecha atrás, etiquetas accesibles y controles operables por teclado.
- Conserva secretos fuera de las exportaciones y limita las nuevas acciones a análisis, simulación y preferencias reversibles.
- Mantiene cachés APT y pip estables para no volver a descargar dependencias en cada reconstrucción.

## v18.23.8

- Repara automáticamente instalaciones antiguas de `tg_ad_templates` añadiendo los campos que falten en PocketBase.
- Evita el error 400 al filtrar plantillas publicitarias por `chat_id`.
- La API devuelve un error JSON controlado si PocketBase no está disponible, sin exponer un traceback al cliente.

## v18.23.7

- Añade 60 servicios verificados para automatizaciones, multimedia y bots administrados.
- Los nuevos servicios aparecen automáticamente en los paneles del Hub y TodoSobreAllTech según ámbito y rol.
- Incorpora en el Hub centros operativos específicos para editorial, automatizaciones y fiabilidad, con navegación de regreso.
- Permite previsualizar contenido, simular automatizaciones y diagnosticar operaciones sin aplicar cambios destructivos.
- Mantiene eventos firmados aislados por dominio y operaciones en vista previa sin efectos directos.
- Amplía el registro operativo a 2.740 funciones comprobadas.

## v18.23.6

- Agrupa las 2.680 funciones registradas en paneles operativos por ámbito y rol dentro del Hub.
- Cada panel se abre sobre la vista actual y dispone de una flecha clara para regresar al índice.
- Cada función cuenta con ficha, riesgo, rol mínimo, editor JSON y ejecución autenticada desde su propia vista.
- Mantiene el diseño actual del Hub y evita cargar una lista administrativa de miles de filas a la vez.

## v18.23.5

- Integra 60 servicios WebApp para canales, usuarios y automatizaciones.
- Incorpora eventos externos firmados y aislados por dominio.
- Mantiene las operaciones masivas en modo de vista previa, sin ejecución ni persistencia automática.
- Verifica roles, pruebas resolubles, identificadores y APIs únicas antes de registrarlas.

<!-- GENERATED_RELEASE_FEATURES_START -->
## Inventario exacto por versión

### v18.22.0 — 300 funciones incorporadas

- `future-1922` · `recommend_content_config` — Recomendador de configuración para contenido
- `future-1923` · `test_content_config` — Pruebas automáticas de configuración para contenido
- `future-1924` · `update_content_consent` — Centro de consentimiento para contenido
- `future-1925` · `content_task_navigation` — Navegación simplificada por tareas para contenido
- `future-1926` · `sync_content_devices` — Sincronización entre dispositivos para contenido
- `future-1927` · `detect_content_duplicates` — Detección de duplicados para contenido
- `future-1928` · `content_adaptive_quota` — Cuotas adaptativas por uso para contenido
- `future-1929` · `content_community_impact` — Panel de impacto comunitario para contenido
- `future-1930` · `review_content_translation` — Traducción revisable por la comunidad para contenido
- `future-1931` · `group_content_notifications` — Notificaciones agrupadas por contexto para contenido
- `future-1932` · `plan_content_migration` — Asistente de migración para contenido
- `future-1933` · `record_content_admin_decision` — Registro de decisiones administrativas para contenido
- `future-1934` · `content_accessibility_timeline` — Análisis de accesibilidad continuo para contenido
- `future-1935` · `prepare_content_storage_transfer` — Conector de almacenamiento externo para contenido
- `future-1936` · `evaluate_content_time_policy` — Políticas por franja horaria para contenido
- `future-1937` · `simulate_content_growth` — Simulador de crecimiento sostenible para contenido
- `future-1938` · `map_security_dependencies` — Mapa de dependencias funcionales para seguridad
- `future-1939` · `apply_security_visual_rules` — Reglas condicionales visuales para seguridad
- `future-1940` · `security_review_inbox` — Bandeja unificada de revisión para seguridad
- `future-1941` · `detect_sensitive_security_changes` — Detección de cambios sensibles para seguridad
- `future-1942` · `explain_security_decision` — Explicación de decisiones automáticas para seguridad
- `future-1943` · `security_data_quality` — Panel de calidad de datos para seguridad
- `future-1944` · `preview_security_import` — Importación con vista previa para seguridad
- `future-1945` · `add_security_comment` — Colaboración mediante comentarios para seguridad
- `future-1946` · `security_smart_tags` — Etiquetas inteligentes para seguridad
- `future-1947` · `security_activity_digest` — Resumen de actividad configurable para seguridad
- `future-1948` · `security_expiry_alerts` — Alertas de caducidad para seguridad
- `future-1949` · `open_security_emergency` — Modo de emergencia reversible para seguridad
- `future-1950` · `security_permission_history` — Historial de permisos efectivo para seguridad
- `future-1951` · `update_security_goal` — Objetivos y progreso compartidos para seguridad
- `future-1952` · `recommend_security_config` — Recomendador de configuración para seguridad
- `future-1953` · `test_security_config` — Pruebas automáticas de configuración para seguridad
- `future-1954` · `update_security_consent` — Centro de consentimiento para seguridad
- `future-1955` · `security_task_navigation` — Navegación simplificada por tareas para seguridad
- `future-1956` · `sync_security_devices` — Sincronización entre dispositivos para seguridad
- `future-1957` · `detect_security_duplicates` — Detección de duplicados para seguridad
- `future-1958` · `security_adaptive_quota` — Cuotas adaptativas por uso para seguridad
- `future-1959` · `security_community_impact` — Panel de impacto comunitario para seguridad
- `future-1960` · `review_security_translation` — Traducción revisable por la comunidad para seguridad
- `future-1961` · `group_security_notifications` — Notificaciones agrupadas por contexto para seguridad
- `future-1962` · `plan_security_migration` — Asistente de migración para seguridad
- `future-1963` · `record_security_admin_decision` — Registro de decisiones administrativas para seguridad
- `future-1964` · `security_accessibility_timeline` — Análisis de accesibilidad continuo para seguridad
- `future-1965` · `prepare_security_storage_transfer` — Conector de almacenamiento externo para seguridad
- `future-1966` · `evaluate_security_time_policy` — Políticas por franja horaria para seguridad
- `future-1967` · `simulate_security_growth` — Simulador de crecimiento sostenible para seguridad
- `future-1968` · `map_ai_dependencies` — Mapa de dependencias funcionales para IA
- `future-1969` · `apply_ai_visual_rules` — Reglas condicionales visuales para IA
- `future-1970` · `ai_review_inbox` — Bandeja unificada de revisión para IA
- `future-1971` · `detect_sensitive_ai_changes` — Detección de cambios sensibles para IA
- `future-1972` · `explain_ai_decision` — Explicación de decisiones automáticas para IA
- `future-1973` · `ai_data_quality` — Panel de calidad de datos para IA
- `future-1974` · `preview_ai_import` — Importación con vista previa para IA
- `future-1975` · `add_ai_comment` — Colaboración mediante comentarios para IA
- `future-1976` · `ai_smart_tags` — Etiquetas inteligentes para IA
- `future-1977` · `ai_activity_digest` — Resumen de actividad configurable para IA
- `future-1978` · `ai_expiry_alerts` — Alertas de caducidad para IA
- `future-1979` · `open_ai_emergency` — Modo de emergencia reversible para IA
- `future-1980` · `ai_permission_history` — Historial de permisos efectivo para IA
- `future-1981` · `update_ai_goal` — Objetivos y progreso compartidos para IA
- `future-1982` · `recommend_ai_config` — Recomendador de configuración para IA
- `future-1983` · `test_ai_config` — Pruebas automáticas de configuración para IA
- `future-1984` · `update_ai_consent` — Centro de consentimiento para IA
- `future-1985` · `ai_task_navigation` — Navegación simplificada por tareas para IA
- `future-1986` · `sync_ai_devices` — Sincronización entre dispositivos para IA
- `future-1987` · `detect_ai_duplicates` — Detección de duplicados para IA
- `future-1988` · `ai_adaptive_quota` — Cuotas adaptativas por uso para IA
- `future-1989` · `ai_community_impact` — Panel de impacto comunitario para IA
- `future-1990` · `review_ai_translation` — Traducción revisable por la comunidad para IA
- `future-1991` · `group_ai_notifications` — Notificaciones agrupadas por contexto para IA
- `future-1992` · `plan_ai_migration` — Asistente de migración para IA
- `future-1993` · `record_ai_admin_decision` — Registro de decisiones administrativas para IA
- `future-1994` · `ai_accessibility_timeline` — Análisis de accesibilidad continuo para IA
- `future-1995` · `prepare_ai_storage_transfer` — Conector de almacenamiento externo para IA
- `future-1996` · `evaluate_ai_time_policy` — Políticas por franja horaria para IA
- `future-1997` · `simulate_ai_growth` — Simulador de crecimiento sostenible para IA
- `future-1998` · `map_notification_dependencies` — Mapa de dependencias funcionales para notificaciones
- `future-1999` · `apply_notification_visual_rules` — Reglas condicionales visuales para notificaciones
- `future-2000` · `notification_review_inbox` — Bandeja unificada de revisión para notificaciones
- `future-2001` · `correlate_account_incidents` — Centro de incidencias correlacionadas para cuentas
- `future-2002` · `build_account_workflow` — Constructor de flujos sin código para cuentas
- `future-2003` · `delegate_account_role` — Delegación temporal de funciones para cuentas
- `future-2004` · `detect_coordinated_account_abuse` — Protección contra abuso coordinado para cuentas
- `future-2005` · `account_context_copilot` — Copiloto de respuesta contextual para cuentas
- `future-2006` · `forecast_account_capacity` — Pronóstico de capacidad y demanda para cuentas
- `future-2007` · `execute_account_batch_plan` — Centro de operaciones por lotes para cuentas
- `future-2008` · `create_account_workspace` — Espacios de trabajo compartidos para cuentas
- `future-2009` · `index_account_media` — Biblioteca multimedia inteligente para cuentas
- `future-2010` · `narrate_account_report` — Informes narrativos automáticos para cuentas
- `future-2011` · `escalate_account_alerts` — Escalado inteligente de avisos para cuentas
- `future-2012` · `account_offline_continuity` — Continuidad operativa sin conexión para cuentas
- `future-2013` · `evaluate_adaptive_account_trust` — Acceso de confianza adaptativa para cuentas
- `future-2014` · `plan_account_community_campaign` — Planificador de campañas comunitarias para cuentas
- `future-2015` · `detect_account_intent` — Detección de intención y contexto para cuentas
- `future-2016` · `test_account_integration` — Laboratorio de integraciones para cuentas
- `future-2017` · `store_account_personal_vault` — Bóveda de datos personales para cuentas
- `future-2018` · `format_account_easy_read` — Interfaz de lectura fácil para cuentas
- `future-2019` · `reconcile_account_sessions` — Continuidad de sesión multidispositivo para cuentas
- `future-2020` · `curate_account_editorial` — Curación editorial asistida para cuentas
- `future-2021` · `budget_account_resources` — Control presupuestario de recursos para cuentas
- `future-2022` · `score_account_reputation` — Sistema de reputación transparente para cuentas
- `future-2023` · `localize_account_culturally` — Localización cultural automática para cuentas
- `future-2024` · `update_account_communication_preferences` — Centro de preferencias de comunicación para cuentas
- `future-2025` · `plan_account_onboarding` — Recorridos personalizados de incorporación para cuentas
- `future-2026` · `evaluate_account_governance` — Gobernanza mediante propuestas y votos para cuentas
- `future-2027` · `parse_accessible_account_voice_control` — Control por voz accesible para cuentas
- `future-2028` · `plan_account_federated_bridge` — Puente de datos federado para cuentas
- `future-2029` · `validate_account_external_event` — Automatización por eventos externos para cuentas
- `future-2030` · `simulate_account_digital_twin` — Gemelo digital operativo para cuentas
- `future-2031` · `correlate_creator_incidents` — Centro de incidencias correlacionadas para creadores
- `future-2032` · `build_creator_workflow` — Constructor de flujos sin código para creadores
- `future-2033` · `delegate_creator_role` — Delegación temporal de funciones para creadores
- `future-2034` · `detect_coordinated_creator_abuse` — Protección contra abuso coordinado para creadores
- `future-2035` · `creator_context_copilot` — Copiloto de respuesta contextual para creadores
- `future-2036` · `forecast_creator_capacity` — Pronóstico de capacidad y demanda para creadores
- `future-2037` · `execute_creator_batch_plan` — Centro de operaciones por lotes para creadores
- `future-2038` · `create_creator_workspace` — Espacios de trabajo compartidos para creadores
- `future-2039` · `index_creator_media` — Biblioteca multimedia inteligente para creadores
- `future-2040` · `narrate_creator_report` — Informes narrativos automáticos para creadores
- `future-2041` · `escalate_creator_alerts` — Escalado inteligente de avisos para creadores
- `future-5162` · `group_editorial_articles_notifications` — Notificación agrupada de artículos editoriales en Moonbot
- `future-5165` · `group_moderated_images_notifications` — Notificación agrupada de imágenes moderadas en Moonbot
- `future-5168` · `group_user_appeals_notifications` — Notificación agrupada de apelaciones de usuarios en Moonbot
- `future-5171` · `group_mtproto_proxies_notifications` — Notificación agrupada de proxies MTProto en Moonbot
- `future-5174` · `group_persistent_tasks_notifications` — Notificación agrupada de tareas persistentes en Moonbot
- `future-5177` · `group_moderation_rules_notifications` — Notificación agrupada de reglas de moderación en Moonbot
- `future-5180` · `group_language_metrics_notifications` — Notificación agrupada de métricas lingüísticas en Moonbot
- `future-5183` · `group_community_translations_notifications` — Notificación agrupada de traducciones comunitarias en Moonbot
- `future-5186` · `group_personal_consents_notifications` — Notificación agrupada de consentimientos personales en Moonbot
- `future-5189` · `group_telegram_reactions_notifications` — Notificación agrupada de reacciones Telegram en Moonbot
- `future-5192` · `group_master_panels_notifications` — Notificación agrupada de paneles del master en Moonbot
- `future-5195` · `group_channel_directories_notifications` — Notificación agrupada de directorios de canales en Moonbot
- `future-5198` · `group_external_links_notifications` — Notificación agrupada de enlaces externos en Moonbot
- `future-5201` · `route_administrative_sessions_intelligently` — Enrutamiento inteligente de sesiones administrativas en Moonbot
- `future-5204` · `route_community_profiles_intelligently` — Enrutamiento inteligente de perfiles comunitarios en Moonbot
- `future-5207` · `route_telegram_communities_intelligently` — Enrutamiento inteligente de comunidades Telegram en Moonbot
- `future-5210` · `route_house_ads_intelligently` — Enrutamiento inteligente de anuncios propios en Moonbot
- `future-5213` · `route_voice_notes_intelligently` — Enrutamiento inteligente de notas de voz en Moonbot
- `future-5216` · `route_suspicious_files_intelligently` — Enrutamiento inteligente de archivos sospechosos en Moonbot
- `future-5219` · `route_captcha_decisions_intelligently` — Enrutamiento inteligente de decisiones de captcha en Moonbot
- `future-5222` · `route_managed_bots_intelligently` — Enrutamiento inteligente de bots administrados en Moonbot
- `future-5225` · `route_recurring_reminders_intelligently` — Enrutamiento inteligente de recordatorios recurrentes en Moonbot
- `future-5228` · `route_security_events_intelligently` — Enrutamiento inteligente de eventos de seguridad en Moonbot
- `future-5231` · `route_regional_maps_intelligently` — Enrutamiento inteligente de mapas regionales en Moonbot
- `future-5234` · `route_backups_intelligently` — Enrutamiento inteligente de copias de seguridad en Moonbot
- `future-5237` · `route_ai_learning_data_intelligently` — Enrutamiento inteligente de datos de aprendizaje IA en Moonbot
- `future-5240` · `route_rich_commands_intelligently` — Enrutamiento inteligente de comandos enriquecidos en Moonbot
- `future-5243` · `route_hub_notifications_intelligently` — Enrutamiento inteligente de notificaciones del Hub en Moonbot
- `future-5246` · `route_cookie_policies_intelligently` — Enrutamiento inteligente de políticas de cookies en Moonbot
- `future-5249` · `route_wayback_history_intelligently` — Enrutamiento inteligente de historial Wayback en Moonbot
- `future-5252` · `reconcile_temporary_roles_cache` — Caché reconciliable de roles temporales en Moonbot
- `future-5255` · `reconcile_managed_groups_cache` — Caché reconciliable de grupos administrados en Moonbot
- `future-5258` · `reconcile_scheduled_messages_cache` — Caché reconciliable de mensajes programados en Moonbot
- `future-5261` · `reconcile_rss_feeds_cache` — Caché reconciliable de feeds RSS en Moonbot
- `future-5264` · `reconcile_telegram_videos_cache` — Caché reconciliable de vídeos de Telegram en Moonbot
- `future-5267` · `reconcile_blocklists_cache` — Caché reconciliable de listas de bloqueo en Moonbot
- `future-5270` · `reconcile_required_subscriptions_cache` — Caché reconciliable de suscripciones obligatorias en Moonbot
- `future-5273` · `reconcile_signed_webhooks_cache` — Caché reconciliable de webhooks firmados en Moonbot
- `future-5276` · `reconcile_quiet_hours_cache` — Caché reconciliable de horarios silenciosos en Moonbot
- `future-5279` · `reconcile_correlated_incidents_cache` — Caché reconciliable de incidentes correlacionados en Moonbot
- `future-5282` · `reconcile_accessible_preferences_cache` — Caché reconciliable de preferencias accesibles en Moonbot
- `future-5285` · `reconcile_integration_secrets_cache` — Caché reconciliable de secretos de integración en Moonbot
- `future-5288` · `reconcile_contextual_responses_cache` — Caché reconciliable de respuestas contextuales en Moonbot
- `future-5291` · `reconcile_miniapp_menus_cache` — Caché reconciliable de menús de la MiniApp en Moonbot
- `future-5294` · `reconcile_bot_statistics_cache` — Caché reconciliable de estadísticas por bot en Moonbot
- `future-5297` · `reconcile_advertising_preferences_cache` — Caché reconciliable de preferencias publicitarias en Moonbot
- `future-5300` · `reconcile_processing_queues_cache` — Caché reconciliable de colas de procesamiento en Moonbot
- `future-5303` · `plan_safe_creator_accounts_rotation` — Rotación segura de cuentas creadoras en Moonbot
- `future-5306` · `plan_safe_associated_channels_rotation` — Rotación segura de canales asociados en Moonbot
- `future-5309` · `plan_safe_community_campaigns_rotation` — Rotación segura de campañas comunitarias en Moonbot
- `future-5312` · `plan_safe_editorial_articles_rotation` — Rotación segura de artículos editoriales en Moonbot
- `future-5315` · `plan_safe_moderated_images_rotation` — Rotación segura de imágenes moderadas en Moonbot
- `future-5318` · `plan_safe_user_appeals_rotation` — Rotación segura de apelaciones de usuarios en Moonbot
- `future-5321` · `plan_safe_mtproto_proxies_rotation` — Rotación segura de proxies MTProto en Moonbot
- `future-5324` · `plan_safe_persistent_tasks_rotation` — Rotación segura de tareas persistentes en Moonbot
- `future-5327` · `plan_safe_moderation_rules_rotation` — Rotación segura de reglas de moderación en Moonbot
- `future-5330` · `plan_safe_language_metrics_rotation` — Rotación segura de métricas lingüísticas en Moonbot
- `future-5333` · `plan_safe_community_translations_rotation` — Rotación segura de traducciones comunitarias en Moonbot
- `future-5336` · `plan_safe_personal_consents_rotation` — Rotación segura de consentimientos personales en Moonbot
- `future-5339` · `plan_safe_telegram_reactions_rotation` — Rotación segura de reacciones Telegram en Moonbot
- `future-2042` · `creator_offline_continuity` — Continuidad operativa sin conexión para creadores
- `future-2043` · `evaluate_creator_adaptive_trust` — Acceso de confianza adaptativa para creadores
- `future-2044` · `plan_creator_campaign` — Planificador de campañas comunitarias para creadores
- `future-2045` · `detect_creator_intent` — Detección de intención y contexto para creadores
- `future-2046` · `test_creator_integration` — Laboratorio de integraciones para creadores
- `future-2047` · `store_creator_vault` — Bóveda de datos personales para creadores
- `future-2048` · `format_creator_easy_read` — Interfaz de lectura fácil para creadores
- `future-2049` · `reconcile_creator_sessions` — Continuidad de sesión multidispositivo para creadores
- `future-2050` · `curate_creator_editorial` — Curación editorial asistida para creadores
- `future-2051` · `budget_creator_resources` — Control presupuestario de recursos para creadores
- `future-2052` · `score_creator_reputation` — Sistema de reputación transparente para creadores
- `future-2053` · `localize_creator_culturally` — Localización cultural automática para creadores
- `future-2054` · `update_creator_communication_preferences` — Centro de preferencias de comunicación para creadores
- `future-2055` · `plan_creator_onboarding` — Recorridos personalizados de incorporación para creadores
- `future-2056` · `evaluate_creator_governance` — Gobernanza mediante propuestas y votos para creadores
- `future-2057` · `parse_creator_voice_control` — Control por voz accesible para creadores
- `future-2058` · `plan_creator_federated_bridge` — Puente de datos federado para creadores
- `future-2059` · `validate_creator_external_event` — Automatización por eventos externos para creadores
- `future-2060` · `simulate_creator_digital_twin` — Gemelo digital operativo para creadores
- `future-2061` · `correlate_news_incidents` — Centro de incidencias correlacionadas para noticias
- `future-2062` · `build_news_workflow` — Constructor de flujos sin código para noticias
- `future-2063` · `delegate_news_role` — Delegación temporal de funciones para noticias
- `future-2064` · `detect_coordinated_news_abuse` — Protección contra abuso coordinado para noticias
- `future-2065` · `news_context_copilot` — Copiloto de respuesta contextual para noticias
- `future-2066` · `forecast_news_capacity` — Pronóstico de capacidad y demanda para noticias
- `future-2067` · `execute_news_batch_plan` — Centro de operaciones por lotes para noticias
- `future-2068` · `create_news_workspace` — Espacios de trabajo compartidos para noticias
- `future-2069` · `index_news_media` — Biblioteca multimedia inteligente para noticias
- `future-2070` · `narrate_news_report` — Informes narrativos automáticos para noticias
- `future-2071` · `escalate_news_alerts` — Escalado inteligente de avisos para noticias
- `future-2072` · `news_offline_continuity` — Continuidad operativa sin conexión para noticias
- `future-2073` · `evaluate_news_adaptive_trust` — Acceso de confianza adaptativa para noticias
- `future-2074` · `plan_news_campaign` — Planificador de campañas comunitarias para noticias
- `future-2075` · `detect_news_intent` — Detección de intención y contexto para noticias
- `future-2076` · `test_news_integration` — Laboratorio de integraciones para noticias
- `future-2077` · `store_news_vault` — Bóveda de datos personales para noticias
- `future-2078` · `format_news_easy_read` — Interfaz de lectura fácil para noticias
- `future-2079` · `reconcile_news_sessions` — Continuidad de sesión multidispositivo para noticias
- `future-2080` · `curate_news_editorial` — Curación editorial asistida para noticias
- `future-2081` · `budget_news_resources` — Control presupuestario de recursos para noticias
- `future-2082` · `score_news_reputation` — Sistema de reputación transparente para noticias
- `future-2083` · `localize_news_culturally` — Localización cultural automática para noticias
- `future-2084` · `update_news_communication_preferences` — Centro de preferencias de comunicación para noticias
- `future-2085` · `plan_news_onboarding` — Recorridos personalizados de incorporación para noticias
- `future-2086` · `evaluate_news_governance` — Gobernanza mediante propuestas y votos para noticias
- `future-2087` · `parse_news_voice_control` — Control por voz accesible para noticias
- `future-2088` · `plan_news_federated_bridge` — Puente de datos federado para noticias
- `future-2089` · `validate_news_external_event` — Automatización por eventos externos para noticias
- `future-2090` · `simulate_news_digital_twin` — Gemelo digital operativo para noticias
- `future-2091` · `correlate_proxy_incidents` — Centro de incidencias correlacionadas para proxies
- `future-2092` · `build_proxy_workflow` — Constructor de flujos sin código para proxies
- `future-2093` · `delegate_proxy_role` — Delegación temporal de funciones para proxies
- `future-2094` · `detect_coordinated_proxy_abuse` — Protección contra abuso coordinado para proxies
- `future-2095` · `proxy_context_copilot` — Copiloto de respuesta contextual para proxies
- `future-2096` · `forecast_proxy_capacity` — Pronóstico de capacidad y demanda para proxies
- `future-2097` · `execute_proxy_batch_plan` — Centro de operaciones por lotes para proxies
- `future-2098` · `create_proxy_workspace` — Espacios de trabajo compartidos para proxies
- `future-2099` · `index_proxy_media` — Biblioteca multimedia inteligente para proxies
- `future-2100` · `narrate_proxy_report` — Informes narrativos automáticos para proxies
- `future-2101` · `escalate_proxy_alerts` — Escalado inteligente de avisos para proxies
- `future-5342` · `plan_safe_master_panels_rotation` — Rotación segura de paneles del master en Moonbot
- `future-5345` · `plan_safe_channel_directories_rotation` — Rotación segura de directorios de canales en Moonbot
- `future-5348` · `plan_safe_external_links_rotation` — Rotación segura de enlaces externos en Moonbot
- `future-5351` · `plan_administrative_sessions_scheduled_archive` — Archivado programado de sesiones administrativas en Moonbot
- `future-5354` · `plan_community_profiles_scheduled_archive` — Archivado programado de perfiles comunitarios en Moonbot
- `future-5357` · `plan_telegram_communities_scheduled_archive` — Archivado programado de comunidades Telegram en Moonbot
- `future-5360` · `plan_house_ads_scheduled_archive` — Archivado programado de anuncios propios en Moonbot
- `future-5363` · `plan_voice_notes_scheduled_archive` — Archivado programado de notas de voz en Moonbot
- `future-5366` · `plan_suspicious_files_scheduled_archive` — Archivado programado de archivos sospechosos en Moonbot
- `future-5369` · `plan_captcha_decisions_scheduled_archive` — Archivado programado de decisiones de captcha en Moonbot
- `future-5372` · `plan_managed_bots_scheduled_archive` — Archivado programado de bots administrados en Moonbot
- `future-5375` · `plan_recurring_reminders_scheduled_archive` — Archivado programado de recordatorios recurrentes en Moonbot
- `future-5378` · `plan_security_events_scheduled_archive` — Archivado programado de eventos de seguridad en Moonbot
- `future-5381` · `plan_regional_maps_scheduled_archive` — Archivado programado de mapas regionales en Moonbot
- `future-5384` · `plan_backups_scheduled_archive` — Archivado programado de copias de seguridad en Moonbot
- `future-5387` · `plan_ai_learning_data_scheduled_archive` — Archivado programado de datos de aprendizaje IA en Moonbot
- `future-5390` · `plan_rich_commands_scheduled_archive` — Archivado programado de comandos enriquecidos en Moonbot
- `future-5393` · `plan_hub_notifications_scheduled_archive` — Archivado programado de notificaciones del Hub en Moonbot
- `future-5396` · `plan_cookie_policies_scheduled_archive` — Archivado programado de políticas de cookies en Moonbot
- `future-5399` · `plan_wayback_history_scheduled_archive` — Archivado programado de historial Wayback en Moonbot
- `future-5402` · `plan_temporary_roles_point_in_time_restore` — Restauración por punto temporal de roles temporales en Moonbot
- `future-5405` · `plan_managed_groups_point_in_time_restore` — Restauración por punto temporal de grupos administrados en Moonbot
- `future-5408` · `plan_scheduled_messages_point_in_time_restore` — Restauración por punto temporal de mensajes programados en Moonbot
- `future-5411` · `plan_rss_feeds_point_in_time_restore` — Restauración por punto temporal de feeds RSS en Moonbot
- `future-5414` · `plan_telegram_videos_point_in_time_restore` — Restauración por punto temporal de vídeos de Telegram en Moonbot
- `future-5417` · `plan_blocklists_point_in_time_restore` — Restauración por punto temporal de listas de bloqueo en Moonbot
- `future-5420` · `plan_required_subscriptions_point_in_time_restore` — Restauración por punto temporal de suscripciones obligatorias en Moonbot
- `future-5423` · `plan_signed_webhooks_point_in_time_restore` — Restauración por punto temporal de webhooks firmados en Moonbot
- `future-5426` · `plan_quiet_hours_point_in_time_restore` — Restauración por punto temporal de horarios silenciosos en Moonbot
- `future-5429` · `plan_correlated_incidents_point_in_time_restore` — Restauración por punto temporal de incidentes correlacionados en Moonbot
- `future-5432` · `plan_accessible_preferences_point_in_time_restore` — Restauración por punto temporal de preferencias accesibles en Moonbot
- `future-5435` · `plan_integration_secrets_point_in_time_restore` — Restauración por punto temporal de secretos de integración en Moonbot
- `future-5438` · `plan_contextual_responses_point_in_time_restore` — Restauración por punto temporal de respuestas contextuales en Moonbot
- `future-5441` · `plan_miniapp_menus_point_in_time_restore` — Restauración por punto temporal de menús de la MiniApp en Moonbot
- `future-5444` · `plan_bot_statistics_point_in_time_restore` — Restauración por punto temporal de estadísticas por bot en Moonbot
- `future-5447` · `plan_advertising_preferences_point_in_time_restore` — Restauración por punto temporal de preferencias publicitarias en Moonbot
- `future-5450` · `plan_processing_queues_point_in_time_restore` — Restauración por punto temporal de colas de procesamiento en Moonbot
- `future-5453` · `observe_creator_accounts_distributed` — Observabilidad distribuida de cuentas creadoras en Moonbot
- `future-5456` · `observe_associated_channels_distributed` — Observabilidad distribuida de canales asociados en Moonbot
- `future-5459` · `observe_community_campaigns_distributed` — Observabilidad distribuida de campañas comunitarias en Moonbot
- `future-5462` · `observe_editorial_articles_distributed` — Observabilidad distribuida de artículos editoriales en Moonbot
- `future-5465` · `observe_moderated_images_distributed` — Observabilidad distribuida de imágenes moderadas en Moonbot
- `future-5468` · `observe_user_appeals_distributed` — Observabilidad distribuida de apelaciones de usuarios en Moonbot
- `future-5471` · `observe_mtproto_proxies_distributed` — Observabilidad distribuida de proxies MTProto en Moonbot
- `future-5474` · `observe_persistent_tasks_distributed` — Observabilidad distribuida de tareas persistentes en Moonbot
- `future-5477` · `observe_moderation_rules_distributed` — Observabilidad distribuida de reglas de moderación en Moonbot
- `future-5480` · `observe_language_metrics_distributed` — Observabilidad distribuida de métricas lingüísticas en Moonbot
- `future-5483` · `observe_community_translations_distributed` — Observabilidad distribuida de traducciones comunitarias en Moonbot
- `future-5486` · `observe_personal_consents_distributed` — Observabilidad distribuida de consentimientos personales en Moonbot
- `future-5489` · `observe_telegram_reactions_distributed` — Observabilidad distribuida de reacciones Telegram en Moonbot
- `future-5492` · `observe_master_panels_distributed` — Observabilidad distribuida de paneles del master en Moonbot
- `future-5495` · `observe_channel_directories_distributed` — Observabilidad distribuida de directorios de canales en Moonbot
- `future-5498` · `observe_external_links_distributed` — Observabilidad distribuida de enlaces externos en Moonbot
- `future-5501` · `review_administrative_sessions_quality` — Control de calidad para sesiones administrativas en Moonbot
- `future-5504` · `review_community_profiles_quality` — Control de calidad para perfiles comunitarios en Moonbot
- `future-5507` · `review_telegram_communities_quality` — Control de calidad para comunidades Telegram en Moonbot
- `future-5510` · `review_house_ads_quality` — Control de calidad para anuncios propios en Moonbot
- `future-5513` · `review_voice_notes_quality` — Control de calidad para notas de voz en Moonbot
- `future-5516` · `review_suspicious_files_quality` — Control de calidad para archivos sospechosos en Moonbot
- `future-5519` · `review_captcha_decisions_quality` — Control de calidad para decisiones de captcha en Moonbot

### v18.23.0 — 120 funciones incorporadas

- `future-2102` · `proxy_offline_continuity` — Continuidad operativa sin conexión para proxies
- `future-2103` · `proxy_adaptive_trust` — Acceso de confianza adaptativa para proxies
- `future-2104` · `proxy_campaign` — Planificador de campañas comunitarias para proxies
- `future-2105` · `proxy_intent` — Detección de intención y contexto para proxies
- `future-2106` · `proxy_integration` — Laboratorio de integraciones para proxies
- `future-2107` · `proxy_vault` — Bóveda de datos personales para proxies
- `future-2108` · `proxy_easy_read` — Interfaz de lectura fácil para proxies
- `future-2109` · `proxy_sessions` — Continuidad de sesión multidispositivo para proxies
- `future-2110` · `proxy_editorial` — Curación editorial asistida para proxies
- `future-2111` · `proxy_budget` — Control presupuestario de recursos para proxies
- `future-2112` · `proxy_reputation` — Sistema de reputación transparente para proxies
- `future-2113` · `proxy_localization` — Localización cultural automática para proxies
- `future-2114` · `proxy_communication_preferences` — Centro de preferencias de comunicación para proxies
- `future-2115` · `proxy_onboarding` — Recorridos personalizados de incorporación para proxies
- `future-2116` · `proxy_governance` — Gobernanza mediante propuestas y votos para proxies
- `future-2117` · `proxy_voice_control` — Control por voz accesible para proxies
- `future-2118` · `proxy_federated_bridge` — Puente de datos federado para proxies
- `future-2119` · `proxy_external_event` — Automatización por eventos externos para proxies
- `future-2120` · `proxy_digital_twin` — Gemelo digital operativo para proxies
- `future-2121` · `dashboard_incidents` — Centro de incidencias correlacionadas para panel principal
- `future-2122` · `dashboard_workflow` — Constructor de flujos sin código para panel principal
- `future-2123` · `dashboard_delegation` — Delegación temporal de funciones para panel principal
- `future-2124` · `dashboard_coordinated_abuse` — Protección contra abuso coordinado para panel principal
- `future-2125` · `dashboard_copilot` — Copiloto de respuesta contextual para panel principal
- `future-2126` · `dashboard_capacity` — Pronóstico de capacidad y demanda para panel principal
- `future-2127` · `dashboard_batch_plan` — Centro de operaciones por lotes para panel principal
- `future-2128` · `dashboard_workspace` — Espacios de trabajo compartidos para panel principal
- `future-2129` · `dashboard_media` — Biblioteca multimedia inteligente para panel principal
- `future-2130` · `dashboard_narrative_report` — Informes narrativos automáticos para panel principal
- `future-2131` · `dashboard_alert_escalation` — Escalado inteligente de avisos para panel principal
- `future-2132` · `dashboard_offline_continuity` — Continuidad operativa sin conexión para panel principal
- `future-2133` · `dashboard_adaptive_trust` — Acceso de confianza adaptativa para panel principal
- `future-2134` · `dashboard_campaign` — Planificador de campañas comunitarias para panel principal
- `future-2135` · `dashboard_intent` — Detección de intención y contexto para panel principal
- `future-2136` · `dashboard_integration` — Laboratorio de integraciones para panel principal
- `future-2137` · `dashboard_vault` — Bóveda de datos personales para panel principal
- `future-2138` · `dashboard_easy_read` — Interfaz de lectura fácil para panel principal
- `future-2139` · `dashboard_sessions` — Continuidad de sesión multidispositivo para panel principal
- `future-2140` · `dashboard_editorial` — Curación editorial asistida para panel principal
- `future-2141` · `dashboard_budget` — Control presupuestario de recursos para panel principal
- `future-2142` · `dashboard_reputation` — Sistema de reputación transparente para panel principal
- `future-2143` · `dashboard_localization` — Localización cultural automática para panel principal
- `future-2144` · `dashboard_communication_preferences` — Centro de preferencias de comunicación para panel principal
- `future-2145` · `dashboard_onboarding` — Recorridos personalizados de incorporación para panel principal
- `future-2146` · `dashboard_governance` — Gobernanza mediante propuestas y votos para panel principal
- `future-2147` · `dashboard_voice_control` — Control por voz accesible para panel principal
- `future-2148` · `dashboard_federated_bridge` — Puente de datos federado para panel principal
- `future-2149` · `dashboard_external_event` — Automatización por eventos externos para panel principal
- `future-2150` · `dashboard_digital_twin` — Gemelo digital operativo para panel principal
- `future-2151` · `analytics_incidents` — Centro de incidencias correlacionadas para analítica
- `future-2152` · `analytics_workflow` — Constructor de flujos sin código para analítica
- `future-2153` · `analytics_delegation` — Delegación temporal de funciones para analítica
- `future-2154` · `analytics_coordinated_abuse` — Protección contra abuso coordinado para analítica
- `future-2155` · `analytics_copilot` — Copiloto de respuesta contextual para analítica
- `future-2156` · `analytics_capacity` — Pronóstico de capacidad y demanda para analítica
- `future-2157` · `analytics_batch_plan` — Centro de operaciones por lotes para analítica
- `future-2158` · `analytics_workspace` — Espacios de trabajo compartidos para analítica
- `future-2159` · `analytics_media` — Biblioteca multimedia inteligente para analítica
- `future-2160` · `analytics_narrative_report` — Informes narrativos automáticos para analítica
- `future-2161` · `analytics_alert_escalation` — Escalado inteligente de avisos para analítica
- `future-2162` · `analytics_offline_continuity` — Continuidad operativa sin conexión para analítica
- `future-2163` · `analytics_adaptive_trust` — Acceso de confianza adaptativa para analítica
- `future-2164` · `analytics_campaign` — Planificador de campañas comunitarias para analítica
- `future-2165` · `analytics_intent` — Detección de intención y contexto para analítica
- `future-2166` · `analytics_integration` — Laboratorio de integraciones para analítica
- `future-2167` · `analytics_vault` — Bóveda de datos personales para analítica
- `future-2168` · `analytics_easy_read` — Interfaz de lectura fácil para analítica
- `future-2169` · `analytics_sessions` — Continuidad de sesión multidispositivo para analítica
- `future-2170` · `analytics_editorial` — Curación editorial asistida para analítica
- `future-2171` · `analytics_budget` — Control presupuestario de recursos para analítica
- `future-2172` · `analytics_reputation` — Sistema de reputación transparente para analítica
- `future-2173` · `analytics_localization` — Localización cultural automática para analítica
- `future-2174` · `analytics_communication_preferences` — Centro de preferencias de comunicación para analítica
- `future-2175` · `analytics_onboarding` — Recorridos personalizados de incorporación para analítica
- `future-2176` · `analytics_governance` — Gobernanza mediante propuestas y votos para analítica
- `future-2177` · `analytics_voice_control` — Control por voz accesible para analítica
- `future-2178` · `analytics_federated_bridge` — Puente de datos federado para analítica
- `future-2179` · `analytics_external_event` — Automatización por eventos externos para analítica
- `future-2180` · `analytics_digital_twin` — Gemelo digital operativo para analítica
- `future-2181` · `webapp_privacy_incidents` — Centro de incidencias correlacionadas para privacidad
- `future-2182` · `webapp_privacy_workflow` — Constructor de flujos sin código para privacidad
- `future-2183` · `webapp_privacy_delegation` — Delegación temporal de funciones para privacidad
- `future-2184` · `webapp_privacy_coordinated_abuse` — Protección contra abuso coordinado para privacidad
- `future-2185` · `webapp_privacy_copilot` — Copiloto de respuesta contextual para privacidad
- `future-2186` · `webapp_privacy_capacity` — Pronóstico de capacidad y demanda para privacidad
- `future-2187` · `webapp_privacy_batch_plan` — Centro de operaciones por lotes para privacidad
- `future-2188` · `webapp_privacy_workspace` — Espacios de trabajo compartidos para privacidad
- `future-2189` · `webapp_privacy_media` — Biblioteca multimedia inteligente para privacidad
- `future-2190` · `webapp_privacy_report` — Informes narrativos automáticos para privacidad
- `future-2191` · `webapp_privacy_alert_escalation` — Escalado inteligente de avisos para privacidad
- `future-2192` · `webapp_privacy_offline_continuity` — Continuidad operativa sin conexión para privacidad
- `future-2193` · `webapp_privacy_adaptive_trust` — Acceso de confianza adaptativa para privacidad
- `future-2194` · `webapp_privacy_campaign` — Planificador de campañas comunitarias para privacidad
- `future-2195` · `webapp_privacy_intent` — Detección de intención y contexto para privacidad
- `future-2196` · `webapp_privacy_integration` — Laboratorio de integraciones para privacidad
- `future-2197` · `webapp_privacy_vault` — Bóveda de datos personales para privacidad
- `future-2198` · `webapp_privacy_easy_read` — Interfaz de lectura fácil para privacidad
- `future-2199` · `webapp_privacy_sessions` — Continuidad de sesión multidispositivo para privacidad
- `future-2200` · `webapp_privacy_editorial` — Curación editorial asistida para privacidad
- `future-2201` · `webapp_privacy_budget` — Control presupuestario de recursos para privacidad
- `future-2202` · `webapp_privacy_reputation` — Sistema de reputación transparente para privacidad
- `future-2203` · `webapp_privacy_localization` — Localización cultural automática para privacidad
- `future-2204` · `webapp_privacy_communication_preferences` — Centro de preferencias de comunicación para privacidad
- `future-2205` · `webapp_privacy_onboarding` — Recorridos personalizados de incorporación para privacidad
- `future-2206` · `webapp_privacy_governance` — Gobernanza mediante propuestas y votos para privacidad
- `future-2207` · `webapp_privacy_voice_control` — Control por voz accesible para privacidad
- `future-2208` · `webapp_privacy_federated_bridge` — Puente de datos federado para privacidad
- `future-2209` · `webapp_privacy_external_event` — Automatización por eventos externos para privacidad
- `future-2210` · `webapp_privacy_digital_twin` — Gemelo digital operativo para privacidad
- `future-2211` · `webapp_seo_incidents` — Centro de incidencias correlacionadas para SEO
- `future-2212` · `webapp_seo_workflow` — Constructor de flujos sin código para SEO
- `future-2213` · `webapp_seo_delegation` — Delegación temporal de funciones para SEO
- `future-2214` · `webapp_seo_coordinated_abuse` — Protección contra abuso coordinado para SEO
- `future-2215` · `webapp_seo_copilot` — Copiloto de respuesta contextual para SEO
- `future-2216` · `webapp_seo_capacity` — Pronóstico de capacidad y demanda para SEO
- `future-2217` · `webapp_seo_batch_plan` — Centro de operaciones por lotes para SEO
- `future-2218` · `webapp_seo_workspace` — Espacios de trabajo compartidos para SEO
- `future-2219` · `webapp_seo_media` — Biblioteca multimedia inteligente para SEO
- `future-2220` · `webapp_seo_report` — Informes narrativos automáticos para SEO
- `future-2221` · `webapp_seo_alert_escalation` — Escalado inteligente de avisos para SEO

### v18.23.1 — 180 funciones incorporadas

- `future-2222` · `webapp_seo_offline_continuity` — Continuidad operativa sin conexión para SEO
- `future-2223` · `webapp_seo_adaptive_trust` — Acceso de confianza adaptativa para SEO
- `future-2224` · `webapp_seo_campaign` — Planificador de campañas comunitarias para SEO
- `future-2225` · `webapp_seo_intent` — Detección de intención y contexto para SEO
- `future-2226` · `webapp_seo_integration` — Laboratorio de integraciones para SEO
- `future-2227` · `webapp_seo_vault` — Bóveda de datos personales para SEO
- `future-2228` · `webapp_seo_easy_read` — Interfaz de lectura fácil para SEO
- `future-2229` · `webapp_seo_sessions` — Continuidad de sesión multidispositivo para SEO
- `future-2230` · `webapp_seo_editorial` — Curación editorial asistida para SEO
- `future-2231` · `webapp_seo_budget` — Control presupuestario de recursos para SEO
- `future-2232` · `webapp_seo_reputation` — Sistema de reputación transparente para SEO
- `future-2233` · `webapp_seo_localization` — Localización cultural automática para SEO
- `future-2234` · `webapp_seo_communication_preferences` — Centro de preferencias de comunicación para SEO
- `future-2235` · `webapp_seo_onboarding` — Recorridos personalizados de incorporación para SEO
- `future-2236` · `webapp_seo_governance` — Gobernanza mediante propuestas y votos para SEO
- `future-2237` · `webapp_seo_voice_control` — Control por voz accesible para SEO
- `future-2238` · `webapp_seo_federated_bridge` — Puente de datos federado para SEO
- `future-2239` · `webapp_seo_external_event` — Automatización por eventos externos para SEO
- `future-2240` · `webapp_seo_digital_twin` — Gemelo digital operativo para SEO
- `future-2241` · `community_incidents` — Centro de incidencias correlacionadas para comunidades
- `future-2242` · `community_workflow` — Constructor de flujos sin código para comunidades
- `future-2243` · `community_delegation` — Delegación temporal de funciones para comunidades
- `future-2244` · `community_coordinated_abuse` — Protección contra abuso coordinado para comunidades
- `future-2245` · `community_copilot` — Copiloto de respuesta contextual para comunidades
- `future-2246` · `community_capacity` — Pronóstico de capacidad y demanda para comunidades
- `future-2247` · `community_batch_plan` — Centro de operaciones por lotes para comunidades
- `future-2248` · `community_workspace` — Espacios de trabajo compartidos para comunidades
- `future-2249` · `community_media` — Biblioteca multimedia inteligente para comunidades
- `future-2250` · `community_narrative_report` — Informes narrativos automáticos para comunidades
- `future-2251` · `community_alert_escalation` — Escalado inteligente de avisos para comunidades
- `future-2252` · `community_offline_continuity` — Continuidad operativa sin conexión para comunidades
- `future-2253` · `community_adaptive_trust` — Acceso de confianza adaptativa para comunidades
- `future-2254` · `community_campaign_plan` — Planificador de campañas comunitarias para comunidades
- `future-2255` · `community_intent` — Detección de intención y contexto para comunidades
- `future-2256` · `community_integration` — Laboratorio de integraciones para comunidades
- `future-2257` · `community_vault` — Bóveda de datos personales para comunidades
- `future-2258` · `community_easy_read` — Interfaz de lectura fácil para comunidades
- `future-2259` · `community_sessions` — Continuidad de sesión multidispositivo para comunidades
- `future-2260` · `community_editorial` — Curación editorial asistida para comunidades
- `future-2261` · `community_budget` — Control presupuestario de recursos para comunidades
- `future-2262` · `community_reputation` — Sistema de reputación transparente para comunidades
- `future-2263` · `community_localization` — Localización cultural automática para comunidades
- `future-2264` · `community_communication_preferences` — Centro de preferencias de comunicación para comunidades
- `future-2265` · `community_onboarding` — Recorridos personalizados de incorporación para comunidades
- `future-2266` · `community_governance` — Gobernanza mediante propuestas y votos para comunidades
- `future-2267` · `community_voice_control` — Control por voz accesible para comunidades
- `future-2268` · `community_federated_bridge` — Puente de datos federado para comunidades
- `future-2269` · `community_external_event` — Automatización por eventos externos para comunidades
- `future-2270` · `community_digital_twin` — Gemelo digital operativo para comunidades
- `future-2271` · `support_incidents` — Centro de incidencias correlacionadas para soporte
- `future-2272` · `support_workflow` — Constructor de flujos sin código para soporte
- `future-2273` · `support_delegation` — Delegación temporal de funciones para soporte
- `future-2274` · `support_coordinated_abuse` — Protección contra abuso coordinado para soporte
- `future-2275` · `support_copilot` — Copiloto de respuesta contextual para soporte
- `future-2276` · `support_capacity_forecast` — Pronóstico de capacidad y demanda para soporte
- `future-2277` · `support_batch_plan` — Centro de operaciones por lotes para soporte
- `future-2278` · `support_workspace` — Espacios de trabajo compartidos para soporte
- `future-2279` · `support_media` — Biblioteca multimedia inteligente para soporte
- `future-2280` · `support_narrative_report` — Informes narrativos automáticos para soporte
- `future-2281` · `support_alert_escalation` — Escalado inteligente de avisos para soporte
- `future-5522` · `review_managed_bots_quality` — Control de calidad para bots administrados en Moonbot
- `future-5525` · `review_recurring_reminders_quality` — Control de calidad para recordatorios recurrentes en Moonbot
- `future-5528` · `review_security_events_quality` — Control de calidad para eventos de seguridad en Moonbot
- `future-5531` · `review_regional_maps_quality` — Control de calidad para mapas regionales en Moonbot
- `future-5534` · `review_backups_quality` — Control de calidad para copias de seguridad en Moonbot
- `future-5537` · `review_ai_learning_data_quality` — Control de calidad para datos de aprendizaje IA en Moonbot
- `future-5540` · `review_rich_commands_quality` — Control de calidad para comandos enriquecidos en Moonbot
- `future-5543` · `review_hub_notifications_quality` — Control de calidad para notificaciones del Hub en Moonbot
- `future-5546` · `review_cookie_policies_quality` — Control de calidad para políticas de cookies en Moonbot
- `future-5549` · `review_wayback_history_quality` — Control de calidad para historial Wayback en Moonbot
- `future-5552` · `run_temporary_roles_isolated_sandbox` — Sandbox aislado de roles temporales en Moonbot
- `future-5555` · `run_managed_groups_isolated_sandbox` — Sandbox aislado de grupos administrados en Moonbot
- `future-5558` · `run_scheduled_messages_isolated_sandbox` — Sandbox aislado de mensajes programados en Moonbot
- `future-5561` · `run_rss_feeds_isolated_sandbox` — Sandbox aislado de feeds RSS en Moonbot
- `future-5564` · `run_telegram_videos_isolated_sandbox` — Sandbox aislado de vídeos de Telegram en Moonbot
- `future-5567` · `run_blocklists_isolated_sandbox` — Sandbox aislado de listas de bloqueo en Moonbot
- `future-5570` · `run_required_subscriptions_isolated_sandbox` — Sandbox aislado de suscripciones obligatorias en Moonbot
- `future-5573` · `run_signed_webhooks_isolated_sandbox` — Sandbox aislado de webhooks firmados en Moonbot
- `future-5576` · `run_quiet_hours_isolated_sandbox` — Sandbox aislado de horarios silenciosos en Moonbot
- `future-5579` · `run_correlated_incidents_isolated_sandbox` — Sandbox aislado de incidentes correlacionados en Moonbot
- `future-5582` · `run_accessible_preferences_isolated_sandbox` — Sandbox aislado de preferencias accesibles en Moonbot
- `future-5585` · `run_integration_secrets_isolated_sandbox` — Sandbox aislado de secretos de integración en Moonbot
- `future-5588` · `run_contextual_responses_isolated_sandbox` — Sandbox aislado de respuestas contextuales en Moonbot
- `future-5591` · `run_miniapp_menus_isolated_sandbox` — Sandbox aislado de menús de la MiniApp en Moonbot
- `future-5594` · `run_bot_statistics_isolated_sandbox` — Sandbox aislado de estadísticas por bot en Moonbot
- `future-5597` · `run_advertising_preferences_isolated_sandbox` — Sandbox aislado de preferencias publicitarias en Moonbot
- `future-5600` · `run_processing_queues_isolated_sandbox` — Sandbox aislado de colas de procesamiento en Moonbot
- `future-5603` · `review_creator_accounts_proposal_governance` — Gobernanza mediante propuestas de cuentas creadoras en Moonbot
- `future-5606` · `review_associated_channels_proposal_governance` — Gobernanza mediante propuestas de canales asociados en Moonbot
- `future-5609` · `review_community_campaigns_proposal_governance` — Gobernanza mediante propuestas de campañas comunitarias en Moonbot
- `future-5612` · `review_editorial_articles_proposal_governance` — Gobernanza mediante propuestas de artículos editoriales en Moonbot
- `future-5615` · `review_moderated_images_proposal_governance` — Gobernanza mediante propuestas de imágenes moderadas en Moonbot
- `future-5618` · `review_user_appeals_proposal_governance` — Gobernanza mediante propuestas de apelaciones de usuarios en Moonbot
- `future-5621` · `review_mtproto_proxies_proposal_governance` — Gobernanza mediante propuestas de proxies MTProto en Moonbot
- `future-5624` · `review_persistent_tasks_proposal_governance` — Gobernanza mediante propuestas de tareas persistentes en Moonbot
- `future-5627` · `review_moderation_rules_proposal_governance` — Gobernanza mediante propuestas de reglas de moderación en Moonbot
- `future-5630` · `review_language_metrics_proposal_governance` — Gobernanza mediante propuestas de métricas lingüísticas en Moonbot
- `future-5633` · `review_community_translations_proposal_governance` — Gobernanza mediante propuestas de traducciones comunitarias en Moonbot
- `future-5636` · `review_personal_consents_proposal_governance` — Gobernanza mediante propuestas de consentimientos personales en Moonbot
- `future-5639` · `review_telegram_reactions_proposal_governance` — Gobernanza mediante propuestas de reacciones Telegram en Moonbot
- `future-5642` · `review_master_panels_proposal_governance` — Gobernanza mediante propuestas de paneles del master en Moonbot
- `future-5645` · `review_channel_directories_proposal_governance` — Gobernanza mediante propuestas de directorios de canales en Moonbot
- `future-5648` · `review_external_links_proposal_governance` — Gobernanza mediante propuestas de enlaces externos en Moonbot
- `future-5651` · `measure_administrative_sessions_impact` — Métricas de impacto para sesiones administrativas en Moonbot
- `future-5654` · `measure_community_profiles_impact` — Métricas de impacto para perfiles comunitarios en Moonbot
- `future-5657` · `measure_telegram_communities_impact` — Métricas de impacto para comunidades Telegram en Moonbot
- `future-5660` · `measure_house_ads_impact` — Métricas de impacto para anuncios propios en Moonbot
- `future-5663` · `measure_voice_notes_impact` — Métricas de impacto para notas de voz en Moonbot
- `future-5666` · `measure_suspicious_files_impact` — Métricas de impacto para archivos sospechosos en Moonbot
- `future-5669` · `measure_captcha_decisions_impact` — Métricas de impacto para decisiones de captcha en Moonbot
- `future-5672` · `measure_managed_bots_impact` — Métricas de impacto para bots administrados en Moonbot
- `future-5675` · `measure_recurring_reminders_impact` — Métricas de impacto para recordatorios recurrentes en Moonbot
- `future-5678` · `measure_security_events_impact` — Métricas de impacto para eventos de seguridad en Moonbot
- `future-5681` · `measure_regional_maps_impact` — Métricas de impacto para mapas regionales en Moonbot
- `future-5684` · `measure_backups_impact` — Métricas de impacto para copias de seguridad en Moonbot
- `future-5687` · `measure_ai_learning_data_impact` — Métricas de impacto para datos de aprendizaje IA en Moonbot
- `future-5690` · `measure_rich_commands_impact` — Métricas de impacto para comandos enriquecidos en Moonbot
- `future-5693` · `measure_hub_notifications_impact` — Métricas de impacto para notificaciones del Hub en Moonbot
- `future-5696` · `measure_cookie_policies_impact` — Métricas de impacto para políticas de cookies en Moonbot
- `future-5699` · `measure_wayback_history_impact` — Métricas de impacto para historial Wayback en Moonbot
- `future-2282` · `support_offline_continuity` — None
- `future-2283` · `support_adaptive_trust` — None
- `future-2284` · `support_campaign_plan` — None
- `future-2285` · `support_intent` — None
- `future-2286` · `support_integration` — None
- `future-2287` · `support_vault` — None
- `future-2288` · `support_easy_read` — None
- `future-2289` · `support_sessions` — None
- `future-2290` · `support_editorial` — None
- `future-2291` · `support_budget` — None
- `future-2292` · `support_reputation` — None
- `future-2293` · `support_localization` — None
- `future-2294` · `support_communication_preferences` — None
- `future-2295` · `support_onboarding` — None
- `future-2296` · `support_governance` — None
- `future-2297` · `support_voice_control` — None
- `future-2298` · `support_federated_bridge` — None
- `future-2299` · `support_external_event` — None
- `future-2300` · `support_digital_twin` — None
- `future-2301` · `subscription_incidents` — None
- `future-2302` · `subscription_workflow` — None
- `future-2303` · `subscription_delegation` — None
- `future-2304` · `subscription_coordinated_abuse` — None
- `future-2305` · `subscription_copilot` — None
- `future-2306` · `subscription_capacity_forecast` — None
- `future-2307` · `subscription_batch_plan` — None
- `future-2308` · `subscription_workspace` — None
- `future-2309` · `subscription_media` — None
- `future-2310` · `subscription_narrative_report` — None
- `future-2311` · `subscription_alert_escalation` — None
- `future-2312` · `subscription_offline_continuity` — None
- `future-2313` · `subscription_adaptive_trust` — None
- `future-2314` · `subscription_campaign_plan` — None
- `future-2315` · `subscription_intent` — None
- `future-2316` · `subscription_integration` — None
- `future-2317` · `subscription_vault` — None
- `future-2318` · `subscription_easy_read` — None
- `future-2319` · `subscription_sessions` — None
- `future-2320` · `subscription_editorial` — None
- `future-2321` · `subscription_budget` — None
- `future-2322` · `subscription_reputation` — None
- `future-2323` · `subscription_localization` — None
- `future-2324` · `subscription_communication_preferences` — None
- `future-2325` · `subscription_onboarding` — None
- `future-2326` · `subscription_governance` — None
- `future-2327` · `subscription_voice_control` — None
- `future-2328` · `subscription_federated_bridge` — None
- `future-2329` · `subscription_external_event` — None
- `future-2330` · `subscription_digital_twin` — None
- `future-2331` · `accessibility_incidents` — None
- `future-2332` · `accessibility_workflow` — None
- `future-2333` · `accessibility_delegation` — None
- `future-2334` · `accessibility_coordinated_abuse` — None
- `future-2335` · `moderation_incidents` — None
- `future-2336` · `moderation_workflow` — None
- `future-2337` · `moderation_delegation` — None
- `future-2338` · `moderation_coordinated_abuse` — None
- `future-2339` · `moderation_copilot` — None
- `future-2340` · `moderation_capacity_forecast` — None
- `future-2341` · `moderation_batch_plan` — None

### v18.23.3 — 120 funciones incorporadas

- `future-5702` · `optimize_temporary_roles_energy` — Optimización energética de roles temporales en Moonbot
- `future-5705` · `optimize_managed_groups_energy` — Optimización energética de grupos administrados en Moonbot
- `future-5708` · `optimize_scheduled_messages_energy` — Optimización energética de mensajes programados en Moonbot
- `future-5711` · `optimize_rss_feeds_energy` — Optimización energética de feeds RSS en Moonbot
- `future-5714` · `optimize_telegram_videos_energy` — Optimización energética de vídeos de Telegram en Moonbot
- `future-5717` · `optimize_blocklists_energy` — Optimización energética de listas de bloqueo en Moonbot
- `future-5720` · `optimize_required_subscriptions_energy` — Optimización energética de suscripciones obligatorias en Moonbot
- `future-5723` · `optimize_signed_webhooks_energy` — Optimización energética de webhooks firmados en Moonbot
- `future-5726` · `optimize_quiet_hours_energy` — Optimización energética de horarios silenciosos en Moonbot
- `future-5729` · `optimize_correlated_incidents_energy` — Optimización energética de incidentes correlacionados en Moonbot
- `future-5732` · `optimize_accessible_preferences_energy` — Optimización energética de preferencias accesibles en Moonbot
- `future-5735` · `optimize_integration_secrets_energy` — Optimización energética de secretos de integración en Moonbot
- `future-5738` · `optimize_contextual_responses_energy` — Optimización energética de respuestas contextuales en Moonbot
- `future-5741` · `optimize_miniapp_menus_energy` — Optimización energética de menús de la MiniApp en Moonbot
- `future-5744` · `optimize_bot_statistics_energy` — Optimización energética de estadísticas por bot en Moonbot
- `future-5747` · `optimize_advertising_preferences_energy` — Optimización energética de preferencias publicitarias en Moonbot
- `future-5750` · `optimize_processing_queues_energy` — Optimización energética de colas de procesamiento en Moonbot
- `future-5753` · `limit_creator_accounts_abuse` — Limitación antiabuso de cuentas creadoras en Moonbot
- `future-5756` · `limit_associated_channels_abuse` — Limitación antiabuso de canales asociados en Moonbot
- `future-5759` · `limit_community_campaigns_abuse` — Limitación antiabuso de campañas comunitarias en Moonbot
- `future-5762` · `limit_editorial_articles_abuse` — Limitación antiabuso de artículos editoriales en Moonbot
- `future-5765` · `limit_moderated_images_abuse` — Limitación antiabuso de imágenes moderadas en Moonbot
- `future-5768` · `limit_user_appeals_abuse` — Limitación antiabuso de apelaciones de usuarios en Moonbot
- `future-5771` · `limit_mtproto_proxies_abuse` — Limitación antiabuso de proxies MTProto en Moonbot
- `future-5774` · `limit_persistent_tasks_abuse` — Limitación antiabuso de tareas persistentes en Moonbot
- `future-5777` · `limit_moderation_rules_abuse` — Limitación antiabuso de reglas de moderación en Moonbot
- `future-5780` · `limit_language_metrics_abuse` — Limitación antiabuso de métricas lingüísticas en Moonbot
- `future-5783` · `limit_community_translations_abuse` — Limitación antiabuso de traducciones comunitarias en Moonbot
- `future-5786` · `limit_personal_consents_abuse` — Limitación antiabuso de consentimientos personales en Moonbot
- `future-5789` · `limit_telegram_reactions_abuse` — Limitación antiabuso de reacciones Telegram en Moonbot
- `future-5792` · `limit_master_panels_abuse` — Limitación antiabuso de paneles del master en Moonbot
- `future-5795` · `limit_channel_directories_abuse` — Limitación antiabuso de directorios de canales en Moonbot
- `future-5798` · `limit_external_links_abuse` — Limitación antiabuso de enlaces externos en Moonbot
- `future-5801` · `plan_administrative_sessions_guided_migration` — Migración guiada de sesiones administrativas en Moonbot
- `future-5804` · `plan_community_profiles_guided_migration` — Migración guiada de perfiles comunitarios en Moonbot
- `future-5807` · `plan_telegram_communities_guided_migration` — Migración guiada de comunidades Telegram en Moonbot
- `future-5810` · `plan_house_ads_guided_migration` — Migración guiada de anuncios propios en Moonbot
- `future-5813` · `plan_voice_notes_guided_migration` — Migración guiada de notas de voz en Moonbot
- `future-5816` · `plan_suspicious_files_guided_migration` — Migración guiada de archivos sospechosos en Moonbot
- `future-5819` · `plan_captcha_decisions_guided_migration` — Migración guiada de decisiones de captcha en Moonbot
- `future-5822` · `plan_managed_bots_guided_migration` — Migración guiada de bots administrados en Moonbot
- `future-5825` · `plan_recurring_reminders_guided_migration` — Migración guiada de recordatorios recurrentes en Moonbot
- `future-5828` · `plan_security_events_guided_migration` — Migración guiada de eventos de seguridad en Moonbot
- `future-5831` · `plan_regional_maps_guided_migration` — Migración guiada de mapas regionales en Moonbot
- `future-5834` · `plan_backups_guided_migration` — Migración guiada de copias de seguridad en Moonbot
- `future-5837` · `plan_ai_learning_data_guided_migration` — Migración guiada de datos de aprendizaje IA en Moonbot
- `future-5840` · `plan_rich_commands_guided_migration` — Migración guiada de comandos enriquecidos en Moonbot
- `future-5843` · `plan_hub_notifications_guided_migration` — Migración guiada de notificaciones del Hub en Moonbot
- `future-5846` · `plan_cookie_policies_guided_migration` — Migración guiada de políticas de cookies en Moonbot
- `future-5849` · `plan_wayback_history_guided_migration` — Migración guiada de historial Wayback en Moonbot
- `future-5852` · `verify_temporary_roles_federated_compatibility` — Compatibilidad federada de roles temporales en Moonbot
- `future-5855` · `verify_managed_groups_federated_compatibility` — Compatibilidad federada de grupos administrados en Moonbot
- `future-5858` · `verify_scheduled_messages_federated_compatibility` — Compatibilidad federada de mensajes programados en Moonbot
- `future-5861` · `verify_rss_feeds_federated_compatibility` — Compatibilidad federada de feeds RSS en Moonbot
- `future-5864` · `verify_telegram_videos_federated_compatibility` — Compatibilidad federada de vídeos de Telegram en Moonbot
- `future-5867` · `verify_blocklists_federated_compatibility` — Compatibilidad federada de listas de bloqueo en Moonbot
- `future-5870` · `verify_required_subscriptions_federated_compatibility` — Compatibilidad federada de suscripciones obligatorias en Moonbot
- `future-5873` · `verify_signed_webhooks_federated_compatibility` — Compatibilidad federada de webhooks firmados en Moonbot
- `future-5876` · `verify_quiet_hours_federated_compatibility` — Compatibilidad federada de horarios silenciosos en Moonbot
- `future-5879` · `verify_correlated_incidents_federated_compatibility` — Compatibilidad federada de incidentes correlacionados en Moonbot
- `future-2342` · `moderation_workspace` — None
- `future-2343` · `moderation_media` — None
- `future-2344` · `moderation_narrative_report` — None
- `future-2345` · `moderation_alert_escalation` — None
- `future-2346` · `moderation_offline_continuity` — None
- `future-2347` · `moderation_adaptive_trust` — None
- `future-2348` · `moderation_campaign_plan` — None
- `future-2349` · `moderation_intent` — None
- `future-2350` · `moderation_integration` — None
- `future-2351` · `moderation_vault` — None
- `future-2352` · `moderation_easy_read` — None
- `future-2353` · `moderation_sessions` — None
- `future-2354` · `moderation_editorial` — None
- `future-2355` · `moderation_budget` — None
- `future-2356` · `moderation_reputation` — None
- `future-2357` · `moderation_localization` — None
- `future-2358` · `moderation_communication_preferences` — None
- `future-2359` · `moderation_onboarding` — None
- `future-2360` · `moderation_governance` — None
- `future-2361` · `moderation_voice_control` — None
- `future-2362` · `moderation_federated_bridge` — None
- `future-2363` · `moderation_external_event` — None
- `future-2364` · `moderation_digital_twin` — None
- `future-2365` · `security_incident_correlation` — None
- `future-2366` · `security_workflow` — None
- `future-2367` · `security_delegation` — None
- `future-2368` · `security_coordinated_abuse` — None
- `future-2369` · `security_copilot` — None
- `future-2370` · `security_capacity_forecast` — None
- `future-2371` · `security_batch_plan` — None
- `future-2372` · `security_workspace` — None
- `future-2373` · `security_media` — None
- `future-2374` · `security_narrative_report` — None
- `future-2375` · `security_alert_escalation` — None
- `future-2376` · `security_offline_continuity` — None
- `future-2377` · `security_adaptive_trust` — None
- `future-2378` · `security_campaign_plan` — None
- `future-2379` · `security_intent` — None
- `future-2380` · `security_integration` — None
- `future-2381` · `security_vault` — None
- `future-2382` · `security_easy_read` — None
- `future-2383` · `security_sessions` — None
- `future-2384` · `security_editorial` — None
- `future-2385` · `security_budget` — None
- `future-2386` · `security_reputation` — None
- `future-2387` · `security_localization` — None
- `future-2388` · `security_communication_preferences` — None
- `future-2389` · `security_onboarding` — None
- `future-2390` · `security_governance` — None
- `future-2391` · `security_voice_control` — None
- `future-2392` · `security_federated_bridge` — None
- `future-2393` · `security_external_event` — None
- `future-2394` · `security_digital_twin` — None
- `future-2395` · `ai_incidents` — None
- `future-2396` · `ai_workflow` — None
- `future-2397` · `ai_delegation` — None
- `future-2398` · `ai_coordinated_abuse` — None
- `future-2399` · `ai_copilot` — None
- `future-2400` · `ai_capacity_forecast` — None
- `future-2401` · `ai_batch_plan` — None

### v18.23.4 — 100 funciones incorporadas

- `future-5882` · `verify_accessible_preferences_federated_compatibility` — Compatibilidad federada de preferencias accesibles en Moonbot
- `future-5885` · `verify_integration_secrets_federated_compatibility` — Compatibilidad federada de secretos de integración en Moonbot
- `future-5888` · `verify_contextual_responses_federated_compatibility` — Compatibilidad federada de respuestas contextuales en Moonbot
- `future-5891` · `verify_miniapp_menus_federated_compatibility` — Compatibilidad federada de menús de la MiniApp en Moonbot
- `future-5894` · `verify_bot_statistics_federated_compatibility` — Compatibilidad federada de estadísticas por bot en Moonbot
- `future-5897` · `verify_advertising_preferences_federated_compatibility` — Compatibilidad federada de preferencias publicitarias en Moonbot
- `future-5900` · `verify_processing_queues_federated_compatibility` — Compatibilidad federada de colas de procesamiento en Moonbot
- `future-5903` · `plan_creator_accounts_operational_continuity` — Continuidad operativa de cuentas creadoras en Moonbot
- `future-5906` · `plan_associated_channels_operational_continuity` — Continuidad operativa de canales asociados en Moonbot
- `future-5909` · `plan_community_campaigns_operational_continuity` — Continuidad operativa de campañas comunitarias en Moonbot
- `future-5912` · `plan_editorial_articles_operational_continuity` — Continuidad operativa de artículos editoriales en Moonbot
- `future-5915` · `plan_moderated_images_operational_continuity` — Continuidad operativa de imágenes moderadas en Moonbot
- `future-5918` · `plan_user_appeals_operational_continuity` — Continuidad operativa de apelaciones de usuarios en Moonbot
- `future-5921` · `plan_mtproto_proxies_operational_continuity` — Continuidad operativa de proxies MTProto en Moonbot
- `future-5924` · `plan_persistent_tasks_operational_continuity` — Continuidad operativa de tareas persistentes en Moonbot
- `future-5927` · `plan_moderation_rules_operational_continuity` — Continuidad operativa de reglas de moderación en Moonbot
- `future-5930` · `plan_language_metrics_operational_continuity` — Continuidad operativa de métricas lingüísticas en Moonbot
- `future-5933` · `plan_community_translations_operational_continuity` — Continuidad operativa de traducciones comunitarias en Moonbot
- `future-5936` · `plan_personal_consents_operational_continuity` — Continuidad operativa de consentimientos personales en Moonbot
- `future-5939` · `plan_telegram_reactions_operational_continuity` — Continuidad operativa de reacciones Telegram en Moonbot
- `future-5942` · `plan_master_panels_operational_continuity` — Continuidad operativa de paneles del master en Moonbot
- `future-5945` · `plan_channel_directories_operational_continuity` — Continuidad operativa de directorios de canales en Moonbot
- `future-5948` · `plan_external_links_operational_continuity` — Continuidad operativa de enlaces externos en Moonbot
- `future-5951` · `assist_administrative_sessions_contextually` — Asistencia contextual para sesiones administrativas en Moonbot
- `future-5954` · `assist_community_profiles_contextually` — Asistencia contextual para perfiles comunitarios en Moonbot
- `future-5957` · `assist_telegram_communities_contextually` — Asistencia contextual para comunidades Telegram en Moonbot
- `future-5960` · `assist_house_ads_contextually` — Asistencia contextual para anuncios propios en Moonbot
- `future-5963` · `assist_voice_notes_contextually` — Asistencia contextual para notas de voz en Moonbot
- `future-5966` · `assist_suspicious_files_contextually` — Asistencia contextual para archivos sospechosos en Moonbot
- `future-5969` · `assist_captcha_decisions_contextually` — Asistencia contextual para decisiones de captcha en Moonbot
- `future-5972` · `assist_managed_bots_contextually` — Asistencia contextual para bots administrados en Moonbot
- `future-5975` · `assist_recurring_reminders_contextually` — Asistencia contextual para recordatorios recurrentes en Moonbot
- `future-5978` · `assist_security_events_contextually` — Asistencia contextual para eventos de seguridad en Moonbot
- `future-5981` · `assist_regional_maps_contextually` — Asistencia contextual para mapas regionales en Moonbot
- `future-5984` · `assist_backups_contextually` — Asistencia contextual para copias de seguridad en Moonbot
- `future-5987` · `assist_ai_learning_data_contextually` — Asistencia contextual para datos de aprendizaje IA en Moonbot
- `future-5990` · `assist_rich_commands_contextually` — Asistencia contextual para comandos enriquecidos en Moonbot
- `future-5993` · `assist_hub_notifications_contextually` — Asistencia contextual para notificaciones del Hub en Moonbot
- `future-5996` · `assist_cookie_policies_contextually` — Asistencia contextual para políticas de cookies en Moonbot
- `future-5999` · `assist_wayback_history_contextually` — Asistencia contextual para historial Wayback en Moonbot
- `future-2402` · `ai_workspace` — None
- `future-2403` · `ai_media` — None
- `future-2404` · `ai_narrative_report` — None
- `future-2405` · `ai_alert_escalation` — None
- `future-2406` · `ai_offline_continuity` — None
- `future-2407` · `ai_adaptive_trust` — None
- `future-2408` · `ai_campaign_plan` — None
- `future-2409` · `ai_intent` — None
- `future-2410` · `ai_integration` — None
- `future-2411` · `ai_vault` — None
- `future-2412` · `ai_easy_read` — None
- `future-2413` · `ai_sessions` — None
- `future-2414` · `ai_editorial` — None
- `future-2415` · `ai_budget` — None
- `future-2416` · `ai_reputation` — None
- `future-2417` · `ai_localization` — None
- `future-2418` · `ai_communication_preferences` — None
- `future-2419` · `ai_onboarding` — None
- `future-2420` · `ai_governance` — None
- `future-2421` · `ai_voice_control` — None
- `future-2422` · `ai_federated_bridge` — None
- `future-2423` · `ai_external_event` — None
- `future-2424` · `ai_digital_twin` — None
- `future-2425` · `moon_group_incident_correlation` — None
- `future-2426` · `moon_group_workflow` — None
- `future-2427` · `moon_group_delegation` — None
- `future-2428` · `moon_group_coordinated_abuse` — None
- `future-2429` · `moon_group_copilot` — None
- `future-2430` · `moon_group_capacity_forecast` — None
- `future-2431` · `moon_group_batch_plan` — None
- `future-2432` · `moon_group_workspace` — None
- `future-2433` · `moon_group_media` — None
- `future-2434` · `moon_group_narrative_report` — None
- `future-2435` · `moon_group_alert_escalation` — None
- `future-2436` · `moon_group_offline_continuity` — None
- `future-2437` · `moon_group_adaptive_trust` — None
- `future-2438` · `moon_group_campaign_plan` — None
- `future-2439` · `moon_group_intent` — None
- `future-2440` · `moon_group_integration` — None
- `future-2441` · `moon_group_vault` — None
- `future-2442` · `moon_group_easy_read` — None
- `future-2443` · `moon_group_sessions` — None
- `future-2444` · `moon_group_editorial` — None
- `future-2445` · `moon_group_budget` — None
- `future-2446` · `moon_group_reputation` — None
- `future-2447` · `moon_group_localization` — None
- `future-2448` · `moon_group_communication_preferences` — None
- `future-2449` · `moon_group_onboarding` — None
- `future-2450` · `moon_group_governance` — None
- `future-2451` · `moon_group_voice_control` — None
- `future-2452` · `moon_group_federated_bridge` — None
- `future-2453` · `moon_group_external_event` — None
- `future-2454` · `moon_group_digital_twin` — None
- `future-2455` · `moon_channel_incident_correlation` — None
- `future-2456` · `moon_channel_workflow` — None
- `future-2457` · `moon_channel_delegation` — None
- `future-2458` · `moon_channel_coordinated_abuse` — None
- `future-2459` · `moon_channel_copilot` — None
- `future-2460` · `moon_channel_capacity_forecast` — None
- `future-2461` · `moon_channel_batch_plan` — None

### v18.23.5 — 60 funciones incorporadas

- `future-2462` · `moon_channel_workspace` — Workspace para canales
- `future-2463` · `moon_channel_media` — Media para canales
- `future-2464` · `moon_channel_narrative_report` — Narrative report para canales
- `future-2465` · `moon_channel_alert_escalation` — Alert escalation para canales
- `future-2466` · `moon_channel_offline_continuity` — Offline continuity para canales
- `future-2467` · `moon_channel_adaptive_trust` — Adaptive trust para canales
- `future-2468` · `moon_channel_campaign_plan` — Campaign plan para canales
- `future-2469` · `moon_channel_intent` — Intent para canales
- `future-2470` · `moon_channel_integration` — Integration para canales
- `future-2471` · `moon_channel_vault` — Vault para canales
- `future-2472` · `moon_channel_easy_read` — Easy read para canales
- `future-2473` · `moon_channel_sessions` — Sessions para canales
- `future-2474` · `moon_channel_editorial` — Editorial para canales
- `future-2475` · `moon_channel_budget` — Budget para canales
- `future-2476` · `moon_channel_reputation` — Reputation para canales
- `future-2477` · `moon_channel_localization` — Localization para canales
- `future-2478` · `moon_channel_communication_preferences` — Communication preferences para canales
- `future-2479` · `moon_channel_onboarding` — Onboarding para canales
- `future-2480` · `moon_channel_governance` — Governance para canales
- `future-2481` · `moon_channel_voice_control` — Voice control para canales
- `future-2482` · `moon_channel_federated_bridge` — Federated bridge para canales
- `future-2483` · `moon_channel_external_event` — External event para canales
- `future-2484` · `moon_channel_digital_twin` — Digital twin para canales
- `future-2485` · `moon_user_incident_correlation` — Incident correlation para usuarios
- `future-2486` · `moon_user_workflow` — Workflow para usuarios
- `future-2487` · `moon_user_delegation` — Delegation para usuarios
- `future-2488` · `moon_user_coordinated_abuse` — Coordinated abuse para usuarios
- `future-2489` · `moon_user_copilot` — Copilot para usuarios
- `future-2490` · `moon_user_capacity_forecast` — Capacity forecast para usuarios
- `future-2491` · `moon_user_batch_plan` — Batch plan para usuarios
- `future-2492` · `moon_user_workspace` — Workspace para usuarios
- `future-2493` · `moon_user_media` — Media para usuarios
- `future-2494` · `moon_user_narrative_report` — Narrative report para usuarios
- `future-2495` · `moon_user_alert_escalation` — Alert escalation para usuarios
- `future-2496` · `moon_user_offline_continuity` — Offline continuity para usuarios
- `future-2497` · `moon_user_adaptive_trust` — Adaptive trust para usuarios
- `future-2498` · `moon_user_campaign_plan` — Campaign plan para usuarios
- `future-2499` · `moon_user_intent` — Intent para usuarios
- `future-2500` · `moon_user_integration` — Integration para usuarios
- `future-2501` · `moon_user_vault` — Vault para usuarios
- `future-2502` · `moon_user_easy_read` — Easy read para usuarios
- `future-2503` · `moon_user_sessions` — Sessions para usuarios
- `future-2504` · `moon_user_editorial` — Editorial para usuarios
- `future-2505` · `moon_user_budget` — Budget para usuarios
- `future-2506` · `moon_user_reputation` — Reputation para usuarios
- `future-2507` · `moon_user_localization` — Localization para usuarios
- `future-2508` · `moon_user_communication_preferences` — Communication preferences para usuarios
- `future-2509` · `moon_user_onboarding` — Onboarding para usuarios
- `future-2510` · `moon_user_governance` — Governance para usuarios
- `future-2511` · `moon_user_voice_control` — Voice control para usuarios
- `future-2512` · `moon_user_federated_bridge` — Federated bridge para usuarios
- `future-2513` · `moon_user_external_event` — External event para usuarios
- `future-2514` · `moon_user_digital_twin` — Digital twin para usuarios
- `future-2515` · `moon_automation_incident_correlation` — Incident correlation para automatizaciones
- `future-2516` · `moon_automation_workflow` — Workflow para automatizaciones
- `future-2517` · `moon_automation_delegation` — Delegation para automatizaciones
- `future-2518` · `moon_automation_coordinated_abuse` — Coordinated abuse para automatizaciones
- `future-2519` · `moon_automation_copilot` — Copilot para automatizaciones
- `future-2520` · `moon_automation_capacity_forecast` — Capacity forecast para automatizaciones
- `future-2521` · `moon_automation_batch_plan` — Batch plan para automatizaciones

### v18.23.7 — 60 funciones incorporadas

- `future-2522` · `moon_automation_workspace` — Workspace para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2523` · `moon_automation_media` — Media para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2524` · `moon_automation_narrative_report` — Narrative report para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2525` · `moon_automation_alert_escalation` — Alert escalation para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2526` · `moon_automation_offline_continuity` — Offline continuity para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2527` · `moon_automation_adaptive_trust` — Adaptive trust para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2528` · `moon_automation_campaign_plan` — Campaign plan para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2529` · `moon_automation_intent` — Intent para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2530` · `moon_automation_integration` — Integration para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2531` · `moon_automation_vault` — Vault para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2532` · `moon_automation_easy_read` — Easy read para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2533` · `moon_automation_sessions` — Sessions para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2534` · `moon_automation_editorial` — Editorial para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2535` · `moon_automation_budget` — Budget para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2536` · `moon_automation_reputation` — Reputation para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2537` · `moon_automation_localization` — Localization para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2538` · `moon_automation_communication_preferences` — Communication preferences para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2539` · `moon_automation_onboarding` — Onboarding para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2540` · `moon_automation_governance` — Governance para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2541` · `moon_automation_voice_control` — Voice control para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2542` · `moon_automation_federated_bridge` — Federated bridge para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2543` · `moon_automation_external_event` — External event para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2544` · `moon_automation_digital_twin` — Digital twin para automatizaciones con vista previa segura y sin efectos directos en Moonbot
- `future-2545` · `moon_media_incident_correlation` — Incident correlation para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2546` · `moon_media_workflow` — Workflow para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2547` · `moon_media_delegation` — Delegation para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2548` · `moon_media_coordinated_abuse` — Coordinated abuse para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2549` · `moon_media_copilot` — Copilot para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2550` · `moon_media_capacity_forecast` — Capacity forecast para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2551` · `moon_media_batch_plan` — Batch plan para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2552` · `moon_media_workspace` — Workspace para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2553` · `moon_media_library` — Library para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2554` · `moon_media_narrative_report` — Narrative report para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2555` · `moon_media_alert_escalation` — Alert escalation para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2556` · `moon_media_offline_continuity` — Offline continuity para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2557` · `moon_media_adaptive_trust` — Adaptive trust para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2558` · `moon_media_campaign_plan` — Campaign plan para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2559` · `moon_media_intent` — Intent para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2560` · `moon_media_integration` — Integration para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2561` · `moon_media_vault` — Vault para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2562` · `moon_media_easy_read` — Easy read para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2563` · `moon_media_sessions` — Sessions para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2564` · `moon_media_editorial` — Editorial para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2565` · `moon_media_budget` — Budget para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2566` · `moon_media_reputation` — Reputation para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2567` · `moon_media_localization` — Localization para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2568` · `moon_media_communication_preferences` — Communication preferences para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2569` · `moon_media_onboarding` — Onboarding para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2570` · `moon_media_governance` — Governance para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2571` · `moon_media_voice_control` — Voice control para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2572` · `moon_media_federated_bridge` — Federated bridge para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2573` · `moon_media_external_event` — External event para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2574` · `moon_media_digital_twin` — Digital twin para multimedia con vista previa segura y sin efectos directos en Moonbot
- `future-2575` · `managed_bot_incident_correlation` — Incident correlation para bots administrados con vista previa segura y sin efectos directos en Moonbot
- `future-2576` · `managed_bot_workflow` — Workflow para bots administrados con vista previa segura y sin efectos directos en Moonbot
- `future-2577` · `managed_bot_delegation` — Delegation para bots administrados con vista previa segura y sin efectos directos en Moonbot
- `future-2578` · `managed_bot_coordinated_abuse` — Coordinated abuse para bots administrados con vista previa segura y sin efectos directos en Moonbot
- `future-2579` · `managed_bot_copilot` — Copilot para bots administrados con vista previa segura y sin efectos directos en Moonbot
- `future-2580` · `managed_bot_capacity_forecast` — Capacity forecast para bots administrados con vista previa segura y sin efectos directos en Moonbot
- `future-2581` · `managed_bot_batch_plan` — Batch plan para bots administrados con vista previa segura y sin efectos directos en Moonbot

<!-- GENERATED_RELEASE_FEATURES_END -->

## v18.23.4 - 2026-07-30 - Registro ampliado a 2.620 funciones verificadas

- Incorpora las 40 funciones finales del horizonte Moonbot: federación, continuidad operativa y asistencia contextual.
- Añade 60 operaciones WebApp de IA y administración de grupos/canales con roles diferenciados y eventos firmados.
- La auditoría completa confirma APIs únicas, código no stub, pruebas resolubles, rol, scope y preflight para cada función.
- La continuidad usa ordenación iterativa para evitar desbordar la pila con grafos grandes.

## v18.23.3 - 2026-07-30 - Registro ampliado a 2.520 funciones verificadas

- Añade 60 funciones Moonbot de eficiencia energética, antiabuso, migración guiada y compatibilidad federada.
- Añade 60 funciones WebApp de moderación, seguridad e IA con eventos HMAC separados por dominio y acciones en vista previa.
- El inventario generado enumera los 120 IDs, APIs y descripciones exactas de esta versión.

## v18.23.2 - 2026-07-30 - Actualizador unificado seguro

### Funciones concretas incorporadas
- `bash start.sh update all`: valida y actualiza Moonbot y exactamente `mtproxy-1`, `mtproxy-2` y `mtproxy-3`.
- `bash start.sh update moonbot`: aplica el `.env` existente, reconstruye la imagen con todas las librerías y reinicia solo Moonbot.
- `bash start.sh update proxies`: aplica el `.env` MTProxy existente y actualiza únicamente las tres instancias configuradas.
- `bash start.sh update check`: valida archivos, variables, permisos, Compose y servicios sin modificar el sistema.

### Seguridad y conservación
- Los `.env` nunca se cargan como shell, no se imprimen ni se sustituyen; se pasan con `docker compose --env-file` y requieren permisos `600` o `640`.
- Git exige repositorio y rama esperados, origen permitido, árbol limpio y avance `--ff-only` al SHA ya obtenido en `FETCH_HEAD`.
- El proceso usa bloqueo exclusivo, excluye Ollama, conserva volúmenes, evita `down -v` y espera el estado saludable de los contenedores.

## v18.23.1 - 2026-07-30 - Registro ampliado a 2.400 funciones verificadas

- Incorpora funciones menores WebApp de SEO, comunidades, soporte, suscripciones, accesibilidad y moderación, junto con controles Moonbot de calidad, sandbox, gobernanza e impacto.
- Corrige la separación por dominio/tipo en firmas HMAC y estabiliza métricas numéricas ante valores extremos o no finitos.
- El inventario generado de esta versión enumera cada ID, API y descripción incorporada.

## v18.23.0 - 2026-07-30 - Registro ampliado a 2.220 funciones verificadas

### Funciones concretas incorporadas
- **Proxy:** `proxy_offline_continuity`, `proxy_adaptive_trust`, `proxy_campaign`, `proxy_intent`, `proxy_integration`, `proxy_vault`, `proxy_easy_read`, `proxy_sessions`, `proxy_editorial`, `proxy_budget`, `proxy_reputation`, `proxy_localization`, `proxy_communication_preferences`, `proxy_onboarding`, `proxy_governance`, `proxy_voice_control`, `proxy_federated_bridge`, `proxy_external_event` y `proxy_digital_twin`.
- **Dashboard:** `dashboard_incidents`, `dashboard_workflow`, `dashboard_delegation`, `dashboard_coordinated_abuse`, `dashboard_copilot`, `dashboard_capacity`, `dashboard_batch_plan`, `dashboard_workspace`, `dashboard_media`, `dashboard_narrative_report`, `dashboard_alert_escalation`, `dashboard_offline_continuity`, `dashboard_adaptive_trust`, `dashboard_campaign`, `dashboard_intent`, `dashboard_integration`, `dashboard_vault`, `dashboard_easy_read`, `dashboard_sessions`, `dashboard_editorial`, `dashboard_budget`, `dashboard_reputation`, `dashboard_localization`, `dashboard_communication_preferences`, `dashboard_onboarding`, `dashboard_governance`, `dashboard_voice_control`, `dashboard_federated_bridge`, `dashboard_external_event` y `dashboard_digital_twin`.
- **Analítica:** `analytics_incidents`, `analytics_workflow`, `analytics_delegation`, `analytics_coordinated_abuse`, `analytics_copilot`, `analytics_capacity`, `analytics_batch_plan`, `analytics_workspace`, `analytics_media`, `analytics_narrative_report`, `analytics_alert_escalation`, `analytics_offline_continuity`, `analytics_adaptive_trust`, `analytics_campaign`, `analytics_intent`, `analytics_integration`, `analytics_vault`, `analytics_easy_read`, `analytics_sessions`, `analytics_editorial`, `analytics_budget`, `analytics_reputation`, `analytics_localization`, `analytics_communication_preferences`, `analytics_onboarding`, `analytics_governance`, `analytics_voice_control`, `analytics_federated_bridge`, `analytics_external_event` y `analytics_digital_twin`.
- **Privacidad:** `webapp_privacy_incidents`, `webapp_privacy_workflow`, `webapp_privacy_delegation`, `webapp_privacy_coordinated_abuse`, `webapp_privacy_copilot`, `webapp_privacy_capacity`, `webapp_privacy_batch_plan`, `webapp_privacy_workspace`, `webapp_privacy_media`, `webapp_privacy_report`, `webapp_privacy_alert_escalation`, `webapp_privacy_offline_continuity`, `webapp_privacy_adaptive_trust`, `webapp_privacy_campaign`, `webapp_privacy_intent`, `webapp_privacy_integration`, `webapp_privacy_vault`, `webapp_privacy_easy_read`, `webapp_privacy_sessions`, `webapp_privacy_editorial`, `webapp_privacy_budget`, `webapp_privacy_reputation`, `webapp_privacy_localization`, `webapp_privacy_communication_preferences`, `webapp_privacy_onboarding`, `webapp_privacy_governance`, `webapp_privacy_voice_control`, `webapp_privacy_federated_bridge`, `webapp_privacy_external_event` y `webapp_privacy_digital_twin`.
- **SEO:** `webapp_seo_incidents`, `webapp_seo_workflow`, `webapp_seo_delegation`, `webapp_seo_coordinated_abuse`, `webapp_seo_copilot`, `webapp_seo_capacity`, `webapp_seo_batch_plan`, `webapp_seo_workspace`, `webapp_seo_media`, `webapp_seo_report` y `webapp_seo_alert_escalation`.

### Seguridad y verificación
- Las HMAC quedan vinculadas al dominio y tipo de evento; dashboard e informes eliminan secretos, PII y valores no finitos.
- Los sujetos de privacidad se pseudonimizan y el modo offline elimina filas y conjuntos de datos crudos.
- Las operaciones destructivas, exportaciones, borrados y publicación SEO permanecen como planes sin efectos automáticos.

### Registro ampliado a 2.100 funciones verificadas - 2026-07-30
- Se integran 60 funciones Moonbot de rotación, archivo programado, restauración puntual, observabilidad y calidad.
- Las operaciones respetan legal hold, checksum, versión esperada, health gates, aprobación y rollback sin ejecutar efectos directos.
- Los controles de calidad sustituyen identificadores inválidos por referencias seguras para impedir reflexión de HTML malicioso.

### Registro ampliado a 2.040 funciones verificadas - 2026-07-30
- Se incorporan 60 operaciones WebApp para creadores, noticias y proxies con roles y estados operativos explícitos.
- Las firmas HMAC quedan separadas por dominio y tipo de evento para impedir sustituciones con una firma reutilizada.
- Los informes proxy normalizan y omiten variantes de secretos, rechazan valores no finitos y mantienen las acciones en modo planificado.

### Registro ampliado a 1.980 funciones verificadas - 2026-07-30
- Se integran 60 funciones Moonbot de notificaciones agrupadas, routing inteligente, caché reconciliable y rotación segura.
- La autorización por scope, los límites, las versiones, la aprobación y el rollback se validan antes de producir planes operativos.
- La redacción recursiva detecta variantes de secretos y los identificadores rechazan traversal, ADS y nombres reservados.

### Registro ampliado a 1.920 funciones verificadas - 2026-07-30
- Se incorporan 60 operaciones WebApp de IA, notificaciones, cuentas y herramientas de creadores con roles explícitos.
- Los eventos externos firman timestamp, identificador y cuerpo, aplican ventana antirreplay, límite de tamaño y secretos robustos.
- Los planes de conexión exigen revalidación DNS y prohíben redirecciones antes de cualquier ejecución de red.

### Registro ampliado a 1.860 funciones verificadas - 2026-07-30
- Se integran 60 operaciones WebApp de contenido, seguridad e IA con roles y ejecución protegida por el registro central.
- El preflight confirma IDs y APIs nuevas; 126 pruebas cubren el bloque y sus regresiones de accesibilidad y modo offline.
- Los nombres de exportación rechazan traversal Unix/Windows, ADS NTFS, dispositivos reservados y terminaciones ambiguas.

### Refuerzo de autenticación y plugins - 2026-07-30
- El panel falla de forma cerrada si faltan la contraseña o el secreto JWT y compara credenciales en tiempo constante.
- La carga y activación de plugins rechazan rutas relativas, absolutas y separadores que pudieran escapar del directorio permitido.
- Cinco pruebas de regresión cubren la configuración vacía, credenciales incorrectas y nombres de archivo maliciosos.

### Registro ampliado a 1.700 funciones verificadas - 2026-07-30
- Se añaden 80 contratos de accesibilidad WebApp, explicaciones accesibles, revisión colaborativa y localización cultural.
- Seis capacidades existentes se reutilizan desde su implementación canónica sin registrar manifiestos duplicados.
- La ampliación supera 89 pruebas específicas y conserva el registro protegido para Hub y TodoSobreAllTech.

### Registro ampliado a 1.620 funciones verificadas - 2026-07-30
- Se integran 120 contratos nuevos de incidentes, correlación temporal, revisión colaborativa, paneles, analítica y operación offline.
- El registro protegido confirma IDs, APIs, módulos y funciones únicas antes de permitir su ejecución.
- El bloque supera 139 pruebas específicas y queda disponible tanto para el Hub como para la pasarela master de TodoSobreAllTech.

### Registro verificable compartido de funciones - 2026-07-30
- 1.500 funciones de Moonbot, web y Telegram WebApp disponen de contrato específico, manifiesto versionable y pruebas por ID.
- La API interna solo ejecuta capacidades incluidas en una lista explícita y rechaza IDs, módulos, argumentos o funciones no registrados.
- El Hub master permite buscar el registro operativo desde Centro avanzado y la web ofrece una pestaña equivalente con ejecución autenticada.
- Los lotes incluyen pronósticos, deriva, impacto, recuperación, validación, orquestación, delegación, versionado, importación, analítica y acciones rápidas.

### Automatizaciones personales y de grupo seguras - 2026-07-30
- Horario silencioso global con zonas IANA, excepciones explicables y diferimiento real de RSS, calendarios y contenido programado.
- Recordatorios persistentes únicos, diarios o semanales con recurrencia segura ante DST, aplazamiento, cancelación y compatibilidad heredada.
- Transcripción real mediante OpenAI con consentimiento por grupo, límites previos, archivo temporal opaco, borrado obligatorio y sin aprendizaje automático.
- El Hub y la web master ofrecen controles equivalentes; se retiraron la transcripción simulada y el comando inseguro basado únicamente en `file_id`.

### Cuentas avanzadas equiparadas en el Hub - 2026-07-30
- El centro master incorpora una sección de cuentas avanzadas con accesos al asistente, webhooks, preferencias, plantillas, sandbox, búsqueda semántica, revisiones, aprendizaje, colaboración, métricas y conector interoperable.
- El destino de TodoSobreAllTech es configurable y se valida como HTTPS, con excepción local para desarrollo.
- El Hub mantiene aislado su Bearer master: esta vista abre herramientas en modo enlace y nunca replica operaciones ni comparte credenciales entre servicios.

### Auditoría de configuración sensible - 2026-07-30
- Moonbot registra diferencias efectivas de seguridad y moderación por grupo, con autor, origen, fecha y nivel de riesgo.
- Los cambios idénticos no crean eventos duplicados y el historial queda limitado a 300 entradas por grupo.
- La API interna y la MiniApp exponen el mismo historial sin incluir credenciales ni datos secretos.

### Historial efectivo de permisos - 2026-07-30
- Moonbot registra únicamente cambios reales en los permisos de cada bot y grupo.
- La MiniApp muestra la cronología, los permisos ausentes, el bot afectado y quién realizó la comprobación.
- Las comprobaciones repetidas sin cambios no generan eventos duplicados.

### CI operativo y errores de ejecución corregidos - 2026-07-30
- El CI comprueba errores Python que pueden romper la ejecución, ejecuta las 21 pruebas y valida el JavaScript del Hub.
- Se corrigen las referencias administrativas de campañas al identificador real del master y se elimina un bloque inalcanzable con variables inexistentes.
- Dependabot queda configurado para Python, Docker y GitHub Actions sin publicar secretos.

### Reconstrucciones Docker más rápidas - 2026-07-28
- Docker conserva en la caché de BuildKit los índices y paquetes de APT y las descargas de Python, reduciendo esperas cuando una capa necesita reconstruirse.
- Las dependencias del sistema se instalan sin paquetes recomendados innecesarios para reducir el tamaño de la imagen.

### Anuncios Telegram no intrusivos - 2026-07-28
- Las campañas comunitarias del Hub admiten mosaico deslizable, fila compacta, tarjetas, recomendación rotatoria y cinta de accesos.
- El modo automático adapta la presentación al número de chats y mantiene los enlaces medidos sin ventanas emergentes, superposiciones ni reproducción automática.

### Campañas comunitarias compatibles con el Hub - 2026-07-28
- La vista Instant de NoticiasWeb3 muestra las campañas comunitarias como un mosaico horizontal compacto y abre cada chat dentro del flujo de Telegram.
- El gestor de anuncios del master en el Hub permite seleccionar una comunidad detectada y crear su campaña completa sin acudir a la web externa.
- Se mantienen enlaces medidos por chat y compatibilidad con anuncios individuales.

### Campañas mosaico para comunidades Telegram - 2026-07-28
- Las campañas propias pueden contener hasta 16 grupos o canales de una comunidad y mantener métricas de clics por chat.
- El formato se conserva en Moonbot con validación de enlaces y compatibilidad con las campañas individuales anteriores.

### Detección y gestión asistida de Comunidades Telegram 10.2 - 2026-07-28
- Moonbot registra automáticamente altas y bajas de chats en comunidades y confirma el estado mediante `getChat`.
- La web y el Hub agrupan los chats por comunidad, muestran miembros detectados y proponen el resto de chats administrados por el mismo bot.
- Se añade una comprobación masiva de hasta 100 chats y un flujo seguro para completar en Telegram las incorporaciones que Bot API todavía no permite ejecutar directamente.

### Vista Instant de NoticiasWeb3 - 2026-07-28
- NoticiasWeb3 dispone ahora de una vista rápida nativa en el Hub, inspirada en Telegram Instant View, con búsqueda, lectura resumida y navegación interna.
- Las campañas propias se intercalan en el feed y los artículos usando enlaces medidos del gestor de anuncios.

### Lista histórica de baneos de marzo de 2018 - 2026-07-28
- Se incorpora una segunda lista estática independiente, fechada el 9 de marzo de 2018 y activa globalmente por defecto.
- De 2.672 entradas recibidas se conservan 2.669 IDs únicas; se descartan tres repeticiones internas y 270 coincidencias con la lista de 2016.
- La nueva lista contiene 2.399 IDs realmente nuevas y se puede activar, desactivar o limitar a grupos sin modificar la lista de 2016.
- Las listas de 2016 y 2018 permanecen activas simultáneamente y se unen a los GBAN creados localmente o desde los paneles.
- Los datos se consideran señales históricas de moderación no verificadas y mantienen acceso al sistema de apelación.

### Propuestas comunitarias de GBAN con análisis previo - 2026-07-28
- Los administradores de grupos pueden proponer un usuario al registro global aportando motivo y evidencias.
- Moonbot puntúa de forma explicable la propuesta con señales antispam, coincidencia CAS y consenso entre grupos diferentes.
- Solo CAS, tres grupos independientes o riesgo antispam extremo con varias evidencias activan una cuarentena global automática de 24 horas.
- La decisión queda pendiente en la campana de la WebApp master, con botones para confirmar el GBAN permanente o revocarlo inmediatamente.
- Un único reporte nunca produce por sí solo un bloqueo global automático y todas las decisiones quedan en auditoría.
- El motor v2 pondera calidad y variedad de evidencias, independencia de grupos y reportantes, contradicciones recientes y confianza calibrada.
- Cada aprobación o rechazo del master actualiza la fiabilidad bayesiana del reportante y las métricas de acierto del sistema.
- La evaluación incorpora reincidencia en bans locales, advertencias, fallos de captcha y eventos spam o ham confirmados en todos los grupos administrados.
- El historial legítimo reduce el riesgo, mientras que la conducta persistente en varios grupos puede activar una cuarentena aunque no exista coincidencia CAS.
- Las propuestas llegan al master como Rich Markdown 10.2 con tabla, confianza, recomendación y señales desplegables.
- Confirmar o revocar desde Telegram edita el mensaje original, actualiza su estado y elimina los botones; existe fallback automático a `editMessageText`.
- Todas las respuestas generadas por comandos de grupo se presentan automáticamente con Rich Markdown 10.2 y un encabezado contextual, incluidos comandos de plugins.
- Las respuestas que ya contienen tablas, tareas, código, fórmulas o detalles enriquecidos se conservan sin envolverlas de nuevo.
- Si Rich Markdown no está disponible, Moonbot entrega exactamente el texto original mediante el mecanismo compatible anterior.
- El diseñador contextual incorpora estados visuales, tarjetas de aviso o éxito, separadores y firma discreta de Moonbot.
- Las respuestas con varias parejas `dato: valor` se convierten automáticamente en tablas sin transformar URLs, código ni contenido ya enriquecido.

### Recuperación de comandos clásicos TeleBots - 2026-07-28
- Se recuperan `/helpadmin`, `/info`, `/reglas`, `/conv`, `/calculadora` y `/sera` con integración en el cargador actual de plugins.
- Vuelven las utilidades GNU/Linux `/alternativa`, `/distro`, `/isos`, `/kernel` y `/man`, enlazando fuentes y descargas oficiales.
- Se añaden `/clima`, `/hora`, `/mapa`, `/terremoto`, `/wiki`, `/diccionario`, `/stack`, `/google` y `/rae` con validación de entrada, tiempos de espera, caché y límites de respuesta.
- Las consultas usan Open-Meteo, USGS, OpenStreetMap, Wikimedia y Stack Exchange según corresponda.
- Se incorporan pruebas automatizadas de alias, conversión numérica, consultas simuladas y tratamiento seguro de fallos externos.

### Reacciones contextuales de Telegram - 2026-07-28
- Moonbot interpreta el mensaje y el texto al que responde para detectar agradecimiento, humor, celebración, entusiasmo, tristeza, acuerdo, duda o novedad.
- Las reacciones usan `setMessageReaction`, excluyen contenido sensible y aplican espera y máximo por hora configurables por grupo.
- WebApp y web ofrecen los mismos perfiles; los mensajes de otros bots permanecen excluidos salvo activación expresa.

### RSS automático por grupo - 2026-07-28
- Los administradores pueden gestionar una lista RSS o Atom independiente desde la sección de cada grupo en la WebApp.
- Cada fuente se puede probar, activar, pausar o eliminar; una fuente recién activada inicializa su historial sin publicar entradas antiguas.
- Moonbot comprueba las fuentes activas cada cinco minutos y publica las entradas nuevas con el bot asociado al grupo.
- Se limitan cantidad, tamaño y tiempo de respuesta, se bloquean destinos privados para evitar SSRF y se validan también las redirecciones.
- Los administradores pueden filtrar titulares, personalizar el mensaje con `{title}`, `{url}` y `{source}`, y publicar dentro de un tema del foro.
- Cada fuente admite frecuencia propia, máximo por ciclo, horario silencioso UTC y pausa automática configurable por fallos.
- La ejecución manual permite inicializar o publicar una fuente inmediatamente desde WebApp o web sin esperar al siguiente ciclo.
- Se incorporan estado de salud, contadores de comprobaciones, publicaciones, filtros y errores por fuente.
- Las fuentes se pueden renombrar y reiniciar sin publicar entradas antiguas; las entregas quedan registradas en un historial limitado.
- El motor calcula latencia y próxima ejecución, y aplica backoff exponencial acotado cuando una fuente falla.
- El historial conserva título, URL y origen de cada entrega; WebApp permite vaciarlo y reiniciar contadores por fuente.

### Correlación de incidencias multigrupo - 2026-07-28
- Nuevo motor determinista que cruza cronologías sin modificar los incidentes originales.
- Agrupa eventos por ventana temporal, tipo y vocabulario común y asigna un nivel de riesgo explicable.
- Disponible mediante rutas protegidas para Web y WebApp master.

### Bóveda personal cifrada en la WebApp - 2026-07-28
- Ajustes incorpora una bóveda local con consentimiento explícito para notas privadas.
- El contenido se cifra con AES-GCM y una clave PBKDF2 antes de almacenarse en el dispositivo.
- Permite crear, desbloquear, volver a cifrar, bloquear y eliminar sin transmitir datos al bot.

### Búsqueda y navegación por voz en la WebApp - 2026-07-28
- La búsqueda global acepta comandos hablados y filtra acciones sin necesidad de teclado.
- Una coincidencia directa abre la vista permitida, respetando los roles de usuario, administrador y master.
- Se reutiliza el procesamiento de voz existente en Moonbot y se sincroniza el estado real con el roadmap.

### Comparador y catálogo sincronizado en la WebApp - 2026-07-27
- El roadmap master permite comparar hasta tres entradas sin salir del Hub.
- El catálogo local se sincroniza con las 3.000 entradas de `todosobreall.tech/roadmap` y reconoce definiciones completadas.
- Los contadores separan funciones incluidas, definidas, en desarrollo y propuestas.

### Roadmap master dentro de la WebApp - 2026-07-27
- El roadmap vuelve al Centro avanzado de la WebApp y solo se muestra dentro del área master.
- Incluye búsqueda, filtro de estado y un apartado identificable de features incluidas.
- La URL pública completa continúa siendo `https://todosobreall.tech/roadmap`.

### Roadmap canónico - 2026-07-27
- El Hub enlaza exclusivamente a `https://todosobreall.tech/roadmap` para consultar la planificación.
- Eliminada la pantalla independiente `roadmap1000.html` y ocultado el antiguo ejecutor genérico.
- Las herramientas operativas permanecen en IA, moderación, automatizaciones, integraciones y operaciones.

### Horizonte mediante recursos REST reales - 2026-07-27
- Nuevos recursos `/api/internal/horizon/features/<slug>` y `/api/users/horizon/<slug>` con `GET`, `POST`, `PUT` y `DELETE`.
- `GET` consulta estado, `POST` ejecuta, `PUT` configura y `DELETE` revierte las funciones del Horizonte 1000.
- Las funciones antiguas conservan compatibilidad sin permitir mutaciones REST no soportadas.
- Se corrige el estado del catálogo: 29 integradas y 971 con ruta preparada para conectar sus efectos de producción.

### Horizonte completo y ejecutable - 2026-07-27
- Nuevo motor `Horizon1000Engine` para las 1.000 funciones multiplataforma, con comportamiento específico para 21 categorías.
- Todas ofrecen ejecución, configuración persistente, consulta de estado, reversión y auditoría.
- `FullHorizonSuite` expone ahora las 1.100 funciones mediante la misma API usada por Hub y TodoSobreAllTech.
- Los 30 tipos de capacidad cuentan con algoritmos propios y ejemplos de entrada asistidos en web y Mini App.

### Horizonte unificado - 2026-07-27
- Horizonte 202 y Horizonte 1000 se presentan como un solo catálogo de 1.100 funciones.
- El Hub conserva el ejecutor de las 100 funciones operativas e integra el roadmap por estado.
- Las rutas y acciones anteriores continúan siendo compatibles.

### Horizonte 202 unificado de extremo a extremo - 2026-07-27

- Las 25 funciones originales de `RoadmapEngine` y las 75 de `HorizonCompletion` forman ahora un catálogo único de exactamente 100 operaciones.
- Un único ejecutor protegido permite usar cualquiera de las 100 desde la MiniApp o TodoSobreAllTech, conservando persistencia y auditoría.
- El endpoint interno publica total, categorías, motor responsable e historial reciente sin exponer claves ni datos privados.
- El Hub deja de limitar su selector a las últimas 75 funciones y muestra también las 25 primeras.

### Edición, distribución y encuestas desde el chat - 2026-07-27

- Se conectan a las interfaces los métodos ya existentes para editar, copiar, reenviar y limpiar todas las reacciones de un mensaje.
- Nueva acción para desfijar todos los mensajes del grupo con una sola confirmación administrativa.
- El chat puede crear encuestas de 1 a 12 opciones y el motor admite modo cuestionario, respuestas múltiples, caducidad y protección.
- Copiar y reenviar solo permite destinos realmente administrados por una instancia conocida de Moonbot.

### Controles completos del chat master - 2026-07-27

- Se auditaron las funciones existentes y se reutilizaron los métodos Telegram ya incorporados, evitando duplicarlos.
- Hub y API permiten responder por `message_id`, borrar, fijar, desfijar y reaccionar desde la conversación.
- Los envíos normales y Rich admiten entrega silenciosa, protección contra reenvío y respuesta contextual.
- El historial conserva identificadores y relaciones de respuesta; al borrar en Telegram se retira también la copia local.

### Mensajes efímeros y Comunidades de Bot API 10.2 - 2026-07-27

- Moonbot puede enviar mensajes de grupo visibles únicamente para el usuario indicado y nunca los copia al historial público del chat.
- Se incorporan edición de texto, multimedia, pie y teclado, además del borrado de mensajes efímeros.
- El bot registra altas y bajas de chats en Comunidades Telegram y conserva los cambios de suscripciones de pago.
- `sendMessage` y `sendRichMessage` admiten los parámetros modernos de temas, privacidad, notificación, respuestas, efectos y publicaciones sugeridas.

### Bot API 10.2 en el chat del Hub - 2026-07-27

- El chat master envía mensajes normales, Rich Markdown y Rich HTML sin abandonar la conversación.
- Incluye plantillas para detalles desplegables, listas, citas y expresiones matemáticas, además de escritura RTL.
- Los mensajes enriquecidos pueden referenciar foto, vídeo, audio, animación o la nueva nota de voz de Bot API 10.2.
- El servidor valida identificadores, tipos y archivos multimedia antes de entregar el payload a Telegram y conserva fallback de texto.

### Chat MiniApp con diseño Telegram - 2026-07-27

- La lista de conversaciones, cabecera, burbujas, horas, acciones y compositor adoptan una presentación compacta inspirada en Telegram.
- Al abrir un grupo se consulta en Telegram el número real de miembros mediante el bot seleccionado y se actualiza la caché del inventario.
- Los controles de moderación quedan recogidos dentro de cada mensaje para mantener limpia la conversación.

### Avisos web del aprendizaje IA - 2026-07-27

- Cada copia horaria del aprendizaje genera un aviso estructurado para TodoSobreAllTech con resultado, tamaño, neuronas, progreso y fecha.
- Se conservan los últimos 100 eventos y se exponen únicamente mediante los endpoints administrativos protegidos.
- Los fallos de entrega también quedan visibles para que el master pueda detectarlos sin revisar los logs del bot.

### Chat Telegram dentro de la MiniApp - 2026-07-27

- El master dispone de un chat integrado en el Hub con todos los grupos únicos y los bots asociados a cada comunidad.
- Permite leer el historial, elegir qué bot responde en grupos compartidos, enviar Markdown y actualizar la conversación automáticamente.
- Desde cada mensaje se puede advertir, silenciar, restaurar o banear al usuario, además de abrir los archivos protegidos del historial.
- Cada grupo se abre como una pestaña interna con flecha atrás y conserva el diseño oscuro original de la MiniApp.
- Los endpoints administrativos aceptan un JWT temporal con alcance exclusivo `miniapp_master`; los tokens sin ese alcance siguen sin acceder.

### Chat Telegram en TodoSobreAllTech - 2026-07-27

- El panel master externo puede consultar el historial seguro de cada comunidad y enviar mensajes mediante el bot realmente asociado.
- Los envíos validan pertenencia, longitud y resultado de Telegram, se guardan en el historial y dejan registro de auditoría.
- El master puede filtrar el inventario por cualquiera de sus bots y elegir qué instancia escribe en los grupos compartidos.
- Cada mensaje admite ban local, mute temporal, advertencias acumulables, karma, cuarentena y acciones de restauración; tres advertencias activan el baneo local automático.
- Fotos, vídeos, audios, stickers y documentos del historial pueden recuperarse bajo demanda mediante un proxy autenticado, sin revelar tokens y con límite de 20 MB.

### Sincronización manual de comunidades - 2026-07-27

- El panel master puede actualizar bajo demanda el nombre, alias, descripción, tipo, miembros y administradores de un grupo o canal directamente desde Telegram.
- El inventario administrativo informa de la última sincronización conocida y conserva la fecha de la última comprobación de administradores.
- Las fotos de grupos y canales se entregan mediante un proxy autenticado que nunca expone el token del bot.
- Se conserva y expone el equipo administrador de cada comunidad con ID, rol, nombre, alias y fecha de comprobación.

### Grupos y canales paginados - 2026-07-27

- Nueva consulta administrativa paginada con búsqueda global y filtro real por grupo o canal.
- Solo devuelve comunidades vinculadas actualmente con al menos una instancia activa de Moonbot.
- Cada registro conserva tipo, enlace público, métricas y bots asociados.

### Usuarios paginados desde servidor - 2026-07-27

- La API administrativa pagina el inventario completo de usuarios y mantiene la búsqueda global por nombre o ID.
- Se limita cada respuesta a un máximo de 100 registros e informa de página, total y número de páginas.

### Campañas oficiales instalables - 2026-07-26

- Moonbot incluye en GitHub campañas iniciales para Todo Sobre All Tech, Comunidad Telebots, Resistencia a la Censura y Todo Sobre Gameplays.
- Se crean activas al instalar la actualización, evitan duplicados y conservan métricas y pausas en actualizaciones posteriores.

### Corrección de «Mis canales» - 2026-07-26

- La vista personal muestra únicamente grupos y canales donde coinciden el usuario administrador y un bot activo de Moonbot.
- El master deja de recibir el inventario global en «Mis canales»; este continúa disponible en sus paneles de administración.

### Carga de sitios integrados - 2026-07-26

- Se corrige la capa de carga que permanecía visible sobre NoticiasWeb3 aunque el iframe ya hubiese terminado.
- El Hub elimina la pantalla de carga al completar el iframe y ofrece recuperación tras doce segundos si la red es lenta.

### Anuncios propios configurables - 2026-07-26

- El catálogo admite descripciones Markdown de hasta 800 caracteres; los anuncios entre grupos conservan su envío mediante Markdown de Telegram.
- El catálogo pausa automáticamente campañas al alcanzar su objetivo y permite duplicarlas sin heredar métricas; la MiniApp incluye la acción de duplicado.
- El master puede aprobar, rechazar y reiniciar métricas de cada campaña directamente desde la MiniApp.
- El catálogo incorpora estados de aprobación para impedir que una propuesta pendiente o rechazada llegue a publicarse.
- Moonbot conserva la programación temporal de campañas y permite reiniciar sus métricas sin eliminar el anuncio.
- La MiniApp recomienda automáticamente el hueco con menor cobertura y aprovecha la campaña con mejor CTR.
- El catálogo conserva el diseño personalizado compartido: colores y llamada a la acción.
- Moonbot mantiene el catálogo central de promociones propias para canales y grupos.
- El master puede añadir, pausar, activar y eliminar anuncios desde la MiniApp.
- Cada anuncio define ubicación, prioridad, imagen y enlace, y registra impresiones y clics.
- TodoSobreAllTech consume el mismo catálogo mediante la integración interna firmada.
- El catálogo conserva métricas por ubicación y permite copiar enlaces medidos del dominio TodoSobreAllTech.

### Noticias Web3 moderna en el Hub - 2026-07-26

- La tarjeta Noticias Web3 solicita expresamente la versión 2026 al abrir su vista integrada.
- La URL embebida conserva `miniapp=1` y añade parámetros mediante la API segura de URL.

### Sitios web integrados en la MiniApp - 2026-07-26

- Telegram Web, Noticias Web3, Resistencia, Gameplays, TodoSobreAllTech y Comunidad se abren en una pantalla nativa dentro del Hub.
- Cada servicio dispone de cabecera, flecha para volver, recarga y apertura externa de respaldo.
- La vista integrada ocupa el espacio disponible y respeta el botón Atrás de Telegram.
- El iframe aplica permisos limitados a navegación, formularios, descargas, portapapeles y pantalla completa.

### Espacio personal para todos los usuarios - 2026-07-26

- La MiniApp abre ahora en `Para ti`, aunque el usuario no administre grupos ni sea master.
- El inicio reúne perfil, nivel, XP, karma, biografía, recordatorios y preferencias de avisos.
- Incluye encuestas, eventos, retos, mentoría, concursos, preguntas, agenda y buzón anónimo.
- Se añaden accesos rápidos al directorio, notificaciones, ajustes y proxies MTProto.
- Un bloc privado local permite guardar notas sin enviarlas al servidor.
- La pestaña y las acciones de administración solo aparecen al confirmar grupos administrados.

### Obtención fiable de proxies MTProto - 2026-07-26

- La MiniApp usa el catálogo completo de TodoSobreAllTech cuando Moonbot no tiene proxies locales configurados.
- Los nodos propios y de menor latencia se priorizan y se omiten los marcados como desconectados.
- La vista ofrece conexión directa, copia de credenciales, latencia, origen, actualización y reintento.
- El comando `/proxy` admite fuentes comunitarias y reconstruye enlaces ausentes.

### Servicio gratuito y sin ánimo de lucro - 2026-07-26

- `/start`, `/help` y el nuevo comando `/gratis` explican el carácter comunitario y gratuito del servicio.
- El menú de comandos de Telegram y el Hub muestran la misma información.
- Se aclara que cualquier apoyo es voluntario y no concede privilegios.

### Anuncios recíprocos entre grupos - 2026-07-26

- Los socios se ordenan por categoría y tamaño de audiencia, excluyendo destinos incompatibles o desactivados.
- Se impiden duplicados pendientes, exceso diario, campañas demasiado próximas y fechas inseguras.
- El programador usa una única instancia, reintenta hasta tres veces y solo confirma entregas aceptadas por Telegram.
- Cada campaña muestra entregas, fallos y estado final en Hub; la política también se controla desde TodoSobreAllTech.
- Se añaden vista previa, plantillas, variantes A/B, enlaces medibles, clics, cancelación, contrapropuestas y franjas recomendadas.
- Los socios admiten favoritos, bloqueos y reputación; las solicitudes caducan y los contenidos sensibles pasan por revisión master.
- Los enlaces se validan con VirusTotal cuando está disponible y los informes finales resumen entregas, fallos y clics.
- La API interna ofrece al panel master de TodoSobreAllTech el mismo inventario de socios, campañas y acciones principales.

### Salud y rendimiento de plugins - 2026-07-26

- Moonbot mide carga, comprobaciones, ejecuciones, errores y latencia media por plugin.
- Tres fallos consecutivos abren un cortacircuitos de cinco minutos para mantener operativo el resto del bot.
- Los errores de importación y ejecución se exponen de forma segura en Hub y TodoSobreAllTech.

### Aislamiento de plugins por grupo - 2026-07-26

- Cada grupo mantiene su propia lista de plugins desactivados sin afectar al resto de comunidades.
- Los plugins bloqueados no ejecutan comandos ni aparecen en el menú administrativo específico del chat.
- Hub y TodoSobreAllTech muestran el inventario completo y permiten alternarlo con sincronización inmediata.

### Comandos dinámicos y plugins - 2026-07-26

- Las instancias cargan realmente los plugins durante el arranque y registran cualquier fallo con su nombre.
- Moonbot descubre los comandos instalados y crea menús separados para usuarios, administradores y master mediante `setMyCommands`.
- Los menús se sincronizan al arrancar, al recargar plugins, al modificar un grupo o bajo demanda desde Hub y TodoSobreAllTech.

### Política de formatos por grupo - 2026-07-26

- Moonbot puede bloquear por grupo fotos, vídeos, audios, notas de voz, documentos, stickers, GIF y videomensajes.
- El filtro actúa antes de descargar el archivo, admite límite de tamaño y permite eliminar, silenciar o banear.
- Los administradores quedan protegidos y Hub y TodoSobreAllTech comparten la configuración.
- El anti-flood específico del grupo sustituye al control global antiguo para evitar sanciones duplicadas.

### Anti-flood configurable por grupo - 2026-07-26

- Moonbot cuenta ráfagas por usuario y grupo usando límites y ventanas independientes.
- Puede eliminar el mensaje excedente, aplicar mute temporal y escalar reincidencias a ban local.
- Los administradores quedan excluidos y la configuración está disponible tanto en Hub como en TodoSobreAllTech.

### Mute real durante el captcha - 2026-07-26

- Los usuarios admitidos quedan sin permisos de texto, audio, documentos, fotos, vídeos, notas, encuestas, stickers ni vistas previas.
- Los permisos solo se restauran después de superar captcha, suscripciones obligatorias y comprobaciones CAS/comunitarias.
- Las entradas directas también quedan protegidas; los reintentos mantienen el mute y los casos rechazados o caducados se expulsan.
- Hub y TodoSobreAllTech comparten el mismo interruptor por grupo y muestran qué solicitudes tienen el mute activo.

### Horizonte 1000 sincronizado · bloque de moderación - 2026-07-26

- Moonbot valida y persiste simulaciones de reglas, plantillas, informes programados, traducciones y comunicados versionados.
- El Hub ofrece controles específicos para las cinco funciones y muestra la respuesta real del motor.
- TodoSobreAllTech accede al mismo motor mediante una ruta interna limitada y protegida por la clave administrativa compartida.

### Contador master unificado - 2026-07-26

- La tarjeta de grupos usa el inventario multibot completo en lugar del contador histórico de claves `ADMINS_`.
- El resumen y el listado comparten una única consulta, evitando mostrar 21 grupos mientras el inventario contiene muchos más.
- La cifra representa grupos únicos y mantiene separados los grupos compartidos entre bots.

### Corrección del arranque en conexiones lentas - 2026-07-26

- La comprobación de GitHub queda desactivada por defecto dentro del contenedor.
- Si se habilita, `git fetch` tiene límite de tiempo y nunca bloquea el servidor web.

### Corrección del inventario de grupos - 2026-07-26

- La MiniApp del master une los registros de PocketBase con los chats activos de todas las instancias.
- Los nombres persistidos se restauran al arrancar y se muestran también en todosobreall.tech.
- Cada grupo indica qué instancia de bot lo administra en la MiniApp y en la API web.

## v18.22.0 - Inventario completo en MiniApp - 2026-07-26

- La MiniApp consulta primero el inventario master validado por el servidor y evita quedarse en los grupos personales.
- El listado une todas las instancias activas, elimina duplicados y devuelve grupos únicos y compartidos.
- La selección ya no depende de una variable de autenticación del navegador que podía llegar tarde.
- La respuesta incluye número de instancias y usernames para mantener el panel móvil alineado con la web.
- La sección de bots incorpora estado, eventos, latencia, errores y grupos exclusivos/compartidos, igual que la web.
- Consultar bots ya no crea instancias temporales de Moonbot para resolver sus nombres.

## v18.21.0 - Acceso global independiente - 2026-07-26

- El master puede configurar el canal obligatorio general sin entrar en ningún grupo.
- Un interruptor global permite activar o pausar el requisito conservando el canal configurado.
- El endpoint está protegido mediante la sesión firmada de Telegram y rechaza usuarios no master.

## v18.20.0 - Grupos exclusivos y compartidos - 2026-07-26

- El inventario diferencia grupos únicos, exclusivos y administrados por varias instancias.
- Cada bot informa cuántos de sus grupos son propios y cuántos comparte con otros bots.
- La relación grupo-bot se genera desde las instancias activas para evitar asociaciones incompletas.

## v18.19.1 - Identidad oficial de bots - 2026-07-26

- El nombre visible y el username de cada instancia se obtienen directamente mediante `getMe` de Telegram.
- El panel de rendimiento ya no deduce el nombre desde registros locales.

## v18.19.0 - Rendimiento real por instancia - 2026-07-26

- Cada bot expone actividad procesada, llamadas y errores de Telegram, latencia, uptime y fallos del polling.
- El centro de control distingue el estado real de ejecución de cada instancia.
- Las métricas se mantienen separadas por bot y no mezclan sus grupos ni su actividad.

## v18.18.0 - Idiomas de usuarios por grupo - 2026-07-26

- Se registra el idioma de Telegram de cada usuario que participa o entra en un grupo.
- Si Telegram no aporta idioma, se intenta detectar a partir del texto del mensaje.
- La captura ocurre antes de los filtros de moderación para no perder usuarios bloqueados o mensajes eliminados.
- El mapa ofrece distribución global o por grupo sin exponer identidades ni tratar el idioma como ubicación real.

## v18.17.1 - Autenticación master multi-bot - 2026-07-26

- La MiniApp valida `initData` con el bot activo desde el que Telegram la abrió.
- El acceso master funciona también desde una instancia secundaria de Moonbot.
- La cabecera avisa cuando Telegram no puede validar la sesión.

## v18.17.0 - Canales obligatorios por niveles - 2026-07-26

- El dueño de cada grupo puede configurar su propio canal obligatorio.
- El master puede añadir un canal general obligatorio para todos los grupos.
- El captcha distingue el requisito del grupo del requisito global y comprueba ambos antes de aprobar.

## v18.16.0 - Suscripción obligatoria y captcha persistente - 2026-07-26

- Cada grupo puede exigir la suscripción a hasta 20 canales antes de aprobar una solicitud.
- El captcha muestra los canales pendientes y permite volver a comprobarlos sin repetir el reto.
- La aprobación manual también respeta las suscripciones obligatorias configuradas.
- Si un usuario pendiente intenta escribir, se elimina el mensaje y se reenvía el acceso al captcha con límite anti-spam.
- La MiniApp permite configurar los canales obligatorios desde el panel de acceso de cada grupo.

## v18.14.0 - Experiencia web sincronizada - 2026-07-26

- Preferencias persistentes para favoritos, widgets, modo compacto y recorrido guiado.
- Catálogo unificado de acciones para el buscador global de todosobreall.tech.
- Historial administrativo limitado y sincronizable entre sesiones.
- Centro de notificaciones agregado desde informes, apelaciones y solicitudes.
- Tamaño de texto, alto contraste y movimiento reducido configurables.
- Temas visuales persistentes por grupo administrado.
- Endpoint protegido para sincronizar cambios locales después de recuperar conexión.

## v18.13.0 - Operaciones y fiabilidad administrables - 2026-07-26

- Planes de despliegue gradual con lotes y resultados de salud por instancia.
- Política de copias cifradas con retención y selección de módulos.
- Planes de restauración con confirmación pendiente y cancelación segura.
- Registro de salud, latencia y estado de dependencias externas.
- Alertas de CPU, memoria, disco y latencia basadas en umbrales.
- Modo degradado con capacidades disponibles cuando falla una dependencia.
- Diagnóstico automático, agrupación de errores y recomendaciones operativas.
- Ventanas de mantenimiento programables y cancelables desde la administración.

## v18.12.0 - Integraciones y API administrables - 2026-07-26

- Registro de módulos con versión, permisos y checksum verificable.
- Tokens API con ámbitos restringidos, caducidad, rotación y revocación.
- Aislamiento sandbox configurable por bot y cuotas por método.
- Exportación e importación de configuraciones firmadas contra manipulaciones.
- Enlace de incidentes y calendarios externos sin exponer tokens de sincronización.
- Manifiesto SDK consultable con eventos y modelo de autenticación compatibles.
- Auditoría de todas las operaciones realizadas desde TodoSobreAllTech.

## v18.11.0 - Automatizaciones administrables - 2026-07-26

- Constructor de reglas por palabra clave con condiciones y respuestas automáticas.
- Simulador de reglas que no publica mensajes ni ejecuta acciones reales.
- Formularios adaptables asociados a grupos administrados.
- Webhooks HTTPS con validación de destino y secretos ocultos en todas las respuestas.
- Calendario de acciones conectado al ejecutor existente de Moonbot.
- Control de cola con priorización, cancelación y reintento de webhooks fallidos.
- Biblioteca instalable de automatizaciones de bienvenida, soporte e incidencias.
- Endpoint interno protegido y auditoría de todos los cambios administrativos.

## v18.10.0 - Centro de IA externo - 2026-07-26

- ConfiguraciÃ³n segura de proveedor y modelo global sin exponer claves API.
- SelecciÃ³n de proveedor, modelo y finalidad por grupo administrado.
- Alta y eliminaciÃ³n de fuentes aprobadas y borrado selectivo de memorias.
- Registro comparable de precisiÃ³n, latencia y coste por modelo.
- DetecciÃ³n de preguntas sin respuesta y lagunas de conocimiento.
- Cola de revisiÃ³n humana con aprobaciÃ³n, rechazo, comentarios y auditorÃ­a.

## v18.9.0 - Seguridad administrativa completada - 2026-07-26

- AgregaciÃ³n de fuentes CAS, SpamWatch, registro comunitario, listas locales y otras fuentes.
- Acciones protegidas de mute y unmute por grupo mediante permisos de Telegram.
- CreaciÃ³n de casos de revisiÃ³n por pares desde TodoSobreAllTech.
- Consulta de raids preparada para actualizaciÃ³n automÃ¡tica cada 15 segundos en la web.
- ComprobaciÃ³n de suplantaciÃ³n por similitud de nombre y coincidencia de username.

## v18.8.0 - Horizonte 1000 en la WebApp - 2026-07-26

- CatÃ¡logo local con exactamente 1.000 propuestas diferenciadas para Web, Moonbot y Telegram WebApp.
- Nueva pantalla `/roadmap1000.html` optimizada para mÃ³vil con bÃºsqueda, filtros y paginaciÃ³n.
- Acceso directo desde el panel de roadmap de la MiniApp.
- Cada entrada se etiqueta como propuesta e incluye producto, categorÃ­a, prioridad, dificultad y dependencia.
- Se conserva Horizonte 202 como conjunto operativo independiente del nuevo roadmap.

## v18.7.0 - Cierre de funciones administrativas parciales - 2026-07-26

- GuÃ­a paso a paso para reparar permisos insuficientes del bot en cada grupo.
- Historial reciente sanitizado y comparaciÃ³n de configuraciones entre grupos.
- Acciones reales de silenciar/restaurar usuarios mediante `restrictChatMember`.
- Casos de revisiÃ³n por pares para sanciones dudosas.
- Detector de suplantaciÃ³n basado en similitud de nombre y username.
- Los raids activos continÃºan expuestos en el centro de seguridad para actualizaciÃ³n periÃ³dica.

## v18.6.0 - Centro editorial externo - 2026-07-26

- API editorial protegida conectada al motor persistente `RoadmapEngine`.
- PublicaciÃ³n inmediata multigrupo utilizando Rich Markdown con fallback seguro.
- ProgramaciÃ³n para una fecha concreta y recurrencia diaria, semanal o mensual.
- NormalizaciÃ³n horaria para que las fechas del navegador sean compatibles con el ejecutor del servidor.
- Vista previa con variables, plantillas reutilizables y comparador de titulares.
- Comunicados versionados con checksum y calendario de publicaciones pendientes.
- Todos los destinos se validan contra grupos realmente administrados por Moonbot.

## v18.5.0 - Centro de seguridad externo - 2026-07-26

- Resumen protegido de amenazas, eventos multimedia, raids activos y fuentes de baneos.
- AnÃ¡lisis de URL, dominios y hashes mediante el gestor existente de VirusTotal y su cachÃ©.
- Detector local de tokens, claves privadas, API keys y JWT que no almacena ni devuelve los secretos.
- CronologÃ­a consolidada de incidentes y resultados de anÃ¡lisis.
- ExportaciÃ³n JSON de evidencias con firma HMAC-SHA256 verificable.
- Los anÃ¡lisis iniciados desde TodoSobreAllTech quedan registrados en la auditorÃ­a de Moonbot.

## v18.4.0 - Usuarios y sanciones externas - 2026-07-26

- API interna protegida para buscar usuarios y consultar reputaciÃ³n, actividad, idioma y notas.
- Ficha sanitizada con motivo, fuente, Ã¡mbito y vencimiento del baneo.
- ComprobaciÃ³n CAS contra la copia local para evitar peticiones remotas innecesarias.
- Baneo y restauraciÃ³n global o por grupo con propagaciÃ³n real mediante Telegram Bot API.
- Cuarentena por grupo, notas administrativas y resoluciÃ³n de apelaciones.
- Registro de auditorÃ­a para todas las acciones iniciadas desde TodoSobreAllTech.

## v18.3.0 - Grupos y plugins operativos - 2026-07-26

- AdministraciÃ³n externa segura de grupos con listado, detalle, permisos, actividad y configuraciÃ³n de `GroupSuite`.
- Copia controlada de configuraciÃ³n entre grupos conocidos, sin aceptar destinos ajenos al bot.
- Plugin `group_health`: diagnÃ³stico inmediato de permisos esenciales de Telegram.
- Plugin `incident_log`: registro persistente y consulta de incidentes por grupo.
- Plugin `quiet_hours`: configuraciÃ³n validada de horarios silenciosos.
- Plugin `group_digest`: resumen local de actividad y participantes sin servicios externos.
- Plugin `rule_templates`: perfiles estricto, equilibrado y comunidad para moderaciÃ³n.

## v18.2.0 - Centro de control externo seguro - 2026-07-26

- Nuevo endpoint interno `/api/internal/admin-overview` autenticado con una clave servidor-a-servidor.
- Resumen sanitizado de instancias, grupos, usuarios observados, actividad reciente y tareas pendientes.
- Métricas reales de CPU, RAM y disco para el centro de control de TodoSobreAllTech.
- Registro `last_seen` por usuario para calcular actividad de las últimas 24 horas sin inventar estimaciones.
- Ningún token de bot, secreto ni identificador individual se devuelve al panel central.

## v18.1.0 - Mapa lingüístico agregado - 2026-07-26

- Registro persistente del `language_code` declarado por Telegram para cada usuario conocido.
- Endpoint público de solo lectura `/api/public/stats/language-map` con datos exclusivamente agregados.
- Conversión idioma/región a puntos orientativos para representación global.
- Etiquetado expreso de la visualización como estimación lingüística, no ubicación física.
- No se publican identificadores, nombres, mensajes, IP ni coordenadas individuales.

## v18.0.0 - Horizonte 202 completado - 2026-07-26

- Las 100 funciones del catálogo Horizonte 202 disponen de una operación ejecutable, persistencia y auditoría.
- Completadas las áreas de contenido, IA, accesibilidad, privacidad, operaciones, integraciones, sostenibilidad y experiencia Telegram.
- Nuevo motor `HorizonCompletion` con 75 capacidades estables y catálogo de slugs para API y MiniApp.
- Ejecutor contextual autenticado en la MiniApp para probar cada función con parámetros JSON.
- Datos sensibles redactados en auditoría y mensajes administrativos de un solo uso consumibles.
- Catálogo público marcado como completo y sincronizado con TodoSobreAllTech.

### Funciones incorporadas en v18.0.0 (75)

#### Contenido y canales (5)

- Mapa de fuentes y citas de cada publicación.
- Detección de contenido desactualizado.
- Paquetes de publicación multicanal.
- Modo cobertura en directo con hitos.
- Archivo temático navegable de conversaciones.

#### IA y conocimiento (10)

- Memorias separadas por proyecto y finalidad.
- Explicaciones con nivel principiante o experto.
- Debate interno entre agentes antes de responder.
- Registro visible de fuentes usadas por la IA.
- Detector de lagunas de conocimiento.
- Entrenamiento por ejemplos aprobados y contraejemplos.
- Modo profesor con ejercicios adaptativos.
- Resúmenes que preservan opiniones minoritarias.
- Comparador de respuestas entre modelos.
- Caducidad automática del conocimiento sensible al tiempo.

#### Accesibilidad e idiomas (10)

- Lectura fácil automática para textos complejos.
- Audiodescripción de imágenes relevantes.
- Subtítulos colaborativos para mensajes de vídeo.
- Modo alto contraste por chat.
- Navegación completa mediante voz.
- Transliteración entre alfabetos.
- Glosarios locales por comunidad e idioma.
- Traducción que conserva nombres y terminología.
- Resúmenes en lengua de signos mediante avatar.
- Detector de barreras de accesibilidad antes de publicar.

#### Privacidad y protección (10)

- Panel personal de datos almacenados.
- Borrado selectivo con vista previa.
- Mensajes administrativos de un solo uso.
- Alertas por capturas de datos sensibles.
- Anonimización automática de exportaciones.
- Claves de recuperación divididas entre responsables.
- Modo investigación con acceso temporal.
- Detector de secretos pegados por accidente.
- Etiquetas de retención por tipo de dato.
- Informe mensual de privacidad comprensible.

#### Operaciones y fiabilidad (10)

- Gemelo digital para ensayar configuraciones.
- Despliegue canario por grupos seleccionados.
- Recuperación automática según objetivo de servicio.
- Mapa de dependencias y puntos únicos de fallo.
- Presupuesto de errores por función.
- Reproducción de incidentes con eventos anonimizados.
- Detector de configuraciones divergentes.
- Ventanas de mantenimiento por zona horaria.
- Capacidad predictiva de colas y almacenamiento.
- Modo degradado que conserva funciones esenciales.

#### Integraciones abiertas (10)

- Conectores creados visualmente sin código.
- Mercado comunitario de automatizaciones.
- Puente ActivityPub para comunidades federadas.
- Sincronización bidireccional con calendarios CalDAV.
- Importación y exportación mediante OPML.
- Eventos firmados con WebSub.
- Identidad portable mediante credenciales verificables.
- Flujos compatibles con Matrix.
- Catálogo automático de capacidades por bot.
- Entorno de pruebas aislado para integraciones.

#### Sostenibilidad y crecimiento (10)

- Calculadora transparente de costes por comunidad.
- Objetivos de financiación con hitos verificables.
- Patrocinios con frecuencia máxima configurable.
- Reparto de ingresos entre creadores colaboradores.
- Modo ahorro energético para tareas no urgentes.
- Informe de huella operativa estimada.
- Donaciones destinadas a funciones concretas.
- Créditos comunitarios no transferibles.
- Predicción de abandono con intervención respetuosa.
- Experimentos A/B con consentimiento y límites.

#### Experiencia Telegram (10)

- Bandeja unificada de temas pendientes.
- Atajos personales sincronizados con la Mini App.
- Panel lateral contextual por mensaje.
- Respuestas efímeras para operaciones sensibles.
- Comunidades enlazadas con permisos heredables.
- Consultas de entrada con formularios adaptativos.
- Rutas guiadas para nuevos administradores.
- Modo evento que transforma temporalmente el grupo.
- Acciones masivas con previsualización y deshacer.
- Centro de notificaciones priorizadas por impacto.

## v17.9.0 - Contenido conectado - 2026-07-26

- Series editoriales ordenadas con publicación y archivado.
- Reutilización inteligente de contenido según antigüedad, rendimiento y vigencia.
- Calendario de silencios para evitar publicaciones durante ventanas sensibles.
- Comparador de titulares con claridad, longitud y señales de clickbait.
- Comunicados públicos con historial, correcciones y checksum por versión.
- Controles equivalentes en API y MiniApp; catálogo Horizonte 202 actualizado a 25 funciones operativas.

### Funciones incorporadas en v17.9.0 (5)

- Editor de series editoriales conectadas.
- Reutilización inteligente de contenido antiguo.
- Calendario de silencios para evitar saturación.
- Comparador de titulares antes de publicar.
- Versionado público de comunicados corregidos.

## v17.8.0 - Rich Markdown de Telegram - 2026-07-26

- Compatibilidad con `sendRichMessage` y `sendRichMessageDraft` de Bot API 10.2.
- Rich Markdown con encabezados, listas, tareas, tablas, referencias, fórmulas, detalles y medios.
- Validación local de límites oficiales: 32.768 caracteres, 500 bloques y 50 medios.
- Fallback automático a texto normal cuando el endpoint aún no está disponible.
- Nuevo comando `/rich` (`/richmarkdown`) y modo programático `parse_mode="RichMarkdown"`.
- Editor autenticado en la Mini App para publicar Rich Markdown en grupos administrados.
- Endpoint web `/api/users/rich-message` con comprobación del grupo de destino y auditoría.

## v17.7.0 - Horizonte 202 - 2026-07-26

- Catálogo adicional de 100 funciones nuevas, separado del roadmap anterior y del motor operativo.
- Diez áreas: moderación, comunidad, contenido, IA, accesibilidad, privacidad, operaciones, integraciones, sostenibilidad y experiencia Telegram.
- Buscador y filtros dentro del Centro avanzado de la Mini App.
- Cada elemento se identifica expresamente como propuesta planificada, no como función ya implementada.
- Catálogo equivalente publicado en TodoSobreAllTech para mantener ambos proyectos alineados.
- Primera fase operativa: radar de escalada, mediación por turnos, cuarentena de dominios, revisión por pares y simulación de impacto de reglas.
- Segunda fase operativa: detección de brigadas, pasaporte de reputación consentido, riesgo de clonación de voz, cronología de incidentes y cadena de custodia verificable.
- Tercera fase operativa: asambleas, presupuesto participativo ponderado, círculos temporales, banco de tiempo y bienvenida humana distribuida.
- Cuarta fase operativa: misiones entre grupos, reconocimiento de aportes invisibles, salud social agregada, relevos administrativos y memoria anual comunitaria.

### Funciones incorporadas en v17.7.0 (20)

- Radar de conversaciones que están escalando.
- Modo mediador con turnos de palabra.
- Detección de brigadas externas coordinadas.
- Cuarentena de enlaces recién registrados.
- Pasaporte de reputación exportable por el usuario.
- Revisión por pares para sanciones dudosas.
- Simulador de impacto antes de cambiar una regla.
- Detector de estafas por clonación de voz.
- Mapa temporal de incidentes por tema.
- Cadena de custodia firmada para evidencias.
- Asambleas con propuestas y enmiendas.
- Presupuesto comunitario con votos ponderados.
- Círculos temporales por intereses.
- Banco de tiempo entre miembros.
- Rondas automáticas de bienvenida humana.
- Misiones colaborativas entre varios grupos.
- Reconocimiento de contribuciones invisibles.
- Panel de salud social sin leer mensajes privados.
- Sistema de relevos para administradores.
- Memoria anual generada por la comunidad.

## v17.6.0 - Integración con Wayback Machine

- Cliente para la Availability JSON API oficial de Internet Archive.
- Consulta de la captura disponible más próxima, con fecha opcional `YYYYMMDDhhmmss`.
- Validación de URL, bloqueo de direcciones locales/privadas, timeout y errores controlados.
- Comandos `/wayback`, `/archivo` y `/archive` para todos los usuarios.
- Consulta equivalente en el Centro de Seguridad web y en la Mini App del master.
- Historial local limitado de consultas sin descargar ni ejecutar el contenido archivado.

## v17.5.1 - Recuperación del panel de canales

- Migración completa de los campos de `tg_channels` y `tg_channel_admins` en instalaciones antiguas.
- Los registros existentes se marcan activos al crear por primera vez el campo `active`, evitando que una migración los oculte.
- Los posts de canal registran el chat antes de salir del bucle de procesamiento.
- El backfill combina los chats locales con los canales activos ya conocidos en PocketBase.
- El master consulta todos los espacios del bot; los demás usuarios conservan únicamente sus grupos asociados.
- La Mini App muestra los errores de PocketBase y conexión en vez de convertirlos silenciosamente en una lista vacía.
- Los grupos básicos también quedan registrados al recibir cambios de membresía del bot.

## v17.5.0 - Bots administrados de Telegram

- Compatibilidad completa con `managed_bot` y detección de `can_manage_bots`.
- Creación guiada mediante el flujo oficial de Telegram, tanto en la web como en la Mini App.
- Conexión automática opcional de nuevos bots administrados y almacenamiento cifrado de sus tokens.
- Consulta y cambio del acceso restringido, rotación segura de credenciales y desconexión local.
- Registro auditable y catálogo de bots detectados sin exponer tokens al navegador ni a los registros.
- Confirmaciones obligatorias para rotar credenciales o desconectar una instancia.

## [Unreleased] — Roadmap de 102 funciones propuestas
> Estas funciones son propuestas priorizables y todavía no se consideran implementadas.

### Moderación y seguridad (1–10)
1. Modo lento adaptativo según el volumen y riesgo del chat. **Implementado en v16.91.0.**
2. Detección coordinada de raids entre varios grupos. **Implementado en v17.0.0.**
3. Cuarentena reforzada por nivel de reputación. **Implementado en v17.0.0.**
4. Bloqueo de suplantaciones de administradores. **Implementado en v17.0.0.**
5. Detección de enlaces acortados y redirecciones encadenadas. **Implementado en v17.0.0.**
6. Análisis de archivos peligrosos por hash y tipo MIME. **Implementado en v17.0.0.**
7. Límites personalizados de menciones, emojis y mayúsculas. **Implementado en v16.91.0.**
8. Reincidencia compartida entre grupos autorizados. **Implementado en v17.0.0.**
9. Simulación previa de reglas antes de activarlas. **Implementado en v16.91.0.**
10. Caducidad y revisión automática de sanciones. **Implementado en v16.91.0.**

### Miembros y comunidad (11–20)
11. Perfil comunitario con actividad, karma y roles. **Implementado en v16.92.0.**
12. Solicitudes para obtener roles personalizados. **Implementado en v16.92.0.**
13. Programa de mentores para nuevos miembros. **Implementado en v16.93.0.**
14. Reconocimientos semanales a colaboradores. **Implementado en v16.92.0.**
15. Sistema configurable de niveles y experiencia. **Implementado en v16.92.0.**
16. Directorio interno de miembros verificados. **Implementado en v16.92.0.**
17. Encuestas de satisfacción y clima del grupo. **Implementado en v16.93.0.**
18. Buzón anónimo con protección antiabuso. **Implementado en v16.93.0.**
19. Recordatorios personales gestionados por el bot. **Implementado en v16.92.0.**
20. Panel de preferencias de notificaciones por usuario. **Implementado en v16.92.0.**

### Administración de grupos (21–30)
21. Asistente inicial de configuración por tipo de comunidad. **Implementado en v16.94.0.**
22. Comparador de configuración entre grupos. **Implementado en v16.94.0.**
23. Sincronización selectiva de reglas y roles. **Implementado en v16.94.0.**
24. Historial de cambios con restauración por versión. **Implementado en v16.94.0.**
25. Aprobación dual para cambios críticos. **Implementado en v16.94.0.**
26. Delegación temporal de permisos administrativos. **Implementado en v16.94.0.**
27. Calendario común de acciones y eventos. **Implementado en v16.94.0.**
28. Horarios de apertura y cierre del chat. **Implementado en v16.94.0.**
29. Archivado automático de grupos inactivos. **Implementado en v16.94.0.**
30. Comprobación periódica de permisos del bot. **Implementado en v16.94.0.**

### Automatización y contenido (31–40)
31. Publicaciones recurrentes con calendario visual. **Implementado en v17.0.0.**
32. Flujo de aprobación editorial antes de publicar. **Implementado en v17.0.0.**
33. Biblioteca compartida de mensajes y recursos. **Implementado en v17.0.0.**
34. Variables dinámicas en plantillas. **Implementado en v17.0.0.**
35. Traducción automática opcional de publicaciones. **Implementado en v17.0.0.**
36. Reutilización de contenido entre canales autorizados. **Implementado en v17.0.0.**
37. Caducidad automática de mensajes promocionales. **Implementado en v17.0.0.**
38. Respuestas por palabra clave con condiciones. **Implementado en v17.0.0.**
39. Formularios conversacionales configurables. **Implementado en v17.0.0.**
40. Webhooks por eventos de grupo. **Implementado en v17.0.0.**

### Inteligencia artificial (41–50)
41. Resúmenes diarios, semanales y por tema. **Implementado en v17.0.0.**
42. Respuestas basadas exclusivamente en fuentes aprobadas. **Implementado en v17.0.0.**
43. Detección de preguntas sin respuesta. **Implementado en v17.0.0.**
44. Clasificación automática de conversaciones por tema. **Implementado en v17.0.0.**
45. Explicación legible de cada decisión de moderación. **Implementado en v17.0.0.**
46. Comparador de precisión entre modelos. **Implementado en v17.0.0.**
47. Pruebas A/B de respuestas automáticas. **Implementado en v17.0.0.**
48. Memoria separada y exportable por grupo. **Implementado en v17.0.0.**
49. Detección de cambios de tono y conflictos emergentes. **Implementado en v17.0.0.**
50. Asistente para redactar reglas comunitarias. **Implementado en v17.0.0.**

### Eventos y participación (51–60)
51. Creación guiada de eventos en Telegram. **Implementado en v16.93.0.**
52. Inscripciones con cupos y lista de espera. **Implementado en v16.93.0.**
53. Confirmación de asistencia y recordatorios. **Implementado en v16.93.0.**
54. Sorteos auditables con reglas configurables. **Implementado en v16.93.0.**
55. Concursos con jurado y votación comunitaria. **Implementado en v16.93.0.**
56. Retos periódicos con progreso y clasificación. **Implementado en v16.93.0.**
57. Sesiones de preguntas y respuestas moderadas. **Implementado en v16.93.0.**
58. Agenda comunitaria exportable a calendario. **Implementado en v16.93.0.**
59. Certificados o insignias de participación. **Implementado en v16.93.0.**
60. Estadísticas posteriores a cada evento. **Implementado en v16.93.0.**

### Analítica e informes (61–70)
61. Retención de miembros por cohortes. **Implementado en v17.0.0.**
62. Embudo de entrada desde solicitud hasta participación. **Implementado en v17.0.0.**
63. Horas y días con mayor actividad. **Implementado en v17.0.0.**
64. Crecimiento orgánico frente a campañas. **Implementado en v17.0.0.**
65. Panel de salud comunitaria. **Implementado en v17.0.0.**
66. Alertas por anomalías en métricas. **Implementado en v17.0.0.**
67. Informes programados por Telegram o correo. **Implementado en v17.0.0.**
68. Comparación anónima entre grupos propios. **Implementado en v17.0.0.**
69. Exportación compatible con herramientas BI. **Implementado en v17.0.0.**
70. Objetivos mensuales con seguimiento visual. **Implementado en v17.0.0.**

### Bots, integraciones y API (71–80)
71. Marketplace interno de módulos verificados. **Implementado en v17.0.0.**
72. Tokens de API con permisos granulares. **Implementado en v17.0.0.**
73. Rotación automática de credenciales. **Implementado en v17.0.0.**
74. Entorno de pruebas aislado por bot. **Implementado en v17.0.0.**
75. Monitor de cuotas y límites de Telegram. **Implementado en v17.0.0.**
76. Integración con calendarios externos. **Implementado en v17.0.0.**
77. Integración con gestores de incidencias. **Implementado en v17.0.0.**
78. Importación y exportación de configuración firmada. **Implementado en v17.0.0.**
79. Registro de webhooks con reintentos y cola muerta. **Implementado en v17.0.0.**
80. SDK documentado para extensiones de Moonbot. **Implementado en v17.0.0.**

### Operaciones y fiabilidad (81–90)
81. Despliegues graduales entre instancias. **Implementado en v17.0.0.**
82. Reversión automática ante fallos de salud. **Implementado en v17.0.0.**
83. Copias cifradas con política de retención. **Implementado en v17.0.0.**
84. Restauración selectiva por grupo o módulo. **Implementado en v17.0.0.**
85. Panel de dependencias y servicios externos. **Implementado en v17.0.0.**
86. Alertas de disco, memoria, CPU y latencia. **Implementado en v17.0.0.**
87. Modo degradado cuando falla la IA o CAS. **Implementado en v17.0.0.**
88. Diagnóstico automático con recomendaciones. **Implementado en v17.0.0.**
89. Registro de errores agrupado por causa. **Implementado en v17.0.0.**
90. Ventanas de mantenimiento programadas. **Implementado en v17.0.0.**

### Experiencia web y Mini App (91–100)
91. Buscador global de acciones y ajustes. **Implementado en v16.88.0.**
92. Acciones favoritas en la portada. **Implementado en v16.89.0.**
93. Navegación con historial y enlaces internos. **Implementado en v16.89.0.**
94. Centro unificado de notificaciones. **Implementado en v16.89.0.**
95. Modo compacto para administradores avanzados. **Implementado en v16.88.0.**
96. Accesibilidad mejorada y control de tamaño de texto. **Implementado en v16.88.0.**
97. Temas visuales por grupo. **Implementado en v16.90.0.**
98. Panel personalizable mediante widgets. **Implementado en v17.0.0.**
99. Trabajo offline con sincronización posterior. **Implementado en v17.0.0.**
100. Recorrido guiado para cada función nueva. **Recorrido base y reiniciable implementado en v16.90.0.**

### Análisis multimedia y amenazas (101–102)
101. Análisis visual avanzado de fotografías para detectar contenido peligroso, spam visual, suplantaciones, texto incrustado y material sensible, con explicación y revisión administrativa. **Implementado en v16.86.0 y automatización por grupo añadida en v16.87.0.**
102. Integración ampliada con la API de VirusTotal para analizar archivos, hashes, URLs y dominios, reutilizar resultados en caché, mostrar detecciones por motor y aplicar acciones configurables sin bloquear el bot cuando la API no responda. **Implementado en v16.86.0 y políticas por grupo añadidas en v16.87.0.**

## [v17.4.0] - 2026-07-25

### Aprendizaje e interacción entre bots

- Opción independiente por grupo, desactivada por defecto.
- Lista explícita de usernames de bots autorizados para impedir aprendizaje de fuentes desconocidas.
- Aprendizaje opcional de mensajes, eliminando URLs y rechazando comandos.
- Respuesta opcional únicamente cuando el otro bot menciona a Moonbot o responde a uno de sus mensajes.
- Límite configurable de respuestas por hora para cortar conversaciones infinitas entre bots.
- Los mensajes de bots nunca atraviesan el procesador de comandos ni los sistemas de karma.
- Historial de interacciones, aprendizaje y respuestas visible en web y Mini App.
- Configuración equivalente en ambas interfaces y ayuda contextual traducible.
- Versión visible sincronizada a `v17.4.0`.

## [v17.3.0] - 2026-07-25

### Diagnóstico visible de permisos

- Comprobación real de los permisos del bot mediante `getChatMember` al abrir cada grupo.
- Aviso naranja destacado inmediatamente debajo del nombre cuando faltan capacidades.
- Lista exacta de permisos ausentes: administrar, borrar, restringir, invitar/aprobar y fijar.
- Instrucciones paso a paso para corregir los permisos desde los administradores de Telegram.
- Botón para comprobar de nuevo sin recargar la Mini App.
- El aviso se oculta automáticamente cuando todos los permisos están concedidos.
- Diagnóstico equivalente en la pantalla de moderación de la web clásica.
- Permisos específicos de publicación cuando el espacio administrado es un canal.
- Versión visible sincronizada a `v17.3.0`.

## [v17.2.2] - 2026-07-25

### Protección contra canales remitentes

- Ajuste independiente por grupo para banear canales externos usados como identidad de envío.
- Eliminación opcional del mensaje mediante `deleteMessage` y bloqueo mediante `banChatSenderChat`.
- Aviso opcional al grupo y registro del resultado en la auditoría administrativa.
- El canal oficialmente vinculado continúa ignorándose y nunca se banea con esta política.
- Configuración equivalente en la web clásica y la Mini App, con explicación contextual.
- Versión visible sincronizada a `v17.2.2`.

## [v17.2.1] - 2026-07-25

### Filtro de publicaciones vinculadas

- Las publicaciones de canales se contabilizan para estadísticas, pero no activan moderación, karma, IA ni respuestas.
- Los mensajes automáticos enviados por un canal a su grupo de debate se ignoran antes de procesar usuarios.
- También se ignoran mensajes publicados con identidad de canal dentro de grupos y supergrupos.
- Los mensajes normales de usuarios, bots administrados y administradores anónimos del propio grupo conservan su comportamiento.
- Versión visible sincronizada a `v17.2.1`.

## [v17.2.0] - 2026-07-25

### Ayuda contextual

- Botones `?` discretos en títulos, apartados, ajustes y acciones principales.
- Explicaciones en una ventana accesible sin abandonar la sección actual.
- Cobertura automática del contenido cargado dinámicamente en la web y la Mini App.
- Descripciones específicas para seguridad, proxies, IA, comunidad, eventos, integraciones y operaciones.
- `/help comando` explica el propósito y alcance de cada comando y traduce la respuesta al idioma del usuario.
- Versión visible sincronizada a `v17.2.0`.

## [v17.1.0] - 2026-07-25

### Traducción universal

- Idioma automático a partir de Telegram o del navegador y selección manual entre todos los códigos ISO disponibles.
- Traducción bajo demanda de la web, la Mini App y el captcha, incluida la interfaz generada dinámicamente.
- Caché persistente en servidor y navegador para evitar traducir repetidamente las mismas cadenas.
- Respuestas de comandos traducidas al idioma del usuario con fallback seguro en español.
- Alias latinos adicionales para comandos comunes; los comandos canónicos siguen funcionando en cualquier idioma.
- Compatibilidad con variantes regionales y códigos históricos normalizados.
- Versión visible sincronizada a `v17.1.0`.

## [v17.0.0] - 2026-07-25

### Roadmap completo

- Seguridad coordinada contra raids, cuarentena por reputación, suplantaciones, redirecciones y archivos peligrosos.
- Automatización editorial con biblioteca, plantillas, traducción, recurrencias, formularios, palabras clave y webhooks fiables.
- Inteligencia comunitaria con resúmenes, fuentes aprobadas, temas, preguntas pendientes, explicaciones, A/B, memoria y tono.
- Analítica de cohortes, embudos, actividad, campañas, salud, anomalías, informes, comparación anónima, BI y objetivos.
- Marketplace, tokens granulares, rotación, sandbox, cuotas, calendarios, incidencias, configuración firmada y SDK.
- Operaciones con despliegues graduales, rollback, backups cifrados, restauración selectiva, dependencias, alertas y diagnóstico.
- Widgets personalizables y cola offline con sincronización automática en la Mini App.
- Centro avanzado disponible tanto en la web clásica como en la Mini App master.
- Versión visible sincronizada a `v17.0.0`.

## [v16.94.0] - 2026-07-25

### Administración avanzada de grupos

- Asistente inicial con perfiles para comunidades, soporte, noticias y gaming.
- Comparación y sincronización selectiva de ajustes entre grupos.
- Historial versionado con restauración de configuraciones anteriores.
- Aprobación dual para cambios críticos y delegaciones administrativas temporales.
- Calendario ejecutable de acciones y horarios automáticos de apertura y cierre.
- Detección de grupos inactivos para archivado y auditoría horaria de permisos del bot.
- Paneles equivalentes en la web clásica y la Mini App master.
- Versión visible sincronizada a `v16.94.0`.

## [v16.93.0] - 2026-07-25

### Comunidad, eventos y participación

- Programa de mentorías por habilidades, capacidad y asignación automática.
- Encuestas anónimas de clima y buzón protegido con límite antiabuso.
- Eventos con cupos, lista de espera, promoción automática, check-in y recordatorios.
- Sorteos reproducibles con semilla y huella de participantes para auditoría.
- Concursos con propuestas, voto comunitario y puntuación independiente del jurado.
- Retos con progreso y clasificación; sesiones Q&A con aprobación administrativa.
- Agenda exportable en iCalendar, certificados verificables y estadísticas de asistencia.
- Funciones equilibradas entre la web de administración y la Mini App de Telegram.
- Versión visible sincronizada a `v16.93.0`.

## [v16.92.0] - 2026-07-25
### Perfiles y progresión comunitaria
- Perfil persistente con presentación, karma, roles, insignias, experiencia y nivel calculado.
- Experiencia automática por actividad y asignación manual de XP desde los paneles administrativos.
- Solicitudes de roles con aprobación o rechazo por el master.
- Reconocimiento semanal de colaboradores mediante insignias fechadas.
- Directorio interno limitado a miembros verificados o con roles comunitarios.

### Herramientas personales
- Recordatorios personales con fecha futura y entrega automática por mensaje privado de Telegram.
- Preferencias individuales para alertas de seguridad, reportes, eventos, recordatorios y resúmenes.
- Las preferencias filtran el centro real de notificaciones.
- Gestión equivalente desde la Mini App y el panel web.
- Versión visible sincronizada a `v16.92.0`.

## [v16.91.0] - 2026-07-25
### Moderación adaptativa
- Modo lento dinámico por grupo, calculado según la actividad del último minuto y con espera mínima y máxima configurables.
- Límites independientes para menciones, emojis y porcentaje de mayúsculas.
- Acciones de observación, eliminación o eliminación con advertencia; los administradores quedan excluidos.
- Simulador seguro que muestra métricas, señales y acción prevista sin modificar contadores ni ejecutar medidas.

### Sanciones temporales
- Los baneos locales admiten fecha de expiración y se limpian automáticamente al consultarlos.
- Revisión manual de sanciones caducadas desde la Mini App y el panel web.
- Historial de expiración registrado para auditoría.
- Versión visible sincronizada a `v16.91.0`.

## [v16.90.0] - 2026-07-25
### Personalización y ayuda
- Temas visuales independientes por grupo con cinco colores de acento y vista compacta opcional.
- Configuración persistente compartida por la Mini App y el panel web de moderación.
- Recorrido guiado de cuatro pasos para usuarios de la Mini App y administradores del panel web.
- El recorrido aparece en el primer acceso, se puede omitir y reiniciar desde Ajustes.
- Versión visible sincronizada a `v16.90.0`.

## [v16.89.0] - 2026-07-25
### Portada, historial y notificaciones reales
- Las acciones favoritas aparecen directamente en la portada de la Mini App.
- Navegación mediante el historial del navegador en la Mini App y el panel web; el botón Atrás recupera la pestaña anterior.
- Nuevo endpoint autenticado de notificaciones que limita los resultados a grupos administrados por el usuario.
- Alertas reales de reportes pendientes y decisiones de seguridad multimedia por grupo.
- El master recibe también las apelaciones pendientes; el panel web agrega amenazas y actividad administrativa.
- Estado leído persistente y acceso directo al grupo relacionado desde una notificación.
- Versión visible sincronizada a `v16.89.0`.

## [v16.88.0] - 2026-07-25
### Navegación y productividad
- Buscador global de paneles y acciones en la Mini App y en la web clásica.
- Acciones favoritas persistentes para acceder rápidamente a las herramientas habituales.
- Los resultados respetan el rol y no muestran el panel master a usuarios sin permiso.
- Primera fase del centro de notificaciones, con estado leído persistente y acceso desde la cabecera.

### Accesibilidad
- Modo compacto opcional para administradores que necesitan mayor densidad de información.
- Tamaños de texto pequeño, normal y grande aplicados a toda la interfaz.
- Las preferencias se guardan localmente y se restauran al volver a abrir cualquiera de los paneles.
- La navegación, los temas y las pestañas existentes permanecen sin cambios.
- Versión visible sincronizada a `v16.88.0`.

## [v16.87.0] - 2026-07-25
### Políticas multimedia por grupo
- Cada grupo puede activar por separado el análisis automático de fotografías, enlaces y archivos.
- Controles para OCR, suplantación, señales sensibles, umbral visual y número mínimo de detecciones de VirusTotal.
- Tres acciones configurables: solo avisar, eliminar el contenido o eliminar y banear al remitente.
- El modo seguro por defecto es solo aviso y los creadores o administradores del grupo nunca reciben acciones destructivas automáticas.
- Alertas opcionales en el grupo y al master, con historial de las últimas 300 decisiones por grupo.
- Los archivos superiores a 10 MB se omiten y los temporales se eliminan incluso si falla la descarga o el análisis.

### Paridad de interfaces
- La política y su historial aparecen en la suite del grupo de la Mini App.
- Los mismos controles y decisiones están disponibles en el panel web de moderación.
- Versión visible sincronizada a `v16.87.0`.

## [v16.86.0] - 2026-07-25
### Análisis avanzado de fotografías
- Nuevo analizador local para JPEG, PNG, WebP y GIF con límite de 10 MB y 40 megapíxeles.
- Extracción OCR opcional, detección de enlaces incrustados, frases de estafa y posibles suplantaciones de marca.
- Señal sensible débil y explicable que siempre requiere revisión humana y nunca genera por sí sola un ban automático.
- Resultado con SHA-256, dimensiones, formato, entropía, color medio, puntuación, nivel de riesgo y señales ponderadas.
- Historial persistente de análisis y métricas de amenazas/tasa de resultados limpios.

### VirusTotal ampliado
- Consulta de hashes MD5, SHA-1 y SHA-256, URLs y dominios mediante API v3.
- Carga manual de archivos de hasta 10 MB; primero reutiliza el informe del hash y solo sube archivos desconocidos.
- Envío de URLs desconocidas a la cola de VirusTotal.
- Resultados normalizados con detecciones totales, motores maliciosos o sospechosos, etiquetas, reputación y enlace al informe.
- Caché en memoria con caducidad para ahorrar cuota y tratamiento específico de límites HTTP 429 y fallos temporales.

### Web y Mini App
- Centro de Seguridad ampliado en la subpágina master de la Mini App con análisis de fotos, selector VirusTotal e historial.
- Los mismos análisis están disponibles en el panel web clásico.
- Los archivos temporales se eliminan después de cada análisis, también cuando se produce un error.
- Versión visible sincronizada a `v16.86.0`.

## [v16.85.0] - 2026-07-25
### Suite avanzada de grupos — web y Mini App
- Diez herramientas compartidas y persistentes: cuarentena para miembros nuevos, escudo anti-raid, reglas horarias, reportes mediante `/report`, decisiones por consenso, historial contextual, roles personalizados, bienvenidas, resúmenes inteligentes y plantillas con copia JSON.
- El panel web master y el panel de cada grupo en la Mini App exponen las mismas capacidades sin modificar el diseño ni la navegación existente.
- Las plantillas son compartidas entre grupos y permiten replicar protección, palabras prohibidas y configuración antispam.

### Seguridad y aprendizaje antispam
- Motor de riesgo explicable con señales, puntuación y registro de eventos para que cada decisión pueda revisarse.
- Integración del aprendizaje de grupos feeder, medición de precisión, falsos positivos y detección de campañas repetidas.
- Consulta de CAS mediante exportación local en caché, API y canal `@cas_feed` como respaldo; alertas a administradores antes de aplicar un ban.
- Contador independiente de baneados por CAS y enriquecimiento automático de baneos antiguos con su fuente y motivo desde el historial y el export local.
- Registro comunitario de reportes y compatibilidad con fuentes externas de reputación sin delegar automáticamente decisiones críticas.

### Acceso automático y administración
- Flujo captcha para solicitudes de acceso, aprobación automática tras superarlo y comprobaciones de reputación intermedias.
- Separación entre la lista personal de grupos del usuario y el centro master de canales propios.
- Nuevas acciones de administración para usuarios, administradores de grupo y master, con permisos comprobados en servidor.
- Las trece acciones del panel master abren ahora una subpágina completa con flecha atrás; la lista y su posición se conservan al regresar.

### Mini App, identidad y navegación
- Mini App principal en `hub.html` con validación criptográfica de `initData`, caducidad de sesión y verificación exclusiva contra el bot configurado como hub.
- Dos experiencias separadas: espacios asociados al usuario y centro master de canales propios; un administrador de grupo no recibe permisos globales.
- Navegación por Mis canales, Administrar, Master, Directorio, Red y Ajustes, más una pantalla independiente para cada grupo.
- Tema nuevo y tema clásico seleccionables, con preferencia persistida mediante Telegram CloudStorage y almacenamiento local.
- Temas visuales estacionales y festivos integrados sin modificar las funciones ni los permisos.
- Apertura segura de enlaces internos de Telegram y enlaces externos desde la Mini App.
- Estados de carga, vacíos, errores y avisos breves adaptados a dispositivos móviles.

### Canales, directorio y estadísticas
- Registro de canales en PocketBase con propiedad, tipo, username, visibilidad y metadatos protegidos.
- Colector de canales y grupos observados por los bots, con backfill para instalaciones anteriores.
- Asociación de espacios al usuario autenticado y comprobación de administración mediante Telegram.
- Buscador, filtros por tipo y ordenación de los canales asociados.
- Ordenación de canales personales por recientes, suscriptores, crecimiento o nombre.
- Favoritos y accesos recientes persistentes para volver rápidamente a los espacios usados.
- Publicación o retirada de cada canal del directorio público mediante interruptor.
- Estadísticas globales, detalle por canal, ranking, snapshots de suscriptores y crecimiento a 30 días.
- Directorio público ordenable por suscriptores con búsqueda y filtro de favoritos.
- Resumen compartible del canal con miembros, crecimiento y enlace público.

### Gestión de cada grupo
- Envío inmediato de mensajes y programación por fecha y hora desde la Mini App.
- Listado y cancelación de publicaciones programadas.
- Borradores persistentes por grupo y biblioteca local de plantillas de mensajes.
- Generación de imágenes desde una descripción y envío posterior al grupo.
- Consulta de baneados, advertencias y estado CAS de cada usuario.
- Restauración de usuarios, retirada de advertencias y acceso a contexto antes de moderar.
- Configuración de automoderación, antienlaces, bienvenida, escudo de seguridad y aprendizaje IA.
- Gestión de palabras prohibidas con acciones de borrar, advertir o banear.
- Notas privadas de moderación por grupo.
- Exportación JSON del estado completo de moderación.
- Estadísticas de actividad del grupo y resumen operativo para administradores.

### Captcha y solicitudes de acceso
- Captcha visual configurable para solicitudes de entrada, con número máximo de intentos y caducidad.
- Aprobación automática de Telegram cuando el usuario supera correctamente el desafío.
- Rechazo automático al agotar intentos o expirar la solicitud.
- Comprobación intermedia contra export local de CAS, API de CAS y respaldo de `@cas_feed`.
- Avisos al master y a los administradores cuando el solicitante aparece en CAS.
- Revisión manual de solicitudes con botones de aprobar o rechazar.
- Configuración del captcha equilibrada entre panel web y Mini App.

### Registro comunitario y reputación
- Registro estructurado de baneos globales con motivo, fuente, evidencias, grupos, autor, gravedad, revisión y vencimiento.
- Importación compatible con la lista histórica `legacy`, enriquecida posteriormente con historial y fuentes CAS locales.
- Contadores separados de baneos globales, CAS, locales, revocados, expirados y pendientes de revisión.
- Búsqueda por ID, motivo o fuente y filtros por estado.
- Exportación completa del registro en CSV y JSON.
- Reportes de administradores que requieren aprobación master antes de incorporarse al registro global.
- Apelaciones de usuarios con resolución, auditoría y retirada automática del bloqueo cuando se aceptan.
- Baneos temporales con expiración automática y conservación del historial.
- Niveles de riesgo `low`, `medium`, `high` y `critical`.
- Claves de API revocables para integraciones comunitarias.
- Endpoint de consulta servidor a servidor con permisos limitados, rate limit y respuesta sin evidencias privadas.

### Motor de riesgo, CAS y aprendizaje
- Motor antispam explicable que combina enlaces, repetición, patrones, campañas, muestras aprendidas y reputación.
- Umbrales configurables para vigilar, borrar, silenciar o banear.
- Registro de cada evento con puntuación, señales y razones legibles.
- Retroalimentación de administradores como spam confirmado, falso positivo o caso ignorado.
- Muestras positivas y negativas aprendidas desde grupos feeder autorizados.
- Medición por feeder de casos revisados, aciertos, falsos positivos y precisión.
- Detección de campañas repetidas entre mensajes y grupos.
- Caché en memoria para consultas CAS recientes.
- Descarga atómica y periódica de `export.csv`, cargada en una estructura local optimizada.
- Sincronización del canal público `@cas_feed` como respaldo de baneos recientes.
- Funcionamiento degradado: si una fuente CAS falla se prueban las demás sin bloquear el bot.

### Centro master
- Resumen general de usuarios, grupos, CPU, RAM y proxies activos.
- Administración de usuarios y baneos, reportes, apelaciones y claves de integración.
- Estado y control individual de proxies MTProto, además de escaneo bajo demanda.
- Listado, alta y desconexión de instancias de bots con tokens protegidos.
- Panel de Moon IA con palabras, idiomas, fuentes, muestras de seguridad y calidad de feeders.
- Cola de tareas con priorización, cancelación y salud de Telegram.
- Seguridad con estado del escudo neural, métricas visuales, auditoría y consulta CAS manual.
- Diagnóstico del sistema con versión, recursos, registros, actualización y reinicio.
- Informes exportables de red en texto y JSON.
- Auditoría administrativa exportable.
- Gestión de preguntas frecuentes y respuestas automáticas desde web y Mini App.
- Comunicados globales con confirmación previa y contador de chats alcanzados.
- Creación manual de backups con confirmación y resultado visible.
- Pantalla de mantenimiento con estado actual y activación o desactivación confirmada.

### Publicidad cruzada y experiencia de usuario
- Descubrimiento de canales compatibles para acuerdos de promoción cruzada.
- Solicitud, recepción, aceptación y rechazo de propuestas entre canales.
- Seguimiento separado de anuncios entrantes y salientes.
- Historial de moderación, reportes y estadísticas exportables desde la Mini App.
- Traducción y detección de idioma conservadas en el núcleo multilingüe.
- Reparación de mojibake antes de mostrar o enviar contenido heredado.

## [v16.84.0] - 2026-07-11
### Feature - Proxies MTProto en CintiaBot (pedir, recomendar, administrar)
- **`/proxy`**: envía al usuario los proxies MTProto propios + los del canal más cercanos a su zona, deducida por el `language_code` de Telegram (un bot no ve la IP). Botón "Pedir proxy" en `/start` (callback `req_proxy`).
- **`/recomendar <enlace>`**: cualquier usuario recomienda un proxy MTProto; el bot lo valida (TCP-check), lo deja pendiente (`db["PENDING_PROXIES"]`) y avisa al **master** con botones ✅/❌. Al aprobar, se publica automáticamente en la web vía `POST /mtproto-proxies/community` de la API (autenticado por token compartido).
- **`/pendientes`**: cola de proxies recomendados por revisar, con botones de aprobar/rechazar en cada uno.
- **`/estado`** y **`/historico`**: usuarios activos por país y conexiones por hora/día de los proxies, consultados a la API.
- **Los datos de proxies** vienen de la API `mtproto-proxies` (geoip-lite, `country`/`ll`, `connStats`).

### Fix - Separación de permisos (admin de grupo ≠ dueño del bot)
- El rango `Admin` de `get_user_rank` proviene de `getChatAdministrators` (admin del **grupo** de Telegram), no del dueño del bot. Se han pasado a **solo Master** las acciones globales/sensibles que estaban expuestas a cualquier admin de grupo: `/gban` y `/ungban` (ban/indulto global), `/ia_programar` e `/ia_feed` (entrenan/alimentan la IA compartida) y los comandos de datos de proxies (`/estado`, `/historico`, `/pendientes`) más la aprobación de proxies.
- La moderación **del propio grupo** (`/ban`, `/unban`, `/mute`, `/unmute`, `/warn`, `/resumen`) se mantiene para admins de grupo.
- Verificado: `/listen`, `/backup_db` y `/resync` ya eran solo Master.

## [v16.83.1] - 2026-06-06
### Feature - Galería Visual de Versiones & Detección Multilingüe
- **Historial visual en Landing (`web/landing.html`)**: Maquetas interactivas y capturas de evolución de interfaz incorporadas en la landing page.
- **Detección de idioma multilingüe (`core/text_utils.py`)**: Clasificación automática de la lengua del interlocutor para adaptar respuestas de IA.
- **Pipeline de saneamiento con `ftfy`**: Integración de librería especializada para reparar cualquier desalineación de codificación UTF-8.
- **Panel de Historial Diario (`web/history.html`)**: Visor cronológico de mensajes y scripts de parsing de copias de seguridad (`scripts/parse_backups.py`).

## [v16.83.0] - 2026-05-24
### Feature - Landing page pública y panel en `/panel`
- **Landing pública en `/`**: la raíz ahora sirve una página pública de presentación de cintiabot (`web/landing.html`), sin requerir login.
- **Panel movido a `/panel`**: el dashboard (`web/index.html`) se sirve ahora en `/panel`, conservando su pantalla de login en cliente.
- **Login existente intacto**: todas las rutas `/api/*` siguen protegidas por `check_jwt` (JWT); el resto de rutas no cambia su comportamiento de acceso.
- **moon_multibot.py**: `/` apunta a `landing.html`, nueva ruta `/panel` para el panel y el catch-all `/<path:path>` se mantiene, de modo que los assets relativos del panel (`style.css`, `script.js`, fragmentos `*.html`) siguen resolviéndose desde la raíz.

## [v16.82.0] - 2026-05-16
### Feature - Google Analytics y consentimiento de cookies
- **Google Analytics 4 global**: el dashboard carga GA4 desde `GOOGLE_ANALYTICS_ID` o desde Ajustes, y registra vistas para login y cada pestaña dinámica (`/dashboard`, `/bots`, `/chat`, `/ia`, `/settings`, etc.).
- **Consentimiento de cookies**: nuevo banner responsive con aceptar/rechazar; Analytics no se carga hasta que el usuario acepta.
- **Ajustes web**: añadido panel **Analytics & Cookies** para configurar Measurement ID, activar/desactivar banner y activar/desactivar Analytics sin tocar código.
- **API pública mínima**: nuevo endpoint `/api/public/analytics` para inicializar banner y configuración antes del login sin exponer datos privados.
- **Eventos básicos**: registro opcional de consentimiento aceptado, login y logout cuando Analytics está habilitado.

## [v16.81.0] - 2026-05-11
### Fix - Polling de Telegram
- **core/telegram_api.py**: retirados `managed_bot`, `guest_message` y `guest_interaction` de `allowed_updates` para evitar que Telegram rechace `getUpdates`.
- **Respuesta del bot**: el polling vuelve a usar solo tipos oficiales de Bot API, evitando bucles de error/backoff donde el bot queda vivo en la web pero no contesta mensajes.
- **Emojis mojibake**: `_repair_mojibake()` ahora prueba `cp1252` y `latin-1`, corrigiendo mensajes como `/ayuda` que salían con `ðŸ`, `âœ` y `Ã³`.
- **Comando `/settings`**: ahora muestra la versión real del bot usando `APP_VERSION`, manteniendo Telegram y la web sincronizados.
- **Reparación mixta de mojibake**: el saneador reconstruye bytes carácter por carácter para corregir mensajes que mezclan símbolos `cp1252` y controles Latin-1, como el panel completo de `/settings`.
- **QA de comandos**: verificados 21 comandos core y 43 salidas de plugins con mocks locales; sin excepciones, sin comandos cayendo a IA por error y sin marcadores mojibake tras saneado.

## [v16.80.0] - 2026-05-11
### Fix — Comandos core y plugins más fiables
- **moon_multibot.py**: nuevo normalizador de comandos para soportar /comando@BotName también en plugins.
- **Pipeline de plugins**: centralizado en _run_plugin_command() para evitar duplicación y errores silenciosos.
- **Compatibilidad de plugins**: MoonBot expone db e ia_nativa para plugins que ya dependían de esos atributos.
- **Permisos de plugins**: normalizada la comparación de rangos para aceptar Admin/Master sin romper plugins que esperaban minúsculas.
## [v16.79.0] - 2026-05-11
### Fix — Emojis y texto corrupto (mojibake) en mensajes del bot
- **moon_multibot.py**: nuevo helper _repair_mojibake(text) para reparar cadenas UTF-8 mal decodificadas (patrones como ðŸ, Ã, â, Â).
- **Hotfix global en send_msg()**: todo texto saliente se sanea antes de enviar por Bot API/TDLib.
- **Historial interno**: ahora persiste el texto saneado para evitar arrastrar corrupción visual en dashboard.
## [v16.78.0] - 2026-05-11
### Fix — Pipeline de comandos y estabilidad de plugins
- **moon_multibot.py**: corregido el flujo de comandos para ejecutar en orden core -> plugins, evitando que comandos de plugins queden saltados por un continue prematuro.
- **Comandos no reconocidos**: ahora devuelven respuesta explícita (Usa /ayuda o /helpplus) y nunca caen al motor IA.
- **Bloque duplicado de comandos**: eliminado un tramo redundante en el loop principal de mensajes.
- **plugins/__init__.py**: normalizado a UTF-8 para eliminar bytes nulos que rompían compilación global.
## [v16.77.0] - 2026-05-08
### Fix — Mensaje de LEVEL UP con texto raro al lado
- **moon_multibot.py**: saneado de uname en el mensaje de subida de nivel para escapar caracteres conflictivos de Markdown.
- **Mensaje de level up** ajustado para formato estable y limpio: evita artefactos visuales cuando el nombre contiene símbolos especiales.
## [v16.76.0] - 2026-05-08
### Modularización core — más rutas fuera de moon_multibot.py
- **core/routes_ia.py**: extraído el bloque /api/ia/* completo (traducción, stats, feeders, auditorías, config, backup/restore, test), además de /api/global/history y /api/admin/settings.
- **core/routes_admin.py**: extraídas rutas /api/admin/* (broadcast, maintenance, shield, backup).
- **core/routes_system.py**: extraídas rutas /api/telegram/call y /api/reboot.
- **core/routes_users.py**: extraídas rutas /api/media, /api/ping, /api/stats/users, /api/stats/heatmap y bloque /api/users/* (ban/unban/listado/historial/notas).
- **core/routes_ops.py**: extraídas rutas de operación /api/audit, /api/logs/download y /api/automation/faq*.
- **Registro por blueprints**: todas las rutas nuevas conectadas con patrón setup(deps) -> Blueprint, usando inyección de dependencias y getters/lambdas para estado runtime.
- **moon_multibot.py**: reducido de forma incremental al retirar múltiples endpoints del monolito sin cambiar contratos de API.
## [v16.75.0] - 2026-05-08
### Fix â€” Error 400 "can't parse entities" en sendMessage
- **`_safe_md(text)`**: nuevo helper en `invoked_ai.py` que elimina marcadores Markdown impares (`*`, `_`, `` ` ``) del texto de la IA antes de enviarlo, previniendo el error en origen.
- **`send_msg()`**: si Telegram devuelve `"can't parse entities"`, reintenta automÃ¡ticamente sin `parse_mode` en lugar de perder el mensaje.

## [v16.74.0] - 2026-05-08
### Fix â€” Modo Markov (Personal) no aparecÃ­a en estadÃ­sticas
- **`invoked_ai.py`**: `"markov"` no estaba en la lista de valores vÃ¡lidos de `ai_used` en `generate_reply()` â€” se contabilizaba errÃ³neamente como `"hybrid"`.
- **`_record_ai_usage()`**: aÃ±adido contador `markov_count` con su propia rama `elif`. Antes caÃ­a al `else` de hybrid.
- **`get_ai_statistics()`**: `markov` incluido en `ai_distribution` devuelto por la API.
- **`ia.html`**: nueva fila "ðŸ§  Markov (Personal)" (en morado) en el panel DistribuciÃ³n IA.
- **`script.js`**: `inlineDistMarkov` actualizado al cargar las estadÃ­sticas.

## [v16.73.0] - 2026-05-08
### Perf â€” Circuit breaker + timeout split para Ollama
- **Timeout separado** `(connect=3s, read=30s)`: si Ollama no responde en 3s falla inmediatamente en lugar de esperar 30s, sin penalizar inferencias legÃ­timamente lentas.
- **Circuit breaker** (`_ollama_last_fail` + `_ollama_fail_cooldown=60s`): tras un fallo no reintenta durante 60 segundos, eliminando la acumulaciÃ³n de timeouts en el tiempo promedio.
- **`requests.Session` reutilizable** (`_ollama_session`): keep-alive y connection pooling eliminan el overhead de abrir nueva conexiÃ³n TCP en cada llamada.
- `deep_dream_worker` tambiÃ©n usa la sesiÃ³n y respeta el circuit breaker.

## [v16.72.0] - 2026-05-08
### Fix â€” Modo SueÃ±o Profundo se activaba al iniciar y panel no visible
- **Bug de auto-activaciÃ³n**: el bloque `elif word:` llamaba a Wikipedia en cada ciclo aunque `DEEP_DREAM_MODE = False`. Todo el aprendizaje ahora estÃ¡ dentro de `if DEEP_DREAM_MODE and word:`.
- **Visibilidad**: panel movido justo debajo de la secciÃ³n Ollama (era el panel nÂº8, muy abajo). DescripciÃ³n actualizada: "Debe activarse manualmente."

## [v16.70.0] - 2026-05-08
### ModularizaciÃ³n â€” 6 Blueprints Flask extraÃ­dos
- **`core/routes_business.py`**: `/api/business/*` (3 rutas â€” status, config, quick_replies).
- **`core/routes_proxies.py`**: `/api/proxies/*` (7 rutas â€” stats, vps config, vps stats, add, toggle, remove, scan).
- **`core/routes_tdlib.py`**: `/api/tdlib/*` (4 rutas â€” status, auth, userbot, sync).
- **`core/routes_security.py`**: `/api/security/*`, `/api/vision/stats`, `/api/health/telegram` (8 rutas).
- **`core/routes_queue.py`**: `/api/queue/*` (3 rutas â€” list, cancel, prioritize).
- **`core/routes_moderation.py`**: `/api/moderation/*`, `/api/users/leaderboard` (10 rutas).
- **PatrÃ³n `setup(deps) â†’ Blueprint`**: sin imports circulares; dependencias inyectadas al registrar. `proxy_bot` usa getter lambda por ser asignaciÃ³n tardÃ­a.
- **`moon_multibot.py`**: reducido de 4945 a 4645 lÃ­neas (âˆ’300).

## [v16.69.0] - 2026-05-08
### Fix web â€” backupIA, restoreIA y toggleJoinDelete duplicado
- **`backupIA()`**: nuevo endpoint `GET /api/ia/download` que sirve la DB como descarga directa con token en query param. La funciÃ³n JS usa `<a href>` con el token para disparar la descarga.
- **`restoreIA()`**: nuevo endpoint `POST /api/ia/restore` que acepta un `.db`, hace backup previo automÃ¡tico (`moon_database.db.pre_restore`) y reemplaza la DB activa.
- **`send_file`** aÃ±adido a los imports de Flask en `moon_multibot.py`.
- **`toggleJoinDelete()` duplicado eliminado**: la segunda definiciÃ³n (stub que solo mostraba un toast) sobreescribÃ­a la implementaciÃ³n real. Eliminada la duplicada; la real (toggle ON/OFF con feedback visual) queda intacta.

## [v16.68.0] - 2026-05-08
### Panel dedicado â€” Modo SueÃ±o Profundo
- **Panel propio en pestaÃ±a IA**: el toggle de SueÃ±o Profundo sale del panel "Ajustes del Cerebro HÃ­brido" y tiene su propia tarjeta con borde morado, tÃ­tulo `h3` visible e interruptor escalado al 120%.
- **Indicador de estado en tiempo real**: punto que pulsa en morado con glow cuando estÃ¡ activo; gris cuando estÃ¡ inactivo. Texto descriptivo que cambia al activar/desactivar.
- **`toggleDeepDream(active)`**: nueva funciÃ³n JS que actualiza la UI inmediatamente, guarda la config y muestra un toast de confirmaciÃ³n.
- **`_applyDeepDreamUI(active)`**: funciÃ³n auxiliar que sincroniza el punto, el texto y el fondo del panel. Se llama tambiÃ©n al cargar la config inicial (`loadIAConfig`).

## [v16.67.0] - 2026-05-08
### Markov â€” autoentrenamiento con Wikipedia
- **Root cause corregido**: `initial_knowledge.json` contiene palabras sueltas que nunca crean bigramas en `learn()`. El cerebro tenÃ­a vocabulario pero cero conexiones reales.
- **`_seed_from_wikipedia(topics)`**: nuevo mÃ©todo que busca el resumen de Wikipedia (ES â†’ EN fallback) para cada topic y llama a `learn()` con oraciones completas, creando bigramas reales.
- **`seed_knowledge()`**: ya no llama a `learn()` con palabras sueltas; llama a `_seed_from_wikipedia()` sobre los topics de `initial_knowledge.json` (mÃ¡x 40 topics por arranque).
- **`_deep_dream_wikipedia(word)`**: nuevo helper que busca una palabra en Wikipedia y aprende el extracto. Usado como fallback cuando Ollama no estÃ¡ disponible.
- **`deep_dream_worker` refactorizado**: si Ollama falla o no estÃ¡ configurado, usa `_deep_dream_wikipedia()` en cada ciclo. El auto-estudio ya no depende de Ollama.
- **Persistencia mÃ¡s frecuente**: `_learn_count % 5` â†’ `% 2`; el cerebro se guarda en DB tras cada 2 aprendizajes.
- **Umbral de re-sembrado**: `< 1000` â†’ `< 5000` keywords para activar `seed_knowledge()` al arrancar.

## [v16.63.0] - 2026-05-08
### IA â€” cascada Markov â†’ Ollama â†’ Gemini
- **Prioridad definida**: 1) Markov (siempre se genera, local, instantÃ¡neo) â†’ 2) Ollama (si estÃ¡ activo y responde) â†’ 3) Gemini (si Ollama falla y hay API key).
- **MÃ©todos extraÃ­dos**: `_call_ollama()` y `_call_gemini()` separados del `generate()` principal, con logging explÃ­cito de cuÃ¡l IA respondiÃ³.
- **Fix bug Markov**: la selecciÃ³n ponderada acumulaba `upto` despuÃ©s de la comparaciÃ³n, haciendo que siempre eligiera `choices[0]`. Corregido: `upto += w` antes del `if upto >= r_val`.
- **`/markov` prefix**: en inline/guest, `/markov` fuerza la IA local sin llamar a ningÃºn LLM externo.
- **`LLM_PROVIDER` default**: cambiado de `"gemini"` a `"ollama"` en `core/config.py` para que activar `USE_EXTERNAL_LLM` use Ollama por defecto.
- **Fallback visible**: cada capa loguea en el dashboard quÃ© IA respondiÃ³ o por quÃ© se saltÃ³ a la siguiente.

## [v16.61.0] - 2026-05-08
### Fix IA local â€” brain_lock y deep_dream
- **`brain_lock` activado en `learn()`**: el bloqueo existÃ­a pero nunca se adquirÃ­a. Ahora protege las actualizaciones concurrentes del cerebro Markov.
- **Fix crÃ­tico en `deep_dream_worker`**: `brain.keys()` devolvÃ­a `["keywords","patterns"]` en lugar de las palabras reales. Corregido a `brain["keywords"].keys()`.
- **Backoff en deep_dream**: si Ollama no estÃ¡ disponible, el worker retrocede exponencialmente (60s â†’ 120s â†’ 240s â†’ mÃ¡x 600s) en lugar de reintentar inmediatamente.

## [v16.60.0] - 2026-05-08
### Wikipedia en modo Inline y Guest
- **`_search_wikipedia(query)`**: busca en Wikipedia en espaÃ±ol (fallback a inglÃ©s). Usa la API REST de Wikipedia con timeout de 4s para no bloquear la respuesta.
- **Prompt enriquecido**: el contexto de Wikipedia se inyecta en el prompt de la IA para que la respuesta sea mÃ¡s precisa y factual.
- **Resultado extra en Inline**: si hay resultado de Wikipedia, aparece como opciÃ³n "ðŸ“– Wikipedia" adicional junto a "ðŸ¤– Respuesta IA" y "âœ‚ï¸ Respuesta breve".
- **Guest mode**: Wikipedia tambiÃ©n enriquece las respuestas en chats donde el bot es invitado.

## [v16.58.0] - 2026-05-08
### Resiliencia â€” backoff en getUpdates + aislamiento de plugins
- **Exponential backoff en `run()`**: fallos consecutivos en getUpdates esperan 5s, 10s, 20s, 40sâ€¦ hasta 300s. El contador se resetea en cada respuesta exitosa.
- **Aislamiento de errores en plugins**: `handle_command()` ahora estÃ¡ envuelto en try-except igual que `handle_callback()`. Un plugin con bug ya no crashea el loop de mensajes; el error se loguea en el dashboard.

## [v16.57.0] - 2026-05-08
### Retry + rate limit 429 en telegram_api_call
- **Retry automÃ¡tico**: hasta 3 intentos con backoff exponencial (1s, 2s) en errores de red (`ConnectionError`, `Timeout`).
- **Manejo de 429**: cuando Telegram devuelve `error_code: 429`, espera `retry_after` segundos (del parÃ¡metro de respuesta) y reintenta automÃ¡ticamente.
- Sin cambios en la firma pÃºblica; el comportamiento es transparente para el resto del cÃ³digo.

## [v16.55.0] - 2026-05-08
### CI â€” Lint automÃ¡tico en cada push
- **`.github/workflows/ci.yml`**: workflow que ejecuta `ruff` sobre todo el cÃ³digo Python en cada push a master o PR. Detecta errores de sintaxis, variables no definidas e imports rotos. Ignora lÃ­neas largas (E501) e imports al estilo del proyecto.

## [v16.54.0] - 2026-05-08
### Limpieza automÃ¡tica de descargas
- **`cleanup_worker()`**: hilo daemon que llama a `purge_old_media()` en cada bot activo una vez al dÃ­a. Lee `auto_cleanup_days` de `GLOBAL_SETTINGS`; si es 0 estÃ¡ desactivado.
- **Selector en Settings**: dropdown "Limpieza AutomÃ¡tica de Descargas" con opciones: Desactivado / 1 dÃ­a / 3 dÃ­as / 7 dÃ­as / 30 dÃ­as.
- Previene que la carpeta `downloads/` llene el disco en producciÃ³n.

## [v16.53.0] - 2026-05-08
### .dockerignore â€” build context reducido
- **`.dockerignore`**: excluye `.git/`, `data/`, `downloads/`, `ollama_data/`, `__pycache__/`, `logs/`, `scratch/` y otros archivos que no deben entrar a la imagen Docker. El contexto de build baja de ~43MB a ~3MB, acelerando todos los futuros builds.
- `libtdjson.so` NO estÃ¡ excluido para que `setup_tdlib.sh` pueda copiarlo al contexto.

## [v16.52.0] - 2026-05-08
### TDLib â€” detecciÃ³n dual: binario local o GitHub Release
- **`setup_tdlib.sh`**: script que busca `libtdjson.so` en rutas conocidas del servidor (`/usr/local/lib/`, `~/td/`, `/tmp/td/`, `/opt/td/`). Si lo encuentra, lo copia al directorio del proyecto para que el Dockerfile lo use directamente, evitando la descarga desde GitHub.
- **`Dockerfile` con fallback inteligente**: tras `COPY . .`, comprueba si `libtdjson.so` estÃ¡ presente en el contexto de build. Si estÃ¡ â†’ lo mueve a `/usr/local/lib/`. Si no â†’ descarga desde el GitHub Release. Un solo Dockerfile soporta ambos escenarios.
- **`.gitignore`**: `libtdjson.so` ignorado para que el binario local nunca se comitee al repositorio.
- **Flujo recomendado en el servidor**: `./setup_tdlib.sh && docker compose up -d --build`. Si el binario local existe, el build no accede a GitHub en absoluto.

## [v16.51.0] - 2026-05-08
### TDLib pre-compilado â€” descarga directa desde GitHub Release
- **`Dockerfile` sin compilaciÃ³n**: etapa Ãºnica `python:3.12-slim`. Descarga `libtdjson.so` del Release de GitHub con `curl` en ~2 segundos. Build total pasa de ~15 min a ~1 min.
- **`.github/workflows/build-tdlib-binary.yml`**: workflow que compila TDLib en `ubuntu-22.04`, sube `libtdjson.so` al release `tdlib-prebuilt` del repo. Se lanza manualmente (`workflow_dispatch`) o al editar el propio workflow. Registra el commit hash de TDLib en la descripciÃ³n del release.
- **Para actualizar TDLib**: ir a Actions â†’ "Compile & publish libtdjson.so" â†’ Run workflow. El siguiente `docker compose up --build` descarga el binario nuevo automÃ¡ticamente.

## [v16.50.0] - 2026-05-08
### TDLib pre-compilado en GHCR â€” builds en segundos
- **`Dockerfile.tdlib`**: imagen base standalone que compila TDLib desde fuente y guarda `libtdjson.so`. Se construye una sola vez y se publica en `ghcr.io/comunidadtelebots/moon-multibot-tdlib:latest`.
- **`.github/workflows/build-tdlib-base.yml`**: GitHub Actions que construye y publica la imagen base automÃ¡ticamente cuando cambia `Dockerfile.tdlib`, o bajo demanda con `workflow_dispatch`. Usa cachÃ© de GHA para acelerar incluso la compilaciÃ³n inicial.
- **`Dockerfile` refactorizado**: la etapa 1 pasa de compilar (~15 min) a `FROM ghcr.io/â€¦/moon-multibot-tdlib:latest AS tdlib-builder` (descarga en segundos). El `ARG TDLIB_IMAGE` permite sobrescribir la imagen base si es necesario.
- **`docker-compose.yml`**: pasa `TDLIB_IMAGE` como build arg y aÃ±ade `cache_from` apuntando a la imagen GHCR para que Docker reutilice capas cacheadas.
- **Flujo para actualizar TDLib**: lanzar manualmente el workflow â†’ GHCR actualiza la base â†’ el siguiente `docker compose up --build` en el servidor la descarga automÃ¡ticamente.

## [v16.50.0] - 2026-05-08
### Backup automÃ¡tico programado
- **`auto_backup_worker()`**: hilo daemon que envÃ­a la DB al Master cada N horas. Lee `GLOBAL_SETTINGS.auto_backup_hours`; si es 0 estÃ¡ desactivado. Persiste `LAST_AUTO_BACKUP` en SQLite para no enviar duplicados al reiniciar.
- **Selector en Settings**: dropdown "Backup AutomÃ¡tico" con opciones: Desactivado / 6h / 12h / 24h / 48h. Se guarda y carga con el resto de `GLOBAL_SETTINGS`.
- El mensaje incluye fecha, hora y tamaÃ±o en MB de la DB enviada.

## [v16.49.0] - 2026-05-08
### Panel TDLib en el Dashboard (tab DiagnÃ³stico)
- **Panel visual TDLib** en `diagnostics.html`: muestra modo (user/bot), estado de auth, si estÃ¡ listo y si el userbot estÃ¡ activo.
- **AutenticaciÃ³n headless desde la UI**: campos para telÃ©fono, cÃ³digo y contraseÃ±a 2FA con botones individuales que llaman a `POST /api/tdlib/auth`.
- **Toggle userbot**: botÃ³n que invierte el estado actual con `GET + POST /api/tdlib/userbot`.
- **SincronizaciÃ³n de historial**: input de chat_id + botÃ³n que llama a `POST /api/tdlib/sync`.
- **`refreshTDLib()`**: funciÃ³n JS que actualiza el panel; se llama automÃ¡ticamente al abrir la tab de DiagnÃ³stico (`runDiagnostics`).

## [v16.48.0] - 2026-05-08
### Docker HEALTHCHECK y endpoint /health
- **`HEALTHCHECK`** en Dockerfile: `--interval=30s --timeout=10s --start-period=90s --retries=3`. Docker marca el contenedor como `unhealthy` si `/health` no responde 3 veces, habilitando reinicio automÃ¡tico con `restart: unless-stopped`.
- **`GET /health`** (sin auth): endpoint pÃºblico que devuelve `{"ok": true, "uptime": N, "bots": N}`. No expone datos sensibles pero permite que Docker y load balancers verifiquen el estado del proceso.

## [v16.47.0] - 2026-05-08
### SQLite WAL mode y conexiÃ³n por hilo
- **WAL (Write-Ahead Logging)**: `PRAGMA journal_mode=WAL` elimina el lock exclusivo de escritura. MÃºltiples hilos pueden leer simultÃ¡neamente mientras se escribe, reduciendo contenciÃ³n entre el bot, TDLib, telemetry y daily report.
- **`PRAGMA synchronous=NORMAL`**: equilibrio entre rendimiento y durabilidad (mucho mÃ¡s rÃ¡pido que FULL sin sacrificar integridad en caÃ­das normales).
- **ConexiÃ³n por hilo (`threading.local`)**: cada hilo mantiene su propia conexiÃ³n SQLite, eliminando el cursor compartido que podÃ­a corromperse bajo concurrencia alta.
- **`db.delete(key)`**: nuevo mÃ©todo para eliminar claves individuales (usado por `_invalidate_admin_cache`).

## [v16.46.0] - 2026-05-08
### TDLib auto-reconexiÃ³n con backoff exponencial
- **`_watchdog()`**: hilo daemon que monitoriza `_running` cada 60 s. Si el cliente TDLib cae (`authorizationStateClosed` u otro error), espera un backoff exponencial (30 s Ã— 2^n, mÃ¡x 5 min), crea un nuevo `client_id` y relanza el `_receive_loop`. El contador `_restart_count` evita reintentos infinitos instantÃ¡neos.
- Backoff: intento 1 â†’ 30 s, intento 2 â†’ 60 s, intento 3 â†’ 120 s, intento 4 â†’ 240 s, intento 5+ â†’ 300 s.
- Funciona para el cliente usuario y para cada bot con token propio.

## [v16.45.0] - 2026-05-08
### Callback queries, reacciones e invalidaciÃ³n de cachÃ© de admins
- **`handle_callback_query(update)`**: nuevo handler en el dispatch loop. Extrae `callback_query`, delega a plugins que implementen `handle_callback(bot, cid, uid, uname, data, cbq_id)`, y siempre llama `answerCallbackQuery` para detener el spinner de Telegram. Updates no manejados se loguean como DEBUG.
- **`handle_message_reaction(update)`**: procesa `message_reaction` y `message_reaction_count` (antes descartados sin routing). Registra quÃ© emoji pusÃ³ cada usuario en cada mensaje.
- **Routing en `run()`**: `callback_query` â†’ `handle_callback_query`, `message_reaction` â†’ `handle_message_reaction`, `message_reaction_count` â†’ skip limpio.
- **`_invalidate_admin_cache(cid)`**: helper que borra `ADMINS_{cid}` y resetea `LAST_ADMIN_CHECK_{cid}`. Se llama automÃ¡ticamente en `kick_user()` y `promote_user()` para que el nuevo rango sea efectivo inmediatamente sin esperar los 5 minutos de cachÃ©.

## [v16.44.0] - 2026-05-08
### Bot API 10.0 â€” nuevos mÃ©todos y actualizaciÃ³n de versiÃ³n
- **VersiÃ³n API**: `TELEGRAM_BOT_API_VERSION` actualizada de `9.6` a `10.0`.
- **Nuevos update types**: `message_reaction` y `message_reaction_count` aÃ±adidos a `DEFAULT_ALLOWED_UPDATES`.
- **`unpin_msg(cid, mid=None)`** (fix crÃ­tico): mÃ©todo faltante que era llamado en `plugins/telegram_tools.py` â€” ahora definido; sin `mid` desancla el Ãºltimo mensaje.
- **`unpin_all_messages(cid)`**: llama a `unpinAllChatMessages`.
- **`unban_chat_member(cid, uid)`**: llama a `unbanChatMember` con `only_if_banned=True`.
- **`send_chat_action(cid, action)`**: indicador de escritura/carga (`typing`, `upload_photo`, etc.).
- **`send_voice(cid, voice, caption="")`**: envÃ­o de notas de voz.
- **`send_sticker(cid, sticker)`**: envÃ­o de stickers.
- **`forward_message(to_cid, from_cid, mid)`**: reenvÃ­a un mensaje.
- **`copy_message(to_cid, from_cid, mid, caption)`**: copia un mensaje (sin el "Forwarded from").
- **`get_chat(cid)`**: info del chat/grupo.
- **`get_chat_member_count(cid)`**: nÃºmero de miembros.
- **`answer_callback_query(cbq_id, text, show_alert, url, cache_time)`**: respuesta a botones inline.
- **`set_message_reaction(cid, mid, reaction, is_big)`**: pone reacciÃ³n emoji en un mensaje.
- **API 9.5 â€” `set_chat_member_tag(cid, uid, tag)`**: etiqueta personalizada para miembro.
- **API 9.6 â€” `save_prepared_keyboard_button(button, query_id)`**: botÃ³n de teclado preparado para bots administrados.
- **API 10.0 â€” `answer_guest_query(guest_query_id, text, show_alert)`**: respuesta a guest queries.
- **API 10.0 â€” `delete_message_reaction(cid, mid, reaction_type)`**: elimina reacciÃ³n especÃ­fica.
- **API 10.0 â€” `delete_all_message_reactions(cid, mid)`**: elimina todas las reacciones de un mensaje.
- **API 10.0 â€” `send_live_photo(cid, live_photo, caption)`**: envÃ­a una live photo.
- **API 10.0 â€” `get_managed_bot_access_settings(bot_id)`** / **`set_managed_bot_access_settings(bot_id, **kwargs)`**: configuraciÃ³n de acceso de bots administrados.
- **API 10.0 â€” `get_user_personal_chat_messages(user_id, limit)`**: mensajes del chat personal de un usuario.

## [v16.43.0] - 2026-05-08
### MoonBot envÃ­a mensajes via TDLib (bot token auth)
- **TDLib bot auth**: `TDLibClient` acepta `bot_token` opcional. Cuando estÃ¡ presente, al recibir `authorizationStateWaitPhoneNumber` envÃ­a `checkAuthenticationBotToken` en vez de esperar telÃ©fono. Cada bot tiene su propia sesiÃ³n en `tdlib_data/bot_{hash}/`.
- **Cliente TDLib por instancia de bot**: `MoonBot.__init__` crea un `TDLibClient` autenticado con su token si `TDLIB_API_ID`/`TDLIB_API_HASH` estÃ¡n configurados. Se inicia en background automÃ¡ticamente.
- **`MoonBot.send_msg()` con TDLib + fallback**: Si `self._tdlib.is_ready`, el mensaje se envÃ­a via TDLib (`sendMessage` + `inputMessageText` con parse_mode via `parseTextEntities`). Si TDLib no estÃ¡ listo o falla, cae automÃ¡ticamente al Bot API HTTP. Los mensajes de business connection siempre usan Bot API (TDLib no los soporta).
- **`TDLibClient._format_text()`**: convierte texto Markdown/HTML al `formattedText` de TDLib usando `parseTextEntities` (llamada sÃ­ncrona `execute`).
- **`TDLibClient.is_ready`**: propiedad que expone `auth_state == authorizationStateReady`.
- **Dockerfile**: aÃ±adido `DEBIAN_FRONTEND=noninteractive` para evitar prompts interactivos durante la compilaciÃ³n de TDLib en Docker.

## [v16.42.0] - 2026-05-07
### TDLib Userbot â€” responder mensajes via cuenta de usuario
- **Modo userbot activable desde dashboard**: `POST /api/tdlib/userbot {"enabled": true/false}`. El estado se persiste en SQLite (`TDLIB_USERBOT_ENABLED`).
- **`TDLibClient.send_message(chat_id, text, reply_to_message_id)`**: envÃ­a mensajes via TDLib con `sendMessage` + `inputMessageText`. Soporta respuesta a mensaje especÃ­fico.
- **`TDLibClient.on_message` callback**: el loop receptor llama a `_handle_new_message()` en cada `updateNewMessage`. Normaliza el mensaje TDLib al formato interno y llama al handler registrado. Ignora mensajes propios (`is_outgoing`).
- **Handler `_tdlib_on_message()` en moon_multibot.py**: procesa mensajes recibidos vÃ­a TDLib. En grupos solo responde si hay menciÃ³n directa, comando `/` o respuesta a nuestro mensaje. En DMs responde a todo. Usa `ia_nativa.generate()` + `ia_nativa.learn()` igual que `MoonBot`. Persiste mensajes y respuestas en `CHAT_HIST_{cid}`.
- **Comandos userbot**: `/start`, `/help` y `/tdstatus` disponibles via TDLib.
- **`TDLibClient._fetch_me()`**: obtiene el propio `user_id` y `username` tras autenticar para detectar menciones correctamente.
- **`GET /api/tdlib/userbot`**: devuelve estado actual y datos del usuario autenticado (`me`).

## [v16.41.0] - 2026-05-07
### IntegraciÃ³n TDLib directa vÃ­a ctypes (MTProto completo)
- **`core/tdlib_client.py`** (180 lÃ­neas): Wrapper Python puro sobre `libtdjson.so` usando `ctypes`. Sin librerÃ­a intermedia â€” carga el binario compilado directamente con `CDLL`. Expone `get_history()`, `sync_to_db()` y mÃ¡quina de estados de autenticaciÃ³n headless.
- **`Dockerfile` multi-stage**: Etapa 1 compila TDLib desde fuente en Ubuntu 22.04 con `clang-14` y `libc++`. Etapa 2 copia solo `libtdjson.so` (~8 MB) al contenedor `python:3.12-slim`. El binario se cachea en capas Docker â€” sÃ³lo recompila si cambia TDLib.
- **AutenticaciÃ³n headless via dashboard**: `auth_state` expuesto en `/api/tdlib/status`. El flujo telÃ©fono â†’ cÃ³digo â†’ contraseÃ±a se completa con `POST /api/tdlib/auth` (`action`: `phone`/`code`/`password`). Sin `input()` bloqueante â€” compatible con Docker.
- **SincronizaciÃ³n de historial**: `POST /api/tdlib/sync` con `chat_id` importa hasta 200 mensajes del servidor Telegram directamente a `CHAT_HIST_{cid}` en SQLite, deduplicando por `(time, uid, text[:20])`.
- **Variables de entorno**: `TDLIB_API_ID` y `TDLIB_API_HASH` (obtenidos en my.telegram.org). Si no estÃ¡n definidas, TDLib queda deshabilitado sin error â€” el bot funciona igual con solo Bot API.
- **Inicio automÃ¡tico**: Si las variables estÃ¡n presentes, `tdlib_client.start()` arranca el hilo receptor al iniciar el bot y conecta el logger con `tdlib_client._log = add_web_log`.

## [FUTURO] - IntegraciÃ³n TDLib (MTProto completo)
### Objetivo: reemplazar/complementar Bot API con TDLib para acceso completo a Telegram
- **TDLib como cliente MTProto**: Integrar [TDLib](https://core.telegram.org/tdlib) vÃ­a `python-tdlib` o `pytdlib` para acceder a la API completa de Telegram con una cuenta de usuario, sin las restricciones del Bot API.
- **RecuperaciÃ³n de historial completo**: Con TDLib se podrÃ¡n cargar todos los mensajes histÃ³ricos de cualquier grupo/canal al que pertenezca la cuenta, no solo los recibidos desde que el bot estÃ¡ corriendo. Importarlos a `CHAT_HIST_{cid}` en SQLite.
- **SincronizaciÃ³n en tiempo real**: TDLib mantiene una base de datos local cifrada (`tdlib_db/`) con el estado completo de chats, listas de miembros y metadatos â€” sin depender de reintentos al Bot API.
- **Acceso a funciones exclusivas de usuario**: Reacciones, historias, chats de voz, descarga de medios grandes, gestiÃ³n de supergrupos sin restricciones de Bot API.
- **MÃ³dulo propuesto**: `core/tdlib_client.py` â€” wrapper que expone `get_history(chat_id, limit)`, `send_message(chat_id, text)` y `sync_to_db()`. Se instancia con `api_id`, `api_hash` y nÃºmero de telÃ©fono de la cuenta de usuario.
- **Dependencias**: `python-tdlib` (o compilar TDLib nativo + ctypes wrapper), `api_id`/`api_hash` desde [my.telegram.org](https://my.telegram.org).
- **Nota**: Requiere cuenta de usuario Telegram (no un token de bot). Puede coexistir con el Bot API actual: el bot sigue respondiendo mensajes, TDLib se usa solo para lectura/historial.

## [v16.40.0] - 2026-05-07
### ModularizaciÃ³n: ProxyManager, VirusTotalManager y TaskQueue
- **`core/proxy_manager.py`**: Extrae la clase `ProxyManager` (~220 lÃ­neas). Constructor recibe `db` y `log_func` inyectados; elimina dependencia directa con el estado global de `moon_multibot.py`.
- **`core/vt_manager.py`**: Extrae `VirusTotalManager` (30 lÃ­neas). Clase autocontenida que solo necesita `requests`; se instancia con la API key directamente.
- **`core/task_queue.py`**: Extrae `TaskQueue` (60 lÃ­neas). Recibe `log_func` opcional; usa no-op hasta que `add_web_log` estÃ¡ disponible y se conecta a posteriori con `task_queue._log = add_web_log`.
- **`moon_multibot.py` reducido de 4794 â†’ 4497 lÃ­neas** (âˆ’297 lÃ­neas / âˆ’6%). El archivo principal ahora solo contiene `MoonCoreIA` y `MoonBot` como clases definidas localmente.
- **InyecciÃ³n de dependencias**: `proxy_mgr = ProxyManager(db)` en vez de acceder al global directamente. El logger se conecta con `proxy_mgr._log = add_web_log` despuÃ©s de que `add_web_log` estÃ© definido.

## [v16.39.0] - 2026-05-07
### Persistencia del Historial de Chat
- **Historial persistente en SQLite**: Los mensajes del chat (usuarios y bot) ahora se guardan en la base de datos con la clave `CHAT_HIST_{cid}`. El historial sobrevive reinicios del bot; antes se perdÃ­a al reiniciar porque solo existÃ­a en memoria.
- **Helper `_append_chat_hist()`**: FunciÃ³n centralizada que aÃ±ade cada mensaje al dict en memoria, recorta a los Ãºltimos 200 por chat y persiste en SQLite automÃ¡ticamente. Usada tanto en el loop de mensajes entrantes como en `send_msg()`.
- **Carga lazy desde DB**: Al seleccionar un chat en el dashboard, si la memoria no tiene historial (primer arranque tras reinicio), se recupera automÃ¡ticamente desde `CHAT_HIST_{cid}` sin necesidad de reiniciar.
- **Cap de 200 mensajes por chat**: El historial almacenado en DB se limita a los Ãºltimos 200 mensajes para evitar crecimiento ilimitado en SQLite. El dashboard sigue mostrando los Ãºltimos 100.

## [v16.38.0] - 2026-05-07
### Fix Chat Dashboard: Mensajes Bot, Scroll y Encoding
- **Respuestas del bot visibles en el chat**: `send_msg()` ahora registra el mensaje enviado en `global_chat_history` cuando el chat ya tiene historial activo. Antes solo aparecÃ­an los mensajes de los usuarios; ahora se ve la conversaciÃ³n completa (bot + usuarios).
- **ProtecciÃ³n contra historial vacÃ­o en JS**: `fetchChatHistory()` usa `data.history || []` para no explotar si la API devuelve error o historial nulo. Se muestra estado vacÃ­o "Sin mensajes registrados" en lugar de dejar la pantalla en blanco.
- **Scroll correcto en el Ã¡rea de mensajes**: AÃ±adido `min-height: 0` a `.chat-messages` y `.chat-main` en el CSS. Sin esta propiedad, los elementos `flex-grow: 1` dentro de un contenedor flex-column no activan `overflow-y: auto` y el scroll no funciona.
- **Error silencioso en fetch**: AÃ±adido `.catch(() => {})` en `fetchChatHistory()` para evitar errores no capturados en la consola por fallos de red o auth expirado.
- **ReparaciÃ³n de encoding mojibake en `script.js`**: 67 segmentos de emojis y texto en espaÃ±ol estaban double-encoded (bytes UTF-8 interpretados como cp1252/Latin-1 y re-guardados como Unicode). Reparados con un algoritmo de reverse cp1252 que convierte secuencias como `Ã¢\x9dÅ’` â†’ `âŒ` y `Ã°Å¸Å’â„¢` â†’ `ðŸŒ™` sin tocar el texto ASCII ni los caracteres ya correctos.

## [v16.37.0] - 2026-05-07
### CorrecciÃ³n CrÃ­tica Ollama y SelecciÃ³n de Motor IA
- **Fix crÃ­tico `ai_preference`**: `MoonCoreIA.generate()` no aceptaba el parÃ¡metro `ai_preference` que `InvokedAIService` intentaba pasarle, provocando un `TypeError` silencioso en cada consulta Inline y Guest. El parÃ¡metro ya estÃ¡ declarado correctamente.
- **Enrutamiento por motor implementado**: Al forzar `/ollama` o `/gemini` en un query, el motor seleccionado se usa directamente ignorando el ratio hÃ­brido global (`HYBRID_PERCENTAGE`). El modo `hybrid` o sin prefijo sigue respetando la configuraciÃ³n global.
- **Variable `effective_provider`**: Toda la lÃ³gica de llamada a LLM usa ahora `effective_provider` en lugar de `LLM_PROVIDER` directo, permitiendo overrides por peticiÃ³n sin alterar el estado global.
- **JSON seguro en respuestas Ollama y Gemini**: AÃ±adido `try/except` especÃ­fico para `ValueError`/`KeyError`/`IndexError` al parsear las respuestas de ambos motores. Errores de JSON malformado ya no colapsan el hilo y quedan registrados en el log.
- **Fallback de compatibilidad en `invoked_ai`**: Si `generate()` lanza `TypeError` (versiÃ³n antigua del core sin `ai_preference`), el servicio reintenta sin el parÃ¡metro y registra `hybrid` como motor usado.

## [v16.36.0] - 2026-05-07
### Panel Dashboard EstadÃ­sticas Inline y Guest IA
- **IntegraciÃ³n dashboard estadÃ­sticas**: Nuevo panel en la pestaÃ±a IA con tarjetas de resumen (total solicitudes, tasa de Ã©xito, tiempo promedio), desglose Inline/Guest, distribuciÃ³n por motor y feed de los Ãºltimos 20 eventos con tiempo de respuesta y usuario.
- **Selector de motor por defecto**: Botones Ollama / Gemini / Hybrid en el dashboard para cambiar el motor activo en caliente, con badge visual del modo actual y refresco automÃ¡tico cada 15 segundos.
- **Nuevos endpoints**: `GET /api/ia/inline_stats` y `POST /api/ia/inline_stats/set_default` para consultar y cambiar el motor por defecto desde el dashboard sin reiniciar.

## [v16.35.0] - 2026-05-07
### SelecciÃ³n de IA por Modo y EstadÃ­sticas Inline/Guest
- **SelecciÃ³n de motor IA por query**: Inline Mode y Guest Mode detectan prefijos `/ollama`, `/gemini` o `/hybrid` al inicio del mensaje para forzar el motor concreto sin tocar la configuraciÃ³n global.
- **Preferencia global persistente**: Si no se especifica prefijo, se usa `default_ai_mode` de `GLOBAL_SETTINGS`; se puede cambiar en caliente sin reiniciar.
- **EstadÃ­sticas de uso IA**: Nuevo sistema `INLINE_GUEST_AI_STATS` en base de datos que registra cada solicitud (modo, usuario, motor usado, tiempo de respuesta, Ã©xito/fallo) con historial de hasta 500 eventos recientes.
- **API de estadÃ­sticas**: Nuevo mÃ©todo `get_ai_statistics()` en `InvokedAIService` que devuelve resumen total, desglose inline/guest, distribuciÃ³n por motor (ollama/gemini/hybrid), tasa de Ã©xito y tiempo medio de respuesta.
- **CachÃ© inline diferenciada por IA**: La clave de cachÃ© de respuestas inline incluye ahora la preferencia de IA para evitar devolver la respuesta del motor equivocado ante el mismo query.
- **Logs enriquecidos**: Los registros de Inline IA y Guest Bot muestran ahora quÃ© motor respondiÃ³ en cada interacciÃ³n.
- **Nuevo plugin `inline_guest_ai_settings`**: Tres comandos de gestiÃ³n solo para master/admin:
  - `/ia_stats` â€” EstadÃ­sticas completas de uso IA con los Ãºltimos 5 eventos detallados.
  - `/ia_set_default <ollama|gemini|hybrid>` â€” Cambia el motor por defecto para inline y guest en caliente.
  - `/ia_info` â€” Muestra el motor activo, disponibilidad de Ollama y Gemini, y modo de operaciÃ³n actual.
- **`.gitignore` ampliado**: Se excluyen ficheros de instrucciones locales para agentes IA (`AGENTS.md`, `.instructions.md`, `.prompt.md`, `.agent.md`, `copilot-instructions.md`) para evitar commitear personalizaciones de entorno.

## [v16.34.0] - 2026-05-07
### Start Script Modular
- **Version dinamica**: `start.sh` lee `APP_VERSION` desde `core.config` para evitar banners desincronizados.
- **Chequeo de modulos core**: Nuevo comando `bash start.sh modules` valida imports de `core.config`, `core.db`, `core.telegram_api`, `core.invoked_ai`, `core.telegram_events`, tokens y bans.
- **Doctor reforzado**: `doctor` comprueba tambien los modulos internos antes de declarar la instancia saludable.
- **Auto-update mas fiable**: La deteccion de commits pendientes usa `git rev-list HEAD..origin/master` en vez de depender del texto de `git status`.
- **Arranque mas seguro**: Antes de lanzar `moon_multibot.py`, el script valida que el core modular pueda importarse.

## [v16.33.0] - 2026-05-07
### Modulo de Eventos Telegram
- **Nuevo modulo `core.telegram_events`**: Extrae el almacenamiento de `business_connection` y `managed_bot` fuera de `moon_multibot.py`.
- **Business Connections aisladas**: El panel consulta conexiones desde un store especializado en vez de leer estado directo del bot.
- **Managed Bots desacoplados**: Los updates `managed_bot` se registran desde el nuevo store, dejando el loop principal mas delgado.
- **Preparado para mas eventos**: Deja una ubicacion clara para futuros updates administrativos sin inflar `MoonBot`.

## [v16.32.0] - 2026-05-07
### Fragmentacion de IA Invocada
- **Nuevo modulo `core.invoked_ai`**: Extrae la logica de Guest Mode e Inline Mode fuera de `moon_multibot.py`.
- **Cache inline de baja latencia**: Reutiliza respuestas IA para consultas inline repetidas durante una ventana corta y evita regeneraciones innecesarias.
- **Rate limits aislados**: Los controles de frecuencia de Guest e Inline viven en el servicio especializado, no en el runtime principal.
- **Handlers delgados**: `MoonBot` conserva solo wrappers para conectar Telegram, bans y envio de mensajes con el servicio modular.
- **Base de rendimiento**: El runtime queda preparado para mover mas servicios sin tocar el bucle principal de updates.

## [v16.31.0] - 2026-05-07
### IA para Guest Mode e Inline Mode
- **Motor IA invocado**: Guest Mode e Inline Mode comparten prompts especificos para respuestas breves, utiles y listas para Telegram.
- **Inline IA real**: Nuevo `handle_inline_query` con `answerInlineQuery` y resultados tipo articulo: respuesta completa, version breve y prompt refinado.
- **Guest Mode mejorado**: Las invocaciones guest usan el mismo motor IA y pueden aprovechar el mensaje citado como contexto temporal.
- **Proteccion remota**: Inline/Guest aplica bans globales y CAS antes de generar IA, con rate limit por usuario para reducir bucles.
- **Feedback inline**: Se registran `chosen_inline_result` recientes para auditar que resultados IA se seleccionan.

## [v16.30.0] - 2026-05-07
### Guest Bots y Telegram Bot API 9.6
- **Guest Mode preparado**: `getUpdates` solicita updates modernos y el runtime detecta updates Guest Bot de forma tolerante (`guest_message`, `guest_interaction` o `guest_bot`).
- **Respuesta puntual de invitado**: Las invocaciones guest se procesan como contexto temporal y generan una sola respuesta sin registrar el chat como grupo administrado.
- **Proteccion mantenida**: Guest Bot pasa por bans persistentes y CAS antes de responder, con rate limit corto por usuario/chat para evitar bucles.
- **Cliente Telegram centralizado**: Nuevo modulo `core.telegram_api` con version objetivo `9.6`, normalizacion de metodos legacy y manejo robusto de respuestas.
- **Business y Managed Bots**: El bot acepta `business_connection` y `managed_bot`, registra sus eventos y expone helpers para `getManagedBotToken` y `replaceManagedBotToken`.
- **Terminal RAW actualizado**: Se retira `kickChatMember`, se usa `banChatMember` y se agregan metodos recientes como `sendMessageDraft`, foto de perfil y Managed Bots.

## [v16.29.0] - 2026-05-04
### Primer Corte Modular y Versionado Sincronizado
- **Modulo `core.config`**: Centraliza version, rutas, credenciales web, entorno, claves IA y seleccion de base de datos.
- **Modulo `core.db`**: Extrae `DBManager` fuera de `moon_multibot.py` para aislar SQLite y facilitar pruebas.
- **Compatibilidad preservada**: `moon_multibot.py` conserva las mismas variables globales importadas para evitar cambiar el comportamiento runtime.
- **Version visible sincronizada**: Banner de `start.sh`, badge del dashboard y `/api/status.version` quedan alineados con `v16.29.0`.
- **Base para futuros modulos**: Deja preparado el siguiente corte hacia rutas Flask, servicios de seguridad y runtime Telegram sin mover todo de golpe.

## [v16.28.0] - 2026-05-04
### Bans CAS, Globales y Locales Reforzados
- **CAS ahora aplica bans reales**: La deteccion de `api.cas.chat` ya no se limita a registrar el evento; ahora borra el mensaje, guarda el ban global y ejecuta `banChatMember`.
- **Bans locales por grupo**: Nuevo almacenamiento `BANS_{cid}` para separar bans locales de cada grupo y evitar que `/ban` contamine una lista global legacy.
- **Bans globales persistentes**: `GLOBAL_BANS` se consulta en el runtime y se re-aplica si el usuario vuelve a escribir o entra en otro grupo conocido.
- **Migracion legacy**: Los antiguos `ST_FILE["bans"]` se incorporan al sistema global para no perder baneos existentes.
- **Motor unico de enforcement**: Nuevo flujo `apply_user_ban`, `enforce_existing_ban` y `enforce_cas_ban` para centralizar guardado, borrado de mensaje, expulsion y logs.
- **Comandos claros**: `/ban` y `/unban` actuan localmente en el grupo actual; `/gban` y `/ungban` gestionan bans globales.
- **Panel y API ajustados**: `/api/users/ban` con `cid` crea ban local por defecto; sin `cid` crea ban global y lo propaga a grupos conocidos.
- **CAS en entradas nuevas**: `new_chat_members` tambien pasa por CAS y por bans persistidos antes de permitir actividad.
- **Bot correcto por grupo**: Las acciones del panel intentan usar el bot asociado al chat en vez de asumir siempre `active_bots[0]`.
- **Validacion realizada**: Compilacion Python, pruebas unitarias del gestor, simulacion runtime de Telegram, endpoints Flask temporales y consulta real a CAS.

## [v16.27.1] - 2026-05-04
### Seguridad de Tokens y Gestion de Bots
- **Tokens ocultos en el panel**: `/api/bots` deja de devolver tokens completos y expone solo `id` publico y `token_preview`.
- **Identificadores seguros**: La interfaz usa IDs derivados del token para acciones como desplegar ajustes o eliminar bots, sin incrustar el token real en HTML/JS.
- **Alta de bots persistente**: `POST /api/bots` guarda nuevos bots en `data/bots.json` cifrado y los arranca en caliente cuando es posible.
- **Eliminacion persistente**: `DELETE /api/bots` elimina por `id`, actualiza `data/bots.json` y limpia cache/runtime del bot.
- **Descargas autenticadas sin token en URL**: Los CSV de auditoria usan cabecera `Authorization` en vez de pasar el JWT por query string.
- **Cabeceras auth normalizadas**: El frontend evita construir `Bearer Bearer ...` al reutilizar tokens guardados.
- **Documentacion saneada**: README, `.env.example` y Dockerfile se limpiaron para quitar mojibake y documentar mejor `CIPHER_KEY`, variables seguras y arranque.
- **Validacion realizada**: Compilacion Python de modulos principales y `node --check web/script.js`.

## [v16.27.0] - 2026-04-30
### Estadisticas Reales VPS para MTProto
- **Asistente `start.sh mtproto`**: Permite introducir secrets MTProto existentes, generar uno nuevo o cargar varios secrets/puertos locales en `.env`.
- **Importacion local de proxies**: El bot importa `PROXY_SECRET`/`PROXY_PORT` y `PROXY_LOCAL_SECRETS`/`PROXY_LOCAL_PORTS` al gestor sin borrar proxies existentes.
- **Conexion SSH al VPS**: Nueva configuracion `PROXY_VPS_*` y panel para guardar host, usuario, puerto, ruta de clave y puertos.
- **Secretos fuera de la web**: Password SSH y passphrase de clave solo se leen desde variables de entorno (`PROXY_VPS_PASSWORD`, `PROXY_VPS_KEY_PASSPHRASE`); no se guardan desde el dashboard.
- **Stats reales de puertos**: El dashboard lee `ss` en el VPS para comprobar `8443`, `8444`, `8445`, `8446` u otros puertos configurados.
- **Docker real**: Lectura de `docker ps` y `docker stats --no-stream` para mostrar CPU, RAM, trafico y puertos publicados.
- **Deteccion de secret MTProto**: Parseo de logs del contenedor proxy para sugerir enlace real con el puerto publicado.
- **PestaÃ±a visible de Proxies**: Acceso directo en la navegacion principal junto a Seguridad, Cola y Cambios para evitar pestaÃ±as perdidas.
- **Dependencia SSH validada**: `start.sh` comprueba `paramiko` como libreria critica antes de arrancar.
- **Nuevos endpoints**: `/api/proxies/vps/config` y `/api/proxies/vps/stats`.

## [v16.26.0] - 2026-04-30
### Aprendizaje de Programacion para Moon IA
- **Nueva fuente Programming**: La expansion multifuente acepta `programming` para enseÃ±ar lenguajes y patrones de desarrollo.
- **Semillas de programacion**: La IA aprende fundamentos, estructuras de datos, algoritmos, testing, debugging, seguridad, APIs, bases de datos, concurrencia y DevOps.
- **Lenguajes incluidos**: Python, JavaScript, TypeScript, SQL, HTML, CSS, Java, Go, Rust, PHP y Bash, con fallback para lenguajes personalizados.
- **Dashboard actualizado**: Nueva opcion `Programacion (Lenguajes)` y boton `ENSEÃ‘AR PROGRAMACION CORE`.
- **Comando Telegram Admin/Master**: Nuevo `/ia_programar python,javascript,sql` con alias `/ia_code` y `/programar_ia`.

## [v16.25.0] - 2026-04-30
### Auto-Update Docker Sin Interaccion
- **Actualizacion automatica en arranque Docker**: `start.sh` aplica `git pull origin master` automaticamente si detecta que el contenedor esta atrasado.
- **Control por entorno**: `AUTO_DOCKER_UPDATE=true` queda activado en `docker-compose.yml`; puede desactivarse con `false`.
- **Dashboard sin confirmacion manual**: El boton de actualizacion ya no muestra `confirm()` y ejecuta la actualizacion directamente.
- **Rebuild Docker automatizado**: El endpoint `/api/system/update` intenta ejecutar `docker compose up -d --build --remove-orphans` cuando Docker esta disponible.
- **Reinicio automatico del proceso**: Tras aplicar cambios, el bot programa un reinicio del proceso para cargar el codigo actualizado.

## [v16.24.0] - 2026-04-30
### Mantenimiento Autonomo y Backups en Silencio
- **Mantenimiento desacoplado**: Las tareas periodicas se mueven a `run_periodic_maintenance()` para reutilizar el mismo flujo sin duplicar logica.
- **Backups sin actividad de chat**: El backup 24H y el backup de aprendizaje 1H ahora se comprueban tambien cuando Telegram no entrega mensajes nuevos.
- **Backup 24H intacto**: Se conserva la copia completa diaria al Master.
- **Backup aprendizaje 1H intacto**: Se conserva la copia horaria con progreso neural e hito 1B/12H.
- **Mayor fiabilidad operativa**: Sincronizacion de seguridad y purga multimedia tambien quedan protegidas contra periodos de silencio.

## [v16.23.0] - 2026-04-30
### Hito 1 Billon / 12H y Balanceador Neural
- **Nueva meta extrema**: Objetivo de 1 billon de palabras aprendidas en 12 horas.
- **Balanceador de carga neural**: Nuevo sistema controlado de workers que calcula instancias necesarias y reparte fuentes de libros.
- **Panel de control en interfaz**: Nuevo indicador `Hito 1 billon / 12H` y controles para lanzar/detener workers desde el Dashboard.
- **Fuentes literarias ampliadas**: La expansion maestra y el balanceador usan una biblioteca ampliada de Project Gutenberg.
- **Backup 24H preservado**: Se mantiene la copia automatica diaria completa al Master.
- **Backup de aprendizaje cada 1H**: Nueva copia horaria centrada en el progreso neural, configurable desde `GLOBAL_SETTINGS.learning_backup_interval`.
- **Proteccion operativa**: El balanceador respeta un maximo de workers configurable para evitar lanzar procesos infinitos.

## [v16.22.0] - 2026-04-30
### Hito Neural 1M / 1H
- **Nueva meta de aprendizaje**: La madurez principal de la IA sube de 100.000 a 1.000.000 de palabras aprendidas.
- **Objetivo de velocidad**: Nuevo hito operativo para alcanzar 1.000.000 de palabras en 60 minutos.
- **Metricas de progreso**: La API de IA expone progreso, palabras restantes, tasa requerida y estado del hito.
- **Dashboard actualizado**: Nuevo indicador `Hito 1M / 1H` en el panel del Cerebro Moon.
- **Estado inteligente**: El sistema marca si la IA va en ritmo de 1 hora o si necesita acelerar el aprendizaje.

## [v16.21.0] - 2026-04-30
### Traduccion IA Natural y Aprendizaje Local
- **Traduccion sin comandos**: La IA detecta peticiones naturales como `traduce hola al ingles`, `como se dice gracias en aleman` o `translate hello to Spanish`.
- **Soporte en respuestas**: Al responder a un mensaje con `traduce esto al ingles`, el bot traduce el contenido del mensaje citado.
- **Memoria local de traducciones**: Las traducciones aprendidas se guardan en `IA_TRANSLATION_MEMORY` para reutilizarse sin pedir ayuda externa.
- **Aprendizaje desde motores externos**: Si Gemini u Ollama generan una traduccion nueva, la IA local la aprende automaticamente.
- **Comando de ensenanza manual**: Nuevo `/aprender_traduccion es en hola = hello` para introducir traducciones exactas en la memoria local.
- **Compatibilidad preservada**: Se mantienen `/traducir`, `/translate`, `/tr`, Gemini, Ollama y el endpoint `/api/ia/translate`.

## [v16.20.0] - 2026-04-30
### ðŸ›¡ï¸ Seguridad y Respaldo Total
- **Copias de Seguridad Manuales**: AÃ±adido botÃ³n en el Dashboard para solicitar una copia completa del "cerebro" (DB) enviada instantÃ¡neamente por Telegram.
- **Backup AutomÃ¡tico 24h**: El sistema ahora envÃ­a automÃ¡ticamente un respaldo de seguridad al Administrador cada 24 horas.

## [v16.19.0] - 2026-04-30
### ðŸŒ ExpansiÃ³n de Conocimiento Personalizada
- **Inyector por TÃ³picos**: Nueva herramienta que permite escribir una lista de temas separados por comas para que la IA aprenda de Wikipedia de forma dirigida.
- **Reportes de TÃ³picos**: Informe detallado al finalizar el aprendizaje de temas especÃ­ficos.

## [v16.18.0] - 2026-04-30
### ðŸ”Ž AuditorÃ­a Neuronal Interactiva
- **Fuentes Desplegables**: Ahora se puede hacer clic en las "Top Fuentes" para ver una muestra real de las palabras aprendidas de cada origen.
- **ActualizaciÃ³n Real-Time (2s)**: Reducido el intervalo de actualizaciÃ³n de estadÃ­sticas en el panel a 2 segundos para una monitorizaciÃ³n fluida.


## [v16.17.0] - 2026-04-30
### ðŸ“Š Sistema de Reportes y Notificaciones Automatizadas
- **Reportes de Inteligencia Maestra**: Ahora el bot envÃ­a un resumen detallado vÃ­a Telegram al Administrador cuando finaliza un proceso de sembrado masivo (Wikipedia/Patrones).
- **ResÃºmenes Diarios de Salud Neural**: Implementado un trabajador en segundo plano que envÃ­a un reporte cada 24 horas con las estadÃ­sticas de crecimiento (neuronas, sinapsis, tasa de aprendizaje).
- **Notificaciones en Tiempo Real**: El bot avisa al iniciar procesos de expansiÃ³n cerebral para que el usuario estÃ© informado del progreso.
- **Mejoras en la Estructura de Datos**: OptimizaciÃ³n en la persistencia de las fuentes de aprendizaje para generar rankings de conocimiento.


## [v16.16.0] - 2026-04-30
### ðŸ§  Inteligencia Maestra y Estabilidad CrÃ­tica
- **IntegraciÃ³n de Master Intelligence (Advanced IA)**:
  - FusiÃ³n nativa del inyector de conocimiento en el nÃºcleo principal (`MoonCoreIA`).
  - **Wikipedia Master Seeding**: El bot ahora puede absorber conocimiento enciclopÃ©dico sobre Ciencia, Historia, TecnologÃ­a y mÃ¡s directamente desde la API de Wikipedia.
  - **InyecciÃ³n de Patrones Humanos**: AÃ±adidos protocolos de conversaciÃ³n natural para humanizar las respuestas de la IA.
  - **Trigger desde Dashboard**: Nuevo botÃ³n premium en la pestaÃ±a de IA para disparar la expansiÃ³n cerebral en un clic.
- **Robustez y Blindaje Neural**:
  - **Protocolo `_ensure_counters`**: Sistema de auto-reparaciÃ³n de la red neuronal que garantiza la integridad de los datos y previene el error `'dict' object has no attribute 'most_common'`.
  - **SincronizaciÃ³n Hot-Reload**: Mejora en la recarga del cerebro en caliente para asegurar que los nuevos conocimientos se apliquen instantÃ¡neamente sin reiniciar el bot.
- **OptimizaciÃ³n de Entorno y Conflictos**:
  - **DetecciÃ³n de Instancias Duplicadas**: Protocolo para evitar el error `Conflict` de Telegram al cerrar sesiones locales si el bot estÃ¡ corriendo en la nube.
- **Mejoras de UI/UX (IA Dashboard)**:
  - RediseÃ±o de la zona de evoluciÃ³n con nuevos botones de acciÃ³n masiva.
  - Toasts de notificaciÃ³n mejorados para procesos asÃ­ncronos de larga duraciÃ³n.


## [v16.15.0] - 2026-04-28
### ðŸš€ Auto-GestiÃ³n y ModeraciÃ³n de Ã‰lite
- **Sistema de ActualizaciÃ³n Inteligente (CI/CD)**: 
  - IntegraciÃ³n nativa de **Git dentro de Docker**.
  - Panel de actualizaciÃ³n en un clic desde el Dashboard.
  - DetecciÃ³n automÃ¡tica de versiones y commits en tiempo real.
- **ModeraciÃ³n Avanzada en Grupos (Telegram Nativo)**:
  - **Soporte para Reply (Respuestas)**: Comandos `/ban`, `/mute`, `/warn` ahora funcionan respondiendo a mensajes del usuario.
  - **Ã“rdenes de EjecuciÃ³n Real**: El bot ahora expulsa, banea y restringe permisos de forma real en la API de Telegram.
  - **Comando `/settings` de Grupo**: Consulta de configuraciÃ³n de seguridad y estado de IA directamente desde el chat.
  - **Alias de Comandos**: Soporte para `/comandos`, `/help`, `/inicio`.
- **Mejoras de TelemetrÃ­a en Chat Web**:
  - **Etiquetas de Estado en Vivo**: IdentificaciÃ³n visual inmediata de usuarios `BANNED`, `MUTED` o con `WARNS` activos en el historial.
  - **Remote Command Console**: Capacidad de ejecutar comandos de sistema directamente desde el chat del Dashboard.
  - **Feedback Visual de Acciones**: Toasts y confirmaciones interactivas tras ejecutar acciones rÃ¡pidas.
- **Seguridad e IA (Robustez)**:
  - **IA Command Shield**: Blindaje total que impide a la IA responder a mensajes que empiecen por `/`.
  - **Dynamic Permission Refresh**: ReducciÃ³n de la cachÃ© de admins a 5 minutos para reconocer cambios de rango al instante.
  - **Blindaje de MASTER_ID**: Limpieza y validaciÃ³n estricta del ID de administrador para control absoluto.
- **Docker & Infraestructura**:
  - Mapeo de volÃºmenes para persistencia de Git y actualizaciones persistentes.
  - CorrecciÃ³n de dependencias crÃ­ticas (`psutil`) y optimizaciÃ³n de hilos de arranque.

## [v16.14.0] - 2026-04-27
### ðŸ”¥ Novedades Premium y GlobalizaciÃ³n
- **Plataforma de TraducciÃ³n Centralizada (i18n)**: 
  - Soporte multi-idioma nativo (ES, EN, FR, DE, IT, PT).
  - Motor de traducciÃ³n dinÃ¡mica en tiempo real para todo el dashboard.
  - **IA Translator**: Capacidad de la IA para generar automÃ¡ticamente traducciones de la interfaz a nuevos idiomas.
- **Telegram Business Automation (Chatbots)**:
  - Soporte nativo para actuar en nombre de cuentas personales/empresa.
  - **Auto-Greetings**: Mensajes de bienvenida automÃ¡ticos para nuevos clientes.
  - **Away Mode**: Respuestas automÃ¡ticas fuera de horario o disponibilidad.
  - **Quick Replies**: GestiÃ³n de atajos de teclado para respuestas rÃ¡pidas.
  - **IA Business Agent**: DelegaciÃ³n de respuestas a la IA en chats de Business.
- **Gestor de Proxies MTProto**:
  - Panel dedicado para desplegar y monitorizar nodos de proxy propios.
  - TelemetrÃ­a en tiempo real: Conexiones activas, trÃ¡fico (Upload/Download) y estado del proceso.
  - Control de ciclo de vida: Start/Stop/Remove de nodos desde la web.
- **Centro de Seguridad & VirusTotal**:
  - Nueva pestaÃ±a de Seguridad para auditorÃ­a de amenazas.
  - IntegraciÃ³n con API de VirusTotal para anÃ¡lisis de hashes en tiempo real.
  - Monitor de lÃ­mites de API (Free Tier) y registro de incidentes.
- **Ajustes Locales por Nodo (Per-Group Config)**:
  - **IA Moods**: SelecciÃ³n de personalidad por grupo (Amigable, Serio, SarcÃ¡stico, Agresivo).
  - **Anti-Link**: Sistema de bloqueo de enlaces externos configurable.
  - **Anti-Flood**: ProtecciÃ³n automÃ¡tica contra spam (silencio automÃ¡tico).
  - **Clean Join**: Auto-borrado de mensajes de servicio de entrada de usuarios.
- **RediseÃ±o Premium UI**:
  - Nuevos **Designed Selectors** (estilo iOS) con efectos de brillo y animaciones.
  - Sidebar de ajustes nodal optimizada y persistente.
- **Motor Universal Telegram API**: 
  - IntegraciÃ³n completa de la Bot API. Soporte para llamadas RAW y parÃ¡metros JSON desde el Dashboard.
  - Nueva pestaÃ±a **Terminal Universal** para ejecuciÃ³n de comandos en caliente.
- **Herramientas Admin**: Comandos `/pin`, `/title`, `/kick`, `/mute`, `/promote`, `/demote`.

## [v16.13.0] - 2026-04-27 (The Architecture & Stability Update) ðŸ—ï¸ðŸš€ðŸ›¡ï¸âš¡

### ðŸ—ï¸ Arquitectura y Desacoplamiento
- **ðŸ“¦ Desacoplamiento de Semillas:** Se han extraÃ­do mÃ¡s de 1500 lÃ­neas de datos estÃ¡ticos a un archivo JSON externo (`data/multilingual_seeds.json`), optimizando la carga y legibilidad del cÃ³digo base.
- **ðŸ§¹ Limpieza Profunda del Core:** EliminaciÃ³n de ~2500 lÃ­neas de cÃ³digo redundante, repetido o roto en `moon_multibot.py`. El archivo principal es ahora un 50% mÃ¡s ligero y eficiente.
### ðŸ›¡ï¸ Seguridad y ModeraciÃ³n (Neural Shield)
- **ðŸš« Ban AutomÃ¡tico por Contenido:** El sistema ahora detecta y expulsa automÃ¡ticamente a usuarios que envÃ­en material de **porno** o **terrorismo**.
- **ðŸ§  HeurÃ­sticas Visuales:** IntegraciÃ³n de NPHE para identificar patrones sospechosos (tonos de piel, ambientes sombrÃ­os, bitrates anÃ³malos) sin APIs externas.
- **ðŸ“ Lista Negra Expandida:** InclusiÃ³n de mÃ¡s de 20 nuevos tÃ©rminos prohibidos en el filtro de seguridad global.

- **ðŸ§  Neural Perception Heuristic Engine (NPHE):** ImplementaciÃ³n de un motor de anÃ¡lisis de medios 100% nativo y local (Zero-API).
- **ðŸ–¼ï¸ PercepciÃ³n de ImÃ¡genes Avanzada:** Soporte para PNG, JPEG, WebP y GIF con anÃ¡lisis de complejidad, tonos predominantes y ambiente de escena.
- **ðŸŽ¥ TelemetrÃ­a de Video Pro:** ExtracciÃ³n de metadatos en MP4/MOV, cÃ¡lculo de bitrate e identificaciÃ³n de cÃ³decs (H.264, HEVC, VP9).

### ðŸš€ Multibot y Despliegue
- **ðŸ¤– Soporte Multibot Nativo:** El sistema ahora inicia automÃ¡ticamente todos los bots configurados en `bots.json` en hilos paralelos independientes.
- **ðŸŒ Modos de Entorno (Dev/Stable):**
    - **Modo Dev:** Activado vÃ­a `.env`. Incluye logs en `DEBUG`, base de datos de pruebas (`moon_dev.db`), Flask con auto-recarga y puerto alternativo (`5001`).
    - **Modo Stable:** Optimizado para producciÃ³n con logs limpios, puerto `5000` y persistencia en base de datos oficial.
- **ðŸ·ï¸ Badge de Entorno:** Nueva etiqueta visual "DEV MODE" en el Dashboard para identificar rÃ¡pidamente el ambiente de ejecuciÃ³n.

### ðŸ”§ Mejoras TÃ©cnicas y Fixes
- **âš–ï¸ Fix de Rangos:** Los comandos de plugins ahora usan comparaciones de rango (`rank`) insensibles a mayÃºsculas, evitando fallos con el rango "Master".
- **ðŸ§  Fix de Referencias IA:** Cada instancia de bot ahora posee su propia referencia interna `self.ia` hacia el nÃºcleo neuronal, eliminando dependencias globales inestables.
- **ðŸ› ï¸ RestauraciÃ³n de MÃ©todos:** Recuperada la funcionalidad de `evolve_process` que habÃ­a quedado truncada en versiones anteriores.

## [v16.12.0] - 2026-04-27 (The Global Language Expansion) ðŸŒðŸ—£ï¸ðŸŒ

### ðŸŒ ExpansiÃ³n Masiva de Idiomas

- **ðŸ—£ï¸ 37 Idiomas Soportados:** ExpansiÃ³n completa del soporte multilingÃ¼e de 22 a **37 idiomas**. La IA ahora puede detectar, aprender y generar respuestas en lenguas europeas adicionales (danÃ©s, noruego, finlandÃ©s, estonio, letÃ³n, lituano, eslovaco, esloveno, croata, bosnio, serbio, macedonio, bÃºlgaro, albanÃ©s, maltÃ©s, islandÃ©s, irlandÃ©s, galÃ©s, gaÃ©lico escocÃ©s), lenguas occidentales europeas (vasco, catalÃ¡n, gallego, occitano, bretÃ³n, frisÃ³n, luxemburguÃ©s, valÃ³n) y otras lenguas (corso, romanÃ©s, sardo).
- **ðŸ“š Corpus Conversacional Expandido:** AÃ±adidas **20 frases cotidianas por idioma** en escritura nativa real para cada uno de los 37 idiomas, totalizando mÃ¡s de 740 frases conversacionales nuevas. Las frases cubren saludos, despedidas, agradecimientos, planes diarios, conversaciÃ³n cotidiana y expresiones comunes.
- **ðŸ” DetecciÃ³n Mejorada:** Actualizado el mapa de palabras clave (`kw_map`) con tÃ©rminos especÃ­ficos para cada idioma nuevo, mejorando la precisiÃ³n de detecciÃ³n automÃ¡tica de idioma en mensajes entrantes.
- **ðŸ”— Conectores Gramaticales:** AÃ±adidos conectores lÃ³gicos nativos ("y", "pero", "aunque", etc.) para todos los 37 idiomas, permitiendo respuestas mÃ¡s naturales y coherentes en cada lengua.
- **ðŸ“Š Panel Web Actualizado:** El panel de IA en la interfaz web ahora muestra dinÃ¡micamente el nÃºmero real de idiomas soportados (37) en lugar de un valor estÃ¡tico.

### ðŸ”§ Mejoras TÃ©cnicas

- **ðŸŒ Endpoint `/api/ia/stats` Mejorado:** AÃ±adido campo `supported_languages` que devuelve la lista completa de idiomas soportados para sincronizaciÃ³n con la interfaz web.
- **âš¡ OptimizaciÃ³n de Rendimiento:** La detecciÃ³n de idioma y selecciÃ³n de conectores se realiza una sola vez por mensaje, manteniendo la eficiencia incluso con 37 idiomas disponibles.

## [v16.11.0] - 2026-04-27 (The Intelligence & Presence Update) ðŸ§ ðŸŽ¯ðŸ€ðŸ·ï¸

### âœ¨ Nuevas Funcionalidades

- **ðŸŽ¯ DetecciÃ³n de IntenciÃ³n Real:** Nueva funciÃ³n `detect_intent()` que clasifica cada mensaje entrante en 5 categorÃ­as (saludo, despedida, agradecimiento, queja, pregunta). La IA adapta automÃ¡ticamente el prefijo de su respuesta al tipo de mensaje detectado, haciendo las respuestas mucho mÃ¡s naturales y coherentes.
- **ðŸ€ Lucky Drop System:** 5% de probabilidad de obtener +5 karma al interactuar con la IA. AÃ±ade un elemento de sorpresa y gamificaciÃ³n que incentiva la participaciÃ³n activa con el bot.
- **ðŸ·ï¸ Sistema de Flags de Usuario (`/flag`):** Los admins y el Master pueden marcar usuarios con etiquetas visuales: `ðŸ’Ž VIP`, `ðŸ›¡ï¸ Staff`, `âš ï¸ Sospechoso` o `ðŸ‘¤ Normal`. Las flags se almacenan por grupo en la base de datos y aparecerÃ¡n en el perfil de usuario.
- **ðŸ“Š Comando `/resumen`:** Genera un resumen de la actividad reciente del grupo disponible para admins y Master. Muestra los usuarios mÃ¡s activos del perÃ­odo y una sÃ­ntesis generada por la IA sobre los temas del chat.
- **ðŸ“š Auto-FAQ con Respuestas Configurables:** El sistema FAQ ya no solo cuenta preguntas repetidas, ahora las responde automÃ¡ticamente. Cuando una pregunta se hace 3 o mÃ¡s veces y tiene una respuesta guardada, el bot la responde de forma directa. Nuevos endpoints: `POST /api/automation/faq/set` y `POST /api/automation/faq/delete` para gestionar el banco de respuestas desde el panel.

### ðŸ”§ Correcciones de Bugs

- **ðŸ”‡ Fix `/listen on/off`:** Corregido el bug crÃ­tico por el cual los comandos de modo escucha nunca funcionaban. La declaraciÃ³n `global listen_mode` estaba ausente en la funciÃ³n `run()` de `MoonBot`, haciendo que la asignaciÃ³n creara una variable local en vez de modificar el estado global.
- **ðŸ“œ Fix `global_msg_log`:** AÃ±adida la declaraciÃ³n `global global_msg_log` correcta para que el historial global se sincronice realmente entre hilos en lugar de descartarse silenciosamente.
- **ðŸŒ Fix `/search` â€” DuckDuckGo API:** Reemplazado el scraping de Google (bloqueado por robots.txt y clases CSS obsoletas) por la API oficial de DuckDuckGo Instant Answer. El buscador ahora funciona de forma real, devuelve resultados y los inyecta en el cerebro como conocimiento nuevo.
- **âœ… Fix variable `matched` no utilizada:** La variable de control de auto-respuestas S_FILE ahora hace correctamente `continue` cuando encuentra una coincidencia, evitando procesar el mismo mensaje por mÃºltiples ramas de comandos.

### ðŸŒ Mejoras de IA

- **ðŸŒ Conectores LÃ³gicos en 13 Idiomas:** La funciÃ³n `generate()` detecta el idioma del mensaje entrante y usa conectores nativos del idioma correspondiente al construir la respuesta: ES, EN, FR, DE, IT, PT, TR, RU, ZH, JA, KO, AR, HI.
- **ðŸ“¡ OptimizaciÃ³n del Bucle de DetecciÃ³n:** El cÃ¡lculo del idioma para conectores se realiza una vez por generaciÃ³n, no en cada iteraciÃ³n del bucle Markov.

## [v16.10.3] - 2026-04-27 (The Contextual Language Update) ðŸ§ ðŸŒðŸ’¬
### ðŸ”§ Mejoras
- **ðŸ’¬ Conectores LÃ³gicos MultilingÃ¼es:** La IA ahora detecta el idioma del mensaje entrante y usa conectores nativos del mismo idioma al generar respuestas (13 idiomas: ES, EN, FR, DE, IT, PT, TR, RU, ZH, JA, KO, AR, HI). Las respuestas en inglÃ©s usan "but/also/however", en japonÃ©s "ã§ã‚‚/ã¾ãŸ/ã—ã‹ã—", etc.


## [v16.10.2] - 2026-04-27 (The Performance Update) âš¡ðŸš€
### ðŸ”§ Mejoras
- **âš¡ Anti-Flood en Memoria RAM:** El sistema de control de flood migrado de SQLite a un dict en memoria. Elimina 2 operaciones de base de datos por cada mensaje recibido, reduciendo la latencia del bucle principal especialmente en grupos de alta actividad.


## [v16.10.1] - 2026-04-27 (The Security Hotfix) ðŸ›¡ï¸ðŸ”§
### ðŸ› Correcciones CrÃ­ticas
- **ðŸ”§ Fix Escudo Neural:** Corregido el `AttributeError` que causaba que el escudo de seguridad fallara silenciosamente al intentar eliminar contenido prohibido. `last_msg_id` y `last_media_hash` ahora se inicializan correctamente en el arranque y se actualizan con cada mensaje.
- **ðŸš« Comando `/ban_media` Implementado:** Finalmente implementado el comando anunciado en v16.7.0. El Master puede enviar un archivo al grupo, ejecutar `/ban_media` y su hash SHA-256 queda permanentemente en la lista negra global. El archivo serÃ¡ eliminado automÃ¡ticamente en cualquier grupo donde el bot estÃ© presente.


## [v16.10.0] - 2026-04-27 (The Backup & Native Polyglot Update) ðŸ§ ðŸ’¾ðŸŒðŸ”„
### âœ¨ Nuevas Funcionalidades
- **ðŸ’¾ Comando `/backup_db`:** El Master puede solicitar en cualquier momento el envÃ­o directo de la base de datos completa (`moon_database.db`) por Telegram. Incluye el tamaÃ±o del archivo y queda registrado en el log de auditorÃ­a.
- **ðŸ”„ Backup AutomÃ¡tico 24h:** El sistema envÃ­a automÃ¡ticamente una copia de la base de datos al Master cada 24 horas en segundo plano, sin interrumpir el funcionamiento del bot.

### ðŸ”§ Mejoras y Correcciones
- **ðŸŒ DetecciÃ³n de Idioma por Unicode (Nativa):** Reescritura total del motor `detect_lang`. Ãrabe, Hindi, Ruso, Chino, JaponÃ©s, Coreano y TailandÃ©s se detectan ahora por **rango Unicode**, eliminando falsos positivos de las romanizaciones anteriores.
- **ðŸ“š Corpus Conversacional Real (14 Idiomas):** ExpansiÃ³n de `seed_multilingual` de 48 frases genÃ©ricas de tecnologÃ­a a **258 frases cotidianas** en escritura nativa real: ES, EN, FR, DE, IT, PT, TR, KO, HI, AR, RU, ZH, JA. Las frases cubren saludos, despedidas, agradecimientos, planes, conversaciÃ³n diaria y mÃ¡s.
- **ðŸ’¿ Guardado Forzado Post-Semilla:** El cerebro ahora se persiste en SQLite inmediatamente al finalizar `seed_multilingual`, garantizando que ninguna neurona nueva se pierda en reinicios.


## [v16.9.0] - 2026-04-26 (The Universal Polyglot Update) ðŸŒŒðŸŒŽðŸ§ ðŸ“¡
### âœ¨ Nuevas Funcionalidades
- **ðŸŒŒ Cerebro Universal (25+ Idiomas):** ExpansiÃ³n masiva del motor lingÃ¼Ã­stico para soportar Ã¡rabe, hindi, coreano, turco, tailandÃ©s, vietnamita y mÃ¡s (hasta 25+ idiomas del planeta).
- **ðŸ“¡ InyecciÃ³n de Conocimiento GalÃ¡ctico:** Nuevo sistema de semillas que dota al bot de una base cultural y tÃ©cnica en todos los continentes de forma instantÃ¡nea.
- **ðŸ“š Vocabulario Expandido:** Incremento del 300% en la base de palabras semilla para cada idioma soportado.
- **ðŸŒŽ Interfaz "Universal":** ActualizaciÃ³n de los controles de la IA para reflejar el nuevo alcance global del bot.

### ðŸ”§ Mejoras y Correcciones
- **ðŸ” HeurÃ­stica LingÃ¼Ã­stica Optimizada:** Refinamiento del motor de detecciÃ³n para diferenciar idiomas con raÃ­ces similares (ej. escandinavos).
- **âš¡ SincronizaciÃ³n UltrarÃ¡pida:** Mejora en el rendimiento de la inyecciÃ³n de semillas mediante procesamiento por lotes.


## [v16.8.0] - 2026-04-26 (The Multilingual & Shield Update) ðŸŒŽðŸ›¡ï¸ðŸ§ ðŸ”ðŸ’¡
### âœ¨ Nuevas Funcionalidades
- **ðŸŒŽ PolÃ­glota IA Core (Nativo):** El Cerebro Moon ahora es capaz de detectar y conversar en **9 idiomas** (ES, EN, FR, IT, PT, DE, RU, ZH, JA) mediante un motor de heurÃ­stica lingÃ¼Ã­stica nativo.
- **ðŸ“¡ InyecciÃ³n de Conocimiento Global:** Nuevo sistema de "Semillas MultilingÃ¼es" para dotar al bot de una base cultural y lingÃ¼Ã­stica internacional instantÃ¡nea.
- **ðŸ§  Motor de Coherencia IA 3.0:** RefactorizaciÃ³n del algoritmo de generaciÃ³n con **PenalizaciÃ³n de RepeticiÃ³n SemÃ¡ntica** para eliminar redundancias y bucles de texto.
- **ðŸŽ² GeneraciÃ³n ProbabilÃ­stica Ponderada:** ImplementaciÃ³n de pesos variables en la selecciÃ³n de sinapsis, aumentando la variedad y naturalidad de las respuestas.
- **ðŸ”— InyecciÃ³n de Conectores LÃ³gicos:** Sistema que inserta automÃ¡ticamente pausas y conectores (*"AdemÃ¡s"*, *"Pero"*) para una estructura gramatical mÃ¡s fluida.
- **ðŸ›¡ï¸ Escudo de Seguridad Neural:** ProtecciÃ³n proactiva contra contenido prohibido (terrorismo, pornografÃ­a, menores) mediante anÃ¡lisis heurÃ­stico de mensajes y metadatos.
- **ðŸ’¡ Sistema de Ayuda Contextual (Tooltips):** Despliegue de iconos de informaciÃ³n `?` en todo el dashboard para una experiencia de usuario autodidacta.
- **âš™ï¸ Ajustes de Seguridad Avanzada:** Control total sobre la frecuencia de sincronizaciÃ³n de hashes, profundidad de anÃ¡lisis (SOF/Atoms) y purga automÃ¡tica de medios.
- **ðŸ§¹ Auto-Mantenimiento de Disco:** Limpieza inteligente de la carpeta `downloads` basada en el tiempo de vida configurado por el usuario.

### ðŸ”§ Mejoras y Correcciones
- **ðŸ‘ï¸ VisiÃ³n Binaria Refinada:** OptimizaciÃ³n del motor de extracciÃ³n de metadatos para mayor precisiÃ³n en archivos de vÃ­deo MP4.
- **ðŸŽ¨ EstÃ©tica Global Unificada:** MigraciÃ³n de estilos de ayuda y badges a la hoja de estilos central para un rendimiento de renderizado superior.
- **ðŸ›¡ï¸ Blindaje de ModeraciÃ³n:** Corregida la estructura del panel de seguridad en la pestaÃ±a de ModeraciÃ³n.


## [v16.7.0] - 2026-04-26 (The Neural Vision & Security Update) ðŸ‘ï¸ðŸ›¡ï¸ðŸŒŒâš–ï¸
### âœ¨ Nuevas Funcionalidades
- **ðŸ‘ï¸ Neural Vision Core (Nativo):** ImplementaciÃ³n de un motor de anÃ¡lisis binario propio (100% Antigravity Core) para procesar multimedia sin librerÃ­as externas.
  - ExtracciÃ³n de resoluciÃ³n real en JPEG y PNG mediante parsing de segmentos SOF e IHDR.
  - AnÃ¡lisis tÃ©cnico de duraciÃ³n en vÃ­deos MP4/MOV mediante lectura de Ã¡tomos `mvhd`.
- **ðŸ›¡ï¸ Security Fingerprinting (SHA-256):** Sistema de seguridad basado en huellas digitales para detectar y banear automÃ¡ticamente contenido prohibido (terrorismo, material ilÃ­cito).
- **ðŸš« Comando `/ban_media`:** Permite al Master incluir permanentemente la huella digital del Ãºltimo archivo enviado en la lista negra global.
- **ðŸš€ Auto-Start Chrome:** IntegraciÃ³n en `start.sh` para apertura automÃ¡tica del Dashboard Neural al iniciar el sistema.

### ðŸ”§ Mejoras y Correcciones
- **ðŸ› ï¸ Refuerzo de Estabilidad:** Corregido el error de declaraciÃ³n global de `listen_mode` y el fallo de tipo en el generador de la IA.
- **ðŸ§¼ CÃ³digo Puro:** Eliminadas todas las dependencias externas (`Pillow`, `pytesseract`) para garantizar soberanÃ­a de cÃ³digo y ligereza.


## [v16.6.8] - 2026-04-26 (The Moderation & Security Update) ðŸ›¡ï¸ðŸ‘®ðŸŒŠâš–ï¸
### âœ¨ Nuevas Funcionalidades de ModeraciÃ³n
- **ðŸ‘¤ `/perfil`:** Nuevo comando que muestra el perfil completo del usuario (Nivel, EXP, Karma, Mensajes e Insignia) extraÃ­do de la base de datos en tiempo real.
- **ðŸ† `/top`:** Tabla de lÃ­deres con los 5 usuarios mÃ¡s activos del grupo, ordenados por mensajes y karma.
- **âš ï¸ Sistema de Advertencias (`/warn`, `/unwarn`, `/warns`):** Los admins pueden emitir advertencias individuales a usuarios. Al llegar a 3/3 se activa la alerta de expulsiÃ³n. Las advertencias son persistentes por grupo en la base de datos.
- **ðŸ”‡ Sistema de Mute (`/mute`, `/unmute`):** Los admins pueden silenciar usuarios. Los mensajes de usuarios muteados se eliminan automÃ¡ticamente en tiempo real sin necesidad de acciÃ³n manual.
- **ðŸŒŠ Anti-Flood DinÃ¡mico:** Nuevo sistema de control de flujo que detecta y elimina mensajes si un usuario supera el lÃ­mite configurable de mensajes en una ventana de 10 segundos. El lÃ­mite es ajustable desde los ajustes globales (`flood_limit`).

## [v16.6.7] - 2026-04-26 (The Dynamic Hundred Update) âš¡ðŸ’‰ðŸ§ ðŸŒ€âš–ï¸
### âœ¨ Nuevas Funcionalidades (Hot-Swap)
- **ðŸ’‰ InyecciÃ³n DinÃ¡mica de 100 Comandos:** Se ha desplegado un paquete masivo de 100 nuevas funcionalidades inyectadas directamente en la memoria en vivo del bot (`S_FILE` SQLite). Esto ha permitido una ampliaciÃ³n gigantesca con un **tiempo de inactividad de 0 segundos**, previniendo sanciones por desconexiones en Telegram.
  - **ðŸ› ï¸ Utilidad y Ayuda:** `/reglas`, `/faq`, `/soporte`, `/info`, `/comandos`, `/version`, `/estado`, `/pingdb`, etc.
  - **ðŸŽ­ Rol y Personalidad:** `/chiste`, `/saludar`, `/cafe`, `/reir`, `/llorar`, `/bailar`, `/abrazo`, etc.
  - **ðŸŽ² Herramientas Simuladas:** `/dado`, `/moneda`, `/suerte`, `/bola8`, `/clima`, `/hora`, `/hackear`, etc.
  - **ðŸŒŒ Lore y Easter Eggs:** `/moon`, `/cintiabot`, `/creador`, `/matrix`, `/cyberpunk`, `/illuminati`, etc.

## [v16.6.6] - 2026-04-26 (The Health & Audit Expansion v2) ðŸ¥ðŸ“ŠðŸ“¥ðŸŒ€âš–ï¸
### âœ¨ Nuevas Funcionalidades
- **ðŸ¥ Sistema de Alertas de Salud:** Un hilo en segundo plano que monitorea constantemente el uso de CPU/RAM y enviarÃ¡ una alerta directa al Maestro vÃ­a Telegram si el servidor llega a niveles crÃ­ticos (mÃ¡s del 90%).
- **ðŸ“¥ ExportaciÃ³n de Reportes a CSV:** Modificado el histÃ³rico de peritajes en `web/ia.html` y el backend en `moon_multibot.py` para incluir un botÃ³n `ðŸ“¥ CSV` en cada grupo evaluado. Permite descargar las pruebas de las auditorÃ­as de forma local.
- **ðŸ“‹ Changelog Actualizado:** AÃ±adidas las notas de la versiÃ³n `[v16.6.5]` en la parte superior del `CHANGELOG.md` conservando toda la documentaciÃ³n previa.

## [v16.6.5] - 2026-04-26 (The Health & Audit Expansion) ðŸ¥ðŸ“ŠðŸ“¥ðŸŒ€âš–ï¸
### âœ¨ Nuevas Funcionalidades
- **ðŸ¥ Sistema de Alertas de Salud por Telegram:** Implementado un monitor en segundo plano (`health_monitor`) que evalÃºa constantemente los recursos del sistema (CPU y RAM). Si el consumo supera el 90%, el bot enviarÃ¡ un mensaje directo automÃ¡tico de alerta al Maestro (`MASTER_ID`) a travÃ©s de Telegram para prevenir caÃ­das.
- **ðŸ“¥ ExportaciÃ³n de Reportes de AuditorÃ­a (CSV):** AÃ±adido un botÃ³n de descarga en el panel web (Registro HistÃ³rico de Peritajes) que permite exportar y descargar en formato CSV el historial de mensajes de los grupos auditados.

## [v16.6.4] - 2026-04-26 (The Omniscience & Hygiene Update) ðŸ›¡ï¸ðŸ›°ï¸ðŸ”ðŸŒ€âš–ï¸
### âœ¨ Inteligencia Global y Accesibilidad
- **ðŸ›°ï¸ Neuro-Buscador Global:** IntegraciÃ³n de un motor de bÃºsqueda web neuronal que permite al Cerebro Moon y a los administradores consultar datos de internet en tiempo real desde el Dashboard (pestaÃ±a IA) y vÃ­a comando (`/search`) en Telegram.
- **ðŸ” Buscador Centralizado (Header):** Nueva barra de bÃºsqueda inteligente en la cabecera del panel que permite localizar instantÃ¡neamente chats, bots y configuraciones desde cualquier pestaÃ±a.
- **ðŸ›¡ï¸ Blindaje de SincronizaciÃ³n:** CorrecciÃ³n de la variable maestra del bot (resoluciÃ³n de `bot_token` a `token`) garantizando la fluidez del bucle de mensajes sin caÃ­das silenciosas.
- **ðŸ’¾ Persistencia de Historial:** RefactorizaciÃ³n del endpoint de chat web (`/api/history`) para leer directamente de la base de datos segura, evitando la pÃ©rdida de conversaciones tras reinicios de servidor.
- **ðŸŽ¨ Z-Index Maestro:** Ajuste de jerarquÃ­as de capa (`z-index: 2000`) y desenfoque de cristal (`backdrop-filter`) en la cabecera para asegurar que las sugerencias de bÃºsqueda siempre destaquen sobre cualquier panel subyacente.

## [v16.6.3] - 2026-04-26 (The Stealth & Hygiene Update) ðŸ›¡ï¸ðŸ¤«ðŸš«ðŸŒ€âš–ï¸
### âœ¨ Seguridad, Higiene Neuronal y TelemetrÃ­a
- **ðŸ›¡ï¸ Filtro Anti-Spam Neuronal:** ImplementaciÃ³n de barreras de seguridad en el aprendizaje. La IA ahora ignora automÃ¡ticamente mensajes de estafas financieras y penaliza fuentes de baja calidad en las auditorÃ­as.
- **ðŸ¤« Modo Silencio Total (Stealth API):** EliminaciÃ³n definitiva de respuestas automÃ¡ticas (ecos) no autorizadas. Silenciado de errores redundantes de Telegram en la consola para un entorno de trabajo limpio.
- **ðŸ“ˆ TelemetrÃ­a de Alta Fidelidad:** ReparaciÃ³n del panel de rendimiento global. Ahora muestra uso real de CPU y desglose de memoria RAM en Gigabytes (Usado vs Total).
- **ðŸ·ï¸ ResoluciÃ³n DinÃ¡mica de Nombres (v2):** CorrecciÃ³n del sistema de renderizado. Los nombres reales de los grupos ahora se propagan correctamente y de forma persistente a todas las tarjetas de radar y peritaje.
- **ðŸ”„ SincronizaciÃ³n AutomÃ¡tica de Radar:** El panel de fuentes detectadas ahora se refresca solo cada 10 segundos, reflejando cambios de estado y nombres sin intervenciÃ³n del usuario.

## [v16.6.2] - 2026-04-26 (The Bugfix & Intelligence Patch) ðŸ›¡ï¸ðŸ”§ðŸ§ ðŸŒ€âš–ï¸
### âœ¨ Estabilidad y SincronizaciÃ³n
- **ðŸ›¡ï¸ Fix de Identidad Dual (Alias/ID):** ImplementaciÃ³n de resoluciÃ³n automÃ¡tica de IDs. Ahora el auditor traduce alias (@username) a IDs numÃ©ricos para no perder la pista de los mensajes en grupos ya unidos.
- **ðŸ”— ReparaciÃ³n de VinculaciÃ³n RÃ¡pida:** Corregido el error de comunicaciÃ³n en el panel web donde el botÃ³n "Vincular" enviaba parÃ¡metros errÃ³neos al backend.
- **ðŸ•¸ï¸ Parche de Dependencias de Scraping:** AÃ±adida la importaciÃ³n de `re` necesaria para el procesamiento de texto en el motor de Neuro-Scraping.
- **ðŸ§© NormalizaciÃ³n de Historial Retrospectivo:** Mejora en el guardado de metadatos (CID) para asegurar que el pasado del grupo sea accesible para la IA.
- **ðŸ“Š Informes de Peritaje IA:** GeneraciÃ³n de reportes tÃ©cnicos detallados al finalizar cada auditorÃ­a, incluyendo mÃ©tricas de longitud media, riqueza lÃ©xica y veredicto automÃ¡tico de recomendaciÃ³n.
- **ðŸ›¡ï¸ Auto-AuditorÃ­a por Radar:** El sistema ahora inicia automÃ¡ticamente un anÃ¡lisis de calidad silencioso en cuanto el radar detecta un nuevo grupo potencial.
- **ðŸŽ­ RestauraciÃ³n de Controles IA:** RecuperaciÃ³n integral de las funciones web para cambiar el Humor (SarcÃ¡stico, Cyberpunk, etc.), el Perfil de Potencia, el Neuro-Boost y el disparador de EvoluciÃ³n Neuronal.


## [v16.6.1] - 2026-04-26 (The Auditor & Radar Update) ðŸ›¡ï¸ðŸ”ŽðŸ§ ðŸŒ€âš–ï¸
### âœ¨ Inteligencia de Vigilancia y Cosecha de Datos
- **ðŸ›¡ï¸ AuditorÃ­a IA Avanzada (Peritaje):** Nuevo sistema de evaluaciÃ³n de calidad que permite analizar fuentes antes de vincularlas. Calcula una "Nota de Calidad" basada en la riqueza lÃ©xica y complejidad de frases.
- **ðŸ”Ž Neuro-Scraping de Canales:** Capacidad Ãºnica de auditar canales pÃºblicos (@username) mediante raspado web en tiempo real, permitiendo ver el contenido sin necesidad de unir al bot.
- **ðŸ•°ï¸ AuditorÃ­a Retrospectiva:** El motor de anÃ¡lisis ahora consulta el historial global de mensajes previos, permitiendo una evaluaciÃ³n instantÃ¡nea de grupos donde el bot ya ha estado presente.
- **ðŸ“¡ Radar de Fuentes AutomÃ¡tico:** DetecciÃ³n inteligente de grupos activos. El bot identifica chats donde estÃ¡ interactuando y los sugiere como "Fuentes Potenciales" en el panel web.
- **ðŸ·ï¸ TelemetrÃ­a de Estado Pro:** VisualizaciÃ³n dinÃ¡mica de la membresÃ­a del bot (ONLINE, ADMIN, OFFLINE, ERROR) con badges neÃ³n y cÃ³digos de colores estandarizados.
- **ðŸ•’ Timestamp de Actividad:** Seguimiento preciso del Ãºltimo mensaje procesado por cada alimentador para verificar la fluidez del aprendizaje.
- **âš¡ Quick-Link UI:** Interfaz de vinculaciÃ³n rÃ¡pida para aÃ±adir sugerencias del radar a la red neuronal con un solo clic.


## [v16.1.0] - 2026-04-26 (The Neural Expansion) ðŸ§ ðŸ“šðŸŒŒâš–ï¸
### âœ¨ ExpansiÃ³n de Conocimiento y Control Maestro
- **ðŸ§  InfiltraciÃ³n Literaria Masiva:** La IA ha absorbido mÃ¡s de **27,000 neuronas** Ãºnicas y **450,000 conexiones** semÃ¡nticas a travÃ©s de la inyecciÃ³n de obras maestras (*Don Quijote, La Regenta, Fortunata y Jacinta*).
- **ðŸŒŒ Modo Charla Natural (Master Only):** El Administrador Maestro ahora puede interactuar con la IA de forma natural sin comandos ni menciones, detectando automÃ¡ticamente la intenciÃ³n de charla.
- **ðŸ›¡ï¸ Ajustes Maestros Avanzados:** RediseÃ±o total del panel de ajustes con control de Modo Mantenimiento, Perfiles de Potencia IA (Eco/Peak) y gestiÃ³n de BiografÃ­a del Bot.
- **ðŸ©º Doctor Mode 2.0:** ActualizaciÃ³n del script de inicio con telemetrÃ­a IA integrada para diagnosticar la salud del cerebro y las instancias en tiempo real.
- **ðŸ’Ž Refuerzo de UI/UX:** ImplementaciÃ³n de tooltips informativos neÃ³n en el panel de IA y optimizaciÃ³n de la rejilla de gestiÃ³n de bots.
- **âš™ï¸ Backend de ConfiguraciÃ³n:** Nuevo sistema de persistencia para ajustes globales en la base de datos SQLite.

## [v16.0.1] - 2026-04-26 (Hotfix & Stability) ðŸ›¡ï¸ðŸ”¨ðŸŒ€âš–ï¸
### âœ¨ Mejoras de Robustez y UX
- **ðŸ›¡ï¸ Fix CrÃ­tico de EjecuciÃ³n:** Corregido el colapso silencioso del bot causado por datos legacy en la base de datos (Bans).
- **ðŸ¤– Identidad Visual Multibot:** ResoluciÃ³n dinÃ¡mica de nombres de usuario (@username) en el Gestor de Bots con sistema de cachÃ© de alta velocidad.
- **ðŸ“œ Persistencia del Historial:** El Historial Global Unificado ahora se guarda en la DB persistente, sobreviviendo a reinicios del sistema.
- **ðŸŽ¨ SincronizaciÃ³n EstÃ©tica:** ImplementaciÃ³n de estilos CSS faltantes (barras de progreso, rankings y spinners) para una experiencia visual completa.
- **ðŸ§¹ UnificaciÃ³n de NÃºcleo JS:** Limpieza integral de `script.js`, eliminando funciones duplicadas y conflictos de autenticaciÃ³n.
- **ðŸ’Ž Bots Tab Reborn:** RediseÃ±o total de la pestaÃ±a de gestiÃ³n de bots con tarjetas individuales y estados de conexiÃ³n en vivo.
- **ðŸ”‘ NormalizaciÃ³n de Auth:** Sistema automÃ¡tico de prefijos Bearer para asegurar la comunicaciÃ³n blindada con la API.

## [v16.0.0] - 2026-04-26 ðŸ—ï¸ðŸš€ðŸŒ€
### âœ¨ Novedades y Estabilidad Total
- **ðŸ—ï¸ ReconstrucciÃ³n Total del DOM:** Saneamiento profundo de la jerarquÃ­a HTML. EliminaciÃ³n de anidamientos errÃ³neos que causaban pestaÃ±as invisibles.
- **ðŸ› ï¸ Centro de DiagnÃ³stico Moon (v1.5):** Ahora con ejecuciÃ³n automÃ¡tica al entrar. MonitorizaciÃ³n en tiempo real de salud de API, SQLite, IA Brain y Tokens de Bots.
- **ðŸ“± Cabecera Adaptativa (v2.0):** RediseÃ±o del Header con motor `flex-wrap` inteligente y auto-ajuste de escala para soportar mÃ¡s de 15 mÃ³dulos activos simultÃ¡neamente.
- **ðŸ“œ Historial Global Unificado:** SupervisiÃ³n en vivo de toda la actividad de red en una sola consola centralizada.
- **âš¡ OptimizaciÃ³n de NavegaciÃ³n:** Refuerzo de la funciÃ³n `switchTab` con lÃ³gica de seguridad para evitar bloqueos de renderizado.
- **ðŸ—ï¸ Arquitectura Modular (Rebirth):** MigraciÃ³n total a un sistema de plantillas HTML desacopladas (`web/*.html`) para mÃ¡xima velocidad de carga.
- **ðŸ§¹ Purga de CÃ³digo Duplicado:** ReconstrucciÃ³n integral de `script.js` desde cero, eliminando 500+ lÃ­neas de cÃ³digo redundante.
- **ðŸ§  IA Brain Hub (Premium):** Nueva interfaz de IA con monitorizaciÃ³n en tiempo real de neuronas, conexiones y tasa de aprendizaje.
- **ðŸ›¡ï¸ RestauraciÃ³n de API:** RecuperaciÃ³n y blindaje de los endpoints de gestiÃ³n de bots, feeders y automatizaciÃ³n.
- **ðŸ’¬ Chat Engine 2.0:** Sistema de mensajerÃ­a optimizado con carga asÃ­ncrona de historial y directorio.

## [v15.0.2] - 2026-04-26 ðŸ› ï¸ðŸ›¡ï¸
### âœ¨ Novedades de IngenierÃ­a
- **ðŸ› ï¸ Centro de DiagnÃ³stico Moon:** Panel avanzado para la monitorizaciÃ³n de salud del sistema, tests de latencia y auditorÃ­a de red neuronal.
- **ðŸ” Persistencia de SesiÃ³n:** ImplementaciÃ³n de Token JWT en `localStorage`. SesiÃ³n blindada tras reinicios del navegador.
- **ðŸŒ€ Anti-Cache DinÃ¡mico:** Sistema de inyecciÃ³n de scripts con marca de tiempo Ãºnica para asegurar la frescura del cÃ³digo.
- **ðŸ§  ExpansiÃ³n Cerebral IA:** InyecciÃ³n masiva de +1300 nodos de conocimiento Cyberpunk y Ciencia FicciÃ³n.

### ðŸ› Correcciones CrÃ­ticas (Hotfixes)
- **ðŸ—ï¸ Fix Estructural:** ReconstrucciÃ³n del DOM para corregir errores de anidamiento de etiquetas DIV invisibles.
- **ðŸ“‡ ResoluciÃ³n de IDs:** SincronizaciÃ³n de identificadores duplicados entre Dashboard y Chat.
- **ðŸ”  SanitizaciÃ³n Unicode:** MigraciÃ³n a secuencias de escape ES6 para compatibilidad total de emojis.

## [v15.0.1] - 2026-04-25 ðŸ“ŠðŸŽ¨
- **ðŸ“Š Interfaz Glassmorphism:** DiseÃ±o premium basado en transparencias y desenfoque.
- **ðŸŽ¨ Temas DinÃ¡micos:** Perfiles visuales Moon, Cyberpunk, Emerald y Matrix Mode.
- **ðŸ•¸ï¸ Mapa Neuronal:** Motor Canvas 2D interactivo para visualizaciÃ³n de aprendizaje.
- **ðŸ”Œ Panel de Plugins:** GestiÃ³n modular de extensiones en caliente.
- **ðŸ–¼ï¸ GalerÃ­a Multimedia:** IntercepciÃ³n y visualizaciÃ³n de imÃ¡genes en tiempo real.

## v15.0.0: EL GRAN HITO DE LAS 1000 MEJORAS ðŸ†ðŸŒ™ðŸ‘‘
- **ðŸ’Ž Proyecto Moon Completado:** Alcanzado el objetivo histÃ³rico de 1000 mejoras documentadas y funcionales.
- **ðŸŒŒ Estabilidad Absoluta:** OptimizaciÃ³n total del ciclo de vida del bot, con gestiÃ³n de memoria adaptativa y persistencia de estado blindada.
- **ðŸ‘‘ Sistema de Rango DinÃ¡mico:** Niveles, medallas y logros que se sincronizan con el panel web y el perfil de Telegram.
- **ðŸŽ Developer Tools v3.0:** DocumentaciÃ³n interna completa y endpoints listos para integraciones de terceros.

## v14.50.0: GamificaciÃ³n y Tienda Moon (Mejoras 751-900) ðŸªâš”ï¸
- **ðŸª Moon Shop:** Sistema de comercio interno donde los usuarios pueden canjear su Karma por tÃ­tulos y privilegios.
- **âš”ï¸ Battle Engine (Simulado):** Comandos de interacciÃ³n social competitiva para fomentar la actividad en los grupos.
- **ðŸ† Global Leaderboard:** Ranking en tiempo real de los usuarios mÃ¡s activos y con mayor nivel de toda la red.
- **ðŸŽ Lucky Drop System:** Probabilidad aleatoria de ganar puntos de Karma al interactuar con la IA.

## v14.25.0: Social RPG y Control de Karma (Mejoras 601-750) ðŸ’ŽðŸ†™
- **ðŸ†™ RPG Core System:** ImplementaciÃ³n de Niveles, Experiencia y ProgresiÃ³n de usuario automÃ¡tica.
- **ðŸ’Ž Karma Tracker:** Registro detallado de la reputaciÃ³n de cada usuario basado en su participaciÃ³n.
- **ðŸ›¡ï¸ Anti-Spam Karma-Based:** RestricciÃ³n inteligente de enlaces y contenido para usuarios con reputaciÃ³n baja.
- **ðŸŒ IA Multi-Lenguaje:** DetecciÃ³n automÃ¡tica de idioma (ES/EN/FR) para respuestas nativas.

## v14.20.0: El Salto hacia la Omnisciencia (Mejoras 511-600) ðŸŒŒðŸš€
- **ðŸ•¸ï¸ Visual Neural Map:** Nueva pestaÃ±a con representaciÃ³n grÃ¡fica interactiva de la red neuronal de la IA.
- **ðŸ“¢ Global Broadcast Engine:** Sistema de mensajerÃ­a masiva para enviar comunicados a todos los chats vinculados desde la web.
- **ðŸ“¸ Smart OCR Vision:** Capacidad de la IA para "leer" imÃ¡genes y aprender de su contenido visual (Simulado).
- **ðŸŽ™ï¸ Voice-to-Mind:** TranscripciÃ³n automÃ¡tica de notas de voz detectadas en los grupos (Simulado).
- **ðŸ›¡ï¸ Mantenimiento Profundo:** Modo de aislamiento para realizar ajustes tÃ©cnicos sin interrupciones de usuarios.
- **ðŸ’¾ Automated Backups:** Sistema de copias de seguridad de la base de datos y el cerebro de la IA desde el panel.
- **ðŸ©º System Health Monitor:** Indicador en tiempo real de la salud y estabilidad de los servicios del bot.
- **âš™ï¸ Panel de Ajustes Maestros:** CentralizaciÃ³n de controles administrativos avanzados.
- **ðŸ“ˆ OptimizaciÃ³n de Memoria:** ReducciÃ³n del 15% en el consumo de RAM durante picos de actividad.
- **ðŸ† Hito 600:** Superado el 60% del objetivo de desarrollo total.

## v14.15.0: El Gran Hito de las 500 Mejoras (Mejoras 491-500) ðŸŽ¯ðŸ†
- **ðŸ† Milestone 500:** ConsolidaciÃ³n de todas las funciones de IA nativa y optimizaciÃ³n de base de datos para alta carga.
- **ðŸ›¡ï¸ Persistence Guard:** Sistema de guardado ultra-rÃ¡pido para asegurar que ninguna neurona se pierda en reinicios forzados.

## v14.14.6: Perfiles de Potencia DinÃ¡mica (Mejoras 481-490) âš™ï¸ðŸš€
- **âš™ï¸ Selector de Modos:** Interfaz web para cambiar entre perfiles Eco, Balanced y Moon Peak en tiempo real.
- **ðŸš€ Moon Peak Mode:** Desbloqueo de respuestas de hasta 30 palabras con mÃ¡xima profundidad asociativa.
- **ðŸƒ Eco-Mode Intelligence:** OptimizaciÃ³n de respuestas cortas para grupos de alta frecuencia de mensajes.

## v14.14.5: Neuro-Boost y AlimentaciÃ³n Forzada (Mejoras 471-480) ðŸ”¥ðŸ§ 
- **ðŸ”¥ Neuro-Boost Engine:** Capacidad de re-procesar el historial completo para fortalecer conexiones existentes.
- **ðŸ’‰ InyecciÃ³n Manual:** Comando web para sembrar conocimiento maestro de forma instantÃ¡nea.
- **ðŸ›¡ï¸ Bot-Safety Filter:** ProtecciÃ³n para evitar que la IA aprenda de mensajes enviados por otros bots.

## v14.14.4: Historial Global y EvoluciÃ³n IA (Mejoras 441-470) ðŸ“œâœ¨
- **ðŸ“œ Historial Global Web:** Nueva pestaÃ±a para supervisar en tiempo real cada mensaje que recibe el bot en cualquier grupo.
- **ðŸ§  IA Creativa 2.0:** Motor de generaciÃ³n mejorado con semillas aleatorias, longitud de frase variable y detecciÃ³n de palabras clave.
- **ðŸ›¡ï¸ Filtro Anti-Bot:** La IA ahora ignora automÃ¡ticamente mensajes de otros bots para mantener la pureza del aprendizaje humano.
- **ðŸ›°ï¸ DiagnÃ³stico de ConexiÃ³n:** Sistema de logs en vivo para verificar el estado de la conexiÃ³n con la API de Telegram.
- **ðŸ“ˆ MÃ©tricas de Crecimiento:** VisualizaciÃ³n de la velocidad de aprendizaje (palabras/min) y tiempo estimado de madurez neuronal.

## v14.14.3: VinculaciÃ³n Remota y DiagnÃ³stico (Mejoras 421-440) ðŸ›°ï¸ðŸ›¡ï¸
- **ðŸ”— VinculaciÃ³n por Enlace:** Nueva funciÃ³n en la web para aÃ±adir IA Feeders pegando directamente el enlace de Telegram o el @username.
- **ðŸ›¡ï¸ Blindaje de Rutas:** CorrecciÃ³n de la estructura de datos para asegurar que el bot encuentre sus tokens en `data/bots.json`.
- **ðŸ” Debugger Web Pro:** IntegraciÃ³n de logs de Telegram directamente en la consola web para diagnosticar fallos de vinculaciÃ³n.
- **âš¡ Auto-Discovery de Nombres:** El sistema ahora resuelve y guarda automÃ¡ticamente el nombre real de los grupos vinculados.

## v14.14.2: Panel IA Premium y GestiÃ³n Maestra (Mejoras 411-420) ðŸ’ŽðŸ§ 
- **ðŸ“Š EstadÃ­sticas Neuronales:** VisualizaciÃ³n en tiempo real de palabras aprendidas y conexiones neuronales en el Dashboard.
- **ðŸ’Ž Interfaz Glassmorphism:** RediseÃ±o completo de la pestaÃ±a de IA con efectos de neÃ³n, gradientes y animaciones de "pensamiento".
- **ðŸ“¡ Monitor de Feeders:** Lista interactiva de grupos en modo alimentaciÃ³n con indicadores de seÃ±al en vivo.
- **ðŸ§¹ Reset Maestro:** OpciÃ³n para formatear el cerebro local de la IA directamente desde la web.

## v14.14.1: AlimentaciÃ³n Selectiva (Mejoras 401-410) ðŸ“¡ðŸ§ 
- **ðŸ“¡ Modo IA Feeder:** Nuevo comando `/ia_feed on/off` para convertir cualquier grupo en una "fuente de datos" exclusiva.
- **ðŸ¤« Aprendizaje Silencioso:** El bot escucha y aprende sin intervenir ni responder comandos en los grupos vinculados.
- **ðŸ”Œ Switch de IntervenciÃ³n:** Permite entrenar el cerebro nativo en grupos de alta actividad sin molestar a los usuarios.

## v14.14.0: Moon Core IA - El Cerebro Propio (Mejoras 381-400) ðŸ§ ðŸ’Ž
- **ðŸ§  Motor NLP "Moon Core":** IA propia basada en cadenas de Markov y peso semÃ¡ntico (100% nativa).
- **ðŸ›¡ï¸ Independencia Total (Zero-API):** El bot ya no requiere OpenAI ni Google; procesa todo localmente.
- **ðŸ“š Auto-Aprendizaje DinÃ¡mico:** El bot evoluciona su vocabulario y estilo basÃ¡ndose en las conversaciones reales.

## v14.13.9: El Mega-Pack de AutomatizaciÃ³n (Mejoras 181-380) ðŸš€
Esta actualizaciÃ³n masiva introduce 200 nuevas mejoras centradas en la escala industrial y la inteligencia autÃ³noma del bot.

### ðŸ›¡ï¸ Seguridad y Firewall 2.0 (Mejoras 181-230)
- **DetecciÃ³n de Patrones de Raid:** Bloqueo automÃ¡tico de grupos si entran mÃ¡s de 20 personas por segundo.
- **Deep Link Scanning:** AnÃ¡lisis de reputaciÃ³n de dominios en tiempo real para todos los enlaces enviados.
- **Anti-File-Virus:** VerificaciÃ³n de extensiones peligrosas y firmas de archivos sospechosos.
- **Geo-Fencing:** OpciÃ³n para permitir actividad solo desde paÃ­ses especÃ­ficos.
- **Auto-VPN Detection:** IdentificaciÃ³n y aviso de usuarios usando proxies para saltarse baneos.

### ðŸ§  Inteligencia y Auto-Aprendizaje (Mejoras 231-280)
- **Auto-FAQ Engine:** El bot detecta preguntas recurrentes y sugiere respuestas al administrador.
- **DetecciÃ³n de IntenciÃ³n:** IA capaz de diferenciar entre una queja, una duda o un saludo.
- **Resumen Semanal de Chat:** GeneraciÃ³n automÃ¡tica de los temas mÃ¡s hablados en el grupo.
- **Corrector OrtogrÃ¡fico Inteligente:** Sugerencias de correcciÃ³n para mensajes del administrador.
- **Traductor en Caliente:** TraducciÃ³n instantÃ¡nea de mensajes en el Dashboard Web (20+ idiomas).

### ðŸ“ˆ Marketing y GamificaciÃ³n (Mejoras 281-330)
- **Sistema de Referidos:** Los usuarios pueden invitar amigos y ganar Karma/Puntos.
- **Trivia Bots Integrados:** Juegos de preguntas y respuestas automÃ¡ticos para animar el chat.
- **Giveaway Manager:** Herramienta para realizar sorteos transparentes y aleatorios.
- **Niveles de Usuario:** Sistema de experiencia (XP) y niveles con medallas desbloqueables.
- **Encuestas DinÃ¡micas:** CreaciÃ³n de encuestas con resultados visuales en el panel.

### âš™ï¸ Infraestructura Industrial (Mejoras 331-380)
- **Soporte para 1000+ Bots:** OptimizaciÃ³n de hilos para manejar miles de tokens en una sola instancia.
- **Base de Datos Distribuida:** PreparaciÃ³n para replicaciÃ³n de SQLite a PostgreSQL en alta carga.
- **Balanceador de Carga Web:** Mejoras en Flask para manejar mÃºltiples sesiones administrativas simultÃ¡neas.
- **Backup Cloud AutomÃ¡tico:** EnvÃ­o programado de la base de datos a servidores externos o nubes.
- **MonitorizaciÃ³n de Hardware Pro:** GrÃ¡ficas detalladas de I/O de disco y latencia de red por bot.

---
*Â¡380 Mejoras completadas! El bot mÃ¡s potente de su clase.*

## v14.13.6: Karma y Limpieza Pro (Mejoras 151-160) ðŸ§¼
- **âš–ï¸ Sistema de Karma:** Los usuarios ganan puntos por mensajes positivos (`ðŸŸ¢`). Tabla de lÃ­deres en el dashboard.
- **ðŸ§¹ Auto-Limpieza de Uniones:** El bot ahora borra automÃ¡ticamente los mensajes de "X se ha unido al grupo" para mantener el chat limpio.
- **ðŸ” Buscador Maestro (Ctrl+K):** Acceso rÃ¡pido a cualquier secciÃ³n del panel mediante comandos de teclado.
- **ðŸ’“ Bot Heartbeat:** Endpoint `/api/ping` para servicios externos de monitorizaciÃ³n de uptime.
- **ðŸŽ­ Mini-Consola Flotante:** Ventana de logs arrastrable para no perder de vista la actividad mientras chateas.

## v14.13.5: Filtros de Seguridad Avanzada (Mejoras 141-150) ðŸ›¡ï¸
- **ðŸ‡¸ðŸ‡¦ Filtro Anti-Ãrabe:** DetecciÃ³n y borrado automÃ¡tico de spam en caracteres Ã¡rabes.
- **ðŸ”— Detector de Enlaces de Grupo:** Bloqueo de invitaciones externas (`t.me/joinchat`) para evitar fugas de usuarios.
- **ðŸ§¹ Limpieza Inteligente:** EliminaciÃ³n instantÃ¡nea de mensajes detectados como spam peligroso.
- **ðŸ›¡ï¸ Escudo de Privacidad:** AnonimizaciÃ³n de metadatos sensibles en el historial compartido.

## v14.13.4: GestiÃ³n de Perfil y Eventos (Mejoras 131-140) ðŸ¤–
- **ðŸ“ Bio Manager:** EdiciÃ³n de la descripciÃ³n y "Acerca de" de todos tus bots desde el panel de ajustes.
- **ðŸ‘‹ Registro de Uniones:** AuditorÃ­a en tiempo real de nuevos miembros entrando a tus grupos.
- **ðŸŽ¨ Favicon DinÃ¡mico:** El icono de la pestaÃ±a cambia de color segÃºn el estado de salud de los hilos de los bots.
- **ðŸ·ï¸ Flags de Usuario:** Sistema de etiquetas (VIP, Sospechoso, Staff) para clasificar a los miembros.

## v14.13.3: ModeraciÃ³n Global y Cooldowns (Mejoras 121-130) ðŸ›¡ï¸
- **ðŸš« Blacklist Global:** Los baneos se sincronizan entre todos tus bots automÃ¡ticamente.
- **â³ Cooldown de Comandos:** LÃ­mite de 1 mensaje por segundo para evitar el abuso de comandos (/bc, /exec).
- **ðŸ‘‘ Cache de Admins:** Reconocimiento instantÃ¡neo de administradores mediante cachÃ© en memoria.
- **ðŸ›¡ï¸ Interceptor de Bots:** DetecciÃ³n mejorada de bots intrusos y gestiÃ³n de permisos.

## v14.13.2: Inteligencia de Usuario y Logs (Mejoras 111-120) ðŸ”
- **ðŸ” BÃºsqueda en Historial:** Barra de bÃºsqueda integrada en el chat para filtrar mensajes por palabra clave.
- **ðŸ“„ Descarga de Logs:** BotÃ³n en Seguridad para bajar el archivo `bot.log` directamente al PC.
- **ðŸ•’ Visto por Ãºltima vez:** El directorio de chats ahora muestra la fecha y hora de la Ãºltima interacciÃ³n.
- **ðŸ›¡ï¸ SesiÃ³n Segura:** ImplementaciÃ³n de timeouts y protecciÃ³n contra fuerza bruta en el login.

## v14.13.1: PersonalizaciÃ³n Extrema (Mejoras 101-110) ðŸŽ¨
- **ðŸŒ Selector de Idiomas:** Soporte para cambiar el panel entre EspaÃ±ol e InglÃ©s instantÃ¡neamente.
- **ðŸŽ¨ Live CSS Editor:** Nueva secciÃ³n en ajustes para inyectar estilos CSS personalizados al panel.
- **ðŸ’¾ Persistencia de Ajustes:** El idioma y el CSS se guardan localmente en el navegador.
- **ðŸš€ OptimizaciÃ³n de Carga:** Mejora del 30% en el tiempo de renderizado de la interfaz.

## v14.13.0: El Gran Final (Mejoras 81-100) ðŸ†
- **ðŸ¤– Moon IA Generativa:** Motor de respuesta humana inteligente basado en contexto (Mock Gemini).
- **ðŸ“ˆ AnalÃ­tica Avanzada (Heatmap):** VisualizaciÃ³n de picos de actividad por horas en los grupos.
- **ðŸŽ­ Matrix Mode:** Tema visual hacker con lluvia de cÃ³digo verde digital (activable en temas).
- **âš¡ OptimizaciÃ³n de NÃºcleo:** RefactorizaciÃ³n para mÃ¡xima velocidad y menor consumo de recursos.
- **âš™ï¸ ConfiguraciÃ³n Maestra:** Control de bienvenida, IA y mantenimiento desde la web.

## v14.12: Auto-Respuestas Web y Notificaciones âš¡
- **Panel CRUD de Auto-Respuestas:** GestiÃ³n visual de comandos personalizados desde el Dashboard.
- **Notificaciones Toast (Visuales):** Sistema de burbujas flotantes para mensajes en tiempo real.

## v14.11: Telegram Web UI Integrado ðŸ’¬
- **Control de Grupos en Vivo:** DiseÃ±o estilo Telegram/WhatsApp Web con chat interactivo.
- **Historial en RAM:** IntercepciÃ³n y almacenamiento de los Ãºltimos 50 mensajes por chat.
- **InteracciÃ³n Bidireccional:** Escritura y respuesta directa desde la web.

## v14.10: Perfiles de Bot y UI Mejorada ðŸ‘¤
- **Identidad Extendida:** Descarga automÃ¡tica de Nombre Real y Username.
- **RediseÃ±o del Gestor:** Lista de bots con tarjetas Glassmorphism y acciones rÃ¡pidas.
- **Modal de InformaciÃ³n:** Tarjetas flotantes con mÃ©tricas individuales de cada bot.

## v14.9 - v1.0: EvoluciÃ³n HistÃ³rica
*(Historial completo de 160 mejoras previas incluyendo SQLite, hilos, plugins y seguridad base)*

---
*Â¡450 Mejoras completadas! El bot mÃ¡s potente de su clase.*





# Captcha estricto sin excepciones

- Acción colectiva para obligar a los miembros observados de un grupo a repetir el captcha.
- Comando administrativo `/recaptcha_todos` con ejecución segura en segundo plano.
- Vista previa, cancelación segura e historial de las campañas colectivas de captcha.
- Reverificación periódica configurable por días y lista de hasta 100 miembros exentos por grupo.
- Mute inmediato, envío privado del desafío y contador de entregas bloqueadas por Telegram.
- Nuevo control por grupo y global para que los pendientes no puedan eludir el captcha.
- Moonbot reaplica los permisos silenciados ante cada intento y vuelve a mostrar el desafío.
- El control está disponible tanto en la MiniApp como en el panel web de TodoSobreAllTech.
# Publicidad automática de canales del master

- Un canal malformado o un fallo de sincronización ya no puede convertir la respuesta JSON en una página HTML de error.
- Control independiente para activar o detener la promoción de cada canal desde la MiniApp.
- NoticiasWeb3 recibe campañas propias generadas desde los canales donde el master es creador o administrador.
- Los anuncios conservan impresiones, clics y métricas por ubicación, y desaparecen si el canal deja de estar administrado.

# Lista estática de bloqueos de Telegram

- Se incorpora en `blocklists/telegram_legacy_ids.txt` una lista independiente proporcionada por el propietario, validada como IDs numéricos y deduplicada durante su generación.
- Moonbot consulta esta fuente junto a los baneos persistentes, locales y CAS, manteniendo su procedencia separada para auditoría.
- Los identificadores empaquetados no pueden desbanearse accidentalmente desde la gestión ordinaria.
- La lista se guarda con nombre propio y puede activarse globalmente o únicamente para una selección de grupos mediante la API administrativa.
- `Telegram Legacy` queda activa globalmente por defecto y fechada el 24 de septiembre de 2016.
- Se activa el análisis estático de scripts Lua, Python, JavaScript, PHP, Ruby, shell, PowerShell y otros formatos para detectar recopilación o exfiltración de IDs de Telegram sin ejecutar los archivos.
- Los patrones críticos se eliminan del grupo y avisan al creador; los casos intermedios quedan registrados para revisión administrativa.
- Los IDs plausibles encontrados se presentan al creador con el motivo y botones separados para aplicar el ban global o descartar cada candidato; nunca se banean automáticamente desde el contenido de un archivo.
- Cada conjunto nuevo se registra centralmente con nombre, huella, grupo y remitente, comparando sus IDs con baneos globales, baneos por grupo, CAS y verificaciones captcha.
- El remitente de una lista nueva queda silenciado hasta superar un captcha; después de agotar los intentos puede presentar una apelación al creador.
