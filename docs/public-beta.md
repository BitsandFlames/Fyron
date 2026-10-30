# Public Beta

Fyron is in public beta. Research teams can use its documented workflows and examples, with the expectation that APIs and dependencies may change before version `1.0`. Pin the version used for a study and review the release notes before upgrading.

## Stability Expectations

| Area | Public-beta expectation |
| --- | --- |
| Core workflows | Tested and intended for real research workflows |
| API compatibility | Best effort within `0.x`; breaking changes should be documented |
| Examples | Synthetic or de-identified only |
| Clinical deployment | Not supported |
| Regulated audit use | Not claimed |

Fyron favors small, explicit APIs and DataFrame-friendly outputs. When an API changes, the project should prefer additive options, compatibility aliases, or release notes that explain the migration.

## Responsible Use

Fyron can help structure clinical data science work, but users remain responsible for:

- study approvals and institutional governance,
- privacy review and de-identification,
- clinical validation and endpoint definitions,
- correct interpretation of statistical and ML outputs,
- secure handling of FHIR, DICOMweb, S3, and other credentials.

Do not share PHI, secrets, private endpoint URLs, or real patient-linked DICOM/FHIR payloads in public issues, pull requests, screenshots, or examples.

## Documentation and Support

- [Getting Started](getting-started.md) covers installation and a first workflow.
- [Research Reliability](reliability.md) records verification evidence, platform coverage, and known boundaries.
- [Release History](releases/index.md) documents changes, corrections, and upgrade requirements.
- The [support guide](https://github.com/bitsandflames/fyron/blob/main/SUPPORT.md) explains how to ask questions and report reproducible issues.

## Current Limitations

- API documentation is still being expanded; some generated function descriptions are incomplete.
- Optional extras have dependency and platform requirements. Check [Installation & Extras](installation.md) for the workflow you intend to use.
- Configured CI jobs do not establish support for every platform. See the dated verification evidence in [Research Reliability](reliability.md).

When upgrading, retain the original data, parameters, and environment information needed to reproduce your analysis. Release notes identify known corrections that may require earlier results to be recalculated.
