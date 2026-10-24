# Moon Multibot - AI Powered Telegram Ecosystem

Moon Multibot es un ecosistema de gestion de Telegram para operar varios bots a la vez, con panel web, memoria contextual, moderacion y utilidades de seguridad.

## Caracteristicas principales

- Dashboard web con telemetria en tiempo real.
- Motor hibrido de IA con memoria contextual y fuentes RAG.
- Proteccion anti-spam, auditoria y gestion de baneos.
- Analiticas de actividad y recursos del sistema.
- Sistema de plugins con carga dinamica.
- Almacenamiento cifrado de tokens de bots mediante `CIPHER_KEY`.

## Instalacion rapida

1. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Crea tu configuracion:
   ```bash
   cp .env.example .env
   ```

3. Ajusta como minimo estas variables:
   ```env
   WEB_PASSWORD=una_contrasena_segura
   JWT_SECRET=un_secreto_largo_y_aleatorio
   MASTER_ID=123456789
   CIPHER_KEY=
   ```

   Si `CIPHER_KEY` esta vacia, la primera ejecucion generara una clave. Copiala al `.env` antes de volver a arrancar para poder descifrar los tokens ya guardados.

4. Inicia el nucleo:
   ```bash
   python moon_multibot.py
   ```

## Docker

```bash
docker compose up --build
```

El panel escucha en el puerto `5000` en produccion y `5001` en modo `dev`.

## Telegram Serverless

El registro de proyectos esta en `config/serverless_bots.json`. La imagen Docker
incluye el CLI oficial y el panel permite consultar metricas, sincronizar,
desplegar cambios, migrar el esquema y actualizar el webhook.

Cada servidor debe vincular una vez cada proyecto; las credenciales quedan en
`.tgcloud/` y nunca se guardan en Git:

```bash
docker compose exec moonbot sh -lc 'cd /app/cintiaandrea_bot && tgcloud login'
```

Tras vincularlo, abre **Panel > Bots > Telegram Serverless**. La accion
**Enviar parche** publica solo los cambios locales que detecte `tgcloud`.

La Mini App de AndreaBot se divide en tres espacios:

- `/`: web publica con acceso al bot, demostracion interactiva y condiciones de servicio.
- `/manage.html`: gestion de grupos para usuarios autenticados desde Telegram.
- `/panel.html`: estadisticas administrativas protegidas por el ID master.

La gestion de grupos comprueba en tiempo real que el usuario sea creador o
administrador antes de mostrar o modificar la bienvenida, el anti-flood y las
normas. El bot abre esta Mini App desde el comando `/panel` y desde su boton de
menu `Mis grupos`.

### Puente Moonbot ↔ Telegram Serverless

Moonbot puede recibir telemetria y mensajes recientes por HTTPS, y ejecutar
acciones remotas auditadas sin guardar el token del bot. En **Panel > Bots >
Telegram Serverless**, pulsa **Conectar directo** una vez. La clave del puente
se deriva de `JWT_SECRET`, es diferente para cada bot y se transfiere mediante
la sesion autenticada de `tgcloud`.

El control remoto solo permite enviar o responder mensajes y borrar mensajes.
No acepta comandos de sistema ni codigo arbitrario. Para produccion configura:

```env
SERVERLESS_BRIDGE_PUBLIC_URL=https://cintiabot.todosobreall.tech
```

## Seguridad

- No publiques `data/bots.json`, `.env` ni backups que contengan tokens.
- Usa valores fuertes para `WEB_PASSWORD`, `JWT_SECRET` y `CIPHER_KEY`.
- El panel devuelve identificadores publicos y previews de token, no tokens completos.
