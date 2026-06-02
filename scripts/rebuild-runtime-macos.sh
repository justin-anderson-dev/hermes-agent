#!/usr/bin/env bash
set -euo pipefail

# Durable macOS runtime refresh script for Hermes.
#
# Default behavior is intentionally useful for the real upgrade path:
#   1. optionally fetch / move the checkout to an explicit ref
#   2. reinstall THIS repo into the selected runtime venv
#   3. refresh the gateway launchd definition
#   4. restart the gateway (unless skipped)
#   5. print verification details
#
# Two safe modes are always available for inspection without service impact:
#   --dry-run     show the exact mutating commands without running them
#   --verify-only gather runtime / config / launchd facts only
#
# Important launchd note:
#   Restarting the gateway alone does NOT refresh a stale plist definition.
#   `hermes gateway install` matters because it repairs/regenerates the launchd
#   unit before any restart.

SCRIPT_NAME="$(basename "$0")"

DRY_RUN=false
VERIFY_ONLY=false
ALLOW_DIRTY=false
DO_FETCH=false
TARGET_REF=""
RESET_HARD=false
VENV_OVERRIDE="${HERMES_RUNTIME_VENV:-}"
SYNC_MODE="${HERMES_RUNTIME_SYNC_MODE:-auto}"   # auto|uv|pip
EXACT_SYNC=false
SKIP_PYTHON_SYNC=false
SKIP_GATEWAY_INSTALL=false
SKIP_GATEWAY_RESTART=false
RESTART_DASHBOARD=false
BUILD_UI_TUI=false
BUILD_WEB=false
ENSURE_DEPS=""
RUN_VERIFY=true

REPO_ROOT=""
SCRIPT_DIR=""
VENV_DIR=""
PYTHON_BIN=""
HERMES_BIN=""
REAL_HOME=""
CURRENT_BRANCH=""
CURRENT_COMMIT=""
DIRTY_STATUS=""
EDITABLE_BEFORE=""
EDITABLE_AFTER=""
GATEWAY_PLIST_DISPLAY=""
GATEWAY_LABEL_DISPLAY=""

MUTATING_COMMANDS=()

usage() {
    cat <<'EOF'
Hermes macOS runtime rebuild / refresh helper.

Usage:
  scripts/rebuild-runtime-macos.sh [options]

Safe inspection modes:
  --dry-run          Print the mutating commands but do not execute them.
  --verify-only      Read-only runtime / launchd / config verification.

Runtime / git options:
  --venv PATH        Override runtime venv (default: repo-local venv, then .venv).
  --fetch            Run `git fetch --all --prune --tags` before any ref change.
  --ref REF          Explicit git ref to checkout, or reset to when paired with
                     --reset-hard. No branch is forced by default.
  --reset-hard       Hard reset the current checkout to --ref. Destructive; only
                     used when explicitly requested.
  --allow-dirty      Permit a dirty working tree.
  --sync-mode MODE   Dependency sync strategy: auto, uv, or pip.
  --exact-sync       Use exact `uv sync` instead of the safer `--inexact` mode.

Optional work:
  --skip-python-sync     Skip the editable reinstall / dependency sync step.
  --skip-gateway-install Skip `hermes gateway install`.
  --skip-gateway-restart Skip `hermes gateway restart`.
  --restart-dashboard    Restart custom com.hermes.dashboard launch agent if present.
  --build-ui-tui         Run npm install/build in ui-tui.
  --build-web            Run npm install/build in web.
  --ensure-deps LIST     Forward to scripts/install.sh --ensure LIST
                         (supported there: node,browser,ripgrep,ffmpeg).
  --no-verify            Skip the final verification block.

Examples:
  scripts/rebuild-runtime-macos.sh --verify-only
  scripts/rebuild-runtime-macos.sh --dry-run --fetch --ref origin/custom/main
  scripts/rebuild-runtime-macos.sh --fetch --ref origin/custom/main --skip-gateway-restart
  scripts/rebuild-runtime-macos.sh --venv /path/to/venv --sync-mode pip --restart-dashboard
EOF
}

log() {
    printf '==> %s\n' "$*"
}

warn() {
    printf 'WARN: %s\n' "$*" >&2
}

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 1
}

