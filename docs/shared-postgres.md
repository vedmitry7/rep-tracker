# Production PostgreSQL dependency

RepTracker production runs only API and bot containers. The standalone
`shared-postgres` Compose project lives at
`/home/dmitry0711/infrastructure/shared-postgres/docker-compose.yml` on the
server. Its operator controls PostgreSQL start/stop; RepTracker deploy never
creates or removes it. API joins the external `shared_postgres_net` network and
uses `shared-postgres:5432`. Bot and Caddy continue to reach the API over
`rep-tracker_default`. AI Gateway shares the server but uses its own
`ai_gateway` database and role; RepTracker uses `rep_tracker` for both.

The server infrastructure README contains start/stop/status/logs, a procedure
for adding applications, migration rollback, and disaster recovery. The
external volume `rep-tracker_postgres_data` retains its historical name and
must never be deleted. During rollout, a server-side `deploy.hold` marker
prevents automatic GitHub Actions deployment until the infrastructure switch
is complete. Remove the marker only after both app configurations and the
database have been verified.

The inherited `rep_tracker` login is a PostgreSQL superuser. This migration
preserved its privileges to avoid breaking production. Least-privilege
hardening needs a separate, tested role migration; the current role can access
other databases on the same PostgreSQL instance.

`pg_dump` backs up database contents, not `.env` files or external API tokens.
Keep those separately in secure storage.
