#!/usr/bin/env bash
# Actualizador seguro de Moonbot y las tres instancias MTProxy.
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MOONBOT_PROJECT_DIR="${MOONBOT_PROJECT_DIR:-$SCRIPT_DIR}"
MTPROTO_PROJECT_DIR="${MTPROTO_PROJECT_DIR:-/root/mtproto-proxy}"
MOONBOT_ENV_FILE="${MOONBOT_ENV_FILE:-$MOONBOT_PROJECT_DIR/.env}"
MTPROTO_ENV_FILE="${MTPROTO_ENV_FILE:-$MTPROTO_PROJECT_DIR/.env}"
UPDATE_MODE="${1:-all}"
UPDATE_GIT="${UPDATE_GIT:-true}"
LOCK_FILE="${MOONBOT_UPDATE_LOCK:-/tmp/moonbot-system-update.lock}"
MTPROTO_GIT_BRANCH="${MTPROTO_GIT_BRANCH:-master}"
ROLLBACK_PROJECT=""
ROLLBACK_ENV=""
ROLLBACK_COMPOSE=""
ROLLBACK_OVERRIDE=""
ROLLBACK_SERVICES=""

log() { printf '[updater] %s\n' "$*"; }
rollback_active_component() {
    [ -n "$ROLLBACK_OVERRIDE" ] || return 0
    log "restaurando el componente anterior tras un fallo"
    local -a rollback=(docker compose --project-directory "$ROLLBACK_PROJECT" --env-file "$ROLLBACK_ENV" -f "$ROLLBACK_COMPOSE" -f "$ROLLBACK_OVERRIDE")
    # shellcheck disable=SC2086
    "${rollback[@]}" up -d --no-deps $ROLLBACK_SERVICES || \
        printf '[updater] CRITICO: el rollback automático falló; revisa los contenedores\n' >&2
    ROLLBACK_OVERRIDE=""
}
fail() {
    printf '[updater] ERROR: %s\n' "$*" >&2
    rollback_active_component
    exit 1
}
require_command() { command -v "$1" >/dev/null 2>&1 || fail "falta el comando $1"; }

cleanup() {
    [ -z "$ROLLBACK_COMPOSE" ] || rm -f -- "$ROLLBACK_COMPOSE"
    [ -z "$ROLLBACK_OVERRIDE" ] || rm -f -- "$ROLLBACK_OVERRIDE"
}
trap cleanup EXIT
on_error() {
    local status=$?
    trap - ERR
    rollback_active_component
    exit "$status"
}
trap on_error ERR

case "$UPDATE_MODE" in
    all|moonbot|proxies|check) ;;
    *) fail "modo no válido: $UPDATE_MODE (all|moonbot|proxies|check)" ;;
esac

require_command docker
docker compose version >/dev/null 2>&1 || fail "Docker Compose v2 no está disponible"
require_command flock
case "$UPDATE_GIT" in true|false) ;; *) fail "UPDATE_GIT debe ser true o false" ;; esac
exec 9>"$LOCK_FILE"
flock -n 9 || fail "ya hay otra actualización en curso"

compose_file() {
    local project_dir="$1"
    local candidate
    for candidate in compose.yml compose.yaml docker-compose.yml docker-compose.yaml; do
        if [ -f "$project_dir/$candidate" ]; then
            printf '%s\n' "$project_dir/$candidate"
            return 0
        fi
    done
    return 1
}

validate_env_file() {
    local env_file="$1"
    [ -f "$env_file" ] || fail "no existe $env_file; se conserva la configuración y no se genera otra automáticamente"
    [ ! -L "$env_file" ] || fail "$env_file no puede ser un enlace simbólico"
    [ -r "$env_file" ] || fail "no se puede leer $env_file"
    if command -v stat >/dev/null 2>&1; then
        local mode
        mode="$(stat -c '%a' "$env_file" 2>/dev/null || true)"
        if [ -n "$mode" ] && [ "$mode" != "600" ] && [ "$mode" != "640" ]; then
            fail "$env_file debe tener permisos 600 o 640 (actual: $mode)"
        fi
    fi
}

require_env_keys() {
    local env_file="$1"; shift
    local key
    for key in "$@"; do
        awk -F= -v wanted="$key" '
            /^[[:space:]]*#/ { next }
            $1 ~ "^[[:space:]]*" wanted "[[:space:]]*$" {
                value=$0; sub(/^[^=]*=/, "", value)
                if (value !~ /^[[:space:]]*$/) found=1
            }
            END { exit(found ? 0 : 1) }
        ' "$env_file" || fail "$key no está configurada en $env_file"
    done
}