quote_cmd() {
    local out=()
    local arg
    for arg in "$@"; do
        out+=("$(printf '%q' "$arg")")
    done
    printf '%s' "${out[*]}"
}

append_mutation() {
    MUTATING_COMMANDS+=("$(quote_cmd "$@")")
}

run_cmd() {
    append_mutation "$@"
    if "$DRY_RUN"; then
        printf '[dry-run] %s\n' "$(quote_cmd "$@")"
        return 0
    fi
    "$@"
}

run_repo_cmd() {
    append_mutation "$@"
    if "$DRY_RUN"; then
        printf '[dry-run] (cd %s && %s)\n' "$REPO_ROOT" "$(quote_cmd "$@")"
        return 0
    fi
    (
        cd "$REPO_ROOT"
        "$@"
    )
}

run_repo_env_cmd() {
    local -a env_args=(env -u PYTHONPATH -u PYTHONHOME)
    while (($# > 0)); do
        env_args+=("$1")
        shift
    done
    run_repo_cmd "${env_args[@]}"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

resolve_real_home() {
    REAL_HOME="$(python3 - <<'PY'
import os
import pwd
print(pwd.getpwuid(os.getuid()).pw_dir)
PY
)"
}

resolve_repo_root() {
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
    if command_exists git; then
        local git_root
        git_root="$(cd "$REPO_ROOT" && git rev-parse --show-toplevel 2>/dev/null || true)"
        if [[ -n "$git_root" ]]; then
            REPO_ROOT="$git_root"
        fi
    fi
}

resolve_venv() {
    if [[ -n "$VENV_OVERRIDE" ]]; then
        VENV_DIR="$VENV_OVERRIDE"
    elif [[ -d "$REPO_ROOT/venv" ]]; then
        VENV_DIR="$REPO_ROOT/venv"
    elif [[ -d "$REPO_ROOT/.venv" ]]; then
        VENV_DIR="$REPO_ROOT/.venv"
    else
        die "No runtime venv found. Checked $REPO_ROOT/venv and $REPO_ROOT/.venv. Use --venv PATH or HERMES_RUNTIME_VENV."
    fi

    [[ -d "$VENV_DIR" ]] || die "Venv path does not exist: $VENV_DIR"
    PYTHON_BIN="$VENV_DIR/bin/python"
    HERMES_BIN="$VENV_DIR/bin/hermes"
    [[ -x "$PYTHON_BIN" ]] || die "Python executable not found in venv: $PYTHON_BIN"
}

parse_args() {
    while (($# > 0)); do
        case "$1" in
            --help|-h)
                usage
                exit 0
                ;;
            --dry-run)
                DRY_RUN=true
                ;;
            --verify-only)
                VERIFY_ONLY=true
                ;;
            --allow-dirty)
                ALLOW_DIRTY=true
                ;;
            --fetch)
                DO_FETCH=true
                ;;
            --ref)
                (($# >= 2)) || die "--ref requires a value"
                TARGET_REF="$2"
                shift
                ;;
            --reset-hard)
                RESET_HARD=true
                ;;
            --venv)
                (($# >= 2)) || die "--venv requires a path"
                VENV_OVERRIDE="$2"
                shift
                ;;
            --sync-mode)
                (($# >= 2)) || die "--sync-mode requires auto, uv, or pip"
                SYNC_MODE="$2"
                shift
                ;;
            --exact-sync)
                EXACT_SYNC=true
                ;;
            --skip-python-sync)
                SKIP_PYTHON_SYNC=true
                ;;
            --skip-gateway-install)
                SKIP_GATEWAY_INSTALL=true
                ;;
            --skip-gateway-restart)
                SKIP_GATEWAY_RESTART=true
                ;;
            --restart-dashboard)
                RESTART_DASHBOARD=true
                ;;
            --build-ui-tui)
                BUILD_UI_TUI=true
                ;;
            --build-web)
                BUILD_WEB=true
                ;;
            --ensure-deps)
                (($# >= 2)) || die "--ensure-deps requires a comma-separated list"
                ENSURE_DEPS="$2"
                shift
                ;;
            --no-verify)
                RUN_VERIFY=false
                ;;
            *)
                die "Unknown option: $1"
                ;;
        esac
        shift
    done

    case "$SYNC_MODE" in
        auto|uv|pip) ;;
        *) die "Invalid --sync-mode '$SYNC_MODE' (expected auto, uv, or pip)" ;;
    esac

    if "$RESET_HARD" && [[ -z "$TARGET_REF" ]]; then
        die "--reset-hard requires --ref REF"
    fi

    if "$VERIFY_ONLY"; then
        SKIP_PYTHON_SYNC=true
        SKIP_GATEWAY_INSTALL=true
        SKIP_GATEWAY_RESTART=true
        RESTART_DASHBOARD=false
        BUILD_UI_TUI=false
        BUILD_WEB=false
        ENSURE_DEPS=""
    fi
}

