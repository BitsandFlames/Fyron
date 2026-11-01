# Start Curate

Curate is now a [standalone application](https://github.com/BitsandFlames/Curate). Detailed guides live in its repository. Fyron retains the preview-preparation tools.

**Version note:** the current Fyron source no longer bundles Curate or provides its launcher. Published Fyron Beta 4 packages remain unchanged. Existing users should follow the [storage migration guide](https://github.com/BitsandFlames/Curate/blob/main/docs/migration.md) before switching checkouts.

## Install

[Read this section in the Curate guide](https://github.com/BitsandFlames/Curate/blob/main/docs/start.md#install).

```bash
git clone https://github.com/BitsandFlames/Curate.git
cd Curate
docker compose up --build -d
```

Open http://localhost:5174/. Git and Docker Compose are required; Python is optional.

## Startup options

[Read this section in the Curate guide](https://github.com/BitsandFlames/Curate/blob/main/docs/start.md#startup-options).

## Stop and restart safely

[Read this section in the Curate guide](https://github.com/BitsandFlames/Curate/blob/main/docs/start.md#stop-and-restart-safely).

## Troubleshooting

[Read this section in the Curate guide](https://github.com/BitsandFlames/Curate/blob/main/docs/start.md#troubleshooting).
