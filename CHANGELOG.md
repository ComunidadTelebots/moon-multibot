# Changelog - Moon Multibot

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
- Los datos de proxies vienen de la API `mtproto-proxies` (geoip-lite, `country`/`ll`, `connStats`).

### Fix - Separación de permisos (admin de grupo ≠ dueño del bot)
- El rango `Admin` de `get_user_rank` proviene de `getChatAdministrators` (admin del **grupo** de Telegram), no del dueño del bot. Se han pasado a **solo Master** las acciones globales/sensibles que estaban expuestas a cualquier admin de grupo: `/gban` y `/ungban` (ban/indulto global), `/ia_programar` e `/ia_feed` (entrenan/alimentan la IA compartida) y los comandos de datos de proxies (`/estado`, `/historico`, `/pendientes`) más la aprobación de proxies.
- La moderación **del propio grupo** (`/ban`, `/unban`, `/mute`, `/unmute`, `/warn`, `/resumen`) se mantiene para admins de grupo.
- Verificado: `/listen`, `/backup_db` y `/resync` ya eran solo Master.

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
- Mute inmediato, envío privado del desafío y contador de entregas bloqueadas por Telegram.
- Nuevo control por grupo y global para que los pendientes no puedan eludir el captcha.
- Moonbot reaplica los permisos silenciados ante cada intento y vuelve a mostrar el desafío.
- El control está disponible tanto en la MiniApp como en el panel web de TodoSobreAllTech.
