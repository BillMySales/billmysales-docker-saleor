#!/bin/sh
# shellcheck disable=SC2153 # variables set by compose
# Entrypoint of the Saleor containers (setup, api, worker, beat, console):
# builds Saleor's settings from the stack's variables, then runs the command.
# - DATABASE_URL, EMAIL_URL / USER_EMAIL_URL (URL-encoded credentials).
# - ALLOWED_HOSTS / ALLOWED_CLIENT_HOSTS: SALEOR_URL's host plus extras.
# - RSA_PRIVATE_KEY (signs the API's JWTs) from the keys volume.
set -eu

urlencode() { python -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$1"; }

DATABASE_URL="postgres://$(urlencode "${DB_USER}"):$(urlencode "${DB_PASSWORD}")@${DB_HOST}:${DB_PORT}/${DB_NAME}"
export DATABASE_URL

host="$(python -c 'import sys, urllib.parse; print(urllib.parse.urlsplit(sys.argv[1]).hostname)' "${SALEOR_URL}")"
ALLOWED_HOSTS="${host}${SALEOR_ALLOWED_HOSTS:+,${SALEOR_ALLOWED_HOSTS}}"
ALLOWED_CLIENT_HOSTS="${host}${SALEOR_ALLOWED_CLIENT_HOSTS:+,${SALEOR_ALLOWED_CLIENT_HOSTS}}"
export ALLOWED_HOSTS ALLOWED_CLIENT_HOSTS

# SMTP_SECURE: tls = STARTTLS, ssl = SMTPS, none = plain. EMAIL_URL is for
# staff emails (AdminEmailPlugin), USER_EMAIL_URL for customer emails
# (UserEmailPlugin). Without SMTP_HOST the email plugins stay inactive.
if [ -n "${SMTP_HOST:-}" ]; then
    auth=""
    if [ -n "${SMTP_USER:-}" ]; then
        auth="$(urlencode "${SMTP_USER}"):$(urlencode "${SMTP_PASSWORD:-}")@"
    fi
    case "$(echo "${SMTP_SECURE:-tls}" | tr '[:upper:]' '[:lower:]')" in
        ssl) query="?ssl=True" ;;
        none) query="" ;;
        *) query="?tls=True" ;;
    esac
    EMAIL_URL="smtp://${auth}${SMTP_HOST}:${SMTP_PORT}/${query}"
    USER_EMAIL_URL="${EMAIL_URL}"
    export EMAIL_URL USER_EMAIL_URL
fi
DEFAULT_FROM_EMAIL="${SMTP_FROM}"
export DEFAULT_FROM_EMAIL

if [ -s "${KEYS_DIR}/rsa.pem" ]; then
    RSA_PRIVATE_KEY="$(cat "${KEYS_DIR}/rsa.pem")"
    export RSA_PRIVATE_KEY
fi

exec "$@"
