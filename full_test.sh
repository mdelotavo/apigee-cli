#!/usr/bin/env bash
set -euo pipefail

########################################
# USAGE
########################################

usage() {
  cat <<EOF
Usage:
  Export required environment variables, then run:

    bash scripts/apigeecli_contract_test.sh

Required variables:
  APIGEE_ORG                Apigee organisation

Optional variables (with defaults):
  APIGEE_ENV                Target environment (default: dev)
  APIGEE_PROXY_NAME         API proxy name (default: test-proxy)
  APIGEE_SHARED_FLOW_NAME   Sharedflow name (default: test-sf)
  APIGEE_CACHE_NAME         Cache name (default: test-cache)

  APIGEE_KVM_FILE           KVM file path (default: ./testdata/kvm.json)
  APIGEE_CACHE_FILE         Cache file path
  APIGEE_TARGETSERVER_FILE  Target server file path
  APIGEE_MASKCONFIG_FILE    Mask config file path

  APIGEE_PROXY_DIR          Proxy directory (default: ./apiproxy)
  APIGEE_SHARED_FLOW_ZIP    Sharedflow zip (default: ./testdata/sharedflow.zip)

  OUTPUT_DIR                Output directory (default: ./apigeecli-test-output)
  DRY_RUN                   true/false (default: false)

Backup options:
  BACKUP_ENVS               Comma list (default: APIGEE_ENV)
  BACKUP_APIS               Comma list (default: all)

Examples:
  export APIGEE_ORG=my-org
  export APIGEE_ENV=uat
  bash scripts/apigeecli_contract_test.sh

EOF
}

########################################
# CONFIGURATION
########################################

: "${APIGEE_ORG:?APIGEE_ORG must be set}"

ORG="$APIGEE_ORG"
ENV="${APIGEE_ENV:-dev}"

PROXY_NAME="${APIGEE_PROXY_NAME:-test-proxy}"
SHAREDFLOW_NAME="${APIGEE_SHARED_FLOW_NAME:-test-sf}"
CACHE_NAME="${APIGEE_CACHE_NAME:-test-cache}"

KVM_FILE="${APIGEE_KVM_FILE:-./testdata/kvm.json}"
CACHE_FILE="${APIGEE_CACHE_FILE:-./testdata/cache.json}"
TARGETSERVER_FILE="${APIGEE_TARGETSERVER_FILE:-./testdata/targetserver.json}"
MASKCONFIG_FILE="${APIGEE_MASKCONFIG_FILE:-./testdata/maskconfig.json}"

PROXY_DIR="${APIGEE_PROXY_DIR:-./apiproxy}"
SHAREDFLOW_ZIP="${APIGEE_SHARED_FLOW_ZIP:-./testdata/sharedflow.zip}"

OUTPUT_DIR="${OUTPUT_DIR:-./apigeecli-test-output}"
DRY_RUN="${DRY_RUN:-false}"

BACKUP_ENVS="${BACKUP_ENVS:-$ENV}"
BACKUP_APIS="${BACKUP_APIS:-}"

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
RUN_DIR="${OUTPUT_DIR}/${TIMESTAMP}"
mkdir -p "$RUN_DIR"

########################################
# VALIDATION
########################################

log() { echo -e "\n========== $1 ==========\n"; }

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

check_file() {
  [ -f "$1" ] || fail "File not found: $1"
}

check_dir() {
  [ -d "$1" ] || fail "Directory not found: $1"
}

validate() {
  log "VALIDATION"

  command -v apigee >/dev/null || fail "apigee CLI not found"

  check_file "$KVM_FILE"
  check_file "$CACHE_FILE"
  check_file "$TARGETSERVER_FILE"
  check_file "$MASKCONFIG_FILE"

  check_file "$SHAREDFLOW_ZIP"
  check_dir  "$PROXY_DIR"

  echo "ORG=$ORG"
  echo "ENV=$ENV"
  echo "OUTPUT_DIR=$RUN_DIR"
  echo "DRY_RUN=$DRY_RUN"
}

########################################
# EXECUTION WRAPPER
########################################

