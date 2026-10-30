# DICOMDownloader

For site-specific access setup, see [DICOMweb authentication](../../authentication/dicomweb.md). Choose the method and permissions approved by your administrator.

Development update: see [Safe Network Diagnostics](../../diagnostics.md) for logging,
safe error text, batch outcome counts, and sensitive-result handling.

## Verified Downloads (Development)

New downloads are staged before publication. Each series receives a hidden
completion record containing output filenames, sizes, and SHA-256 hashes.
`skip_existing=True` skips only outputs that still match that record. This checks
local integrity, not whether the server supplied every instance in its archive.

Filename-bearing DICOM UIDs must satisfy the DICOM numeric-dot grammar and
64-character limit. Invalid UIDs and duplicate SOP Instance UIDs fail before
publication, including when `skip_existing=True`; they cannot overwrite another
instance or escape the staging directory.

Older outputs without records, missing files, and modified files are not assumed
complete. If a new download would collide with such an output, Fyron preserves
it and returns an error. Review or back up the files before explicitly setting
`skip_existing=False` to replace them. There is no automatic adoption of legacy
files and no silent overwrite during a normal restart.

Transfer or conversion failures before publication leave final files untouched.
Publishing a multi-file DICOM series is not one atomic filesystem operation:
a failure during publication can leave partial files, but no valid completion
record. Such files require review before a retry. Completion records are local,
potentially sensitive sidecars and must stay with their outputs. Concurrent
explicit-overwrite runs targeting the same series are not supported.

When a reference DICOM is requested, it must also be present in the verified
record before a NIfTI series is skipped. A shared flat study folder can produce
filename conflicts if several series use the same reference filename; use a
hierarchical layout to keep each series' reference separate. Conflicts are
reported instead of silently replacing another series' metadata.

`DICOMDownloader` is Fyron's DICOMweb acquisition helper. It downloads individual series or full studies, writes DICOM or NIfTI outputs, and returns result metadata that can be stored beside a cohort table.

## When To Use It

- download a known `StudyInstanceUID` / `SeriesInstanceUID`,
- batch-download imaging rows from a CSV/DataFrame,
- fetch a full study when the relevant series is not known yet,
- create reproducible manifests before local image processing.

Use [Imaging](../../imaging/index.html) after files are already local. Use [DICOM SEG](seg.md) for segmentation objects and [Synthetic Export](synthetic.md) for generated intensity volumes.

## Service-Account Authentication

Fyron 0.3.12 accepts `worker_auth_timeout=120` (finite
positive seconds). Parallel token/device/service-account authentication uses
parent-created pipes and process-local access-token leases, with parent-owned
renewal and no listening TCP port. Token waiting is bounded; download HTTP and
conversion behavior are otherwise unchanged. Existing result/error reporting is
preserved and uncertain downloads are not automatically resubmitted.
Use a guarded script entrypoint for spawned workers. Device approval callbacks
must return promptly. Worker access tokens are limited to 16 KiB.

Use `Auth.client_credentials(...)` for unattended OAuth/OIDC-backed DICOMweb:

```python
import os
from fyron import Auth, DICOMDownloader

with Auth.client_credentials(
    auth_url="https://identity.example.org/realms/research",
    client_id=os.environ["OAUTH_CLIENT_ID"],
    client_secret=os.environ["OAUTH_CLIENT_SECRET"],
    scope=os.environ["OAUTH_SCOPE"],
) as auth:
    downloader = DICOMDownloader(
        dicom_web_url="https://hospital.example.org/dicom-web",
        auth=auth,
        output_format="dicom",
        num_processes=6,
    )
    # Perform downloads inside this context, before auth is closed.
```

