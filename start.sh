#!/bin/bash
echo "======================================"
echo "    🌙 MOON MULTIBOT CORE v16.31.0   "
echo "    Premium Dashboard & Automation    "
echo "======================================"

# Detectar comando Python
if command -v python3 &>/dev/null; then
    PY_CMD="python3"
elif command -v python &>/dev/null; then
    PY_CMD="python"
else
    echo "❌ ERROR FATAL: Python no está instalado en el sistema."
    exit 1
fi

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
        $PY_CMD migrate_ia.py
    fi

    echo "✅ Proceso de migración finalizado."
}

# 🆕 Gestión de tokens encriptados
function manage_tokens() {
    echo ""
    echo "======================================"
    echo "   🔐 GESTOR DE TOKENS ENCRIPTADOS    "
    echo "======================================"
    echo ""
    echo "1. Agregar un nuevo token"
    echo "2. Listar tokens actuales"
    echo "3. Cifrar tokens (Migración)"
    echo "4. Ver estado de encriptación"
    echo "5. Salir"
    echo ""
    read -p "Selecciona una opción (1-5): " option

    case $option in
        1)
            add_token
            ;;
        2)
            list_tokens
            ;;
        3)
            encrypt_tokens
            ;;
        4)
            check_encryption_status
            ;;
        5)
            return 0
            ;;
        *)
            echo "❌ Opción no válida"
            manage_tokens
            ;;
    esac
}

# Agregar nuevo token
function add_token() {
    echo ""
    echo "📝 AGREGAR NUEVO TOKEN DE BOT"
    echo "=============================="
    read -p "Ingresa el token del bot: " token

    if [ -z "$token" ]; then
        echo "❌ El token no puede estar vacío"
        return 1
    fi

    # Agregar a bots.json
    if [ ! -f "data/bots.json" ]; then
        echo "[]" > data/bots.json
    fi

    # Usar Python para manipular JSON de forma segura
    $PY_CMD << PYTHON_EOF
import json
import os

token = "$token"

# Leer archivo actual
with open("data/bots.json", "r") as f:
    bots = json.load(f)

# Buscar si el token ya existe
if any(b.get("token") == token for b in bots):
    print("⚠️  El token ya existe en la configuración")
else:
    # Agregar nuevo bot
    bots.append({"token": token})

    # Guardar
    with open("data/bots.json", "w") as f:
        json.dump(bots, f, indent=4)

    print(f"✅ Token agregado exitosamente. Total de bots: {len(bots)}")
PYTHON_EOF

    echo ""
    read -p "¿Deseas agregar otro token? (s/n): " cont
    if [ "$cont" = "s" ] || [ "$cont" = "S" ]; then
        add_token
    fi
}

# Listar tokens actuales
function list_tokens() {
    echo ""
    echo "📋 TOKENS DE BOTS ACTUALES"
    echo "==========================="

    if [ ! -f "data/bots.json" ]; then
        echo "❌ No se encontró data/bots.json"
        return 1
    fi

    $PY_CMD << PYTHON_EOF
import json

with open("data/bots.json", "r") as f:
    bots = json.load(f)

if not bots:
    print("❌ No hay bots configurados")
else:
    print(f"✅ Total de bots: {len(bots)}\n")
    for i, bot in enumerate(bots, 1):
        token = bot.get("token", "N/A")
        encrypted = bot.get("encrypted", False)
        status = "🔒 ENCRIPTADO" if encrypted else "⚠️  PLAIN TEXT"
        # Mostrar primeros 20 caracteres del token
        token_preview = token[:20] + "..." if len(token) > 20 else token
        print(f"{i}. {token_preview} [{status}]")
PYTHON_EOF

    echo ""
}

# Cifrar tokens
function encrypt_tokens() {
    echo ""
    echo "🔐 CIFRAR TOKENS DE BOTS"
    echo "========================="

    if [ ! -f "migrate_bots_encryption.py" ]; then
        echo "❌ Script de migración no encontrado (migrate_bots_encryption.py)"
        return 1
    fi

    read -p "⚠️  IMPORTANTE: Guarda la CIPHER_KEY que se generará. ¿Continuar? (s/n): " confirm
    if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
        echo "Operación cancelada"
        return 1
    fi

    echo ""
    $PY_CMD migrate_bots_encryption.py

    echo ""
    echo "📌 PRÓXIMOS PASOS:"
    echo "1. Copia la CIPHER_KEY mostrada arriba"
    echo "2. Abre el archivo .env"
    echo "3. Agrega: CIPHER_KEY=<tu_clave_aqui>"
    echo "4. Guarda y reinicia el bot"
    echo ""
}