git_branch() {
    git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD 2>/dev/null || true
}

git_commit() {
    git -C "$REPO_ROOT" rev-parse --short=12 HEAD 2>/dev/null || true
}

collect_git_state() {
    CURRENT_BRANCH="$(git_branch)"
    CURRENT_COMMIT="$(git_commit)"
    DIRTY_STATUS="$(git -C "$REPO_ROOT" status --short --untracked-files=normal 2>/dev/null || true)"
}

preview_multiline() {
    local text="$1"
    local limit="${2:-12}"
    if [[ -z "$text" ]]; then
        return 0
    fi
    printf '%s' "$text" | python3 -c '
import sys
limit = int(sys.argv[1])
lines = sys.stdin.read().splitlines()
for line in lines[:limit]:
    print(f"    {line}")
if len(lines) > limit:
    print(f"    ... ({len(lines) - limit} more lines)")
' "$limit"
}

get_editable_location() {
    "$PYTHON_BIN" -m pip show hermes-agent 2>/dev/null | awk -F': ' '/^Editable project location:/ {print $2}' | head -n 1
}

normalize_path() {
    python3 - "$1" <<'PY'
import os
import sys
print(os.path.realpath(sys.argv[1]))
PY
}

get_pip_show() {
    "$PYTHON_BIN" -m pip show hermes-agent 2>/dev/null || true
}

