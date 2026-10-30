# Research Reliability and Compatibility

Fyron's public modules are **evolving**. Passing software tests is evidence about
specified behavior, not clinical validation or proof that a method suits a study.

## Maturity Criteria

| Status | Meaning |
| --- | --- |
| Experimental | Explicitly identified prototypes with incomplete contracts or coverage; unsuitable as an assumed stable foundation |
| Evolving | Current public modules: documented workflows and regression tests, with corrections and additive development still expected |
| Stable | Requires documented input/output and compatibility contracts, executable examples, scientific reference checks where applicable, and passing relevant platform/extra gates |

No module is promoted to stable automatically. A reviewed maturity change must
identify its supported capabilities and evidence. Existing compatibility aliases
remain supported; see the [survival workflow](survival-workflow.md) for an example
of API consistency kept separate from scientific assumptions.

## Configured Checks Versus Verified Support

| Environment | Configured gate | Evidence status |
| --- | --- | --- |
| Linux, Python 3.11/3.12 | Full development suite, docs, package audit | Passed at `7baebd6`; pending local changes require new hosted runs |
| Linux, Python 3.12 | Fresh wheel: base, survival, survival-ml, ml on PRs | Passed at `7baebd6`; pending local changes require new hosted runs |
| macOS/Windows, Python 3.12 | Base wheel, CLI, spawned workers, download completion | Passed at `7baebd6`; not full scientific-extra certification |
| Linux, Python 3.12 | Weekly isolated operations for every declared extra | Broad matrix; individual job results determine verified coverage |
| Linux, Python 3.11 | Weekly radiomics and all-extra operations | Radiomics has a Python-version restriction |

The [CI run for `7baebd6`](https://github.com/BitsandFlames/Fyron/actions/runs/39620906028) passed the jobs listed above. These results precede the subsequent local module corrections; they do not certify the uncommitted working tree.

Local verification uses macOS arm64. The current full suite uses a fresh Python
3.11 environment; fresh-wheel checks use Python 3.12 and Python 3.11 where stated
in the task's verification report. These local results do not establish Windows,
Linux, or other architecture compatibility. Python versions beyond this matrix
are not certified by the `requires-python` lower bound.

The 2026-10-21 local pre-release check passed 696 tests on Python 3.11, with
two live-service integration tests intentionally skipped. Curate passed eight
backend tests, two frontend batching tests, a frontend production build, and
an isolated Docker upload/review/restart/export check with synthetic images
and DICOM instances. Browser upload and review-state rendering were also checked.
The final locked Python inventory and both npm lockfile inventories had no known
advisories in the public advisory services queried on that date. This is dated
evidence, not a guarantee that dependencies have no vulnerabilities.

The wheel matrix exercises base and every declared extra on Python 3.12, plus
radiomics and the combined all-extra environment on Python 3.11. Check the
exact artifact's results before release. Hosted Linux and Windows Python results
remain unverified for this working tree. The Docker check verifies Curate's
Linux containers, not the complete Python scientific stack on Linux.

Use the CI run for the exact commit as the source of hosted results. A weekly run
resolves package metadata in a fresh environment; the main suite uses `uv.lock`.
Both matter: a passing locked environment alone cannot establish that a published
wheel's dependency declarations are sufficient.

## Installation Isolation

Each workflow builds one package artifact. Fresh environments install that wheel
non-editably, without the development environment or its optional packages.
Probes and examples are copied outside the checkout and run with Python's `-I`
isolation; imports must resolve inside the environment's site-packages.

Every extra has a synthetic operation: Excel round trips, model fitting, numerical
summaries, plots, feature selection/explanation, image/SEG output, or mocked S3.
Dependency-free aliases exercise their APIs too. Curate checks packaged assets
and launcher configuration, not a live Docker deployment. Base platform tests
explicitly exclude S3 tests; S3 has its own isolated gate. No remote clinical
service or credentials are needed.

Known boundaries:

- Device token caching requires POSIX owner-only permissions and locking. Windows
  must reject protected caching clearly; uncached authentication is separate.
- PyRadiomics 3.0.1 is limited to Python 3.11 in package metadata. `all` on
  Python 3.12 therefore does not include radiomics; this is not full radiomics coverage.
- A bare PyRadiomics source install fails because upstream omits NumPy from its
  isolated build requirements. Python 3.11 radiomics/all jobs explicitly enable
  `--radiomics-build-workaround`, supplying `numpy<2` only to the dependency's
  isolated build environment. This is an operational check of a documented
  workaround, not proof that an unassisted installation works. It adds no
  undeclared packages to the runtime environment. Bare installs remain unverified
  where an appropriate upstream wheel is unavailable.
- Curate requires a separately available Docker runtime for actual operation.
- Optional-extra probes are small operational checks, not exhaustive tests of
  every public function, provider, database, imaging geometry, or deployment.

## Scientific Reference Coverage

These existing tests remain part of the mandatory full suite:

| Tests | Reference or contract |
| --- | --- |
| `tests/test_rmst.py` | Independently evaluated area/Greenwood formulas based on the pinned survRM2 implementation; uncensored analytic variance and edge cases |
| `tests/test_survival_inference_regressions.py` | Underlying estimator concordance for all boosting losses; IPCW/KM reference examples; independently constructed start-stop Cox data; PH decisions |
| `tests/test_survival_contracts.py` | Captured pre-refactor Cox/AFT numerical outputs, fitting cohorts, lazy dependencies and aliases; parity, not independent scientific validation |
| `tests/test_inference_regressions.py` | SciPy paired/OLS comparisons and closed-form logistic references; undefined effects and invalid designs |
| `tests/test_endpoint_audits.py` | Explicit endpoint chronology, censor boundaries, missingness, timezone and join-multiplicity contracts |

Seeded synthetic examples check artifact creation and cohort counts. Neither an
example nor agreement with a third-party estimator replaces scientific review.

## Reproduce the Gates

```bash
uv run pytest
uv run python scripts/check_docstrings.py
uv build --out-dir /tmp/fyron-wheel-check
python3.12 scripts/check_wheel.py --wheel /tmp/fyron-wheel-check/fyron-0.3.15-py3-none-any.whl --extra survival-ml
python3.12 scripts/check_wheel.py --wheel /tmp/fyron-wheel-check/fyron-0.3.15-py3-none-any.whl --platform-tests
uv run python examples/ingestion_workflow.py --output-dir /tmp/fyron-ingestion
uv run python examples/survival_workflow.py --output-dir /tmp/fyron-survival
```

Use the filename actually produced by the package build. The wheel runner uses
the Python interpreter invoking it, requires `uv`, propagates subprocess failures,
and cleans up its temporary environments. Installation needs package-index access;
the operations themselves use synthetic/local or mocked data.

## Documentation Ratchet

The generated report distinguishes priority APIs from the full public backlog.
`scripts/docstring_baseline.json` records existing gaps for all generated public
APIs, not just the priority subset. New gaps or worsening existing entries fail
`check_docstrings.py`. Fixed or partially fixed entries also require baseline
pruning so their gaps cannot silently return:

```bash
uv run python scripts/check_docstrings.py --prune
```

Pruning refuses to add exemptions. Do not regenerate or expand the baseline to
make a new API pass. Document its parameters and returns instead. Existing gaps
remain visible in the [coverage report](reference/docstring-coverage.md).
