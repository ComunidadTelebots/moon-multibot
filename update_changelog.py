import codecs

with codecs.open("CHANGELOG.md", "r", "utf-8") as f:
    lines = f.readlines()

new_changelog = """# Changelog - Moon Multibot

## [v18.26.0-alpha] - 2026-08-19 (Fusión Arquitectónica de Interfaces)

**Refactorización Completa del Hub (Diseño Todo-en-Uno)**
* Se ha unificado toda la evolución histórica del diseño web en un solo archivo inmaculado (`hub.html`).
* **Selector de Apariencia (Arquitectura):** Se ha añadido un menú para alternar en tiempo real entre 4 estructuras UI diferentes sin perder funcionalidades:
  - 🚀 **Alfa Definitivo (Aurora)**: El motor actual Cyberpunk con pestañas.
  - ✨ **New Hub**: El diseño moderno de transiciones sin pestañas.
  - ✅ **Clásico Estable**: El diseño oficial de tarjetas largas (de la rama master).
  - 📺 **Clásico Puro**: La maqueta original e inalterada de tarjetas apiladas.
* **Separación de Temas:** El selector de "Tema de Color" ahora es independiente de la estructura de la web, recuperando los **Temas Nativos Apple iOS (Día/Noche)** y **Android Material 3 (Día/Noche)**.
* **Sincronización Multi-Rama:** Se absorbieron todos los arreglos crudos y parches estabilizados de la rama `master` (arreglos en el simulador 3D, bugs de WebApp y enrutador inteligente) directamente en la rama `alfa`.
* **Corrección de Codificación (Encoding):** Reparación quirúrgica de tildes y eñes perdidas (`Diseño`, `Añadir`, `Clásico`) usando diccionarios directos, garantizando que el DOM y el motor Javascript permanecen intactos sin generar caracteres nulos (UTF-16).

""" + "".join(lines[1:])

with codecs.open("CHANGELOG.md", "w", "utf-8") as f:
    f.write(new_changelog)

print("Changelog updated")