print_launchd_detection() {
    local launch_agents_dir="$REAL_HOME/Library/LaunchAgents"
    shopt -s nullglob
    local plists=("$launch_agents_dir"/ai.hermes.gateway*.plist)
    shopt -u nullglob

    if ((${#plists[@]} == 0)); then
        log "Launchd gateway plist: not found under $launch_agents_dir"
        GATEWAY_PLIST_DISPLAY="(not found)"
        GATEWAY_LABEL_DISPLAY="ai.hermes.gateway"
        return 0
    fi

    log "Launchd gateway plist(s):"
    local plist
    for plist in "${plists[@]}"; do
        local label
        label="$(basename "$plist" .plist)"
        printf '    %s\n' "$plist"
        if launchctl list "$label" >/tmp/${label}.launchctl.stdout 2>/tmp/${label}.launchctl.stderr; then
            printf '      loaded: yes (%s)\n' "$label"
            python3 - "/tmp/${label}.launchctl.stdout" <<'PY'
from pathlib import Path
path = Path(__import__('sys').argv[1])
for raw in path.read_text(encoding='utf-8', errors='replace').splitlines():
    raw = raw.rstrip()
    if '"Program" = ' in raw or '"PID" = ' in raw or '"ProgramArguments" = (' in raw:
        print(f"      {raw}")
PY
        else
            printf '      loaded: no (%s)\n' "$label"
        fi
        if [[ -z "$GATEWAY_PLIST_DISPLAY" ]]; then
            GATEWAY_PLIST_DISPLAY="$plist"
            GATEWAY_LABEL_DISPLAY="$label"
        fi
    done
}

print_preflight() {
    collect_git_state
    EDITABLE_BEFORE="$(get_editable_location || true)"

    log "Preflight"
    printf '    repo root: %s\n' "$REPO_ROOT"
    printf '    platform: %s %s\n' "$(uname -s)" "$(sw_vers -productVersion 2>/dev/null || uname -r)"
    printf '    runtime venv: %s\n' "$VENV_DIR"
    printf '    python: %s\n' "$PYTHON_BIN"
    printf '    branch: %s\n' "${CURRENT_BRANCH:-unknown}"
    printf '    commit: %s\n' "${CURRENT_COMMIT:-unknown}"
    if [[ -n "$EDITABLE_BEFORE" ]]; then
        printf '    editable location (before): %s\n' "$EDITABLE_BEFORE"
    else
        printf '    editable location (before): (not reported by pip show)\n'
    fi
    print_launchd_detection

    if [[ -n "$DIRTY_STATUS" ]]; then
        warn "Working tree is dirty"
        preview_multiline "$DIRTY_STATUS"
        if ! "$ALLOW_DIRTY" && ! "$VERIFY_ONLY" && ! "$DRY_RUN"; then
            die "Refusing to continue with a dirty tree. Re-run with --allow-dirty if this is intentional."
        fi
    else
        printf '    working tree: clean\n'
    fi
}

macos_preflight() {
    [[ "$(uname -s)" == "Darwin" ]] || die "$SCRIPT_NAME is macOS-focused and must run on Darwin"
    resolve_real_home
    resolve_repo_root
    resolve_venv
    git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Repo root is not inside a git worktree: $REPO_ROOT"
}

maybe_fetch() {
    if ! "$DO_FETCH"; then
        return 0
    fi
    log "Fetching remotes"
    run_repo_cmd git fetch --all --prune --tags
}

maybe_checkout_or_reset_ref() {
    if [[ -z "$TARGET_REF" ]]; then
        return 0
    fi

    if "$RESET_HARD"; then
        log "Hard-resetting current checkout to explicit ref: $TARGET_REF"
        run_repo_cmd git reset --hard "$TARGET_REF"
    else
        log "Checking out explicit ref: $TARGET_REF"
        run_repo_cmd git checkout "$TARGET_REF"
    fi

    CURRENT_BRANCH="$(git_branch)"
    CURRENT_COMMIT="$(git_commit)"
}

can_use_uv_sync() {
    command_exists uv && [[ -f "$REPO_ROOT/uv.lock" ]]
}

sync_runtime_uv() {
    local -a cmd=(uv sync --extra all --locked)
    local sync_desc="inexact"
    if ! "$EXACT_SYNC"; then
        cmd+=(--inexact)
    else
        sync_desc="exact"
    fi
    log "Refreshing Python runtime with uv sync ($sync_desc)"
    run_repo_env_cmd UV_PROJECT_ENVIRONMENT="$VENV_DIR" "${cmd[@]}"
}

sync_runtime_pip() {
    log "Refreshing editable install with pip fallback"
    run_repo_env_cmd "$PYTHON_BIN" -m pip install --upgrade pip setuptools wheel
    run_repo_env_cmd "$PYTHON_BIN" -m pip install --upgrade --editable '.[all]'
}

ensure_repo_editable_install() {
    local expected current expected_norm current_norm
    expected="$REPO_ROOT"
    current="$(get_editable_location || true)"
    expected_norm="$(normalize_path "$expected")"

    if [[ -n "$current" ]]; then
        current_norm="$(normalize_path "$current")"
    else
        current_norm=""
    fi

    if [[ -n "$current_norm" && "$current_norm" == "$expected_norm" ]]; then
        log "Editable install already points at repo root"
        return 0
    fi

    if [[ -n "$current" ]]; then
        warn "Editable install points at '$current'; forcing repo-local editable reinstall"
    else
        warn "Editable install location unavailable; forcing repo-local editable reinstall"
    fi

    sync_runtime_pip
}

maybe_sync_runtime() {
    if "$SKIP_PYTHON_SYNC"; then
        log "Skipping Python runtime sync (--skip-python-sync or --verify-only)"
        return 0
    fi

    case "$SYNC_MODE" in
        uv)
            can_use_uv_sync || die "--sync-mode uv requested, but uv or uv.lock is unavailable"
            sync_runtime_uv
            ;;
        pip)
            sync_runtime_pip
            ;;
        auto)
            if can_use_uv_sync; then
                if "$DRY_RUN"; then
                    sync_runtime_uv
                elif sync_runtime_uv; then
                    :
                else
                    warn "uv sync failed; falling back to pip editable reinstall"
                    sync_runtime_pip
                fi
            else
                log "uv sync unavailable; using pip editable reinstall"
                sync_runtime_pip
            fi
            ;;
    esac

    ensure_repo_editable_install
}

maybe_ensure_deps() {
    [[ -n "$ENSURE_DEPS" ]] || return 0
    log "Ensuring optional runtime dependencies via installer helper: $ENSURE_DEPS"
    run_repo_cmd "$REPO_ROOT/scripts/install.sh" --ensure "$ENSURE_DEPS"
}

