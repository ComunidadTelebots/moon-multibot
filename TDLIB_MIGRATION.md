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
