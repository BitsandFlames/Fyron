# DICOMDownloader

**Version scope:** Fyron 0.3.20b5 (Beta 5). Reporting, timeout, validation and naming additions described here require Beta 5 or newer.

## Find the right operation

Download source DICOM when you need the complete instances and metadata. Choose NIfTI when your next step needs a volume per series. Start with one study, inspect the results, then run a reviewed manifest.

**[All parameters, defaults and accepted options](downloader/parameters.md)** · [Authentication](../../authentication/dicomweb.md) · [Hands-on walkthrough](../../onboarding/dicomweb.md)

| What you want | Use | Important controls |
| --- | --- | --- |
| One selected series | `download_series` | study UID, series UID, `skip_existing` |
| All returned series in one study | `download_study` | `study_layout`, `study_folder_name` |
| Whole studies from a table | `download_from_dataframe` | `download_full_study=True`, `study_uid_col` |
| Exact accession-number folders | full-study methods | label/label column plus `append_study_hash=False` |
| Preserve source instances | constructor | `output_format="dicom"` |
| One volume per series | constructor | `output_format="nifti"`; optional reference DICOM |
| Detailed batch accounting | DataFrame methods | `return_report=True`, optional `results_csv` |

### Example: whole studies, flat DICOM, exact folder labels

First create your approved `auth`. The IDs below are invented; replace them with a reviewed manifest. Whole-study mode does not require a series UID column.

```python
import os
import pandas as pd
from dotenv import load_dotenv
from fyron import DICOMDownloader
from fyron.console import configure_logging

configure_logging("INFO", color=True)
load_dotenv(".env", override=False)
studies = pd.DataFrame({
    "study_instance_uid": ["2.25.1001", "2.25.1002"],
    "ACC_NR": ["00123", "00124"],
})
# For CSV input: studies = pd.read_csv("studies.csv", dtype="string")

with DICOMDownloader(
    auth=auth, dicom_web_url=os.environ["DICOM_WEB_URL"],
    output_format="dicom", num_processes=1,
    request_timeout=90, log_downloads=True,
    write_completion_record=False,
) as loader:
    result = loader.download_from_dataframe(
        df=studies, output_dir="dicom_out",
        study_uid_col="study_instance_uid", download_full_study=True,
        study_layout="flat", study_folder_name_col="ACC_NR",
        append_study_hash=False, save_study_manifest=False,
        results_csv="results/dicom.csv", return_report=True,
    )

series_results = result["data"]
summary = result["report"]["summary"]
failed = series_results.loc[series_results["error"].notna()]
```

Output is `dicom_out/00123/<SOPInstanceUID>.dcm`, with no new JSON sidecars. Each study retains its own folder. A repeated accession label for different studies raises before fetching. `download_id` remains a deterministic hash in results even when the folder name omits it.

| Control | Default behavior | Alternative and consequence |
| --- | --- | --- |
| `append_study_hash` | Append study hash to custom labels | False requires exact safe, unique labels |
| `study_layout` | Per-series folders | `"flat"` removes series folders, retaining the study folder |
| `save_study_manifest` | Inherit `write_manifest` | False omits the study summary JSON |
| constructor `write_completion_record` | Write per-series completion JSON | False omits new records, so new files cannot be verified for later skips |
| `skip_existing` | Skip verified outputs only | False explicitly permits replacement after review |
| `request_timeout` / `parallel_job_timeout` | Both unset for DICOM | Set request waits and a separate worker execution deadline |