npm_install_and_build() {
    local project_dir="$1"
    local label="$2"
    [[ -d "$project_dir" ]] || die "$label directory not found: $project_dir"
    command_exists npm || die "npm is required for $label build steps"

    log "$label: installing node dependencies"
    if [[ -f "$project_dir/package-lock.json" ]]; then
        run_repo_cmd npm --prefix "$project_dir" ci
    else
        run_repo_cmd npm --prefix "$project_dir" install
    fi

    log "$label: building"
    run_repo_cmd npm --prefix "$project_dir" run build
}

maybe_build_assets() {
    if "$BUILD_UI_TUI"; then
        npm_install_and_build "$REPO_ROOT/ui-tui" "ui-tui"
    fi
    if "$BUILD_WEB"; then
        npm_install_and_build "$REPO_ROOT/web" "web dashboard"
    fi
}

maybe_gateway_install() {
    if "$SKIP_GATEWAY_INSTALL"; then
        log "Skipping gateway plist refresh (--skip-gateway-install or --verify-only)"
        return 0
    fi
    [[ -x "$HERMES_BIN" ]] || die "Hermes CLI not found in venv: $HERMES_BIN"
    log "Refreshing gateway launchd definition via hermes gateway install"
    run_repo_env_cmd "$HERMES_BIN" gateway install
}

maybe_gateway_restart() {
    if "$SKIP_GATEWAY_RESTART"; then
        log "Skipping gateway restart (--skip-gateway-restart or --verify-only)"
        return 0
    fi
    [[ -x "$HERMES_BIN" ]] || die "Hermes CLI not found in venv: $HERMES_BIN"
    log "Restarting gateway service"
    run_repo_env_cmd "$HERMES_BIN" gateway restart
}

maybe_restart_dashboard_agent() {
    if ! "$RESTART_DASHBOARD"; then
        return 0
    fi

    local dashboard_label="com.hermes.dashboard"
    local dashboard_plist="$REAL_HOME/Library/LaunchAgents/${dashboard_label}.plist"
    if [[ ! -f "$dashboard_plist" ]]; then
        warn "Dashboard launch agent not found at $dashboard_plist; skipping"
        return 0
    fi

    log "Restarting dashboard launch agent: $dashboard_label"
    if "$DRY_RUN"; then
        printf '[dry-run] launchctl list %s >/dev/null 2>&1 || launchctl bootstrap gui/%s %s\n' "$dashboard_label" "$UID" "$(printf '%q' "$dashboard_plist")"
        printf '[dry-run] launchctl kickstart -k gui/%s/%s\n' "$UID" "$dashboard_label"
        append_mutation launchctl list "$dashboard_label"
        append_mutation launchctl bootstrap "gui/$UID" "$dashboard_plist"
        append_mutation launchctl kickstart -k "gui/$UID/$dashboard_label"
        return 0
    fi

    if ! launchctl list "$dashboard_label" >/dev/null 2>&1; then
        launchctl bootstrap "gui/$UID" "$dashboard_plist"
    fi
    launchctl kickstart -k "gui/$UID/$dashboard_label"
}

print_command_block() {
    local title="$1"
    shift
    printf '\n%s\n' "$title"
    printf '    $ %s\n' "$(quote_cmd "$@")"
    local rc=0
    set +e
    "$@" 2>&1 | sed 's/^/    /'
    rc=${PIPESTATUS[0]}
    set -e
    if ((rc != 0)); then
        printf '    [exit %d]\n' "$rc"
    fi
}

print_python_block() {
    local title="$1"
    local snippet="$2"
    printf '\n%s\n' "$title"
    printf '    $ (cd %s && %s - <<'"'"'PY'"'"')\n' "$REAL_HOME" "$PYTHON_BIN"
    printf '%s\n' "$snippet" | sed 's/^/    /'
    printf '    PY\n'
    local rc=0
    set +e
    (
        cd "$REAL_HOME"
        "$PYTHON_BIN" - <<PY
$snippet
PY
    ) 2>&1 | sed 's/^/    /'
    rc=${PIPESTATUS[0]}
    set -e
    if ((rc != 0)); then
        printf '    [exit %d]\n' "$rc"
    fi
}

