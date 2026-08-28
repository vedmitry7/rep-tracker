#!/usr/bin/env bash
set -Eeuo pipefail

readonly DEPLOY_SHA="${1:-}"
readonly PROJECT_DIR="/opt/rep-tracker"
readonly BACKUP_DIR="${PROJECT_DIR}/backups"
readonly COMPOSE_FILE="docker-compose.prod.yml"

if [[ ! "${DEPLOY_SHA}" =~ ^[0-9a-f]{40}$ ]]; then
  echo "A full 40-character Git commit SHA is required." >&2
  exit 2
fi

cd "${PROJECT_DIR}"

git fetch origin
git checkout main
git pull --ff-only origin main

readonly CHECKED_OUT_SHA="$(git rev-parse HEAD)"
if [[ "${CHECKED_OUT_SHA}" != "${DEPLOY_SHA}" ]]; then
  echo "Refusing stale deployment: main is ${CHECKED_OUT_SHA}, requested image tag is ${DEPLOY_SHA}." >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  echo "Production .env is missing." >&2
  exit 1
fi

if ! git check-ignore --quiet .env; then
  echo "Production .env must remain ignored by Git." >&2
  exit 1
fi

if [[ "$(stat -c '%a' .env)" != "600" ]]; then
  echo "Production .env must have mode 600." >&2
  exit 1
fi

export IMAGE_TAG="${DEPLOY_SHA}"

compose() {
  docker compose \
    --project-name rep-tracker \
    --env-file .env \
    --file "${COMPOSE_FILE}" \
    "$@"
}

compose config --quiet

postgres_id="$(compose ps --quiet postgres)"
if [[ -z "${postgres_id}" ]]; then
  echo "The production PostgreSQL container is not running." >&2
  exit 1
fi

postgres_volume="$(docker inspect --format '{{range .Mounts}}{{if eq .Destination "/var/lib/postgresql/data"}}{{.Name}}{{end}}{{end}}' "${postgres_id}")"
if [[ "${postgres_volume}" != "rep-tracker_postgres_data" ]]; then
  echo "Refusing deployment: PostgreSQL uses unexpected volume '${postgres_volume}'." >&2
  exit 1
fi

mkdir -p "${BACKUP_DIR}"
chmod 700 "${BACKUP_DIR}"

readonly SHORT_SHA="${DEPLOY_SHA:0:12}"
readonly BACKUP_NAME="$(date -u +'%Y%m%d-%H%M%S')-${SHORT_SHA}.dump"
readonly BACKUP_FILE="${BACKUP_DIR}/${BACKUP_NAME}"
readonly BACKUP_TMP="${BACKUP_DIR}/.${BACKUP_NAME}.tmp"

cleanup_backup_tmp() {
  rm -f -- "${BACKUP_TMP}"
}
trap cleanup_backup_tmp EXIT INT TERM

echo "Creating PostgreSQL backup ${BACKUP_NAME}"
compose exec --no-TTY postgres sh -ec \
  'exec pg_dump --format=custom --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' \
  > "${BACKUP_TMP}"

if [[ ! -s "${BACKUP_TMP}" ]]; then
  echo "PostgreSQL backup is empty; deployment stopped." >&2
  exit 1
fi

chmod 600 "${BACKUP_TMP}"
mv -- "${BACKUP_TMP}" "${BACKUP_FILE}"
trap - EXIT INT TERM

mapfile -t deploy_backups < <(
  find "${BACKUP_DIR}" -maxdepth 1 -type f -name '*.dump' -printf '%T@ %p\n' \
    | sort --numeric-sort --reverse \
    | cut --delimiter=' ' --fields=2-
)
for ((index = 7; index < ${#deploy_backups[@]}; index++)); do
  rm -- "${deploy_backups[index]}"
done

echo "Pulling immutable application images for ${DEPLOY_SHA}"
compose pull api bot

echo "Recreating API without touching PostgreSQL"
compose up --detach --no-deps --force-recreate api

api_id="$(compose ps --all --quiet api)"
api_health=""
for _ in {1..30}; do
  if [[ -n "${api_id}" ]]; then
    api_health="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "${api_id}")"
    if [[ "${api_health}" == "healthy" ]]; then
      break
    fi
    if [[ "${api_health}" == "exited" || "${api_health}" == "dead" ]]; then
      break
    fi
  fi
  sleep 5
  api_id="$(compose ps --all --quiet api)"
done

if [[ "${api_health}" != "healthy" ]]; then
  echo "API did not become healthy (state: ${api_health:-missing})." >&2
  compose logs --no-color --tail 100 api >&2 || true
  exit 1
fi

curl --fail --silent --show-error http://127.0.0.1:8000/health/db
echo

echo "Recreating bot after API health verification"
compose up --detach --no-deps --force-recreate bot
sleep 10

bot_id="$(compose ps --all --quiet bot)"
if [[ -z "${bot_id}" || "$(docker inspect --format '{{.State.Running}}' "${bot_id}")" != "true" ]]; then
  echo "Bot is not running after deployment." >&2
  compose logs --no-color --tail 100 bot >&2 || true
  exit 1
fi

bot_count="$(docker ps --quiet \
  --filter 'label=com.docker.compose.project=rep-tracker' \
  --filter 'label=com.docker.compose.service=bot' \
  | wc -l)"
if [[ "${bot_count}" -ne 1 ]]; then
  echo "Expected exactly one production bot container, found ${bot_count}." >&2
  exit 1
fi

postgres_health="$(docker inspect --format '{{.State.Health.Status}}' "${postgres_id}")"
api_restarts="$(docker inspect --format '{{.RestartCount}}' "${api_id}")"
bot_restarts="$(docker inspect --format '{{.RestartCount}}' "${bot_id}")"
api_image="$(docker inspect --format '{{.Config.Image}}' "${api_id}")"
bot_image="$(docker inspect --format '{{.Config.Image}}' "${bot_id}")"
expected_api_image="ghcr.io/vedmitry7/rep-tracker-api:${DEPLOY_SHA}"
expected_bot_image="ghcr.io/vedmitry7/rep-tracker-bot:${DEPLOY_SHA}"

if [[ "${postgres_health}" != "healthy" || "${api_restarts}" -ne 0 || "${bot_restarts}" -ne 0 ]]; then
  echo "Post-deploy verification failed: postgres=${postgres_health}, api_restarts=${api_restarts}, bot_restarts=${bot_restarts}." >&2
  exit 1
fi

if [[ "${api_image}" != "${expected_api_image}" || "${bot_image}" != "${expected_bot_image}" ]]; then
  echo "Post-deploy image verification failed: api=${api_image}, bot=${bot_image}." >&2
  exit 1
fi

compose ps
echo "api_image=${api_image}"
echo "bot_image=${bot_image}"
echo "api_restarts=${api_restarts}"
echo "bot_restarts=${bot_restarts}"
echo "backup=${BACKUP_FILE}"
