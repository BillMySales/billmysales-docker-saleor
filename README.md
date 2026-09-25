Saleor Docker stack
===================

Docker Compose stack for [Saleor](https://saleor.io) (open source headless
commerce platform: GraphQL API, dashboard, webhooks for apps), usable for
local development and for simple production deployments (a single server).
Maintained by [BillMySales](https://www.billmysales.com).

| Component   | Image                                   | Default version |
|-------------|-----------------------------------------|-----------------|
| Web server  | `caddy:<ver>-alpine`                    | 2.11            |
| Saleor API, worker, beat | `ghcr.io/saleor/saleor`    | 3.23.36         |
| Dashboard   | `ghcr.io/saleor/saleor-dashboard`       | 3.23.34         |
| Database    | `postgres:<ver>-alpine`                 | 15              |
| Cache/queue | `valkey/valkey:<ver>-alpine`            | 8.1             |
| Mailpit     | `axllent/mailpit` (optional, dev)       | v1.31           |

Saleor's official images are production images (amd64 and arm64; tested on
arm64): the API (Python 3.12, uvicorn) and the dashboard (a static app on
nginx). PostgreSQL 15 and Valkey 8.1 are what Saleor's CI tests with.
Saleor's own `saleor-platform` compose file is for local development only
(published database ports, default secrets, debug on).

**There is no shop front for customers**: Saleor is headless, this stack
gives the dashboard and the API, and the public shop is a separate app. See
[Storefronts](#storefronts).

Requirements
------------

- Docker Engine 24+ with the Compose v2 plugin (`docker compose`, 2.24+).
- About 1.5 GB of disk for the images; 1.5 GB of RAM for the stack.
- Development: ports 8113, 8413 and 8025 free on the host.
- Production: a server with ports 80 and 443 reachable, and a DNS record for
  the site's domain pointing to it.

Quick start (development)
-------------------------

```shell
cp .env.dev.example .env
docker compose up -d
docker compose logs -f setup   # wait for "==> Done" (~2 minutes the first time)
```

- Dashboard: http://localhost:8113/dashboard/ (user `admin@example.com`,
  password `admin12345`).
- GraphQL API: http://localhost:8113/graphql/ (the playground is enabled in
  the development template).
- Mailpit (every email Saleor sends): http://localhost:8025

Production
----------

```shell
cp .env.prod.example .env
# Fill in SALEOR_URL, SITE_ADDRESS, SECRET_KEY, DB_PASSWORD,
# SALEOR_ADMIN_EMAIL, SALEOR_ADMIN_PASSWORD and the SMTP_* values.
docker compose up -d
```

- With `SITE_ADDRESS` set to the domain, Caddy gets a Let's Encrypt certificate
  and renews it automatically (certificates live in the `caddy_data` volume).
