#!/usr/bin/env bash
# Generic deploy script (local or SSH)
# Usage: ./deploy.sh [git|up|down|destroy|logs|app-logs|status|deploy|help] [options]
# Requires: bash 4+, git, docker (or docker-compose), optional: ssh

set -euo pipefail

# -----------------------------
# Tiny flat-YAML parser (top-level "key: value" only, no nesting)
# -----------------------------
CONFIG_FILE="$(dirname "$0")/deploy_config.yml"
[[ -f "$CONFIG_FILE" ]] || CONFIG_FILE="$(dirname "$0")/deploy_config.yaml"
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "[ERROR] Missing deploy_config.yml. Copy deploy_config.yml.example and edit it."
  exit 1
fi

# Read simple "key: value" pairs into env vars (UPPERCASE keys)
while IFS= read -r line; do
  # strip comments
  line="${line%%#*}"
  [[ -z "${line// }" ]] && continue
  if [[ "$line" =~ ^[[:space:]]*([A-Za-z0-9_]+)[[:space:]]*:[[:space:]]*(.*)$ ]]; then
    k="${BASH_REMATCH[1]}"
    v="${BASH_REMATCH[2]}"
    # strip surrounding quotes & trailing spaces
    v="${v%\"}"; v="${v#\"}"
    v="${v%\'}"; v="${v#\'}"
    v="$(echo -n "$v" | sed 's/[[:space:]]*$//')"
    declare -g "$(echo "$k" | tr '[:lower:]-' '[:upper:]_')"="$v"
  fi
done < "$CONFIG_FILE"

# -----------------------------
# Defaults & derived values
# -----------------------------
PROJECT_NAME="${PROJECT_NAME:-project}"
DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
REMOTE_HOST="${REMOTE_HOST:-}"                # empty → local mode
SSH_CMD="${SSH_CMD:-ssh}"
REMOTE_PATH="${REMOTE_PATH:-/srv/$PROJECT_NAME}"
MOUNTED_PATH="${MOUNTED_PATH:-}"              # optional local path mount; preferred for git
COMPOSE_WORKDIR="${COMPOSE_WORKDIR:-.}"       # relative to REMOTE_PATH (or local cwd if local)
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"

DOCKER_CMD="${DOCKER_CMD:-docker}"            # or full path to docker
COMPOSE_SUBCMD="${COMPOSE_SUBCMD:-compose}"   # set to empty ("") to use docker-compose binary
# Build the compose command string
if [[ -z "${COMPOSE_SUBCMD}" ]]; then
  COMPOSE_BIN="${DOCKER_CMD}"                 # user set DOCKER_CMD to docker-compose, if desired
  COMPOSE_ARGS=()
  if [[ "$DOCKER_CMD" != *"docker-compose"* ]]; then
    # fallback search
    if command -v docker-compose >/dev/null 2>&1; then
      COMPOSE_BIN="docker-compose"
    else
      echo "[ERROR] COMPOSE_SUBCMD is empty but no 'docker-compose' found. Set DOCKER_CMD or COMPOSE_SUBCMD."
      exit 1
    fi
  fi
else
  COMPOSE_BIN="${DOCKER_CMD}"
  COMPOSE_ARGS=( "${COMPOSE_SUBCMD}" )
fi

GIT_ORIGIN_URL="${GIT_ORIGIN_URL:-}"          # empty → infer from current repo on 'git' command
LOG_VOLUME_SUFFIX="${LOG_VOLUME_SUFFIX:-log_data}" # app-logs uses ${PROJECT_NAME}_${LOG_VOLUME_SUFFIX}
CONFIRM_DESTROY="${CONFIRM_DESTROY:-true}"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $*"; }

# -----------------------------
# Helpers
# -----------------------------
_is_remote() {
  [[ -n "$REMOTE_HOST" ]]
}

# Execute a command either locally or over SSH, inside compose workdir
# Usage: _run_compose <args...>   (will cd into COMPOSE_WORKDIR first)
_run_compose() {
  local in_cd="cd \"$COMPOSE_WORKDIR\" &&"
  local cmd=("$COMPOSE_BIN" "${COMPOSE_ARGS[@]}" "$@")
  if _is_remote; then
    $SSH_CMD "$REMOTE_HOST" "cd \"$REMOTE_PATH\" && $in_cd ${cmd[*]}"
  else
    ( cd "$REMOTE_PATH"; cd "$COMPOSE_WORKDIR"; "${cmd[@]}" )
  fi
}

# Run arbitrary command at REMOTE_PATH (or local)
_run_at_project() {
  local cmd="$*"
  if _is_remote; then
    $SSH_CMD "$REMOTE_HOST" "cd \"$REMOTE_PATH\" && $cmd"
  else
    ( cd "$REMOTE_PATH"; eval "$cmd" )
  fi
}

