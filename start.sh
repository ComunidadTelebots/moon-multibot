#!/bin/bash
echo "======================================"
echo "    🌙 MOON MULTIBOT CORE v16.14.0   "
echo "    Premium Dashboard & Automation    "
echo "======================================"

# 0. Migración e Importación de datos antiguos
function run_migration() {
    echo "🔍 Buscando datos de versiones anteriores..."
    mkdir -p data
    
    # Migrar tokens de archivos antiguos
    if [ -f "config.json" ] && [ ! -f "data/bots.json" ]; then
        echo "📦 Importando tokens desde config.json antiguo..."
        cp config.json data/bots.json
        mv config.json config.json.bak
    fi
    
    if [ -f "tokens.txt" ] && [ ! -f "data/bots.json" ]; then
        echo "📦 Detectado tokens.txt. Convirtiendo a formato JSON..."
        TOKEN=$(cat tokens.txt | tr -d '\r')
        echo "[\"$TOKEN\"]" > data/bots.json
        mv tokens.txt tokens.txt.bak
    fi

    # Migrar bases de datos antiguas
    if [ -f "moon_database.db" ] && [ ! -f "data/moon_database.db" ]; then
        echo "🗄️ Migrando base de datos al nuevo directorio..."
        mv moon_database.db data/moon_database.db
    fi

    # Detectar plugins antiguos
    if [ -d "old_plugins" ]; then
        echo "🔌 Importando plugins heredados..."
        cp -r old_plugins/* plugins/ 2>/dev/null
    fi
    
    # Migrar datos generados por la IA (Cerebro y Conocimiento)
    if [ -f "migrate_ia.py" ]; then
        echo "🧠 Ejecutando transferencia de inteligencia IA..."
        if command -v python3 &>/dev/null; then
            python3 migrate_ia.py
        else
            python migrate_ia.py
        fi
    fi
    
    echo "✅ Proceso de migración finalizado."
}

# 1. Instalación automática de dependencias si se solicita
if [ "$1" == "setup" ]; then
    echo "📦 Iniciando configuración completa..."
    run_migration
    pip install -r requirements.txt
    echo "✅ Instalación y migración completadas."
    exit 0
fi

if [ "$1" == "doctor" ]; then
    echo "🩺 Iniciando Diagnóstico de Salud (Doctor Mode)..."
    echo "------------------------------------------------"
    
    # 1. Comprobar Python
    if command -v python3 &>/dev/null; then
        echo "✅ Python 3 detectado: $(python3 --version)"
        PY_CMD="python3"
    elif command -v python &>/dev/null; then
        echo "✅ Python detectado: $(python --version)"
        PY_CMD="python"
    else
        echo "❌ ERROR FATAL: Python no está instalado en el sistema."
        exit 1
    fi
    
    # 2. Entorno Virtual
    if [ -d "venv" ]; then
        echo "✅ Entorno virtual (venv) encontrado."
    else
        echo "⚠️  ADVERTENCIA: No se encontró la carpeta 'venv'. El bot usará librerías globales."
    fi
    
    # 3. Base de datos y Cerebro
    if [ -f "data/moon_database.db" ]; then
        echo "✅ Base de datos SQLite encontrada."
    else
        echo "⚠️  ADVERTENCIA: No se encontró 'moon_database.db' (Cerebro vacío)."
    fi
    
    # 4. Configuración de Bots
    if [ -f "data/bots.json" ]; then
        echo "✅ Archivo de tokens bots.json detectado."
    else
        echo "❌ ERROR: Falta 'data/bots.json'. El bot no podrá conectarse a Telegram."
        exit 1
    fi
    
    # 5. Comprobar librerías críticas (Actualizado para i18n y Business)
    echo "⏳ Verificando librerías requeridas..."
    $PY_CMD -c "import requests, psutil, sqlite3, flask, jwt, dotenv, cryptography" &>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Todas las librerías críticas están instaladas (incluyendo Cryptography para Proxies)."
    else
        echo "❌ ERROR: Faltan librerías. Por favor ejecuta: bash start.sh setup"
        exit 1
    fi
    
    # 6. Comprobar Docker (Para el nuevo Proxy Manager)
    if command -v docker &>/dev/null; then
        echo "✅ Docker detectado. Escáner de Proxies activado."
    else
        echo "⚠️  ADVERTENCIA: Docker no detectado. El escáner de red en el Dashboard no funcionará."
    fi

    # 7. Comprobar Internet y API
    echo "⏳ Verificando conexión a la API de Telegram..."
    curl -s https://api.telegram.org > /dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Conexión a Internet y a Telegram: OK."
    else
        echo "❌ ERROR: No hay conexión a Internet o Telegram está bloqueado en tu red."
        exit 1
    fi

    echo "------------------------------------------------"
    echo "🎉 DIAGNÓSTICO COMPLETADO: El Servidor está Saludable y listo para operar."
    exit 0
fi

# Buscar y activar entorno virtual si existe
if [ -d "venv" ]; then
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    fi
fi

# Ejecutar migración automática antes de arrancar
run_migration

# Bucle infinito para auto-reiniciar el bot
while true; do
    echo "[*] Lanzando Moon Multibot..."
    if command -v python3 &>/dev/null; then
        python3 moon_multibot.py
    else
        python moon_multibot.py
    fi
    
    echo "[!] El bot se ha cerrado inesperadamente."
    echo "[!] Reiniciando en 5 segundos... (Presiona Ctrl+C para cancelar)"
    sleep 5
done