- Behind another TLS-terminating proxy, use `SITE_ADDRESS=:80`.
- Compose refuses to start while a required value is missing.
- The `backup` profile is enabled by default in the production template.
- Behind an existing Traefik (no host ports), use `overrides/traefik.yaml`
  (see [Overrides](#overrides)).

Services
--------

| Service     | Profile   | Role                                                          |
|-------------|-----------|---------------------------------------------------------------|
| `db`        |           | PostgreSQL, data in the `db_data` volume.                     |
| `valkey`    |           | Cache and Celery broker.                                      |
| `setup`     |           | One-shot job (`scripts/setup.sh`), runs on every `up`.        |
| `api`       |           | GraphQL API (uvicorn), thumbnails, JWKS, app webhooks.        |
| `worker`    |           | Celery worker: emails, webhooks, thumbnails, exports.         |
| `beat`      |           | Celery beat: Saleor's scheduled tasks.                        |
| `dashboard` |           | The dashboard (static app on the image's nginx).              |
| `caddy`     |           | TLS, routing, media and static files; the only published ports. |
| `console`   | `tools`   | Saleor's `manage.py`.                                         |
| `backup`    | `backup`  | Database dump + media + RSA key on a schedule.                |
| `mailpit`   | `mailpit` | Development SMTP server that catches all mail.                |

Caddy routes one site: `/graphql/` and Saleor's other routes to the API,
`/dashboard/` to the dashboard (which calls the API on the same origin, so
changing `SALEOR_URL` needs no rebuild), `/media/` (uploads) and `/static/`
(copied from the image by `setup`) from volumes, since Saleor doesn't serve
them in production, and `/` redirects to the dashboard.

The Saleor containers run as the image's `saleor` user (the image itself
runs as root). Saleor's settings come from environment variables; the stack
adds a small settings module (`config/saleor/stack_settings.py`, Saleor's
settings plus the `stack` app) for the setup command and the email price
format.

### What `setup` does

- The RSA key (`keys` volume), generated once: it signs the API's JWTs
  (logins, app tokens) and webhook payloads. **Back it up**: the `backup`
  service includes it.
- `manage.py migrate`: on a new database, Saleor also creates its defaults
  (channel, warehouse, shipping zone, product type, category).
- `manage.py stack_setup` (`config/saleor/stack/management/commands`):
  - the admin user (a superuser: `SALEOR_ADMIN_EMAIL`,
    `SALEOR_ADMIN_PASSWORD`), if missing;
  - once (then kept as edited in the dashboard): the defaults adapted to the
    store (channel "Tienda" in CLP for Chile, unpaid orders allowed, warehouse
    "Bodega" in Santiago, shipping zone Chile with a free "Despacho" method,
    IVA 19% flat rate with prices including tax, product type "Producto" and
    category "General"), the admin as recipient of new order emails, and
    Spanish email templates and subjects;
  - every run: the site's domain from `SALEOR_URL`, the email plugins on or
    off (`SMTP_HOST`) and their sender (`SMTP_FROM`, `SMTP_FROM_NAME`).
- Copies the image's static files for Caddy.

Common commands
---------------

```shell
docker compose ps                        # status: every service "healthy", setup "Exited (0)"
docker compose logs -f api worker        # logs
docker compose exec db psql -U saleor saleor   # SQL shell
docker compose run --rm console help     # manage.py (profile "tools")
docker compose run --rm console changepassword admin@example.com
docker compose down                      # stop, keep data
docker compose down -v                   # stop and DELETE all data
```

Store settings
--------------

- Prices are entered including IVA; Saleor computes the tax inside them
  (2 × $9.990 = $19.980, of which $3.190 IVA). Amounts in CLP have no
  decimals.
- **Payments**: Saleor has no built-in offline payment method; payment
  gateways are apps (Stripe, Adyen...) hosted separately. The channel allows
  unpaid orders (`SALEOR_ALLOW_UNPAID_ORDERS`): the checkout completes
  without a payment, the order stays unconfirmed and unpaid, and staff
  confirms it and marks it as paid in the dashboard (like a bank transfer).
- The dashboard's default language is fixed when its image is built
  (English); each user can switch it to Spanish in the dashboard (stored in
  the browser).
- Saleor keeps dates in UTC (not configurable).

Emails
------

Saleor's built-in email plugins send them through SMTP (`SMTP_*`; `SMTP_SECURE`:
`tls` = STARTTLS, `ssl` = SMTPS, `none`), from the Celery worker:

- **User emails** (customers, per channel): order details, order confirmed,
  fulfillment (shipped), shipping update, payment, cancellation, refund,
  account confirmation, password reset, email change, gift card, invoice.
- **Admin emails** (staff): new order (to the staff notification recipients;
  the admin is added), staff invitation, dashboard password reset, CSV
  exports.

The stack stores Spanish versions of Saleor's own templates (the image's
templates with the texts translated by `config/saleor/stack/emails_es.py`)
and subjects, once; edit them in the dashboard (Configuration > Plugins).
Saleor formats amounts in emails in English (`CLP19,980`); the stack formats
them with `SALEOR_EMAIL_LOCALE` (`$19.980`). Without `SMTP_HOST` the
plugins are off and no email is sent.

Storefronts
-----------

Saleor is **headless**: products, prices and taxes, checkout, orders and
customers are in the API and the dashboard, but there are no public shop
pages. The shop front is a separate application that calls the GraphQL API
(`checkoutCreate`, `checkoutDeliveryMethodUpdate`, `checkoutComplete`...):
Saleor's [storefront](https://github.com/saleor/storefront) (Next.js) is the
usual starting point, not part of this stack. Its host goes in
`SALEOR_ALLOWED_CLIENT_HOSTS` (redirect links in emails) and, if it calls the
API from the browser, its origin in `ALLOWED_GRAPHQL_ORIGINS`.

