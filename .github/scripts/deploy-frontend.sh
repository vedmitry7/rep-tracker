#!/usr/bin/env bash
set -Eeuo pipefail

# This script is copied to a per-deployment temporary directory by GitHub
# Actions. It deploys only already-built static files and never reloads Caddy.
readonly DEPLOY_SHA="${1:-}"
readonly ARCHIVE_PATH="${2:-}"
readonly STATIC_ROOT="/var/www/repka"
readonly RELEASES_DIR="${STATIC_ROOT}/releases"
readonly CURRENT_LINK="${STATIC_ROOT}/current"

if [[ ! "${DEPLOY_SHA}" =~ ^[0-9a-f]{40}$ ]]; then
  echo "A full 40-character Git commit SHA is required." >&2
  exit 2
fi
if [[ ! -f "${ARCHIVE_PATH}" ]]; then
  echo "Frontend archive is missing." >&2
  exit 2
fi

# The artifact must be a normal, relative static-file archive. This also makes
# accidental archives containing a host path fail before extraction.
if ! tar -tzf "${ARCHIVE_PATH}" | awk '
  /^\// || /(^|\/)\.\.($|\/)/ { bad = 1 }
  { found = 1 }
  END { exit bad || !found }
'; then
  echo "Frontend archive contains no safe relative files." >&2
  exit 1
fi

install -d -m 755 "${RELEASES_DIR}"
readonly RELEASE_DIR="${RELEASES_DIR}/${DEPLOY_SHA}"
readonly STAGING_DIR="$(mktemp -d "${RELEASES_DIR}/.incoming-${DEPLOY_SHA:0:12}.XXXXXX")"

cleanup() {
  rm -rf -- "${STAGING_DIR}"
}
trap cleanup EXIT INT TERM

tar --extract --gzip --file "${ARCHIVE_PATH}" --directory "${STAGING_DIR}" \
  --no-same-owner --no-same-permissions
if [[ ! -f "${STAGING_DIR}/index.html" ]]; then
  echo "Frontend artifact does not contain index.html." >&2
  exit 1
fi

chmod -R u=rwX,go=rX "${STAGING_DIR}"
if [[ -d "${RELEASE_DIR}" ]]; then
  # A retry of an already-uploaded immutable SHA must not overwrite it.
  if [[ ! -f "${RELEASE_DIR}/index.html" ]]; then
    echo "Existing frontend release is incomplete: ${RELEASE_DIR}" >&2
    exit 1
  fi
else
  mv -- "${STAGING_DIR}" "${RELEASE_DIR}"
fi

readonly NEXT_LINK="${STATIC_ROOT}/.current-${DEPLOY_SHA:0:12}"
ln -s "releases/${DEPLOY_SHA}" "${NEXT_LINK}"
mv -Tf -- "${NEXT_LINK}" "${CURRENT_LINK}"
rm -f -- "${ARCHIVE_PATH}"

echo "frontend_release=${RELEASE_DIR}"
echo "frontend_current=${CURRENT_LINK}"