verify_runtime() {
    local phase="$1"
    local import_path_snippet
    local config_summary_snippet

    import_path_snippet=$(cat <<'PY'
import pathlib
import hermes_cli.main

print(pathlib.Path(hermes_cli.main.__file__).resolve())
PY
)

    config_summary_snippet=$(cat <<'PY'
from hermes_cli.config import load_config

cfg = load_config() or {}


def dig(data, *path):
    cur = data
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def first_nonempty(*values):
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if value not in (None, '', {}):
            return value
    return '(unset)'


model_cfg = cfg.get('model') if isinstance(cfg.get('model'), dict) else {}
aux_cfg = cfg.get('auxiliary') if isinstance(cfg.get('auxiliary'), dict) else {}
legacy_curator = dig(cfg, 'curator', 'auxiliary')
legacy_curator = legacy_curator if isinstance(legacy_curator, dict) else {}

main_provider = first_nonempty(model_cfg.get('provider'))
main_model = first_nonempty(
    model_cfg.get('default'),
    model_cfg.get('model'),
    model_cfg.get('name'),
)
main_base_url = first_nonempty(model_cfg.get('base_url'))

session_cfg = aux_cfg.get('session_search') if isinstance(aux_cfg.get('session_search'), dict) else {}
session_provider = first_nonempty(session_cfg.get('provider'), model_cfg.get('provider'))
session_model = first_nonempty(
    session_cfg.get('model'),
    session_cfg.get('default'),
    model_cfg.get('default'),
    model_cfg.get('model'),
    model_cfg.get('name'),
)
session_source = 'auxiliary.session_search' if session_cfg else 'main model fallback'

curator_cfg = aux_cfg.get('curator') if isinstance(aux_cfg.get('curator'), dict) else {}
curator_source = 'main model fallback'
if curator_cfg:
    curator_source = 'auxiliary.curator'
elif legacy_curator:
    curator_source = 'curator.auxiliary (legacy)'

active_curator = curator_cfg or legacy_curator
curator_provider = first_nonempty(active_curator.get('provider'), model_cfg.get('provider'))
curator_model = first_nonempty(
    active_curator.get('model'),
    active_curator.get('default'),
    model_cfg.get('default'),
    model_cfg.get('model'),
    model_cfg.get('name'),
)

print(f'main: provider={main_provider} model={main_model} base_url={main_base_url}')
print(f'session_search: provider={session_provider} model={session_model} source={session_source}')
print(f'curator: provider={curator_provider} model={curator_model} source={curator_source}')
PY
)

    EDITABLE_AFTER="$(get_editable_location || true)"

    log "$phase"
    print_command_block "Hermes version" "$HERMES_BIN" --version
    print_command_block "pip show hermes-agent" "$PYTHON_BIN" -m pip show hermes-agent
    print_python_block "Import path for hermes_cli.main" "$import_path_snippet"
    print_command_block "Gateway status" "$HERMES_BIN" gateway status
    print_python_block "Config/provider summary" "$config_summary_snippet"

    printf '\nEditable location summary\n'
    printf '    before: %s\n' "${EDITABLE_BEFORE:-unknown}"
    printf '    after:  %s\n' "${EDITABLE_AFTER:-unknown}"
}

print_mutation_plan() {
    if ((${#MUTATING_COMMANDS[@]} == 0)); then
        return 0
    fi
    printf '\nPlanned mutating commands\n'
    local cmd
    for cmd in "${MUTATING_COMMANDS[@]}"; do
        printf '    %s\n' "$cmd"
    done
}

main() {
    parse_args "$@"
    macos_preflight
    print_preflight

    if "$VERIFY_ONLY"; then
        if "$RUN_VERIFY"; then
            verify_runtime "Verify-only runtime report"
        fi
        exit 0
    fi

    maybe_fetch
    maybe_checkout_or_reset_ref
    maybe_sync_runtime
    maybe_ensure_deps
    maybe_build_assets
    maybe_gateway_install
    maybe_gateway_restart
    maybe_restart_dashboard_agent

    if "$DRY_RUN"; then
        print_mutation_plan
    fi

    if "$RUN_VERIFY"; then
        if "$DRY_RUN"; then
            verify_runtime "Dry-run current runtime report (no changes applied)"
        else
            verify_runtime "Post-rebuild runtime report"
        fi
    fi
}

main "$@"