Integrations (apps and webhooks)
--------------------------------

External systems integrate as Saleor apps: an app (created in the dashboard
or with `appCreate`) gets a token with its permissions and webhooks for
events (`ORDER_CREATED`, `ORDER_FULLY_PAID`, `ORDER_FULFILLED`,
`ORDER_REFUNDED`, `ORDER_CANCELLED`...), with a GraphQL subscription as the
payload. Payloads are signed (`Saleor-Signature`, JWS RS256 with the RSA key;
public key at `<url>/.well-known/jwks.json`). A BillMySales integration would
be such an app.

Saleor refuses webhook and app URLs on private or loopback addresses
(`HTTP_IP_FILTER_ENABLED=True`, SSRF protection); the development template
disables it so apps on the host (`http://host.docker.internal:<port>`)
work.

Backups
-------

With the `backup` profile, the `backup` service writes `<timestamp>-db.dump`
(`pg_dump` custom format) and `<timestamp>-files.tar.gz` (media and the RSA
key) to the `backups` volume (or `./data/backups` with
`overrides/local-dirs.yaml`) at start and then every `BACKUP_INTERVAL_HOURS`,
and deletes files older than `BACKUP_KEEP_DAYS`. Files are readable by their
owner only (they contain the key).

```shell
docker compose run --rm --no-deps backup now                  # back up now
docker compose run --rm --no-deps backup list                 # list timestamps
docker compose stop api worker beat                 # stop the app first
docker compose run --rm --no-deps backup restore <timestamp>   # database, media, key
docker compose exec valkey valkey-cli FLUSHALL      # cache and queued tasks of the old data
docker compose up -d
```

`--no-deps` keeps the commands from starting `setup` first (with a
damaged database or key `setup` fails and the restore would never run);
the database must be running (`docker compose up -d db` if the stack is
down). A restore replaces the database with a fresh
copy, so nothing created after the backup remains.

Upgrades
--------

Saleor maintains several minor lines at once (3.21, 3.22, 3.23), with patch
releases about weekly. Back up first, then change `SALEOR_VERSION` (and
`SALEOR_DASHBOARD_VERSION`, the latest of the same minor line) in `.env` and
run `docker compose up -d`: the new images are pulled and `setup` runs the
migrations before the API starts. Read Saleor's release notes for a new
minor version.

Overrides
---------

Optional compose files in `overrides/`, enabled with `COMPOSE_FILE` in `.env`
(several are combined with `:`). Each file documents its variables.

```shell
COMPOSE_FILE=compose.yaml:overrides/traefik.yaml:overrides/local-dirs.yaml
```

| File                        | Purpose                                                            |
|-----------------------------|--------------------------------------------------------------------|
| `overrides/traefik.yaml`    | Publish through an existing Traefik on a shared external network:  |
|                             | no host ports, Traefik terminates TLS (`TRAEFIK_HOST`, ...).       |
| `overrides/local-dirs.yaml` | Database, Valkey, media, key, static files, Caddy and backups in   |
|                             | local directories (`DATA_DIR`, default `./data`).                  |

A local `compose.override.yaml` (gitignored) is also loaded automatically by
Docker Compose, for changes specific to one machine.

Configuration
-------------

Every variable is documented in `.env.prod.example`. Main groups:

- **Site and network**: `SALEOR_URL`, `SITE_ADDRESS`, `HTTP_BIND`,
  `HTTP_PORT`, `HTTPS_PORT`, `SALEOR_ALLOWED_HOSTS`,
  `SALEOR_ALLOWED_CLIENT_HOSTS`, `ALLOWED_GRAPHQL_ORIGINS`, `SALEOR_PLAYGROUND`.
- **Credentials**: `SECRET_KEY`, `DB_PASSWORD`, `SALEOR_ADMIN_EMAIL`,
  `SALEOR_ADMIN_PASSWORD` (required).
- **Store** (first install only): `SALEOR_STORE_NAME`, `SALEOR_CHANNEL_*`,
  `SALEOR_CURRENCY`, `SALEOR_COUNTRY`, `SALEOR_CITY`, `SALEOR_ZONE_NAME`,
  `SALEOR_TAX_RATE`, `SALEOR_PRICES_INCLUDE_TAX`,
  `SALEOR_ALLOW_UNPAID_ORDERS`, `SALEOR_EMAILS_SPANISH`, `SALEOR_EMAIL_LOCALE`.