# -----------------------------
# Git deploy (clone/update)
# -----------------------------
deploy_via_git() {
  local branch="${1:-$DEFAULT_BRANCH}"
  local start_time=$(date +%s)

  # Prefer MOUNTED_PATH for clone/update if it exists or is set.
  local target_path="$REMOTE_PATH"
  local mode="remote"
  if [[ -n "$MOUNTED_PATH" ]]; then
    target_path="$MOUNTED_PATH"
    mode="mounted"
  fi

  log_info "Git deploy → branch '${branch}' → target: $target_path (${mode})"

  # Warn about unpushed commits if current repo matches branch
  if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    local current_branch
    current_branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")"
    if [[ "$current_branch" == "$branch" ]]; then
      local ahead_count
      ahead_count="$(git rev-list --count @{upstream}..HEAD 2>/dev/null || echo "0")"
      if [[ "$ahead_count" -gt 0 ]]; then
        log_warn "You have $ahead_count unpushed commit(s) on '$branch'. They won't be deployed."
        git log --oneline @{upstream}..HEAD || true
        read -r -p "Continue anyway? (y/N): " ans
        [[ "${ans:-N}" =~ ^[Yy]$ ]] || { log_info "Cancelled."; exit 0; }
      fi
    fi
  fi

  # Determine origin URL
  local origin="$GIT_ORIGIN_URL"
  if [[ -z "$origin" ]]; then
    origin="$(git config --get remote.origin.url 2>/dev/null || true)"
    if [[ -z "$origin" ]]; then
      log_error "No GIT_ORIGIN_URL configured and not in a git repo. Set GIT_ORIGIN_URL in deploy_config.yml."
      exit 1
    fi
  fi

  # Ensure parent dir exists
  if [[ "$mode" == "mounted" ]]; then
    mkdir -p "$(dirname "$target_path")"
  else
    $SSH_CMD "$REMOTE_HOST" "mkdir -p \"$(dirname "$target_path")\""
  fi

  # Clone or update
  if [[ "$mode" == "mounted" ]]; then
    if [[ ! -d "$target_path/.git" ]]; then
      log_info "Cloning → $origin"
      git clone "$origin" "$target_path"
    else
      log_info "Updating existing repo..."
      ( cd "$target_path"
        git fetch origin
        git checkout -f "$branch"
        git reset --hard "origin/$branch"
        git clean -fd
      )
    fi
  else
    # remote mode via ssh
    if ! $SSH_CMD "$REMOTE_HOST" "[ -d \"$target_path/.git\" ]"; then
      log_info "Cloning (remote) → $origin"
      $SSH_CMD "$REMOTE_HOST" "git clone \"$origin\" \"$target_path\""
    else
      log_info "Updating existing repo (remote)..."
      $SSH_CMD "$REMOTE_HOST" "cd \"$target_path\" && git fetch origin && git checkout -f \"$branch\" && git reset --hard \"origin/$branch\" && git clean -fd"
    fi
  fi

  local duration=$(( $(date +%s) - start_time ))
  log_success "Git deploy OK (branch: $branch) in ${duration}s"
}

# -----------------------------
# Compose actions
# -----------------------------
docker_up() {
  local build=""
  local clean=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --build) build="--build"; shift;;
      --clean) clean="true"; shift;;
      *) shift;;
    esac
  done

  if [[ -n "$clean" ]]; then
    log_info "compose down before up (clean)..."
    _run_compose down || true
  fi

  if [[ -n "$build" ]]; then
    log_info "compose up (rebuild)..."
    _run_compose up -d --build
  else
    log_info "compose up..."
    _run_compose up -d
  fi
  log_success "Containers started."
  show_status
}

docker_down() {
  log_info "compose down..."
  _run_compose down
  log_success "Containers stopped."
}

docker_destroy() {
  if [[ "${CONFIRM_DESTROY,,}" == "true" ]]; then
    read -r -p "This removes containers & volumes for ${PROJECT_NAME}. Continue? (y/N): " ans
    [[ "${ans:-N}" =~ ^[Yy]$ ]] || { log_info "Cancelled."; return 0; }
  fi
  log_warn "compose down -v (remove named volumes referenced by compose file)"
  _run_compose down -v || true

  # Additionally remove volumes that match "${PROJECT_NAME}_*"
  log_info "Checking for extra project volumes to remove (${PROJECT_NAME}_*)..."
  if _is_remote; then
    $SSH_CMD "$REMOTE_HOST" "(${DOCKER_CMD} volume ls -q --filter name='^${PROJECT_NAME}(_|$)' | xargs -r ${DOCKER_CMD} volume rm)" || true
  else
    (${DOCKER_CMD} volume ls -q --filter name="^${PROJECT_NAME}(_|$)" | xargs -r ${DOCKER_CMD} volume rm) || true
  fi

  log_success "Destroyed containers & volumes for ${PROJECT_NAME}."
}

