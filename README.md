## Twio X Website ##
This Repo contains the codebase for our current website at https://twio-x.de/.

### Requirements ###

- [uv](https://docs.astral.sh/uv/) – installs Python and all dependencies
- SQLite – the local database; Python ships with it, the `sqlite3` CLI is optional
- MySQL client library and `pkg-config` – needed to build `mysqlclient`
  - macOS: `brew install mysql-client pkgconf` and `export PKG_CONFIG_PATH="$(brew --prefix mysql-client)/lib/pkgconfig"`
  - Debian/Ubuntu: `apt install default-libmysqlclient-dev pkg-config`

### Local setup ###

```bash
git clone https://github.com/twiox/web
cd web
uv sync
uv run manage.py migrate
uv run manage.py createsuperuser
uv run manage.py runserver
```

Open http://localhost:8000 and log in with your superuser.

No configuration needed: `twio_web/settings.py` defaults to local development (debug on, `db.sqlite3`, emails printed to the console). Every value can be overridden with an environment variable.

### Tests ###

```bash
uv run manage.py test
```

### Production ###

Deployed with Coolify from `docker-compose-server.yml`. The values come from environment variables set in Coolify. `SECRET_KEY` is required. The SQLite database lives at `SQLITE_PATH` on the `sqlite-volume`.