- **Webhooks**: `HTTP_IP_FILTER_ENABLED`, `HTTP_IP_FILTER_ALLOW_LOOPBACK_IPS`.
- **Versions**: `SALEOR_VERSION`, `SALEOR_DASHBOARD_VERSION`,
  `POSTGRES_VERSION`, `VALKEY_VERSION`, `CADDY_VERSION`, ...
- **Mail**: `SMTP_HOST`, `SMTP_PORT`, `SMTP_SECURE`, `SMTP_USER`,
  `SMTP_PASSWORD`, `SMTP_FROM`, `SMTP_FROM_NAME`.
- **Processes, resources and logs**: `UVICORN_WORKERS`, `CELERY_CONCURRENCY`,
  `*_MEMORY_LIMIT` per service, `UPLOAD_MAX_SIZE`, `LOG_MAX_SIZE`,
  `LOG_MAX_FILE`.

Notes:

- Production settings: `DEBUG=False` (Saleor defaults to `True`), usage
  telemetry off (Saleor sends it by default), GraphQL playground off.
- uvicorn trusts `X-Forwarded-For`/`-Proto` from Caddy (the only client of
  the API), so Saleor sees the real client IP and `https://` behind Caddy and
  Traefik.
- Uploads are public under `/media/` (like Saleor with local storage),
  including CSV exports (random file names).
- From inside the containers, the host machine is reachable as
  `host.docker.internal`.

Security
--------

- No default secrets: compose fails if the required passwords and secrets are
  missing. The development template uses public values; never use it on a
  server.
- Saleor runs as the `saleor` user, not root; only Caddy (and Mailpit in
  development) publishes ports; the API, the dashboard, PostgreSQL and Valkey
  are internal. `HTTP_BIND` defaults to `127.0.0.1`.
- The RSA key volume is private (mode 700); the key is passed to Saleor in an
  environment variable, as Saleor expects.
- Webhooks to private addresses are refused in production (see above).
- Not included: a web application firewall or off-site backup copies.

Validation
----------

What was checked for this stack (2026-09-24):

- Clean start (`down -v` + `up -d`, images pulled) in about 2 minutes (the
  migrations take most of it): every service `healthy`, `setup` `Exited (0)`;
  a second run makes no changes; changes in the dashboard (channel name,
  unpaid orders) are kept.
- Dashboard and its 47 assets; API login (`tokenCreate`); product, variant,
  stock and channel listing through the API; a full checkout (2 × $9.990 =
  $19.980 with $3.190 IVA, "Despacho" shipping, unpaid order); staff flow
  (confirm, mark as paid, fulfill).
- Emails through SMTP to Mailpit, in Spanish with `$19.980`: order details
  (customer), new order (staff), order confirmed, order shipped, dashboard
  password reset (link to the dashboard; a redirect to another host is
  refused).
- Product image upload; thumbnails generated and served by Caddy.
- An app webhook (`ORDER_CREATED`) delivered to a receiver on the host,
  signed with the RSA key.
- Backup and restore (an order created after the backup is gone; media and
  key back, logins work).
- Upgrade 3.22.71 → 3.23.36 with data: migrations applied, orders kept, a new
  order afterwards; the upgraded schema (columns, indexes, constraints) is
  identical to a fresh 3.23.36 install's.
- HTTPS with `SITE_ADDRESS=localhost` (site domain and email links on
  `https://localhost:8413`); URL change and back; overrides: Traefik v3.6
  routing with no host ports (client IP kept), local directories (fresh
  install).
- Not tested: issuing a real Let's Encrypt certificate (needs a public
  domain), payment apps, a storefront, SMTPS/STARTTLS with a real provider.

Resource usage
--------------

Idle, after a few requests: API ~530 MiB (2 uvicorn workers), Celery worker
~450 MiB (2 processes), beat ~260 MiB, PostgreSQL ~50 MiB, Caddy ~15 MiB,
dashboard ~10 MiB, Valkey ~5 MiB (about 1.3 GiB in total). API image ~920 MB.

License
-------

[MIT](LICENSE).