show_logs() {
  local service="${1:-}"
  if [[ -n "$service" ]]; then
    _run_compose logs -f "$service"
  else
    _run_compose logs -f
  fi
}

show_app_logs() {
  local file="${1:-}"
  local vol="${PROJECT_NAME}_${LOG_VOLUME_SUFFIX}"
  log_info "Reading app logs from volume: ${vol}"
  local base_cmd=( "${DOCKER_CMD}" run --rm -v "${vol}:/logs" alpine )
  if _is_remote; then
    if [[ -n "$file" ]]; then
      $SSH_CMD "$REMOTE_HOST" "${base_cmd[*]} sh -lc 'test -f /logs/${file} && cat /logs/${file} || { echo \"File not found: ${file}\"; exit 1; }'"
    else
      $SSH_CMD "$REMOTE_HOST" "${base_cmd[*]} sh -lc 'find /logs -maxdepth 2 -type f \\( -name \"*.log\" -o -name \"*.txt\" \\) -print 2>/dev/null || true'"
      echo
      log_info "Recent (last 50 from all .log):"
      $SSH_CMD "$REMOTE_HOST" "${base_cmd[*]} sh -lc 'find /logs -name \"*.log\" -exec tail -n 50 {} + 2>/dev/null || echo \"No .log files found\"'"
    fi
  else
    if [[ -n "$file" ]]; then
      "${base_cmd[@]}" sh -lc "test -f /logs/${file} && cat /logs/${file} || { echo 'File not found: ${file}'; exit 1; }"
    else
      "${base_cmd[@]}" sh -lc 'find /logs -maxdepth 2 -type f \( -name "*.log" -o -name "*.txt" \) -print 2>/dev/null || true'
      echo
      log_info "Recent (last 50 from all .log):"
      "${base_cmd[@]}" sh -lc 'find /logs -name "*.log" -exec tail -n 50 {} + 2>/dev/null || echo "No .log files found"'
    fi
  fi
}

show_help() {
  cat <<EOF
Generic deploy for Docker Compose projects (local or remote via SSH)

Usage:
  $0 git [--branch NAME]         Deploy via git (clone/update, default: ${DEFAULT_BRANCH})
  $0 up [--build] [--clean]      Start containers (optionally rebuild and/or clean first)
  $0 down                        Stop containers
  $0 destroy                     Stop & remove containers and volumes (with confirmation)
  $0 logs [service]              Tail compose logs (optionally a specific service)
  $0 app-logs [file]             Read app logs from volume "\${PROJECT_NAME}_\${LOG_VOLUME_SUFFIX}"
  $0 status                      Show container status
  $0 deploy [--branch NAME] [--build] [--clean]
                                 Full deploy: git + up
  $0 help                        Show this help

Notes:
- Configure behavior in deploy_config.yml (beside this script).
- Works locally (REMOTE_HOST empty) or remote via SSH (REMOTE_HOST set).
- Compose command auto-supports:
    * "docker compose" (default) or
    * "docker-compose" (set COMPOSE_SUBCMD: "" and DOCKER_CMD: docker-compose)
EOF
}

show_status() {
  log_info "Compose status:"
  _run_compose ps
}

full_deploy() {
  local build=""
  local clean=""
  local branch="$DEFAULT_BRANCH"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --build) build="--build"; shift;;
      --clean) clean="--clean"; shift;;
      --branch) branch="$2"; shift 2;;
      *) shift;;
    esac
  done
  log_info "Full deploy → branch=${branch} ${build:+(build)} ${clean:+(clean)}"
  deploy_via_git "$branch"
  local args=()
  [[ -n "$build" ]] && args+=(--build)
  [[ -n "$clean" ]] && args+=(--clean)
  docker_up "${args[@]}"
  log_success "Full deploy complete."
}

# -----------------------------
# Main
# -----------------------------
cmd="${1:-help}"
shift || true
case "$cmd" in
  git)       # optional: --branch
    branch="$DEFAULT_BRANCH"
    while [[ $# -gt 0 ]]; do
      case "$1" in
        --branch) branch="${2:-$DEFAULT_BRANCH}"; shift 2;;
        *) shift;;
      esac
    done
    deploy_via_git "$branch"
    ;;
  up)        docker_up "$@";;
  down)      docker_down;;
  destroy)   docker_destroy;;
  logs)      show_logs "${1:-}";;
  app-logs)  show_app_logs "${1:-}";;
  status)    show_status;;
  deploy)    full_deploy "$@";;
  help|--help|-h|"") show_help;;
  *) log_error "Unknown command: $cmd"; echo; show_help; exit 1;;
esac