# Verificar estado de encriptación
function check_encryption_status() {
    echo ""
    echo "🔍 ESTADO DE ENCRIPTACIÓN"
    echo "========================="

    $PY_CMD << PYTHON_EOF
import json
import os

# Verificar .env
has_env = os.path.exists(".env")
has_cipher = False

if has_env:
    with open(".env", "r") as f:
        content = f.read()
        has_cipher = "CIPHER_KEY=" in content and "CIPHER_KEY=" not in content.split("CIPHER_KEY=")[1].startswith("#")

print(f"Archivo .env: {'✅ EXISTE' if has_env else '❌ NO EXISTE'}")
print(f"CIPHER_KEY configurada: {'✅ SÍ' if has_cipher else '⚠️  NO'}")

# Verificar bots.json
if os.path.exists("data/bots.json"):
    with open("data/bots.json", "r") as f:
        bots = json.load(f)

    if bots:
        encrypted_count = sum(1 for b in bots if b.get("encrypted", False))
        total = len(bots)
        print(f"\nBots cifrados: {encrypted_count}/{total}")

        if encrypted_count == total and has_cipher:
            print("\n✅ SISTEMA COMPLETAMENTE ENCRIPTADO")
        elif encrypted_count == total and not has_cipher:
            print("\n⚠️  TOKENS CIFRADOS PERO CIPHER_KEY NO CONFIGURADA")
            print("   El bot no podrá desencriptar los tokens. Añade CIPHER_KEY al .env")
        elif encrypted_count > 0 and encrypted_count < total:
            print("\n⚠️  ENCRIPTACIÓN PARCIAL")
            print("   Ejecuta 'bash start.sh tokens' y selecciona opción 3 para completar")
        else:
            print("\n⚠️  TOKENS EN PLAIN TEXT")
            print("   Tu sistema NO está encriptado. Considera ejecutar la migración")
PYTHON_EOF

    echo ""
}

function set_env_value() {
    local key="$1"
    local value="$2"
    MOON_ENV_KEY="$key" MOON_ENV_VALUE="$value" $PY_CMD << PYTHON_EOF
import os
from pathlib import Path

key = os.environ["MOON_ENV_KEY"]
value = os.environ["MOON_ENV_VALUE"]
env_path = Path(".env")
lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
updated = False
for i, line in enumerate(lines):
    raw = line.strip()
    if raw.startswith(f"{key}=") or raw.startswith(f"# {key}=") or raw.startswith(f"#{key}="):
        lines[i] = f"{key}={value}"
        updated = True
        break
if not updated:
    if lines and lines[-1].strip():
        lines.append("")
    lines.append(f"{key}={value}")
env_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
PYTHON_EOF
}

function generate_mtproto_secret() {
    $PY_CMD << PYTHON_EOF
import secrets
print(secrets.token_hex(16))
PYTHON_EOF
}

function show_mtproto_config() {
    $PY_CMD << PYTHON_EOF
from pathlib import Path

env = {}
if Path(".env").exists():
    for line in Path(".env").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()

def mask(value):
    if not value:
        return "NO CONFIGURADO"
    parts = [p.strip() for p in value.split(",") if p.strip()]
    return ", ".join((p[:6] + "..." + p[-4:]) if len(p) > 12 else "***" for p in parts)

print("")
print("CONFIGURACION LOCAL MTPROTO")
print("===========================")
print(f"PROXY_PORT: {env.get('PROXY_PORT', 'NO CONFIGURADO')}")
print(f"PROXY_SECRET: {mask(env.get('PROXY_SECRET', ''))}")
print(f"PROXY_LOCAL_PORTS: {env.get('PROXY_LOCAL_PORTS', 'NO CONFIGURADO')}")
print(f"PROXY_LOCAL_SECRETS: {mask(env.get('PROXY_LOCAL_SECRETS', ''))}")
PYTHON_EOF
}

