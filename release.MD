# Release Guide

Fyron uses `uv`, PEP 621 package metadata, and Git tags named `vX.Y.Z`. Use this guide for beta, release-candidate, and stable PyPI releases.

## Versioning

Use PEP 440 versions:

- Beta: `0.2.7b1`, `0.2.7b2`
- Release candidate: `0.2.7rc1`
- Stable: `0.2.7`

Update every version source before building:

- `pyproject.toml` (`project.version`)
- `CITATION.cff` (`version` and release date when applicable)
- any explicit fallback version constants or docs snippets found by:

```bash
rg -n "0\\.2\\.|version|__version__" pyproject.toml CITATION.cff src docs README.md
```

## Preflight

Start from a clean working tree and update release notes:

```bash
git status --short
uv run python scripts/check_release_readiness.py --skip-package
uv run python scripts/generate_function_reference.py
uv run python scripts/build_docs.py
uv run pytest
uv build
uv run python scripts/check_release_readiness.py
rg -n "href=\"[^\"]+\\.md" site
```

For larger releases, also run focused checks for changed areas, for example:

```bash
uv run pytest tests/test_api_design.py tests/test_dicom_downloader.py tests/test_cohort.py
```

## Build And Inspect

Clean stale artifacts, build, and inspect the wheel metadata:

```bash
rm -rf dist/
uv build
python -m zipfile -l dist/*.whl | head
python -m tarfile -l dist/*.tar.gz | head
uv run python scripts/check_release_readiness.py
```

The release-readiness audit must not report generated Curate files such as `node_modules`, frontend `dist`, uploads, exports, local databases, or Docker volume data in package archives.

Smoke-test the built wheel in a temporary environment:

```bash
uv venv /tmp/fyron-wheel-smoke
uv pip install --python /tmp/fyron-wheel-smoke/bin/python dist/fyron-*.whl
/tmp/fyron-wheel-smoke/bin/python -c "import fyron; print(fyron.__version__)"
```

## Publish

TestPyPI is recommended for first-time or large packaging changes:

```bash
uv publish --publish-url https://test.pypi.org/legacy/ --token YOUR_TESTPYPI_TOKEN
```

Publish to PyPI only after tests, docs, and wheel smoke checks pass:

```bash
uv publish --token YOUR_PYPI_TOKEN
```

Treat PyPI tokens as short-lived secrets. Do not commit or paste them into release notes. Rotate the token after use when it has been shared in a chat or terminal transcript.

## Verify PyPI

Install from PyPI in a fresh temporary environment and confirm the published version:

```bash
uv venv /tmp/fyron-pypi-smoke
uv pip install --python /tmp/fyron-pypi-smoke/bin/python "fyron==0.2.7"
/tmp/fyron-pypi-smoke/bin/python -c "import fyron; print(fyron.__version__)"
```

## Tag And Push

Commit release files, tag the exact commit, and push both branch and tag:

```bash
git add pyproject.toml CITATION.cff CHANGELOG.md docs/reference docs/releases
git commit -m "Release Fyron 0.2.7"
git tag v0.2.7
git push origin main
git push origin v0.2.7
```

Create a GitHub Release from the tag. Use the matching note in `docs/releases/` as the release body when available.

## Software DOI With Zenodo

1. Sign in to [Zenodo](https://zenodo.org/) with the maintainer account and connect
   GitHub. Grant the organization access needed for BitsandFlames/Fyron.
2. Enable Fyron in [Zenodo's GitHub settings](https://zenodo.org/account/settings/github/).
   Check for an existing Fyron record first to avoid creating a separate DOI family.
3. Review CITATION.cff authors, license, version, and date before publishing.
   Keep this as the metadata source; adding .zenodo.json would override it.
4. Publish a GitHub Release for the pushed version tag. A tag push alone does not
   archive the software. Wait for Zenodo to process the release and verify the record.
5. Record the minted version DOI in citation metadata and the all-versions
   (concept) DOI in the README badge, after verifying both. Never insert placeholders.
   Do not move the published tag to add a subsequently assigned DOI.
6. In papers, cite the version DOI for the exact release used. The concept DOI
   identifies the software across releases. Export BibTeX from the Zenodo record.

If a GitHub Release predates the integration, follow Zenodo's manual software
upload workflow or publish a subsequent release; do not assume old releases were
automatically archived. DOI publication requires an authenticated Zenodo account.

Official guides: [enable and archive GitHub software](https://help.zenodo.org/docs/github/),
[citation metadata](https://help.zenodo.org/docs/github/describe-software/),
[DOI versioning](https://zenodo.org/help/versioning).

## Final Checklist

- Version bumped in `pyproject.toml` and `CITATION.cff`.
- Changelog and GitHub release draft updated.
- Generated reference and docs rebuilt.
- `scripts/check_release_readiness.py` passes before and after `uv build`, including postponed desktop-tool absence, Pages workflow, built-site link, and package archive checks.
- No raw `.md` links in `site/`.
- Tests passed.
- Package built.
- Built wheel smoke test passed.
- PyPI publish succeeded.
- Fresh PyPI install verified.
- Git tag pushed.
- PyPI token rotated if it was exposed outside a secret manager.
