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

`compose.yml` permite desplegar una imagen ya verificada mediante
`MOON_GATEWAY_IMAGE` y `MOON_TDLIB_SECRET_FILE`. El archivo de credenciales debe
tener permisos 0600 y pertenecer al UID del usuario `telegram` de esa imagen;
mantener su directorio en el host con permisos 0700. No introducir credenciales
en el Compose ni en Git. Conectar únicamente los workers autorizados a la red
`moon-telegram` y conservar esa conexión en su Compose para los recreados.
El servicio no publica puertos en el host, conserva las sesiones en un volumen
y limita CPU, memoria, procesos y tamaño de logs. Su healthcheck verifica el
puerto local, no la autenticación ni la entrega de mensajes de cada bot.

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

Las pruebas de endpoints y migración validan selección por bot, rutas de archivos,
identidad y autenticación del diagnóstico. `TDLIB_COMPATIBILITY.json` es un
inventario estático de esta rama, no una certificación de todos los plugins.

Antes de ampliar la selección, verificar un bot de pruebas con identidad,
recepción real, respuesta, medios y reconexión. Esta incorporación a estable
no añade una cola distribuida ni escalado automático de bots gestionados.

Referencia: https://github.com/tdlib/telegram-bot-api
