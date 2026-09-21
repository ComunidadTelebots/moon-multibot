# Estado de migración a TDLib

La migración completa de bots y plugins **no está habilitada**. `MoonBot.run`
sigue recibiendo con `getUpdates`, y las llamadas de plugins conservan Bot API.
Una sesión TDLib lista no certifica que sus funciones estén adaptadas.

## Base implementada

- Un solo consumidor de `td_receive` por proceso, con reparto por `@client_id`.
  Las respuestas usan también `@extra`, sin cruzar cuentas aunque compartan el
  mismo identificador de petición. Las respuestas no esperan a los callbacks.
- Una cola de eventos por sesión conserva su orden, con límite de 4096 eventos.
  Desbordarla detiene esa sesión, registra el fallo y requiere revisión manual.
  No es una cola persistente: al detenerse o desbordarse puede haber eventos sin
  procesar que deben reconciliarse. No se garantiza entrega exactamente una vez.
- Una parada intencionada no dispara el reinicio del watchdog.
- `/api/telemetry/tdlib-migration`, protegido por el JWT existente, publica
  preparación, biblioteca cargada, sesiones listas, eventos, cola y desbordamientos.
  No publica credenciales, contenido ni perfiles de usuario.
- `python tools/audit_tdlib_compatibility.py` genera el inventario estático.
  Guardar su salida en `TDLIB_COMPATIBILITY.json` tras cambiar llamadas o plugins.
  Las llamadas dinámicas, HTTP directo y plugins externos requieren revisión.

## Pendiente antes de migrar

1. Adaptar eventos de TDLib al contrato que consumen los plugins, incluyendo IDs,
   usuarios, chats, medios, callbacks y eventos administrativos.
2. Traducir peticiones y respuestas de cada método utilizado. La coincidencia de
   nombres no basta. Conservar errores y límites, y no repetir un envío por HTTP
   después de un timeout ambiguo de TDLib.
3. Separar sesiones receptoras y procesamiento distribuido con cola persistente,
   orden por chat, recuperación y control de efectos duplicados.
4. Probar un bot de pruebas con API ID/hash configurados y biblioteca TDLib,
   incluyendo recepción, respuesta, plugins, reconexión y parada de workers.
5. Migrar por bot solo después de validar las funciones que realmente utiliza.

Las pruebas automatizadas de esta entrega utilizan clientes simulados; no
certifican una sesión real ni todos los plugins. La copia local señalada por el
usuario no se modifica ni se inicia como parte del inventario.

Referencia: https://github.com/tdlib/td/blob/master/td/telegram/td_json_client.h

## Comprobación con biblioteca real

`tools/tdlib-smoke.Dockerfile` construye una imagen mínima, sin arrancar Moonbot.
Montar el archivo de configuración en `/run/secrets/tdlib.env` en solo lectura.
Por defecto se ejecuta sin red: dos clientes consultan la versión y verifican
que sus respuestas lleguen al cliente correcto, y ambos confirman el cierre.
Validado localmente con TDLib 1.8.64. Esto no valida credenciales ni plugins.

Para una prueba autenticada, configurar `TDLIB_TEST_BOT_TOKEN` en el archivo
local y ejecutar `python tdlib_smoke.py --bot NOMBRE_DEL_BOT` con red. Solo se usa
ese token; se confirma el nombre mediante getMe antes de autenticar por TDLib.
No lee el almacén de bots ni envía mensajes. Las sesiones son temporales. El
registro nativo se desactiva antes de iniciar clientes para evitar que escriba
parámetros de autenticación. No incluir el archivo de configuración en imágenes,
commits ni argumentos que contengan valores de credenciales.

## Validación local del 22 de septiembre de 2026

Con TDLib 1.8.64 en un contenedor temporal:

- Dos clientes sin red: 32 consultas concurrentes `getOption(version)` con
  correlación de cliente/petición correcta y sin peticiones pendientes al finalizar.
- `@Ctbapptestbot`: autenticación real y verificación de identidad con `getMe`.
- Parada y reapertura de la sesión temporal, conservando la identidad del bot.
- Recepción real de `/tdlib_probe` a través de `updateNewMessage` y el callback
  opcional `on_update`. No se registraron remitente, chat ni contenido.
- Cierre confirmado con `authorizationStateClosed`. Cero mensajes enviados.

Repetir la prueba con `--restart` verifica reapertura; `--receive` espera hasta
180 segundos el mensaje de prueba, sin contestarlo. No afirmar entrega sin
duplicados, recuperación de red ni recuperación tras caída abrupta basándose en
este reinicio limpio. Tampoco valida plugins, moderación, envío multimedia o
distribución entre Docker. Estos flujos siguen pendientes de adaptar e integrar.

## Prueba del gateway y del plugin (22 de septiembre de 2026)

Se verificó la identidad de @Ctbapptestbot en el servidor oficial local y cuatro
contratos de lectura. El comando privado /calculadora 2+2 atravesó el gateway
sobre TDLib, la cola SQLite y el plugin existente de calculadora. Telegram
confirmó una respuesta «Resultado: 4». La cola terminó con una tarea completada,
sin tareas pendientes ni inciertas. No se migraron los demás bots.

La ruta para conservar el contrato de los plugins está documentada en
`deploy/telegram-gateway/README.md`. Esta prueba no certifica todos los plugins:
el bucle principal de Moonbot todavía no consume la cola persistente.
