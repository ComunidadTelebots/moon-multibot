# Gobernador de bots en estable

Implementación optativa. No activada ni certificada en producción.

MOON_GOVERNOR_PATH habilita una carpeta local persistente dedicada: una cola SQLite y un ejecutor de plugins por bot. Sin esa variable se mantiene el procesamiento síncrono. Los nuevos bots iniciados desde el registro existente reciben su ejecutor automáticamente. Esto no crea identidades nuevas en Telegram.

La recepción guarda cada actualización antes de avanzar el checkpoint. La cola deduplica entregas repetidas y admite hasta 10.000 tareas por bot. Si está llena, no avanza el checkpoint. Una excepción durante el procesamiento deja la tarea como incierta y bloquea las siguientes de ese bot, evitando reenviar automáticamente una respuesta que pudo haberse entregado. Requiere reconciliación manual.

Se conserva el cuerpo completo del procesamiento de plugins, comprobado mediante comparación del AST. Plugins y mantenimiento se ejecutan de forma serializada por bot porque comparten estado mutable. Diferentes bots pueden avanzar simultáneamente, como procesos lógicos separados. Un bloqueo de archivo impide dos receptores para ese bot usando la misma carpeta; no coordina servidores ni volúmenes distintos.

El receptor TDLib compartido importado de dev enruta por client_id y separa las respuestas de los callbacks. No migra por sí solo los bots que usan Bot API. La pasarela oficial local sigue siendo la vía de compatibilidad prevista para conservar los plugins.

La telemetría autenticada de migración incluye governor con su estado, alcance single_process y estadísticas agregadas de cola. No publica tokens ni mensajes.

Pendiente: elección de gobernador de respaldo entre servidores, varios ejecutores paralelos para un mismo bot, interfaz para reconciliar trabajos inciertos y flujo completo de creación administrada de bots con confirmación en Telegram. No hay autoescalado ni creación automática de identidades.

Antes de activarlo en los bots principales hay que validar el recorrido con un bot aislado, reinicios y plugins reales. Para desactivarlo se debe drenar o reconciliar primero la cola; deshabilitarlo con pendientes permitiría que nuevas entregas pasaran por delante. No se debe borrar la cola como método de recuperación.
