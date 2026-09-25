#!/bin/sh
# Installs or upgrades Saleor on every `docker compose up`; safe to repeat.
# Runs as root (volumes' owners), Saleor commands as the image's saleor user:
# - RSA key in the `keys` volume, generated once: it signs the API's JWTs
#   (logins, app tokens). Back it up (see backup.sh).
# - Static files of the image copied to Caddy's `static` volume.
# - `manage.py migrate`: schema, plus on a new database Saleor's defaults
#   (channel, warehouse, shipping zone, product type, category).
# - `manage.py stack_setup` (config/saleor/stack): admin user and store
#   settings (see there).
set -eu
cd /app

saleor() { runuser -u saleor -- "$@"; }

for _ in $(seq 60); do
    python -c 'import os, psycopg; psycopg.connect(os.environ["DATABASE_URL"]).close()' 2>/dev/null && break
    sleep 2
done

echo "==> RSA key"
key="${KEYS_DIR}/rsa.pem"
if [ ! -s "${key}" ]; then
    (umask 077 && openssl genrsa -out "${key}.tmp" 2048 2>/dev/null)
    mv "${key}.tmp" "${key}"
    echo "Generated ${key}"
fi
chown -R saleor:saleor "${KEYS_DIR}"
chmod 700 "${KEYS_DIR}"
chmod 600 "${key}"
RSA_PRIVATE_KEY="$(cat "${key}")"
export RSA_PRIVATE_KEY

echo "==> Static files for Caddy"
find /srv/static -mindepth 1 -delete
cp -R /app/static/. /srv/static/

# Uploads written by the API and the worker (saleor), read by Caddy.
find /app/media ! -user saleor -exec chown saleor:saleor {} +

echo "==> Migrations"
saleor python manage.py migrate --no-input

echo "==> Admin user and store settings"
saleor python manage.py stack_setup

echo "==> Done: Saleor ${SALEOR_VERSION:-}"
echo "    Dashboard: ${SALEOR_URL}/dashboard/ (${SALEOR_ADMIN_EMAIL})"
echo "    API:       ${SALEOR_URL}/graphql/"
