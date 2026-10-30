# Support And Maintenance

Fyron is source-available public-beta software under CC BY-NC 4.0 for clinical data science, healthcare AI, imaging workflows, and reproducible manuscript artifacts.

## Supported Versions

| Version | Support status |
| --- | --- |
| `0.3.x` | Public beta; bug fixes, documentation updates, and additive features |
| `<0.3` | Best-effort only |

## Support Scope

The maintainers prioritize:

- reproducible bugs with synthetic or de-identified examples,
- installation and optional-extra issues,
- documentation gaps that block first-time use,
- correctness issues in documented public APIs,
- privacy or security reports shared through the private channel in [SECURITY.md](SECURITY.md).

Fyron is not a medical device, clinical decision support product, hosted service, or compliance platform. Users remain responsible for institutional approvals, de-identification, access control, validation, and local governance before using outputs in clinical, regulatory, or publication workflows.

## Python Versions

Fyron supports Python 3.10, 3.11, and 3.12 in CI. Some optional dependencies have narrower support:

- `fyron[radiomics]` uses PyRadiomics and is currently intended for Python 3.10-3.11.
- `fyron[curate]` requires Docker Compose at runtime.
- survival and ML extras rely on their upstream scientific Python compatibility.

## Security And Privacy

Report security issues privately using the process in [SECURITY.md](SECURITY.md). Do not open public issues containing credentials, private endpoint URLs, PHI, DICOM identifiers linked to real patients, or real FHIR payloads.

## Compatibility Policy For `0.x`

Documented public APIs are intended to change additively where possible. During the `0.x` line, the maintainers may still adjust APIs that need better clinical semantics, safer defaults, or clearer return shapes.

When a breaking change is necessary, the preferred path is:

1. add the replacement first,
2. keep aliases when feasible,
3. document the migration path,
4. mention the change in the changelog or release notes.

Curate is a beta Docker Compose app behind `fyron[curate]`. It is included for practical local image review workflows, but its UI and storage behavior may evolve faster than the core Python APIs.

## Getting Help

For public issues, reduce examples to synthetic tables, synthetic FHIR JSON, or de-identified minimal reproductions. Include the Fyron version, Python version, installed extras, and the smallest command or snippet that reproduces the behavior.
