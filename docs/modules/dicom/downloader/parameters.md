# DICOM downloader: complete parameter reference

[Back to the workflow guide](../downloader.md)

Use this page when you know the operation and need every argument, its actual Python default and its interactions. Signatures and parameter coverage are generated from the current source; descriptions explain operational choices.

**Version scope:** Fyron 0.3.20b5 (Beta 5). The reporting, deadline, naming and validation options below require Beta 5 or newer; they are not available in previously published Beta 4 packages.

## Reading the tables

- **Required** means the Python signature has no default. A default of `None` can still require environment configuration or a value from the resource.
- **Keyword only** arguments must be passed by name. Boolean options accept Python `True` / `False`; `None` is a separate inherit/unset choice where documented.
- Use the workflow guide for setup, authentication, return schemas and safe restarts. FHIR `params` and SQL schemas are site-specific; this page lists Fyron arguments, not every parameter a remote service might support.
- These clients support `with ... as client:` and `close()`; they close owned resources and keep borrowed HTTP sessions open.

## Function index

- [DICOMDownloader](#constructor)
- [close](#close)
- [download_id](#download-id)
- [download_series](#download-series)
- [download_study](#download-study)
- [download_from_dataframe](#download-from-dataframe)
- [download_from_df](#download-from-df)

## Constructor

`DICOMDownloader`

Signature reference (use the workflow guide for runnable calls):

```python
def DICOMDownloader(
    auth=None,
    dicom_web_url=None,
    dicom_user=None,
    dicom_password=None,
    basic_auth=None,
    output_format='nifti',
    use_compression=False,
    num_processes=1,
    log_downloads=False,
    save_reference_dicom=False,
    reference_dicom_name='reference.dcm',
    *,
    worker_auth_timeout=120,
    append_study_hash=True,
    write_completion_record=True,
    request_timeout=None,
    parallel_job_timeout=None,
    retries=None,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `auth` | `Optional[Union[Auth, requests.Session]]` | `None` | An existing Fyron `Auth` or `requests.Session`. Borrowed sessions stay open and retain their configuration. Use a service-approved authentication method. |
| `dicom_web_url` | `Optional[str]` | `None` | Approved DICOMweb base endpoint. None reads `DICOM_WEB_URL`; an endpoint is required. |
| `dicom_user` | `Optional[str]` | `None` | HTTP Basic username; None can read `DICOM_USER` when explicit auth is absent. Do not combine explicit authentication methods. |
| `dicom_password` | `Optional[str]` | `None` | HTTP Basic password; None can read `DICOM_PASSWORD` when explicit auth is absent. Keep credentials out of shared code and logs. |
| `basic_auth` | `Optional[Tuple[str, str]]` | `None` | Optional `(username, password)` tuple. Do not combine with shared `auth` or conflicting explicit credentials. |
| `output_format` | `str` | `'nifti'` | Canonical choices: `"dicom"` preserves DICOM instances; `"nifti"` converts each series to a NIfTI volume. Format normalization also accepts `dcm`, `.dcm`, `nii`, `.nii`, `nii.gz` and `.nii.gz`. |
| `use_compression` | `bool` | `False` | Pass compression through to the NIfTI writer. Saved NIfTI names use the implementation’s `.nii.gz` naming; this does not change DICOM preservation. |
| `num_processes` | `int` | `1` | Worker process count. Use `1` while learning. FHIR uses it for parallel fetch/conversion; DICOM uses it for DataFrame downloads with supported worker authentication. Guard spawned script entrypoints. |
| `log_downloads` | `bool` | `False` | Enable controlled download timing, outcomes and counts. Configure console colors or JSON logging once in the application. |
| `save_reference_dicom` | `bool` | `False` | Keep one original DICOM instance beside each converted NIfTI series. Unnecessary for DICOM output. Method-level None inherits the constructor setting. |
| `reference_dicom_name` | `str` | `'reference.dcm'` | File name for the optional reference DICOM, not a path; `.dcm` is appended when missing. Method-level None inherits the constructor setting. Prefer hierarchical layout to avoid cross-series conflicts. |
| `worker_auth_timeout` (keyword only) | `float` | `120` | Positive finite seconds a worker may wait for parent-coordinated authentication. |
| `append_study_hash` (keyword only) | `bool` | `True` | True keeps `<label>__<study_hash>`. False requires an exact safe label and rejects collisions. A method-level None inherits the constructor setting. Applies only to full-study folders. |
| `write_completion_record` (keyword only) | `bool` | `True` | Write new hidden JSON completion records for verified restarts. False omits new records; it neither deletes existing JSON nor disables token caching. |
| `request_timeout` (keyword only) | `Optional[float]` | `None` | Positive seconds for each network connect/read wait. This is not a whole-extraction deadline. DICOM also accepts `None` to retain unbounded request waits. |
| `parallel_job_timeout` (keyword only) | `Optional[float]` | `None` | Positive finite worker execution deadline in seconds, excluding queue wait; `None` disables it. FHIR and DICOM have different constructor defaults, shown in the table. |
| `retries` (keyword only) | `Optional[Retry]` | `None` | An optional `urllib3.util.retry.Retry` GET policy. `None` selects Fyron’s bounded default, including 429/502/503/504 and Retry-After. Existing retry-capable caller adapters retain their own policy. No automatic SQL or write retries. |

## close

`close`

Signature reference (use the workflow guide for runnable calls):

```python
def close(
):
    ...
```

No arguments. Closes owned resources; call once work has finished.

## download id

`download_id`

Signature reference (use the workflow guide for runnable calls):

```python
def download_id(
    study_uid,
    series_uid=None,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `study_uid` | `str` | **Required** | Nonmissing DICOM StudyInstanceUID string. Use the numeric-dot UID, not a FHIR ImagingStudy resource ID or accession number. |
| `series_uid` | `Optional[str]` | `None` | DICOM SeriesInstanceUID string for a known series. It is optional only on the hash helper; whole-study methods discover series themselves. |

## download series

`download_series`

Signature reference (use the workflow guide for runnable calls):

```python
def download_series(
    study_uid,
    series_uid,
    output_dir,
    skip_existing=True,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `study_uid` | `str` | **Required** | Nonmissing DICOM StudyInstanceUID string. Use the numeric-dot UID, not a FHIR ImagingStudy resource ID or accession number. |
| `series_uid` | `str` | **Required** | DICOM SeriesInstanceUID string for a known series. It is optional only on the hash helper; whole-study methods discover series themselves. |
| `output_dir` | `Union[str, pathlib.Path]` | **Required** | Destination directory. DICOM creates study/series folders beneath it; documents use flat or per-document layout according to `flat_output`. |
| `skip_existing` | `bool` | `True` | True skips only outputs verified by matching completion records. False explicitly permits replacement. Disabling JSON does not make existing files automatically trusted. |

## download study

`download_study`

Signature reference (use the workflow guide for runnable calls):

```python
def download_study(
    study_uid,
    output_dir,
    skip_existing=True,
    write_manifest=True,
    study_layout='hierarchical',
    study_folder_name=None,
    save_study_manifest=None,
    *,
    append_study_hash=None,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `study_uid` | `str` | **Required** | Nonmissing DICOM StudyInstanceUID string. Use the numeric-dot UID, not a FHIR ImagingStudy resource ID or accession number. |
| `output_dir` | `Union[str, pathlib.Path]` | **Required** | Destination directory. DICOM creates study/series folders beneath it; documents use flat or per-document layout according to `flat_output`. |
| `skip_existing` | `bool` | `True` | True skips only outputs verified by matching completion records. False explicitly permits replacement. Disabling JSON does not make existing files automatically trusted. |
| `write_manifest` | `bool` | `True` | Whether to write the full-study `study_manifest.json` summary. Independent of per-series completion JSON; unused for individual series. |
| `study_layout` | `Literal['hierarchical', 'flat']` | `'hierarchical'` | `"hierarchical"` creates a directory per series inside the study directory. `"flat"` stores instances or per-series NIfTI files directly in the study directory; it does not remove the study folder. |
| `study_folder_name` | `Optional[object]` | `None` | Optional explicit label for one full-study folder. By default it prefixes a study hash; with hash appending disabled it must be an exact safe unique label. |
| `save_study_manifest` | `Optional[bool]` | `None` | None inherits `write_manifest`; True/False explicitly enables/disables the study summary. Does not control hidden per-series completion records. |
| `append_study_hash` (keyword only) | `Optional[bool]` | `None` | True keeps `<label>__<study_hash>`. False requires an exact safe label and rejects collisions. A method-level None inherits the constructor setting. Applies only to full-study folders. |

## download from dataframe

`download_from_dataframe`

Signature reference (use the workflow guide for runnable calls):

```python
def download_from_dataframe(
    df,
    output_dir,
    study_uid_col='study_instance_uid',
    series_uid_col='series_instance_uid',
    download_full_study=False,
    skip_existing=True,
    write_manifest=True,
    study_layout='hierarchical',
    study_folder_name_col=None,
    save_study_manifest=None,
    results_csv=None,
    save_reference_dicom=None,
    reference_dicom_name=None,
    keep_reference_dicom=None,
    *,
    append_study_hash=None,
    return_report=False,
    show_progress=True,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `df` | `pd.DataFrame` | **Required** | Input pandas DataFrame. Column labels must be unique; mapped identifiers must meet the method’s missing-value rules. Preserve identifier strings and leading zeros. |
| `output_dir` | `Union[str, pathlib.Path]` | **Required** | Destination directory. DICOM creates study/series folders beneath it; documents use flat or per-document layout according to `flat_output`. |
| `study_uid_col` | `str` | `'study_instance_uid'` | Input column containing StudyInstanceUID strings. Read CSV with `dtype="string"` to preserve identifier text. |
| `series_uid_col` | `str` | `'series_instance_uid'` | Input column containing SeriesInstanceUID strings. Required for series-level batch downloads; unused in full-study mode. |
| `download_full_study` | `bool` | `False` | True retrieves every returned series in each requested study. False downloads the selected study/series pairs. |
| `skip_existing` | `bool` | `True` | True skips only outputs verified by matching completion records. False explicitly permits replacement. Disabling JSON does not make existing files automatically trusted. |
| `write_manifest` | `bool` | `True` | Whether to write the full-study `study_manifest.json` summary. Independent of per-series completion JSON; unused for individual series. |
| `study_layout` | `Literal['hierarchical', 'flat']` | `'hierarchical'` | `"hierarchical"` creates a directory per series inside the study directory. `"flat"` stores instances or per-series NIfTI files directly in the study directory; it does not remove the study folder. |
| `study_folder_name_col` | `Optional[str]` | `None` | Optional input column supplying full-study labels, such as `"ACC_NR"`. Different studies must not collide when hashes are disabled. |
| `save_study_manifest` | `Optional[bool]` | `None` | None inherits `write_manifest`; True/False explicitly enables/disables the study summary. Does not control hidden per-series completion records. |
| `results_csv` | `Optional[Union[str, pathlib.Path]]` | `None` | Optional sensitive CSV of outcome rows and actual paths. Written atomically; keep it separate from downloaded files and client metadata. |
| `save_reference_dicom` | `Optional[bool]` | `None` | Keep one original DICOM instance beside each converted NIfTI series. Unnecessary for DICOM output. Method-level None inherits the constructor setting. |
| `reference_dicom_name` | `Optional[str]` | `None` | File name for the optional reference DICOM, not a path; `.dcm` is appended when missing. Method-level None inherits the constructor setting. Prefer hierarchical layout to avoid cross-series conflicts. |
| `keep_reference_dicom` | `Optional[bool]` | `None` | Deprecated compatibility alias for `save_reference_dicom`; conflicting simultaneous values raise. Prefer the supported name in new code. |
| `append_study_hash` (keyword only) | `Optional[bool]` | `None` | True keeps `<label>__<study_hash>`. False requires an exact safe label and rejects collisions. A method-level None inherits the constructor setting. Applies only to full-study folders. |
| `return_report` (keyword only) | `bool` | `False` | False keeps the normal data return. True returns `{"data": ..., "report": ...}`. Read the return-format section below for the client-specific report tables. |
| `show_progress` (keyword only) | `bool` | `True` | Display a progress bar. Units depend on the operation: pages, partitions, input queries or download tasks. Disable for noninteractive jobs; CLI quiet/no-progress/JSON settings disable bars. |

## download from df

`download_from_df`

Signature reference (use the workflow guide for runnable calls):

```python
def download_from_df(
    df,
    output_dir,
    study_uid_col='study_instance_uid',
    series_uid_col='series_instance_uid',
    download_full_study=False,
    skip_existing=True,
    write_manifest=True,
    study_layout='hierarchical',
    study_folder_name_col=None,
    save_study_manifest=None,
    results_csv=None,
    save_reference_dicom=None,
    reference_dicom_name=None,
    keep_reference_dicom=None,
    *,
    append_study_hash=None,
    return_report=False,
    show_progress=True,
):
    ...
```

| Parameter | Type | Python default | Purpose and accepted options |
| --- | --- | --- | --- |
| `df` | `pd.DataFrame` | **Required** | Input pandas DataFrame. Column labels must be unique; mapped identifiers must meet the method’s missing-value rules. Preserve identifier strings and leading zeros. |
| `output_dir` | `Union[str, pathlib.Path]` | **Required** | Destination directory. DICOM creates study/series folders beneath it; documents use flat or per-document layout according to `flat_output`. |
| `study_uid_col` | `str` | `'study_instance_uid'` | Input column containing StudyInstanceUID strings. Read CSV with `dtype="string"` to preserve identifier text. |
| `series_uid_col` | `str` | `'series_instance_uid'` | Input column containing SeriesInstanceUID strings. Required for series-level batch downloads; unused in full-study mode. |
| `download_full_study` | `bool` | `False` | True retrieves every returned series in each requested study. False downloads the selected study/series pairs. |
| `skip_existing` | `bool` | `True` | True skips only outputs verified by matching completion records. False explicitly permits replacement. Disabling JSON does not make existing files automatically trusted. |
| `write_manifest` | `bool` | `True` | Whether to write the full-study `study_manifest.json` summary. Independent of per-series completion JSON; unused for individual series. |
| `study_layout` | `Literal['hierarchical', 'flat']` | `'hierarchical'` | `"hierarchical"` creates a directory per series inside the study directory. `"flat"` stores instances or per-series NIfTI files directly in the study directory; it does not remove the study folder. |
| `study_folder_name_col` | `Optional[str]` | `None` | Optional input column supplying full-study labels, such as `"ACC_NR"`. Different studies must not collide when hashes are disabled. |
| `save_study_manifest` | `Optional[bool]` | `None` | None inherits `write_manifest`; True/False explicitly enables/disables the study summary. Does not control hidden per-series completion records. |
| `results_csv` | `Optional[Union[str, pathlib.Path]]` | `None` | Optional sensitive CSV of outcome rows and actual paths. Written atomically; keep it separate from downloaded files and client metadata. |
| `save_reference_dicom` | `Optional[bool]` | `None` | Keep one original DICOM instance beside each converted NIfTI series. Unnecessary for DICOM output. Method-level None inherits the constructor setting. |
| `reference_dicom_name` | `Optional[str]` | `None` | File name for the optional reference DICOM, not a path; `.dcm` is appended when missing. Method-level None inherits the constructor setting. Prefer hierarchical layout to avoid cross-series conflicts. |
| `keep_reference_dicom` | `Optional[bool]` | `None` | Deprecated compatibility alias for `save_reference_dicom`; conflicting simultaneous values raise. Prefer the supported name in new code. |
| `append_study_hash` (keyword only) | `Optional[bool]` | `None` | True keeps `<label>__<study_hash>`. False requires an exact safe label and rejects collisions. A method-level None inherits the constructor setting. Applies only to full-study folders. |
| `return_report` (keyword only) | `bool` | `False` | False keeps the normal data return. True returns `{"data": ..., "report": ...}`. Read the return-format section below for the client-specific report tables. |
| `show_progress` (keyword only) | `bool` | `True` | Display a progress bar. Units depend on the operation: pages, partitions, input queries or download tasks. Disable for noninteractive jobs; CLI quiet/no-progress/JSON settings disable bars. |

## Return formats and limits

`download_series` returns DicomResult; `download_study` returns a list of series results. Batch methods return a DataFrame, or data with `report.rows` / `report.summary` when requested. A study can yield multiple series rows. Completion records verify local files, not the server inventory.

**Sensitive outputs:** result paths, identifiers, URLs and detailed reports belong in approved research storage. Progress logs use controlled labels and counts.

Return to the [workflow guide](../downloader.md) for worked examples.
