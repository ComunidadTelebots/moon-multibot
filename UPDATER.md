# Actualizador unificado

El actualizador conserva los `.env`, datos y volúmenes existentes. Nunca carga un
`.env` como script ni muestra sus valores.

## Preparación

```bash
chmod 600 /root/moonbot/.env /root/mtproto-proxy/.env
cd /root/moonbot
bash start.sh update check
```

Las imágenes de `mtproxy-1`, `mtproxy-2` y `mtproxy-3` deben estar fijadas en el
Compose mediante `imagen@sha256:digest`. Cada servicio debe tener un secret y un
puerto publicado diferentes.

Si MTProxy está en otra ruta:

```bash
MTPROTO_PROJECT_DIR=/ruta/del/proyecto bash start.sh update check
```

## Modos

```bash
bash start.sh update all       # Moonbot y los tres MTProxy
bash start.sh update moonbot   # dependencias, imagen y contenedor Moonbot
bash start.sh update proxies   # mtproxy-1, mtproxy-2 y mtproxy-3
bash start.sh update check     # solo preflight; no modifica nada
```

El modo Moonbot reconstruye la imagen, por lo que instala todas las librerías de
`requirements.txt` y del `Dockerfile`. Ollama queda fuera de todos los modos.

Por defecto se actualizan repositorios Git limpios y verificados. Si el proyecto
MTProxy es una configuración local sin repositorio, se puede omitir Git de forma
explícita y seguir validando Compose e imágenes:

```bash
UPDATE_GIT=false bash start.sh update proxies
```

El actualizador nunca ejecuta `down -v`, no elimina volúmenes y se detiene ante
ramas divergentes, archivos locales, servicios adicionales o contenedores sin
salud.
