#!/usr/bin/env bash
set -euo pipefail

########################################
# CONFIGURATION (override via env vars)
########################################

# Core Apigee settings
ORG="${APIGEE_ORG:-your-org}"
ENV="${APIGEE_ENV:-dev}"

# Resource names
PROXY_NAME="${APIGEE_PROXY_NAME:-test-proxy}"
SHAREDFLOW_NAME="${APIGEE_SHARED_FLOW_NAME:-test-sf}"
CACHE_NAME="${APIGEE_CACHE_NAME:-test-cache}"

# Input test files
KVM_FILE="${APIGEE_KVM_FILE:-./testdata/kvm.json}"
CACHE_FILE="${APIGEE_CACHE_FILE:-./testdata/cache.json}"
TARGETSERVER_FILE="${APIGEE_TARGETSERVER_FILE:-./testdata/targetserver.json}"
MASKCONFIG_FILE="${APIGEE_MASKCONFIG_FILE:-./testdata/maskconfig.json}"

# Prefix/auth config
PREFIX_REMOTE="${CICD_PREFIXES_REMOTE_URL:-https://example.com/prefixes.git}"
DEVELOPER_EMAIL="${GITLAB_USER_EMAIL:-test@example.com}"

# Proxy + sharedflow artefacts
PROXY_DIR="${APIGEE_PROXY_DIR:-./apiproxy}"
SHAREDFLOW_ZIP="${APIGEE_SHARED_FLOW_ZIP:-./testdata/sharedflow.zip}"

# Output & behaviour
OUTPUT_DIR="${OUTPUT_DIR:-./apigeecli-test-output}"
DRY_RUN="${DRY_RUN:-false}"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"

RUN_DIR="${OUTPUT_DIR}/${TIMESTAMP}"
mkdir -p "$RUN_DIR"

########################################
# HELPERS
########################################

log() {
  echo -e "\n========== $1 ==========\n"
}

# Executes command and logs output to file
run_cmd() {
  local name="$1"
  shift

  local logfile="${RUN_DIR}/${name}.log"

  echo ">> $*"
  echo "   ↳ log: $logfile"

  if [ "$DRY_RUN" = "true" ]; then
    echo "⚠️ DRY RUN (command not executed)" | tee "$logfile"
    return 0
  fi

  # Run command, capture stdout+stderr
  if ! "$@" >"$logfile" 2>&1; then
    echo "❌ FAILED: $name"
    echo "---- LOG OUTPUT ----"
    cat "$logfile"
    exit 1
  fi
}

cleanup_prefixes() {
  rm -rf .apigee-prefixes || true
}

########################################
# PRE-FLIGHT CHECKS
########################################

log "PRE-FLIGHT CHECKS"

command -v apigee >/dev/null || { echo "❌ apigee CLI not found"; exit 1; }

echo "ORG=$ORG"
echo "ENV=$ENV"
echo "OUTPUT_DIR=$RUN_DIR"
echo "DRY_RUN=$DRY_RUN"

########################################
# CLI + PLUGINS
########################################

log "CLI VERSION"
run_cmd "cli_version" apigee -V

log "PLUGIN UPDATE"
run_cmd "plugins_update" apigee plugins update

########################################
# AUTH VALIDATION
########################################

log "AUTH CHECK"
cleanup_prefixes
run_cmd "check_auth" apigee check-auth \
  --remote "$PREFIX_REMOTE" \
  --developer "$DEVELOPER_EMAIL" \
  --destination-path .apigee-prefixes \
  -n "$PROXY_NAME"
cleanup_prefixes

########################################
# CONFIG PUSH TESTS
########################################

log "KVM PUSH"
run_cmd "kvm_push" apigee keyvaluemaps push \
  --file "$KVM_FILE" \
  -e "$ENV" \
  -o "$ORG"

log "CACHE PUSH"
run_cmd "cache_push" apigee caches push \
  --file "$CACHE_FILE" \
  -e "$ENV" \
  -o "$ORG"

log "TARGETSERVER PUSH"
run_cmd "targetserver_push" apigee targetservers push \
  --file "$TARGETSERVER_FILE" \
  -e "$ENV" \
  -o "$ORG"

log "MASKCONFIG PUSH"
run_cmd "maskconfig_push" apigee maskconfigs push \
  --file "$MASKCONFIG_FILE" \
  --name "$PROXY_NAME" \
  -o "$ORG"

########################################
# SHAREDFLOW OPERATIONS
########################################

log "SHAREDFLOW DEPLOY"
run_cmd "sharedflow_deploy" apigee sharedflows deploy \
  --override \
  -n "$SHAREDFLOW_NAME" \
  -f "$SHAREDFLOW_ZIP" \
  -e "$ENV" \
  -o "$ORG"

log "SHAREDFLOW CLEAN"
run_cmd "sharedflow_clean" apigee sharedflows clean \
  -n "$SHAREDFLOW_NAME" \
  --save-last 1 \
  -o "$ORG"

########################################
# API PROXY OPERATIONS
########################################

log "API DEPLOY"
run_cmd "api_deploy" apigee apis deploy \
  --seamless-deploy \
  -d "$PROXY_DIR" \
  -n "$PROXY_NAME" \
  -e "$ENV" \
  -o "$ORG"

log "API CLEAN"
run_cmd "api_clean" apigee apis clean \
  -n "$PROXY_NAME" \
  --save-last 1 \
  -o "$ORG"

########################################
# CACHE CLEAR
########################################

log "CACHE CLEAR"
run_cmd "cache_clear" apigee caches clear \
  -n "$CACHE_NAME" \
  -e "$ENV"

########################################
# SECURITY / QUALITY
########################################

log "SECURITY ASSESSMENT"
run_cmd "security_scan" apigee security-assessment -d ./

log "APIGEELINT"
if command -v apigeelint >/dev/null; then
  run_cmd "apigeelint" apigeelint -s "$PROXY_DIR" -f table
else
  echo "⚠️ apigeelint not installed, skipping"
fi

########################################
# SUMMARY OUTPUT
########################################

log "SUMMARY"

echo "✅ All commands executed successfully"
echo "📁 Output directory: $RUN_DIR"

echo ""
echo "Generated logs:"
ls -1 "$RUN_DIR"

echo ""
echo "💡 To compare runs:"
echo "diff -r previous_run_dir $RUN_DIR"
