# Selector master de interfaces del Hub

El selector verifica el rol mediante tg_auth y muestra canal, versión declarada y commit.
La estable implementada se registra separada de master y de las etiquetas Git.
El cambio afecta a la interfaz de la sesión, no al backend, los tokens ni los Docker.
Las funciones de ramas recientes pueden requerir un backend más reciente.

Generar snapshots con tools/build_hub_versions.py indicando --repo, --output,
--stable y --backend-version. El catálogo fija cada commit; no descarga código en
cada visita. Publicar el directorio generado en web/hub-releases, el selector JS
en web/hub-version-switcher.js y la candidata estable en web/hub.html, tras respaldo.
Añadir el script con data-hub-version="stable-deployed" a futuras interfaces estables.

El exportador valida JavaScript y recursos locales. Retira el antiguo selector
layouts anidado en las ramas afectadas antes de validarlas, y lo registra en el
catálogo; las copias resultantes no se presentan como archivos idénticos al original.
Los refs sin Hub no se ofrecen. No se normalizan versiones declaradas inconsistentes:
el nombre de la rama y el número de versión se muestran por separado.

Comprobación: node --test tests/hub_version_switcher.test.cjs.
