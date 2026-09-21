# Servidor oficial Bot API sobre TDLib

Este contenedor mantiene el contrato HTTP de los plugins de Moonbot y ejecuta
TDLib dentro del servidor oficial. No es un proxy MTProto ni distribuye por sí
solo las tareas de Moonbot entre workers.

Se compila desde `tdlib/telegram-bot-api`, revisión
`e3e9dd8e5b3d7ab8537cd5a10dc31d5ffa8f82d1`, con su submódulo TDLib fijado. No se
activa `--local`: las descargas conservan rutas HTTP relativas, sin requerir que
los workers lean el sistema de archivos del servidor.

Montar un archivo de secretos en `/run/secrets/tdlib.env`, solo lectura, con
`TDLIB_API_ID` y `TDLIB_API_HASH`, y un volumen persistente local en
`/var/lib/telegram-bot-api`. No publicar el puerto 8081 en Internet. El servidor
se ejecuta como usuario sin privilegios. Usar red Docker privada; cualquier
acceso remoto requiere TLS y autenticación adicional.

En Moonbot configurar `MOON_BOT_API_URL=http://telegram-gateway:8081` y
`MOON_LOCAL_BOT_IDS` con los identificadores numéricos de los bots seleccionados,
separados por comas. Un valor vacío conserva todos en la nube. `*` selecciona
todos, y solo debe usarse después de completar la migración de cada bot.
Las sesiones TDLib nativas por bot no se inician cuando ese bot usa el gateway.
El userbot independiente no cambia. Los identificadores de telemetría y pausa
se conservan al cambiar el origen HTTP.

Antes de mover un bot, detener su receptor anterior, comprobar el servidor nuevo
y ejecutar `logOut` en el servidor anterior según la documentación oficial.
No ejecutar dos receptores `getUpdates` para el mismo bot. Esta integración no
realiza migraciones masivas automáticamente ni añade fallback entre servidores.

## Pruebas y compatibilidad

`tools/gateway_smoke.py` solo usa `TDLIB_TEST_BOT_TOKEN`, verifica el nombre
esperado y permite migrar únicamente ese bot mediante `--migrate`. La opción
`--plugin-test` espera `/calculadora 2+2` en privado, lo guarda en la cola
persistente y ejecuta el plugin de calculadora existente. El envío de prueba
usa un solo intento para evitar duplicarlo ante un timeout ambiguo.

`BOT_API_GATEWAY_COMPATIBILITY.json` registra la comparación estática con el
registro de métodos del servidor oficial. No es una certificación de todos los
plugins: falta revisar las llamadas dinámicas y los efectos de cada función.

## Cola persistente experimental

`core/persistent_inbox.py` ofrece deduplicación, orden por partición/chat,
reservas de trabajo, pausa de workers, reasignación de reservas que no han
empezado y contadores sin contenido. Usa SQLite WAL con transacciones FULL y
debe residir en un volumen local compartido del mismo host, nunca NFS/SMB.

Límites: 10.000 trabajos no finalizados, 256 KiB por payload, reservas de hasta
300 segundos y ejecución de hasta 3.600 segundos. Los payloads completados se
vacían lógicamente; las claves de deduplicación se conservan hasta que se ejecute
`prune_completed` (siete días por defecto). Los backups y páginas del archivo
requieren la política de almacenamiento correspondiente.

Las tareas cuya ejecución caduca quedan `uncertain`: no se repiten solas porque
ya podrían haber enviado mensajes o modificado permisos. Requieren reconciliar
los efectos. Una pausa solo reasigna reservas sin iniciar; deja terminar las
tareas en curso. No se promete ejecución exactamente una vez.

Configurar `MOON_INBOX_PATH` permite consultar sus estadísticas desde el panel
Moonbot/Todosobrealltech. **El bucle principal de Moonbot aún no usa esta cola.**
La prueba de calculadora es una integración acotada. Antes de distribuir todos
los plugins hay que separar el estado mutable de `MoonBot`, la configuración y
los efectos de los plugins entre procesos; compartir solo una cola no lo resuelve.

Referencia: https://github.com/tdlib/telegram-bot-api
