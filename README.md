# pybackup-engine

> Production-grade backup engine for files and databases — with a built-in web dashboard, user login system, and pluggable database backends.

[![PyPI version](https://img.shields.io/pypi/v/pybackup-engine)](https://pypi.org/project/pybackup-engine/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Tests](https://github.com/selvaraj2003/pybackup/actions/workflows/pipeline.yml/badge.svg)](https://github.com/selvaraj2003/pybackup/actions)

---

## Features

| Feature               | Detail                                                                                              |
| --------------------- | --------------------------------------------------------------------------------------------------- |
| **Backup engines**    | Files, PostgreSQL (`pg_dump`), MySQL (`mysqldump`), MongoDB (`mongodump`), MS SQL Server (`sqlcmd`) |
| **Web dashboard**     | Built-in pure Python HTTP server — no Flask, FastAPI or Django                                      |
| **Login system**      | PBKDF2 password hashing, session tokens, admin/viewer roles                                         |
| **User management**   | Create, list, delete users via CLI or web UI                                                        |
| **Change password**   | Users can change their own password in the dashboard                                                |
| **Database backends** | SQLite (default), PostgreSQL, MySQL, MongoDB, MSSQL — like Django's `DATABASES`                     |
| **CLI**               | `run`, `serve`, `verify`, `checksum`, `config-check`, `user add/list/delete`                        |
| **Fonts**             | Space Grotesk headings · Inter body                                                                 |
| **Theme**             | Dark / Light toggle                                                                                 |

---

## Install

```bash
pip install pybackup-engine
```

With optional database backend support:

```bash
pip install pybackup-engine[postgresql]   # psycopg2-binary
pip install pybackup-engine[mysql]        # PyMySQL
pip install pybackup-engine[mongodb]      # pymongo
pip install pybackup-engine[mssql]        # pyodbc
pip install pybackup-engine[all]          # all backends
```

---

## Quick Start

### 1. Create the first admin user

```bash
pybackup user add --username admin --role admin
```

### 2. Write a config

```yaml
# pybackup.yaml
version: 1

global:
  backup_root: /backups
  retention_days: 7
  compress: true

# Internal metadata database (SQLite by default, switch to postgres/mysql/etc)
database:
  backend: sqlite
  name: /var/lib/pybackup/pybackup.db

postgresql:
  enabled: true
  jobs:
    - name: prod-db
      host: localhost
      database: myapp
      username: backup_user
      password: ${PGPASSWORD}

files:
  enabled: true
  jobs:
    - name: configs
      source: /etc/myapp
      exclude: ["*.log", "*.tmp"]
```

### 3. Run backups

```bash
pybackup run --config pybackup.yaml
```

### 4. Start the dashboard

```bash
pybackup serve --port 8200
```

Open **http://localhost:8200** → login with your admin credentials.

---

## CLI Reference

```
pybackup run           -c config.yaml [--dry-run]
pybackup serve         [--host 0.0.0.0] [--port 8200] [-c config.yaml]
pybackup verify        FILE --checksum SHA256 [--algorithm sha256]
pybackup checksum      FILE [--algorithm sha256]
pybackup config-check  -c config.yaml

pybackup user add          --username USER --role admin|viewer
pybackup user list
pybackup user delete       --username USER
pybackup user set-password --username USER
```

---

## Database Backends

Inspired by Django's `DATABASES` setting — just change the `backend:` value:

```yaml
# SQLite (default, zero config)
database:
  backend: sqlite
  name: /var/lib/pybackup/pybackup.db

# PostgreSQL
database:
  backend:  postgresql
  host:     localhost
  port:     5432
  name:     pybackup
  user:     pybackup_user
  password: ${DB_PASSWORD}

# MySQL / MariaDB
database:
  backend:  mysql
  host:     localhost
  name:     pybackup
  user:     pybackup_user
  password: ${MYSQL_PASSWORD}

# MongoDB
database:
  backend:  mongodb
  host:     localhost
  name:     pybackup
  user:     pybackup_user
  password: ${MONGO_PASSWORD}

# MS SQL Server
database:
  backend:  mssql
  host:     localhost
  name:     pybackup
  user:     sa
  password: ${MSSQL_PASSWORD}
```

---

## REST API

All endpoints under `/api/` — authenticated via `Authorization: Bearer <token>`:

| Method | Path                        | Auth    | Description                  |
| ------ | --------------------------- | ------- | ---------------------------- |
| POST   | `/api/auth/login`           | Public  | Login, returns session token |
| POST   | `/api/auth/logout`          | Session | Logout                       |
| GET    | `/api/auth/me`              | Session | Current user info            |
| POST   | `/api/auth/change-password` | Session | Change own password          |
| GET    | `/api/users`                | Admin   | List all users               |
| POST   | `/api/users`                | Admin   | Create user                  |
| DELETE | `/api/users/:id`            | Admin   | Delete user                  |
| GET    | `/api/stats`                | Session | Dashboard statistics         |
| GET    | `/api/runs`                 | Session | Paginated run list           |
| POST   | `/api/runs`                 | Session | Create a run entry           |
| GET    | `/api/runs/:id`             | Session | Run detail + files           |
| DELETE | `/api/runs/:id`             | Admin   | Delete a run                 |
| GET    | `/api/settings`             | Session | Get settings                 |
| POST   | `/api/settings`             | Session | Update settings              |

---

## Project Structure

```
pybackup/
├── cli.py                    # Click CLI (run/serve/verify/user)
├── auth.py                   # PBKDF2 passwords, session tokens, UserDB
├── constants.py
├── config/loader.py          # YAML + env var expansion
├── engine/
│   ├── base.py               # BaseBackupEngine (prepare/run/finalize)
│   ├── files.py              # File/dir backup with tar.gz support
│   ├── mongo.py / postgres.py / mysql.py / mssql.py
│   ├── verify.py             # SHA-256/512 checksums
│   └── manifest.py           # JSON sidecar manifests
├── db/
│   ├── database.py           # SQLite implementation
│   └── backends/
│       ├── __init__.py       # get_database() factory
│       ├── postgres_backend.py
│       ├── mysql_backend.py
│       ├── mongo_backend.py
│       └── mssql_backend.py
├── server/
│   ├── httpserver.py         # Pure stdlib ThreadingHTTPServer + Router
│   └── handlers.py           # All REST API handlers
└── static/
    ├── login.html            # Login page
    ├── index.html            # SPA dashboard
    ├── css/app.css           # Space Grotesk + Inter · dark/light
    └── js/app.js             # Vanilla JS SPA
```

---

## Security

- Passwords hashed with **PBKDF2-HMAC-SHA256** (600,000 iterations, 32-byte salt)
- Session tokens are **cryptographically random** 32-byte hex strings
- Sessions expire after **8 hours**
- Database credentials resolved from **environment variables** (`${VAR}` syntax)
- Constant-time password comparison to prevent timing attacks

---

## License

MIT © PyBackup Contributors
