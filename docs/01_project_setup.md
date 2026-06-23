# Project Setup & Configuration Documentation

This document outlines the architecture, design choices, and file configurations implemented for the `wingz-technical-assessment` backend REST API boilerplate.

---

## 1. Design Philosophy: KISS

To minimize tech debt and avoid over-engineering, this boilerplate adheres strictly to the KISS principle, optimizing for size, readability, and modern tooling compatibility:

- **Up-to-Date Core Tech Stack**: Target **Python 3.14**, **Django 6**, and **PostgreSQL 17** (Alpine) to leverage the latest performance improvements, security patches, and language features from day one.
- **Minimalist Settings**: Removed unnecessary default configurations for now (Django Admin, templates configuration, static files serving, internalization, password validators) to keep the configuration file small and focused on a headless REST API.
- **Single Database Engine**: Configured strictly for PostgreSQL using environment variables.
- **Absolute Environment Parity**: Development dependencies are installed and run exclusively inside the Docker containers to keep the host machine clean and guarantee the exact same setup across all developer environments and the CI pipeline.

---

## 2. Directory Layout Tree

The generated boilerplate matches the following structure:

```
wingz-technical-assessment/
├── .github/
│   └── workflows/
│       └── ci.yml             # CI workflow
├── config/
│   ├── __init__.py            # Package marker
│   ├── settings.py            # Django settings
│   ├── urls.py                # Root URLs
│   ├── asgi.py                # ASGI entrypoint
│   └── wsgi.py                # WSGI entrypoint
├── docs/
│   └── 01_project_setup.md       # [THIS FILE] Project setup documentation
├── tests/
│   └── test_placeholder.py    # Suite verifying settings and pytest config
├── Dockerfile                 # Container configuration with uv
├── docker-compose.yml         # Container services orchestration (web, db)
├── Makefile                   # Developer CLI commands wrapped around docker
├── manage.py                  # Django manage.py
├── pyproject.toml             # Project metadata, dependencies, lint & test configs
└── README.md                  # Project README
```

---

## 3. Component Details

### A. Dependency Management (`pyproject.toml`)
- Configured using PEP 621 standards.
- Production dependencies: `django>=6.0.0`, `djangorestframework>=3.15.2`, `psycopg[binary]>=3.2.1`, `python-dotenv>=1.0.1`.
- Dev/Test dependency group: `pytest`, `pytest-django`, `pytest-cov`, `ruff`, and `complexipy`.
- **Ruff Quality Assurance**: Configured with strict quality rules including `E` (Pycodestyle errors), `F` (Pyflakes), `I` (Isort), `W` (Pycodestyle warnings), `UP` (Pyupgrade), `PL` (Pylint), `RUF` (Ruff-specific), `N` (naming conventions), `B` (Bugbear), and `C4` (comprehensions).

### B. Core Django (`config/`)
- **`settings.py`**: Loads variables from a `.env` file if it exists, falling back to secure defaults. Has a minimal `INSTALLED_APPS` registration (`django.contrib.auth`, `django.contrib.contenttypes`, `rest_framework`) and a single `CommonMiddleware`.
- **`urls.py`**: Declares an empty `urlpatterns` block to serve as a clean canvas for future REST routes.
- **`manage.py`**: Excludes the nested import rule locally via a `# noqa: PLC0415` comment to preserve Django's native dependency checking behavior when starting the server.

### C. Containerization (`Dockerfile` & `docker-compose.yml`)
- **`Dockerfile`**: Leverages `python:3.14-slim` and secures the Astral `uv` binary. It runs a cached two-step dependency sync (`uv pip install --system -r pyproject.toml` and `uv pip install --system --group dev`) to ensure all development utilities are available inside the container.
- **`docker-compose.yml`**: Defines a `db` service using the latest `postgres:17-alpine` with an mapped port and persistent volume, and a `web` service linked to the local workspace code to hot-reload edits.

### D. Automation (`Makefile`)
- Wraps docker commands to offer short CLI commands to developers and improve DX:
  - `make build`: Compiles the dev docker container.
  - `make up`: Spins up the PostgreSQL database and Django web server.
  - `make down`: Shuts down active compose containers.
  - `make migrate`: Generates and runs database migrations.
  - `make test`: Runs `pytest` inside the container.
  - `make lint-check`: Performs Ruff quality and styling checks inside the container.
  - `make lint-format`: Performs Ruff format check.
  - `make complexity-check`: Audits cognitive complexity inside the container.
  - `make lock`: Resolves project requirements and generates/syncs a local `uv.lock` file.

### E. Continuous Integration (`.github/workflows/ci.yml`)
- Runs the test, lint, and formatting pipelines on **pushes to the `main` branch**.
- Uses GitHub Actions **container jobs** syntax to run directly inside a `python:3.14-slim` container, avoiding installation overheads.
- Syncs dependencies using `uv` cache actions and runs the suite.

---

## 4. How to run checks locally

Ensure **Docker** is installed and running on your system, then execute the following steps:

1. **Build the environment:**
   ```bash
   make build
   ```

2. **Start the database and web server:**
   ```bash
   make up
   ```

3. **Run migrations, code checks, and tests:**
   ```bash
   make migrate
   make test
   make lint
   make complexity
   ```

4. **Shutdown the environment:**
   ```bash
   make down
   ```
