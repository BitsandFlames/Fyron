# Security Policy

Fyron is a local-first Python toolkit. It does not send telemetry, upload data, or contact external services on import. Network calls happen only when a user explicitly configures a client or CLI command for systems such as FHIR, DICOMweb, Teable, S3, or document downloads.

## Reporting A Vulnerability

Please report security issues privately by emailing `hello@bitsandflames.ai`. Include:

- affected Fyron version,
- the module or command involved,
- a minimal reproduction when possible,
- whether credentials, PHI, DICOM metadata, FHIR resources, or generated artifacts may be exposed.

Do not open public issues containing secrets, tokens, patient identifiers, private URLs, DICOM UIDs linked to real patients, or protected health information.

## Supported Versions

Security fixes are prioritized for the latest released version on PyPI and the current `main` branch. Older releases may receive fixes when the issue is severe and the patch can be applied safely.

## Healthcare Data Caution

Fyron is a research toolkit, not a compliance product or medical device. Users remain responsible for institutional approvals, data-use agreements, de-identification, access control, audit logging, and validation before using outputs in clinical or regulatory settings.

## Handling Secrets

- Store tokens and passwords in environment variables or ignored `.env` files.
- Do not commit real FHIR, DICOMweb, S3, Teable, or model-service credentials.
- Use synthetic examples when filing issues or pull requests.
- Review generated manifests and logs before sharing them, because they may include local paths, endpoint URLs, or study-specific parameters.