The no-JSON example deliberately trades verified restarts for fewer sidecars. For resumable jobs, keep completion records enabled. Always inspect per-series errors: a completed study task can produce several series rows and does not prove the archive's entire inventory was supplied.


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
[service-account authentication](https://docs.fyron.bitsandflames.ai/modules/fhir/rest/#service-account-authentication)
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
[device authentication](https://docs.fyron.bitsandflames.ai/modules/fhir/rest/#device-authentication) for provider setup,
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

## Exact study folders and optional JSON records

Default folder naming remains `<label>__<study_hash>`. To use an accession-number
column exactly, set `append_study_hash=False`. This is available on the
constructor, `download_study`, `download_from_dataframe` and its
`download_from_df` alias. `study_folder_name` controls a single study;
`study_folder_name_col` selects the batch column. Without the hash, an explicit,
nonmissing safe folder label is required. Labels are neither sanitized nor
truncated. Different studies cannot share a label, including case-insensitive
collisions. Keep leading zeros by loading CSV identifiers with `dtype="string"`.

```python
import pandas as pd
from fyron import DICOMDownloader

# Use your existing approved Auth instance and DICOMweb endpoint.
studies = pd.DataFrame({
    "study_instance_uid": ["2.25.1001"],
    "ACC_NR": ["00123"],
})
with DICOMDownloader(
    auth=auth,
    dicom_web_url=dicom_web_url,
    output_format="dicom",
    write_completion_record=False,
) as loader:
    results = loader.download_from_dataframe(
        studies,
        output_dir="dicom_out",
        download_full_study=True,
        study_layout="flat",
        study_folder_name_col="ACC_NR",
        append_study_hash=False,
        save_study_manifest=False,
        results_csv="results/dicom.csv",
    )
# Inspect results["error"] and results["path"] privately.
```

This produces `dicom_out/00123/<SOPInstanceUID>.dcm`, without new JSON sidecars.
`study_layout="flat"` removes series subfolders; it retains the study folder.
These options apply to DICOM and NIfTI output. The naming switch affects full
studies only; individual-series folder naming remains unchanged.

There are two independent JSON controls:

| Option | Controls | Default |
| --- | --- | --- |
| `save_study_manifest=False` | Omit `study_manifest.json` for full studies | Inherits `write_manifest` |
| `write_completion_record=False` on the constructor | Omit per-series `.fyron-complete-*.json` for every download route | Records enabled |

Disabling writes does not delete existing JSON files. Without a valid completion
record, a rerun cannot silently skip or replace existing files. Review the output
and use `skip_existing=False` only for an intentional replacement. In hash-free
mode existing folders must also identify the same study through original DICOM
headers or a valid study manifest. NIfTI-only folders with neither cannot establish
study identity; retain the manifest or choose a new folder. No sidecar-free
migration or rename of older hashed folders is performed. Do not run independent
jobs that write different studies to the same output folder.

The corresponding CLI options work in `fyron dicom-download` and the compatibility
DICOM command:

```bash
fyron dicom-download --csv studies.csv --full-study \
  --output-dir dicom_out --output-format dicom \
  --study-folder-col ACC_NR --study-layout flat \
  --no-study-hash --no-study-manifest --no-completion-record \
  --results-csv results/dicom.csv
```

For one study, use `--study-uid` and `--study-folder-name` instead of the CSV
options. Authentication and access settings remain site-specific.

## Reliable batch reports and deadlines

Use `return_report=True` on `download_from_dataframe` or `download_from_df` for
`{"data": ..., "report": {"rows": ..., "summary": ...}}`. The default remains
a DataFrame. `data` retains the existing series-level results, ordered by input
task rather than worker finish time. Reports count input rows, distinct requested
tasks, completed/failed/skipped tasks, unfinished tasks and returned series rows
separately. A two-series study is one task with two result rows. Reports contain
ordinals and counts; identifying metadata remains in explicit result columns.
Empty inputs retain the result-column schema.

```python
with DICOMDownloader(
    auth=auth, dicom_web_url=dicom_web_url, output_format="dicom",
    request_timeout=90, parallel_job_timeout=600, log_downloads=True,
) as loader:
    result = loader.download_from_dataframe(
        studies, output_dir="dicom_out", download_full_study=True,
        return_report=True, show_progress=True,
        results_csv="results/dicom.csv",
    )
    data = result["data"]
    summary = result["report"]["summary"]
```

Both new timeouts default to `None` for compatibility. `request_timeout` limits
network connect/read waits. `parallel_job_timeout` starts when a worker executes,
not while its task waits in the queue. A read timeout is not a total study-size
or total-transfer deadline. Parallel deadline failures raise and terminate owned
workers; already published series remain present and the batch is incomplete.

Every retrieved instance must have usable SOP, study and series identifiers that
agree with the request. Invalid or unreadable instances fail validation before
the study is published, rather than being silently omitted. Later conversion or
publication failures remain explicit per-series errors. Validation accounts for
received instances; it does not prove the server supplied its entire inventory.
A failed series can coexist with successfully published series, so inspect each
error and retry deliberately.

`show_progress=False` disables bars. The CLI also respects `--quiet`,
`--no-progress`, `--no-color` and `--json-log`. Configure shared logging for Python
applications; logs contain controlled timing, task ordinals and counts only.
Upstream transport debug URLs, headers and warnings are suppressed within Fyron
operations. Supplied sessions retain their adapters and hooks and stay open.

Transient GET retries support `retries=Retry(...)`, including HTTP 429 and
`Retry-After`. CLI deadlines are `--request-timeout` and
`--parallel-job-timeout`. Result CSVs are replaced atomically after serialization;
keep them separate from image files and client metadata. On interruption they
contain only received task outcomes, not a promise of a complete extraction.