run_cmd() {
  local name="$1"
  shift
  local logfile="${RUN_DIR}/${name}.log"

  echo ">> $*"
  echo "   log: $logfile"

  if [ "$DRY_RUN" = "true" ]; then
    echo "DRY RUN" > "$logfile"
    return
  fi

  if ! "$@" >"$logfile" 2>&1; then
    echo "FAILED: $name"
    cat "$logfile"
    exit 1
  fi
}

########################################
# BUILD FLAGS SAFELY
########################################

build_env_args() {
  local args=()
  IFS=',' read -ra arr <<< "$BACKUP_ENVS"
  for e in "${arr[@]}"; do
    args+=("-e" "$e")
  done
  printf '%s\n' "${args[@]}"
}

build_api_args() {
  local args=()
  if [ -n "$BACKUP_APIS" ]; then
    IFS=',' read -ra arr <<< "$BACKUP_APIS"
    for a in "${arr[@]}"; do
      args+=("--apis" "$a")
    done
  fi
  printf '%s\n' "${args[@]}"
}

########################################
# RUN
########################################

validate

log "CLI VERSION"
run_cmd cli_version apigee -V

log "PLUGIN UPDATE"
run_cmd plugins_update apigee plugins update

log "CONFIG PUSH"

run_cmd kvm_push apigee keyvaluemaps push --file "$KVM_FILE" -e "$ENV" -o "$ORG"
run_cmd cache_push apigee caches push --file "$CACHE_FILE" -e "$ENV" -o "$ORG"
run_cmd targetserver_push apigee targetservers push --file "$TARGETSERVER_FILE" -e "$ENV" -o "$ORG"
run_cmd maskconfig_push apigee maskconfigs push --file "$MASKCONFIG_FILE" --name "$PROXY_NAME" -o "$ORG"

log "SHAREDFLOWS"

run_cmd sharedflow_deploy apigee sharedflows deploy \
  --override -n "$SHAREDFLOW_NAME" -f "$SHAREDFLOW_ZIP" -e "$ENV" -o "$ORG"

run_cmd sharedflow_clean apigee sharedflows clean \
  -n "$SHAREDFLOW_NAME" --save-last 1 -o "$ORG"

log "APIS"

run_cmd api_deploy apigee apis deploy \
  --seamless-deploy -d "$PROXY_DIR" -n "$PROXY_NAME" -e "$ENV" -o "$ORG"

run_cmd api_clean apigee apis clean \
  -n "$PROXY_NAME" --save-last 1 -o "$ORG"

########################################
# BACKUPS
########################################

log "BACKUPS"

BACKUP_DIR="${RUN_DIR}/backups"
SNAPSHOT_DIR="${BACKUP_DIR}/snapshot"

mkdir -p "$SNAPSHOT_DIR"

mapfile -t ENV_ARGS < <(build_env_args)
mapfile -t API_ARGS < <(build_api_args)

run_cmd backup_snapshot apigee backups take-snapshot \
  --target-directory "$SNAPSHOT_DIR" \
  -o "$ORG" \
  "${ENV_ARGS[@]}" \
  "${API_ARGS[@]}"

########################################
# NORMALISATION (optional)
########################################

log "NORMALISATION"

NORMALISED_DIR="${BACKUP_DIR}/snapshot_normalised"
mkdir -p "$NORMALISED_DIR"

if [ "$DRY_RUN" != "true" ]; then
  cp -R "$SNAPSHOT_DIR/." "$NORMALISED_DIR/" 2>/dev/null || true
  find "$NORMALISED_DIR" -type f -name "*.log" -delete || true
fi

########################################
# CACHE CLEAR
########################################

log "CACHE CLEAR"
run_cmd cache_clear apigee caches clear -n "$CACHE_NAME" -e "$ENV"

########################################
# SUMMARY
########################################

log "SUMMARY"

echo "All commands completed successfully"
echo "Output directory: $RUN_DIR"

echo ""
echo "Logs:"
ls -1 "$RUN_DIR"

echo ""
echo "To compare runs:"
echo "  diff -r <previous_run_dir> $RUN_DIR"