safe_git_update() {
    local project_dir="$1" allowed_repository="$2" expected_branch="$3"
    [ "$UPDATE_GIT" = "true" ] || { log "Git omitido para $project_dir"; return 0; }
    require_command git
    git -C "$project_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1 || \
        fail "$project_dir debe ser un repositorio Git verificable"
    if [ -n "$(git -C "$project_dir" status --porcelain --untracked-files=normal)" ]; then
        fail "$project_dir tiene cambios o archivos nuevos sin guardar; no se actualiza"
    fi
    local remote
    remote="$(git -C "$project_dir" remote get-url origin)"
    case "$remote" in
        "https://github.com/$allowed_repository"|"https://github.com/$allowed_repository.git"|"git@github.com:$allowed_repository"|"git@github.com:$allowed_repository.git") ;;
        *) fail "origin no coincide con el repositorio permitido $allowed_repository" ;;
    esac
    local branch
    branch="$(git -C "$project_dir" branch --show-current)"
    [ "$branch" = "$expected_branch" ] || fail "$project_dir debe estar en la rama $expected_branch (actual: ${branch:-detached})"
    git -C "$project_dir" fetch --prune origin "$branch"
    local fetched_sha
    fetched_sha="$(git -C "$project_dir" rev-parse --verify FETCH_HEAD)"
    git -C "$project_dir" merge-base --is-ancestor HEAD "$fetched_sha" || \
        fail "$project_dir divergió del commit remoto $fetched_sha"
    git -C "$project_dir" merge --ff-only "$fetched_sha"
}

verify_services_running() {
    local compose_name="$1"; shift
    local service container state health
    local -a compose=("$@")
    for service in $compose_name; do
        container="$("${compose[@]}" ps -q "$service")"
        [ -n "$container" ] || fail "$service no creó ningún contenedor"
        state="$(docker inspect --format '{{.State.Status}}' "$container")"
        health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "$container")"
        [ "$state" = "running" ] || fail "$service no está en ejecución ($state)"
        if [ "$health" != "none" ]; then
            local waited=0
            while [ "$health" = "starting" ] && [ "$waited" -lt 60 ]; do
                sleep 2; waited=$((waited + 2))
                health="$(docker inspect --format '{{.State.Health.Status}}' "$container")"
            done
            [ "$health" = "healthy" ] || fail "$service no está saludable ($health)"
        fi
    done
}

prepare_component_rollback() {
    local project="$1" env_file="$2" compose_file_path="$3"; shift 3
    local -a compose=(docker compose --project-directory "$project" --env-file "$env_file" -f "$compose_file_path")
    local override service container image_id
    override="$(mktemp)"
    chmod 600 "$override"
    printf 'services:\n' > "$override"
    for service in "$@"; do
        container="$("${compose[@]}" ps -q "$service")"
        [ -n "$container" ] || { rm -f -- "$override"; fail "no existe contenedor previo para rollback: $service"; }
        image_id="$(docker inspect --format '{{.Image}}' "$container")"
        [ -n "$image_id" ] || { rm -f -- "$override"; fail "no se obtuvo la imagen previa de $service"; }
        printf '  %s:\n    image: "%s"\n' "$service" "$image_id" >> "$override"
    done
    ROLLBACK_PROJECT="$project"
    ROLLBACK_ENV="$env_file"
    ROLLBACK_COMPOSE="$compose_file_path"
    ROLLBACK_OVERRIDE="$override"
    ROLLBACK_SERVICES="$*"
}

complete_component_update() {
    [ -z "$ROLLBACK_OVERRIDE" ] || rm -f -- "$ROLLBACK_OVERRIDE"
    ROLLBACK_OVERRIDE=""
    ROLLBACK_SERVICES=""
}

preflight_moonbot() {
    local file
    file="$(compose_file "$MOONBOT_PROJECT_DIR")" || fail "no se encontró Compose de Moonbot"
    validate_env_file "$MOONBOT_ENV_FILE"
    require_env_keys "$MOONBOT_ENV_FILE" WEB_PASSWORD JWT_SECRET MASTER_ID
    docker compose --project-directory "$MOONBOT_PROJECT_DIR" --env-file "$MOONBOT_ENV_FILE" -f "$file" config --quiet
    docker compose --project-directory "$MOONBOT_PROJECT_DIR" --env-file "$MOONBOT_ENV_FILE" -f "$file" config --format json | \
        python3 "$SCRIPT_DIR/tools/validate_compose_policy.py" --kind moonbot
}

preflight_proxies() {
    local file services service
    file="$(compose_file "$MTPROTO_PROJECT_DIR")" || fail "no se encontró Compose MTProxy"
    validate_env_file "$MTPROTO_ENV_FILE"
    local -a compose=(docker compose --project-directory "$MTPROTO_PROJECT_DIR" --env-file "$MTPROTO_ENV_FILE" -f "$file")
    "${compose[@]}" config --quiet
    "${compose[@]}" config --format json | python3 "$SCRIPT_DIR/tools/validate_compose_policy.py" --kind proxies
    services="$("${compose[@]}" config --services)"
    for service in mtproxy-1 mtproxy-2 mtproxy-3; do
        printf '%s\n' "$services" | grep -Fxq "$service" || fail "falta el servicio $service"
    done
    if printf '%s\n' "$services" | grep -E '^mtproxy-' | grep -Ev '^mtproxy-[123]$' >/dev/null; then
        fail "el Compose contiene instancias MTProxy adicionales"
    fi
}

