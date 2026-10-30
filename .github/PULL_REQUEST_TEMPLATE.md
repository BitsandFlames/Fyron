## Summary

Describe the change and the workflow it supports.

## API and behavior

- [ ] No public API behavior changed.
- [ ] Public API changes are documented and tested.
- [ ] Optional dependencies remain behind extras with clear install messages.

## Tests and docs

- [ ] Added or updated tests.
- [ ] Updated relevant docs under `docs/`.
- [ ] Ran `uv run pytest` or a focused equivalent.
- [ ] Ran `uv run python scripts/build_docs.py` when docs changed.

## Data safety

- [ ] Examples use synthetic or de-identified data only.
- [ ] No secrets, PHI, private endpoint URLs, or patient-identifying DICOM/FHIR data are included.
- [ ] Generated artifacts such as frontend `dist`, `node_modules`, upload/export folders, databases, and local caches are not included.

## Release readiness

- [ ] Version, changelog, citation metadata, and release notes are aligned when this is a release PR.
- [ ] `uv run python scripts/check_release_readiness.py --skip-package` passes for release-facing changes.
