#!/usr/bin/env bash
# Deploy Model Router to Vercel (production) with env vars from .env
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "Missing .env — copy .env.example and fill in secrets first."
  exit 1
fi

if ! command -v vercel >/dev/null 2>&1; then
  echo "Installing Vercel CLI…"
  npm install -g vercel
fi

if ! vercel whoami >/dev/null 2>&1; then
  echo "Log in to Vercel (browser will open)…"
  vercel login
fi

# Link / create project non-interactively when possible
vercel link --yes --project model-router-budget || true

set_env() {
  local key="$1"
  local value="$2"
  local env_name="$3"
  if [[ -z "${value}" ]]; then
    return 0
  fi
  # Remove existing value then add (idempotent-ish for re-deploys)
  printf '%s' "${value}" | vercel env add "${key}" "${env_name}" --force >/dev/null 2>&1 \
    || printf '%s' "${value}" | vercel env add "${key}" "${env_name}" >/dev/null 2>&1 \
    || true
}

# shellcheck disable=SC1091
set -a
source .env
set +a

# Strip surrounding quotes from DATABASE_URL if present
DATABASE_URL_CLEAN="${DATABASE_URL%\"}"
DATABASE_URL_CLEAN="${DATABASE_URL_CLEAN#\"}"
DATABASE_URL_CLEAN="${DATABASE_URL_CLEAN%\'}"
DATABASE_URL_CLEAN="${DATABASE_URL_CLEAN#\'}"

for ENV_NAME in production preview development; do
  set_env DATABASE_URL "${DATABASE_URL_CLEAN}" "${ENV_NAME}"
  set_env OPENAI_API_KEY "${OPENAI_API_KEY:-}" "${ENV_NAME}"
  set_env DEEPSEEK_API_KEY "${DEEPSEEK_API_KEY:-}" "${ENV_NAME}"
  set_env LLM_PROVIDER "${LLM_PROVIDER:-openai}" "${ENV_NAME}"
  set_env MONTHLY_BUDGET "${MONTHLY_BUDGET:-5.00}" "${ENV_NAME}"
  set_env MAX_PROMPT_CHARS "${MAX_PROMPT_CHARS:-4000}" "${ENV_NAME}"
  set_env USE_REAL_LLM "${USE_REAL_LLM:-false}" "${ENV_NAME}"
done

echo "Deploying to Vercel production…"
vercel deploy --prod --yes
