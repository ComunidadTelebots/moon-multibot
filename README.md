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

## Seguridad

- No publiques `data/bots.json`, `.env` ni backups que contengan tokens.
- Usa valores fuertes para `WEB_PASSWORD`, `JWT_SECRET` y `CIPHER_KEY`.
- El panel devuelve identificadores publicos y previews de token, no tokens completos.