function configure_mtproto_secrets() {
    echo ""
    echo "======================================"
    echo "   GESTOR LOCAL DE SECRETOS MTPROTO   "
    echo "======================================"
    echo ""
    echo "1. Introducir un secret existente"
    echo "2. Generar un secret nuevo"
    echo "3. Introducir varios secrets existentes"
    echo "4. Ver configuracion actual (oculta secrets)"
    echo "5. Salir"
    echo ""
    read -p "Selecciona una opcion (1-5): " option

    case $option in
        1)
            read -p "Puerto MTProto (ej. 8443): " proxy_port
            read -s -p "Secret MTProto existente (hex): " proxy_secret
            echo ""
            if [ -z "$proxy_port" ] || [ -z "$proxy_secret" ]; then
                echo "ERROR: puerto y secret son obligatorios."
                return 1
            fi
            set_env_value "PROXY_PORT" "$proxy_port"
            set_env_value "PROXY_SECRET" "$proxy_secret"
            echo "OK: secret principal guardado en .env local."
            ;;
        2)
            read -p "Puerto MTProto para el nuevo secret (ej. 8443): " proxy_port
            if [ -z "$proxy_port" ]; then
                echo "ERROR: el puerto es obligatorio."
                return 1
            fi
            proxy_secret=$(generate_mtproto_secret)
            set_env_value "PROXY_PORT" "$proxy_port"
            set_env_value "PROXY_SECRET" "$proxy_secret"
            echo "OK: secret nuevo generado y guardado en .env local."
            echo "Secret generado: $proxy_secret"
            ;;
        3)
            read -p "Puertos separados por coma (ej. 8443,8444,8445): " proxy_ports
            read -s -p "Secrets separados por coma y en el mismo orden: " proxy_secrets
            echo ""
            if [ -z "$proxy_ports" ] || [ -z "$proxy_secrets" ]; then
                echo "ERROR: puertos y secrets son obligatorios."
                return 1
            fi
            set_env_value "PROXY_LOCAL_PORTS" "$proxy_ports"
            set_env_value "PROXY_LOCAL_SECRETS" "$proxy_secrets"
            echo "OK: lista de secrets MTProto guardada en .env local."
            ;;
        4)
            show_mtproto_config
            ;;
        5)
            return 0
            ;;
        *)
            echo "Opcion no valida."
            ;;
    esac
}

# 1. Instalación automática de dependencias si se solicita
if [ "$1" == "setup" ]; then
    echo "📦 Iniciando configuración completa..."
    run_migration
    echo ""
    echo "📦 Instalando dependencias..."
    pip install -r requirements.txt
    echo "✅ Instalación y migración completadas."
    exit 0
fi

# 🆕 Gestión de tokens
if [ "$1" == "tokens" ]; then
    manage_tokens
    exit 0
fi

if [ "$1" == "mtproto" ]; then
    configure_mtproto_secrets
    exit 0
fi

if [ "$1" == "doctor" ]; then
    echo "🩺 Iniciando Diagnóstico de Salud (Doctor Mode)..."
    echo "------------------------------------------------"

    # 1. Comprobar Python
    echo "✅ Python detectado: $($PY_CMD --version)"

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

    # 5. Comprobar encriptación
    echo "🔍 Verificando encriptación de tokens..."
    $PY_CMD << PYTHON_EOF
import json
import os

if os.path.exists("data/bots.json"):
    with open("data/bots.json", "r") as f:
        bots = json.load(f)
    encrypted = sum(1 for b in bots if b.get("encrypted", False))
    if encrypted > 0:
        print(f"✅ Tokens encriptados: {encrypted}/{len(bots)}")
    else:
        print("⚠️  ADVERTENCIA: Tokens en plain text (ejecuta 'bash start.sh tokens')")
PYTHON_EOF

    # 6. Comprobar librerías críticas
    echo "⏳ Verificando librerías requeridas..."
    $PY_CMD -c "import requests, psutil, sqlite3, flask, jwt, dotenv, cryptography, paramiko" &>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ Todas las librerías críticas están instaladas (incluyendo Cryptography)."
    else
        echo "❌ ERROR: Faltan librerías. Por favor ejecuta: bash start.sh setup"
        exit 1
    fi

    # 7. Comprobar Docker
    if command -v docker &>/dev/null; then
        echo "✅ Docker detectado. Escáner de Proxies activado."
    else
        echo "⚠️  ADVERTENCIA: Docker no detectado. El escáner de red en el Dashboard no funcionará."
    fi

    # 8. Comprobar Internet y API
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

# 2. Comprobación de actualizaciones de Git (Opcional)
if command -v git &>/dev/null; then
    echo "🚀 Comprobando actualizaciones en GitHub..."
    git fetch origin master &>/dev/null
    BEHIND=$(git status -uno | grep "Your branch is behind")
    if [ ! -z "$BEHIND" ]; then
        if [ "${AUTO_DOCKER_UPDATE:-true}" = "true" ]; then
            echo "Auto-update: nueva version detectada. Aplicando git pull..."
            git pull origin master
            echo "Auto-update: actualizacion aplicada."
        else
            echo "Nueva version detectada. Ejecuta bash start.sh update para actualizar."
        fi
    else
        echo "✅ El sistema está al día."
    fi
fi

if [ "$1" == "update" ]; then
    echo "🔄 Actualizando desde el repositorio oficial..."
    git pull origin master
    echo "✅ Sistema actualizado. Reiniciando..."
    exit 0
fi

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