Resource requests use Bearer tokens with parent-coordinated renewal. Explicit
`auth` overrides environment Basic credentials. See
[service-account authentication](https://fyron.bitsandflames.ai/modules/fhir/rest/#service-account-authentication)
for endpoint overrides, provider setup, supported client methods, and limitations.

## Core Concepts

| Concept | Meaning |
| --- | --- |
| `StudyInstanceUID` | DICOM study identifier. Required for study and series downloads. |
| `SeriesInstanceUID` | DICOM series identifier. Required when downloading one known series. |
| `download_id` | Deterministic SHA-256 identifier derived from the study UID alone or from `study_uid_series_uid`. |
| `output_format` | `"dicom"` preserves source slices; `"nifti"` converts each series into a NIfTI volume. |
| reference DICOM | Optional single source `.dcm` retained beside a NIfTI output for metadata/provenance. |
| `study_layout` | Full-study output style: `hierarchical` uses per-series folders; `flat` stores all series in one study folder. |
| result table | DataFrame with UIDs, `download_id`, output path, format, and error text. |

## API Contract

| Topic | Contract |
| --- | --- |
| Input shape | Study/series UID strings for single downloads, or a DataFrame/CSV manifest for batch downloads. |
| Required columns/files | Batch manifests need study UID and, for series downloads, series UID columns; output directories must be writable. |
| Return shape | Single downloads return result metadata; batch helpers return a DataFrame with paths, identifiers, status, and errors. |
| Saved artifacts | DICOM folders, NIfTI files, optional reference DICOM files, manifests, and results CSV files. |
| Failure modes | Missing UIDs, DICOMweb authentication/server errors, conversion failures, existing-file conflicts, or invalid output layout. |

The `download_id` can be reproduced without contacting the server:

```python
from fyron.dicom import DICOMDownloader

download_id = DICOMDownloader.download_id(
    study_uid="1.2.3",
    series_uid="1.2.3.4",
)
```

## Required Inputs

| Input | Needed for | Notes |
| --- | --- | --- |
| DICOMweb URL | all downloads | May come from `DICOM_WEB_URL`. |
| study UID | single study/series | `StudyInstanceUID`. |
| series UID | series download | Optional for full-study mode. |
| output directory | all downloads | Destination folder. |

## Optional Inputs

| Input | Use |
| --- | --- |
| credentials/session | authenticated PACS/DICOMweb |
| `output_format` | `"dicom"` or `"nifti"` |
| `save_reference_dicom` | keep one source DICOM slice beside each NIfTI output |
| `reference_dicom_name` | custom file name for the retained metadata DICOM |
| `skip_existing` | resumable jobs |
| `write_manifest` | reproducibility metadata |
| `results_csv` | batch job audit output |

## Minimal Example

```python
from fyron import DICOMDownloader

downloader = DICOMDownloader(
    dicom_web_url="https://pacs.example.org/dicomweb",
    output_format="dicom",
)

result = downloader.download_series(
    study_uid="1.2.3",
    series_uid="1.2.3.4",
    output_dir="dicom_out",
)

result.download_id
result.path
result.error
```

## Password-To-Token Authentication

`Auth.token_env()` reads `FHIR_USER` and `FHIR_PASSWORD` to obtain a token.
With `token_auth_method="basic"`, Basic authentication is used only for the
login GET request. The DICOMweb requests use `Authorization: Bearer <token>`.

```python
import os
from fyron import Auth, DICOMDownloader

with Auth.token_env(
    auth_url=os.environ["FHIR_AUTH_URL"],
    refresh_url=os.getenv("FHIR_REFRESH_URL"),
    token_auth_method="basic",
) as auth:
    downloader = DICOMDownloader(
        auth=auth,
        dicom_web_url=os.environ["DICOM_WEB_URL"],
        output_format="nifti",
        num_processes=6,
    )
    # Download your selected studies or series here.
```

This is Fyron's existing password-to-token protocol, not an OAuth refresh-token
grant. A configured refresh endpoint receives a GET with the current Bearer
token and must return a token response. Redirects are rejected. A refresh 401,
or no refresh endpoint, causes re-login. For a login endpoint expecting a JSON
POST with username/password, use `token_auth_method="json"` instead.

Starting with 0.3.8, explicit `auth` overrides environment DICOM Basic credentials.
An unauthorized response from login still indicates a credential/protocol problem;
a DICOMweb 401 can indicate missing audience, scopes, or access rights.

## Device Authentication

Use the same `Auth` interface as FHIR for browser-approved sign-in. See
[device authentication](https://fyron.bitsandflames.ai/modules/fhir/rest/#device-authentication) for provider setup,
cache security, unattended jobs, and token-refresh behavior.

```python
from fyron import Auth, DICOMDownloader, read_csv

if __name__ == "__main__":
    cohort = read_csv("cohort.csv")
    with Auth(
        auth_type="device_code",
        auth_url="https://keycloak.example.org/realms/research",
        client_id="fyron-cli",
    ) as auth:
        downloader = DICOMDownloader(
            auth=auth,
            dicom_web_url="https://pacs.example.org/dicomweb",
            output_format="dicom",
            num_processes=6,
        )
        results = downloader.download_from_dataframe(
            df=cohort.drop_duplicates("study_instance_uid"),
            study_uid_col="study_instance_uid",
            output_dir="dicom_out",
            download_full_study=True,
            save_study_manifest=True,
        )
```

Device- and password-token-authenticated workers share one parent-owned token lifecycle, so parallel
downloads do not independently refresh rotating tokens or ask for multiple
sign-ins. Existing basic-auth worker behavior is unchanged. Generic custom
sessions without Fyron token authentication still fall back to sequential mode.
`Auth.token_env()` now supports `num_processes > 1`: workers request tokens from
the parent, which serializes proactive renewal and refresh after a 401. Worker
tasks do not serialize credentials or perform independent logins; child processes
still inherit the operating-system environment. Set `token_refresh_delta` (minutes) for
proactive renewal of opaque tokens when needed. This parallel password-token
support is available starting with Fyron 0.3.9.

Explicit `auth` now takes precedence over `DICOM_USER` and `DICOM_PASSWORD` from
the environment. Passing explicit basic credentials together with `auth` raises
an error. Without explicit auth, environment-based Basic authentication still
works. One auth instance can serve FHIR and DICOMweb only when both services
accept that token's audience and permissions.

## NIfTI With One Metadata DICOM

When `output_format="nifti"`, Fyron normally converts through a temporary DICOM folder and keeps only the NIfTI output. If you also need a source DICOM header for later metadata checks, set `save_reference_dicom=True`:

```python
from fyron import DICOMDownloader

downloader = DICOMDownloader(
    dicom_web_url="https://pacs.example.org/dicomweb",
    output_format="nifti",
    save_reference_dicom=True,
    reference_dicom_name="reference.dcm",
)

result = downloader.download_series(
    study_uid="1.2.3",
    series_uid="1.2.3.4",
    output_dir="downloads",
)
```

The series folder then contains:

```text
downloads/{download_id}/
  1.2.3.4.nii.gz
  reference.dcm
```

Use this when downstream tools work with NIfTI but you still want one original DICOM file for `PatientID`, acquisition metadata, frame of reference, or audit checks. If an existing NIfTI is skipped with `skip_existing=True`, Fyron does not contact the DICOMweb server and cannot backfill the reference file; rerun with `skip_existing=False` to create it.

For repeated download jobs, prefer constructor-level configuration:

```python
downloader = DICOMDownloader(
    dicom_web_url="https://pacs.example.org/dicomweb",
    output_format="nifti",
    save_reference_dicom=True,
    reference_dicom_name="meta.dcm",
)
```

For one-off DataFrame downloads, you can override the reference-DICOM behavior directly on the batch call without mutating the downloader:

```python
results = downloader.download_from_dataframe(
    df=imaging_df,
    output_dir="downloads",
    save_reference_dicom=True,
    reference_dicom_name="meta.dcm",
)
```

`download_from_df(...)` accepts the same arguments. Older scripts that use `keep_reference_dicom=True` still run with a `DeprecationWarning`, but new code should use `save_reference_dicom=True`.

## Batch Example

```python
results = downloader.download_from_df(
    imaging_df,
    output_dir="dicom_out",
    study_uid_col="study_instance_uid",
    series_uid_col="series_instance_uid",
    save_reference_dicom=True,
    reference_dicom_name="meta.dcm",
    results_csv="dicom_results.csv",
)
```

The input DataFrame should contain one row per requested series unless `download_full_study=True`.

| Column | Meaning |
| --- | --- |
| `study_instance_uid` | Study UID used for every request. |
| `series_instance_uid` | Series UID used for per-series downloads. |
| optional label column | Can be used as `study_folder_name_col` for human-readable full-study folders. |

## Study Versus Series Downloads

| Mode | Use when | Folder naming |
| --- | --- | --- |
| `download_series` | You already know the relevant series. | `{output_dir}/{download_id}` |
| `download_study` | You need all series in a study or do not know the target series. | `{output_dir}/{study_download_id}` or `{output_dir}/{sanitized_label}__{study_download_id}` |
| `download_from_df` | A cohort CSV/DataFrame contains UIDs. | One row per result in the returned result table. |

Use `output_format="dicom"` when later writing DICOM SEG because SEG export needs source-referenced DICOM slices. Use `output_format="nifti"` when the next step is local image processing, BOA-like processing, or array-based analysis. Use `output_format="nifti", save_reference_dicom=True` when the analysis should run on NIfTI but metadata provenance still needs one original source DICOM.

### Multiple Studies Per Patient

Patient IDs do not uniquely identify studies. Custom full-study labels now retain
the study hash as a suffix, including when using `study_folder_name_col="patient_id"`.
Two studies for the same patient therefore have distinct output folders and
manifests. Omitting the label column continues to use only the study hash.
Labels may contain identifying information; prefer the default hash-only names
when readable patient identifiers are unnecessary. Hashes alone do not anonymize
the downloaded DICOM content.

Identical study/series tasks targeting the same resolved folder are deduplicated
before starting download workers. Changing the label changes the destination.
Existing patient-only folders are not automatically migrated or reused, so an
upgrade can download a study again into its new study-specific folder.
This naming change is available starting with Fyron 0.3.9. Version 0.3.8 used
custom labels alone; default hash-only folder names are unchanged.

For NIfTI plus reference DICOM output, keep `study_layout="hierarchical"` to avoid
different series within one study overwriting the same `meta.dcm`.

## Research Decision: DICOM Or NIfTI

| Choice | Use when | Artifact to save |
| --- | --- | --- |
| `output_format="dicom"` | You need source slices, DICOM SEG, or detailed acquisition metadata. | DICOM folder and result CSV |
| `output_format="nifti"` | Downstream image processing works on arrays/volumes. | NIfTI and result CSV |
| `save_reference_dicom=True` | You want NIfTI processing plus one original DICOM header for provenance. | `reference.dcm` beside the NIfTI |

Always keep the returned result table. It is the bridge between cohort rows, `download_id`, study/series UIDs, and local files.

## CLI Workflow

```bash
fyron dicom-download \
  --csv imaging.csv \
  --study-col study_instance_uid \
  --series-col series_instance_uid \
  --output-dir dicom_out \
  --save-reference-dicom \
  --results-csv dicom_results.csv
```

## Function Table

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `DICOMDownloader(...)` | URL or env var | auth, output format, compression, workers, reference DICOM | downloader |
| `download_series(...)` | study UID, series UID, output dir | skip existing | `DicomResult` |
| `download_study(...)` | study UID, output dir | layout, manifests, folder name | list of `DicomResult` |
| `download_from_df(...)` | DataFrame, output dir | UID columns, full-study mode, CSV output, one-call reference DICOM override | DataFrame/result table |

## Return Values

`DicomResult` contains:

| Field | Meaning |
| --- | --- |
| `study_uid` | Requested study UID. |
| `series_uid` | Requested or discovered series UID; `None` only for study-level failures. |
| `download_id` | Deterministic identifier used for result matching. |
| `path` | Output folder path. |
| `format` | `dicom` or `nifti`. |
| `error` | `None` on success or a formatted error string. |

## Common Pitfalls

- Use `output_format="dicom"` when later writing DICOM SEG; SEG needs original source images.
- Keep result manifests with the study cohort.
- Confirm UID columns before a batch download; UID mixups are expensive.
- Start with one test series before scaling to many studies.
- For BOA-style downstream extraction, keep a stable mapping between `download_id`, patient ID, study UID, and series UID.

## Related Modules

- [DICOM](../../dicom/index.html) for the overview.
- [Imaging](../../imaging/index.html) for local DICOM/NIfTI reading and QC.
- [Audit & Provenance](../../audit/index.html) for reproducibility manifests.
