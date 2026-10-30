# Start Curate

Run Curate locally with Fyron and Docker Compose. You do not need to configure a database yourself.

## Install

You need **Python 3.11+**, `uv`, and Docker Desktop or another running Docker engine with the Compose plugin. Run these commands in your Python project:

```bash
uv add "fyron[curate]"
docker info
docker compose version
uv run fyron curate --open
```

The first launch builds the app containers and may download Docker images and dependencies. It starts the frontend, API, and PostgreSQL. Open [localhost:5174](http://localhost:5174/) if the browser does not open automatically. If Fyron is already on your shell's PATH, `fyron curate --open` is equivalent.

The frontend uses port **5174** and the API uses **4000**. Both bind to `127.0.0.1`; PostgreSQL has no host port. Curate is intended for local use with one API process and has no shared-server authentication. Do not expose these ports to a network without an authenticated deployment.

## Startup options

| Option | When to use it |
| --- | --- |
| `--open` | Open the browser after startup. |
| `--no-build` | Reuse existing images after a successful first build. |
| `--foreground` | Keep Docker logs attached to the terminal. |
| `--app-dir PATH` | Use a specific Curate folder containing `docker-compose.yml`. |

```bash
uv run fyron curate --no-build --open
```

Use the same app directory and Compose project when returning to existing cohorts. Changing the project or app location may select a different set of Docker volumes.

## Stop and restart safely

For the default app location, resolve the same directory that the Fyron launcher uses:

```bash
CURATE_APP_DIR="$(uv run python -c 'from fyron.curate import default_app_dir; print(default_app_dir())')"
docker compose --project-directory "$CURATE_APP_DIR" stop
```

If you started with `--app-dir`, set `CURATE_APP_DIR` to that directory instead. To resume the same project:

```bash
docker compose --project-directory "$CURATE_APP_DIR" start
```

Stopping containers preserves data. **Do not use `down --volumes` or remove the volumes unless you intend to delete Curate's stored data.**

| Persistent volume | Contents |
| --- | --- |
| `postgres_data` | Cohorts, review decisions, settings, and export metadata |
| `uploaded_cohorts` | Uploaded originals, mounted at `/data/uploads` in the backend |
| `clean_exports` | Selected-file exports, mounted at `/data/exports` in the backend |

Compose prefixes volume names with its project name. Uploaded data is copied into these volumes; your original source directory is not mounted or modified.

## Troubleshooting

| Symptom | Next step |
| --- | --- |
| Docker is missing or unreachable | Install/start your Docker runtime, then check `docker info` and `docker compose version`. |
| Port 5174 or 4000 is already in use | Stop the conflicting local service or the earlier Curate project you intended to replace, then retry. |
| First build fails | Check Docker's network access and available disk space. Retry without `--no-build`; use `--foreground` to inspect startup logs. |
| Browser opens before the app is ready | Wait for startup to finish, then refresh `http://localhost:5174/`. |
| Existing cohorts appear missing | Confirm you are using the original app directory and Compose project. Do not delete volumes while investigating. |

[Prepare your data](prepare-data.md) · [Review and export](review-export.md) · [Try the synthetic cohort](../curate.md#try-the-example-cohort)
