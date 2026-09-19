# Recuperación del Hub

El Hub actual usa Original como tema predeterminado y conserva las preferencias guardadas. NoticiasWeb3 se abre en el lector integrado, con ampliación dentro del Hub.

Los diseños históricos se restauran desde d1290bd en web/hub-estable.html, web/hub-new.html y web/hub-clasico.html, convertidos a UTF-8. El selector los abre como documentos separados y permite volver al Hub sin perder su estado.

sources/hub-before-layout-repair.html.txt conserva íntegro el archivo previo a esta reparación, incluidos los bloques históricos anidados que rompían JavaScript. Es un archivo de archivo, no una página ejecutable. No se eliminan los diseños antiguos.

Validación: node tests/test_hub_documents.cjs y node tests/test_hub_news_navigation.cjs. Comprobación de navegador del Hub completo, noticias y los tres diseños con respuestas API de ejemplo; no valida servicios de producción ni el envío real por Telegram.
