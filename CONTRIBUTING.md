# Contributing

Thanks for your interest in Fyron. By participating, you agree to uphold our [Code of Conduct](CODE_OF_CONDUCT.md).

Fyron is built for inspectable clinical data science workflows. Prefer small, explicit functions that make healthcare, statistics, and imaging assumptions visible.

## Development Setup

Public modules are currently **evolving**. See the [research reliability guide](docs/reliability.md)
for maturity criteria, configured versus verified platforms, and numerical reference coverage.
PRs run the Linux suite plus selected clean-wheel and cross-platform checks; every
declared extra gets a broader weekly/manual isolated operation check. Examples must
use synthetic data and no institutional credentials or live patient services.

New public APIs must pass `uv run python scripts/check_docstrings.py`. Existing
gaps are ratcheted, not silently accepted for new APIs. After fixing documentation,
run `uv run python scripts/check_docstrings.py --prune` and review the reduced baseline.
Do not add exemptions. Run examples and wheel checks with the commands in the guide.

Install the full development environment:

```bash
uv sync --all-extras --dev
```

For a smaller docs/core setup:

```bash
uv sync --dev
```

## Common Commands

| Task | Command |
| --- | --- |
| Run all tests | `uv run pytest` |
| Run focused tests | `uv run pytest tests/test_api_design.py` |
| Compile source | `python3 -m py_compile scripts/build_docs.py` |
| Build docs | `uv run python scripts/build_docs.py` |
| Preview docs | `uv run python -m http.server 8001 --directory site` |
| Build package | `uv build` |

Optional integration tests call public services and are disabled by default. Set `FYRON_INTEGRATION=1` to run tests such as [tests/test_fhir_rest_integration.py](tests/test_fhir_rest_integration.py).

## API Design Expectations

- Keep APIs DataFrame-, array-, path-, or dictionary-friendly.
- Use explicit clinical parameter names such as `duration_col`, `event_col`, `group_col`, `id_col`, and `save_path`.
- Return inspectable objects: DataFrames, dictionaries, dataclasses, Matplotlib handles, file paths, or fitted estimators.
- Avoid hidden clinical assumptions. If a function assumes event coding, time units, geometry alignment, or endpoint semantics, document it.
- Keep optional dependencies behind extras and raise a clear `ImportError` with the install command.
- Do not add broad abstractions when a focused helper is clearer.

Clear optional dependency messages should include the exact extra, for example:

```text
Install with: uv add "fyron[visualization]"
```

See [docs/api-design.md](docs/api-design.md) for the full API design policy.

## Documentation Expectations

When adding or changing a public API:

- update the relevant page under `docs/modules/`,
- add a docstring with parameter and return information,
- include a small realistic example when the workflow is non-obvious,
- make return shapes explicit,
- keep examples synthetic or de-identified.

The generated reference is rebuilt by:

```bash
uv run python scripts/build_docs.py
```

## Pull Request Checklist

- [ ] The change is focused and documented.
- [ ] Tests cover the new behavior or guardrail.
- [ ] Public API behavior is unchanged, or the change is documented.
- [ ] Optional dependency imports are protected by extras.
- [ ] Docs build successfully when documentation changes.
- [ ] Examples contain no secrets, PHI, private endpoint URLs, or patient-identifying DICOM/FHIR data.

## Commit and merge workflow

Keep pull requests focused on one change. Use a short, descriptive title that
explains the resulting behavior, followed by the relevant test evidence in the
PR description. Documentation-only changes should say what became clearer.

Maintainers should normally squash merge a pull request into one meaningful
commit. Edit the squash message to summarize the final change rather than
listing every intermediate adjustment. Preserve contributor attribution.

Published release tags and their source history are part of the reproducibility
record. Do not rewrite them to tidy commit messages. Summarize changes in release
notes, and make corrections in new commits.
