# Auditoría conservadora de dependencias

Fecha: 2026-07-30. Alcance: `requirements.txt`, imports Python, Dockerfile,
scripts de arranque, binarios y Compose. Esta auditoría no autoriza retiradas.

## Python

Con uso directo demostrado: `requests`, `psutil`, `flask`, `PyJWT` (`jwt`),
`python-dotenv`, `cryptography`, `openai`, `tzdata` (datos de `zoneinfo`),
`scikit-learn`, `textblob`, `paramiko`, `pytesseract`, `Pillow`, `waitress`,
`langdetect` y `ftfy`. Las evidencias principales están en `moon_multibot.py`,
`core/`, `plugins/`, `token_manager.py` y `voice_transcription_service.py`.

Sin uso importable demostrado en el árbol actual: `speechrecognition` y
`gunicorn`. No se eliminan: pueden ser compatibilidad de despliegues o plugins
externos. Las dependencias instaladas por las anteriores son transitivas y no
deben copiarse manualmente a `requirements.txt`.

`pip check` informa que el entorno de auditoría no tiene requisitos rotos. Esto
no certifica la imagen porque el archivo no fija versiones ni hashes. Sin una
imagen construida no es posible asignar CVE concretos de forma fiable: cada
reconstrucción puede resolver versiones diferentes. Debe generarse primero un
lock probado y después auditar ese lock y la imagen; no se fijan versiones a
ciegas.

## APT y binarios

- `curl`: descarga TDLib, healthcheck y doctor.
- `git`: comprobación/actualización opcional desde `start.sh` y el bot.
- `tesseract-ocr` y español: OCR real mediante `pytesseract`.
- `libssl3` y `zlib1g`: runtime nativo de TDLib/criptografía.
- `gcc`: dependencia de compilación de emergencia cuando no existe wheel. Su
  retirada requiere demostrar wheels para todas las plataformas objetivo.
- `/usr/local/lib/libtdjson.so`: usado por `ctypes`; se copia localmente o se
  descarga de GitHub. Falta verificación SHA-256 del binario descargado.

APT pierde la capa cuando cambia la imagen base o cualquier instrucción previa,
cuando se poda BuildKit o se usa otro builder. Además `apt-get update` siempre
consulta metadatos. Antes, `apt-get clean` y la regla `docker-clean` eliminaban
los `.deb` del caché montado. El Dockerfile ahora usa IDs estables, conserva
índices/paquetes fuera de la imagen y comprueba los binarios críticos.

## Compose y riesgos operativos

- `ollama/ollama:latest` no es reproducible y el entrypoint ejecuta `ollama
  pull` en cada creación; explica esperas y tráfico. Debe fijarse una imagen y
  separar la descarga del modelo, pero solo tras inventariar el modelo existente.
- El bind `.:/app` oculta el código copiado en la imagen. Es intencionado para el
  flujo actual, pero mezcla despliegue inmutable y actualización desde Git.
- El contenedor no declara usuario, por lo que arranca como root.
- `AUTO_DOCKER_UPDATE=true` amplía el comportamiento operativo, aunque Docker no
  está montado explícitamente en este Compose.

## Riesgos que requieren una tarea funcional separada

1. `plugins/moderation_advanced.py` carga `data/spam_model.pkl` con `pickle`:
   un archivo manipulable puede ejecutar código al deserializarse.
2. `ProxyManager` usa `paramiko.AutoAddPolicy`, que acepta una clave SSH nueva
   sin verificación previa y permite un ataque de intermediario.
3. TDLib descargada no tiene checksum obligatorio.
4. Requisitos e imágenes sin pin impiden reproducibilidad y una conclusión CVE
   estable.

## Interfaces específicas aún pendientes

Continúan dependiendo del editor genérico: restauración por punto temporal,
reconciliación de caché, rotación segura, observabilidad distribuida, controles
de calidad específicos por esquema y varias familias antiguas de alertas/ruteo.
Cada una necesita formulario derivado de su firma real; no se debe inferir un
payload común. No se modificó `web/hub.html`.