moonbot_compose() {
    local file previous_compose
    file="$(compose_file "$MOONBOT_PROJECT_DIR")" || fail "no se encontró Compose de Moonbot"
    validate_env_file "$MOONBOT_ENV_FILE"
    require_env_keys "$MOONBOT_ENV_FILE" WEB_PASSWORD JWT_SECRET MASTER_ID
    local -a compose=(docker compose --project-directory "$MOONBOT_PROJECT_DIR" --env-file "$MOONBOT_ENV_FILE" -f "$file")
    previous_compose="$(mktemp)"; chmod 600 "$previous_compose"; cp -- "$file" "$previous_compose"
    ROLLBACK_COMPOSE="$previous_compose"
    safe_git_update "$MOONBOT_PROJECT_DIR" "ComunidadTelebots/moon-multibot" "master"
    file="$(compose_file "$MOONBOT_PROJECT_DIR")" || fail "Compose de Moonbot desapareció tras actualizar"
    compose=(docker compose --project-directory "$MOONBOT_PROJECT_DIR" --env-file "$MOONBOT_ENV_FILE" -f "$file")
    "${compose[@]}" config --quiet
    "${compose[@]}" config --format json | python3 "$SCRIPT_DIR/tools/validate_compose_policy.py" --kind moonbot
    [ "$UPDATE_MODE" = "check" ] && return 0
    # Reconstruir instala requirements y librerías del Dockerfile. Ollama queda fuera.
    DOCKER_BUILDKIT=1 "${compose[@]}" build moonbot
    prepare_component_rollback "$MOONBOT_PROJECT_DIR" "$MOONBOT_ENV_FILE" "$previous_compose" moonbot
    "${compose[@]}" up -d --no-deps --pull never moonbot
    verify_services_running "moonbot" "${compose[@]}"
    complete_component_update
    rm -f -- "$previous_compose"
    "${compose[@]}" ps moonbot
}

proxy_compose() {
    local file previous_compose
    file="$(compose_file "$MTPROTO_PROJECT_DIR")" || fail "no se encontró Compose de MTProxy en $MTPROTO_PROJECT_DIR"
    validate_env_file "$MTPROTO_ENV_FILE"
    local -a compose=(docker compose --project-directory "$MTPROTO_PROJECT_DIR" --env-file "$MTPROTO_ENV_FILE" -f "$file")
    previous_compose="$(mktemp)"; chmod 600 "$previous_compose"; cp -- "$file" "$previous_compose"
    ROLLBACK_COMPOSE="$previous_compose"
    safe_git_update "$MTPROTO_PROJECT_DIR" "ComunidadTelebots/mtproto-proxy" "$MTPROTO_GIT_BRANCH"
    file="$(compose_file "$MTPROTO_PROJECT_DIR")" || fail "Compose MTProxy desapareció tras actualizar"
    compose=(docker compose --project-directory "$MTPROTO_PROJECT_DIR" --env-file "$MTPROTO_ENV_FILE" -f "$file")
    "${compose[@]}" config --quiet
    "${compose[@]}" config --format json | python3 "$SCRIPT_DIR/tools/validate_compose_policy.py" --kind proxies
    local services service
    services="$("${compose[@]}" config --services)"
    local -a proxies=()
    for service in mtproxy-1 mtproxy-2 mtproxy-3; do
        printf '%s\n' "$services" | grep -Fxq "$service" || fail "falta el servicio $service en el Compose MTProxy"
        proxies+=("$service")
    done
    if printf '%s\n' "$services" | grep -E '^mtproxy-' | grep -Ev '^mtproxy-[123]$' >/dev/null; then
        fail "el Compose contiene instancias MTProxy adicionales; revisa el alcance antes de actualizar"
    fi
    [ "$UPDATE_MODE" = "check" ] && return 0
    # Se actualizan exactamente los tres proxies; no se eliminan volúmenes ni otros servicios.
    "${compose[@]}" pull --ignore-buildable "${proxies[@]}"
    prepare_component_rollback "$MTPROTO_PROJECT_DIR" "$MTPROTO_ENV_FILE" "$previous_compose" "${proxies[@]}"
    "${compose[@]}" up -d --no-deps "${proxies[@]}"
    verify_services_running "${proxies[*]}" "${compose[@]}"
    complete_component_update
    rm -f -- "$previous_compose"
    "${compose[@]}" ps "${proxies[@]}"
}

case "$UPDATE_MODE" in
    moonbot) preflight_moonbot; moonbot_compose ;;
    proxies) preflight_proxies; proxy_compose ;;
    all) preflight_moonbot; preflight_proxies; moonbot_compose; proxy_compose ;;
    check) preflight_moonbot; preflight_proxies; log "configuración válida; no se aplicaron cambios" ;;
esac

log "actualización completada"
