# Development

## Install From a Clone

```bash
git clone https://github.com/bitsandflames/fyron.git
cd fyron
uv sync --all-extras --dev
```

## Run Tests

```bash
uv run pytest
```

Optional integration tests require a reachable FHIR server:

```bash
FYRON_INTEGRATION=1 uv run pytest tests/test_fhir_rest_integration.py
```

## Build Documentation Locally

```bash
uv run python scripts/build_docs.py
uv run python -m http.server 8001 --directory site
```

Then open `http://127.0.0.1:8001`.

## Publish Documentation With GitHub Pages

The repository ships a `Docs` GitHub Actions workflow that builds the custom BF docs site and deploys the generated `site/` folder.

1. Open repository settings on GitHub.
2. Go to **Pages**.
3. Set **Source** to **GitHub Actions**.
4. Push to `main` or run the workflow manually.

The deployed URL usually follows `https://<owner>.github.io/<repo>/`. For private repositories, GitHub Pages must be available for the current plan or enabled by the organization.

## Preparing a Release

Maintainers should follow the [repository release guide](https://github.com/bitsandflames/fyron/blob/main/release.MD) before tagging or publishing.

Minimum local checks:

```bash
uv run pytest
uv run python scripts/build_docs.py
uv build
uv run python scripts/check_release_readiness.py --skip-git-clean
```

Also confirm optional extras install cleanly for the release surface you changed, update README/docs for public API changes, and add release notes under `docs/releases/`.
