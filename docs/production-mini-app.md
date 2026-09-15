# Production: Telegram Mini App

This repository deploys the React/Vite application as static files. Caddy is
the only public entry point; the Docker API and PostgreSQL bindings stay on
loopback and are not published to the Internet.

## Files on the VPS

Create the static-file root once, replacing `DEPLOY_USER` with the account used
by the GitHub Actions SSH key:

```bash
sudo install -d -o DEPLOY_USER -g DEPLOY_USER -m 755 /var/www/repka
sudo install -d -o DEPLOY_USER -g DEPLOY_USER -m 755 /var/www/repka/releases
```

The GitHub deployment writes immutable releases to
`/var/www/repka/releases/<commit-sha>` and atomically points
`/var/www/repka/current` at the new release. It does not restart or reload
Caddy. Caddy must be able to traverse and read `/var/www/repka` (mode `755`
above is sufficient); `DEPLOY_USER` must own the root too because it switches
the `current` symlink there.

## Caddy

On the current VPS Caddy runs in the `lucera-site-caddy-1` container, with its
configuration in `/home/dmitry0711/projects/lucera-site`. Add the following
read-only bind mount and external network to its existing `caddy` service in
`/home/dmitry0711/projects/lucera-site/docker-compose.yml`:

```yaml
services:
  caddy:
    volumes:
      - /var/www/repka:/srv/repka:ro
    networks:
      - default
      - rep_tracker

networks:
  rep_tracker:
    external: true
    name: rep-tracker_default
```

`rep-tracker_default` already exists on this VPS. It lets Caddy reach only the
Docker-internal `api` service; it does not publish a new port.

Then add this site block to the existing
`/home/dmitry0711/projects/lucera-site/Caddyfile`. Keep the existing sites
unchanged. It forwards **only** the Mini App API prefix, and rejects every
legacy API path so the bot's unauthenticated, internal API contract cannot be
called through the public hostname.

```caddyfile
repka.lucerasoftware.ru {
	encode zstd gzip

	@mini_app_api path /api/mini-app/*
	handle @mini_app_api {
		uri strip_prefix /api
		reverse_proxy api:8000
	}

	@other_api path /api/*
	handle @other_api {
		respond "Not found" 404
	}

	root * /srv/repka/current
	try_files {path} /index.html
	file_server
}
```

Check the Compose configuration, validate Caddy, then recreate only the Caddy
container so it receives the new mount and network:

```bash
cd /home/dmitry0711/projects/lucera-site
docker compose config
docker compose exec caddy caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile
docker compose up -d caddy
```

The Repka `api` and `postgres` Compose ports must remain loopback-only, as they are
in `docker-compose.prod.yml`:

```text
127.0.0.1:8000:8000
127.0.0.1:${POSTGRES_HOST_PORT}:5432
```

## Authentication

The frontend reads `Telegram.WebApp.initData` and passes it unchanged as the
`X-Telegram-Init-Data` header. FastAPI verifies Telegram's HMAC using the
backend-only `TELEGRAM_BOT_TOKEN`, rejects stale data (default: 24 hours), and
uses the verified Telegram user ID as `telegram` identity. The frontend never
sends an identity field and never receives the bot token.

`TELEGRAM_BOT_TOKEN` is already the bot's secret in production `.env`; the API
service now receives the same value solely to validate Mini App requests.
Optionally set `TELEGRAM_INIT_DATA_MAX_AGE_SECONDS=86400` in that `.env`.

## GitHub Actions secrets

The existing production workflow needs these repository or environment secrets:

- `VPS_SSH_PRIVATE_KEY` — dedicated deploy key, with no passphrase prompt.
- `VPS_KNOWN_HOSTS` — pinned `known_hosts` line for the VPS SSH host and port.
- `VPS_HOST`, `VPS_PORT`, `VPS_USER` — SSH destination details.

`GITHUB_TOKEN` is supplied by GitHub Actions and is used only to read the
private GHCR application images. No bot token or database password belongs in
GitHub Secrets for the frontend deployment; those stay in the VPS `.env`.

## BotFather

After Caddy serves the site over HTTPS, configure the bot's Main Mini App URL
to `https://repka.lucerasoftware.ru` in BotFather. Use the Mini App launch
button/menu for testing. Telegram will then supply the signed `initData` used
by this API.
