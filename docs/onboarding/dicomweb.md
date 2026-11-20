# DICOMweb: download a study or a cohort

**You will produce:** DICOM originals in `dicom_out/` and a batch results table at `results/dicom.csv`.

**Prerequisite:** [Setup](index.md), the [authentication helper](authentication.md), a permitted DICOMweb endpoint and reviewed StudyInstanceUIDs. FHIR patient IDs are not DICOM study UIDs.

**Exercise 2.** Save this complete script as `download_images.py` beside the auth helper. Replace the three synthetic study UIDs with approved study UIDs from your reviewed manifest before using a real service:

```python
import os
from pathlib import Path
import pandas as pd
from fyron import DICOMDownloader
from onboarding_auth import make_auth


def download_images(auth):
    Path("results").mkdir(exist_ok=True)
    studies = pd.DataFrame({"study_instance_uid": ["2.25.1001", "2.25.1002"]})
    with DICOMDownloader(
        dicom_web_url=os.environ["DEMO_DICOM_URL"], auth=auth,
        output_format="dicom", num_processes=1,
    ) as downloader:
        single = downloader.download_study(
            study_uid="2.25.1000", output_dir="dicom_out",
        )
        if not single or any(item.error is not None for item in single):
            raise RuntimeError("A study download failed; inspect its results privately")
        results = downloader.download_from_dataframe(
            studies, output_dir="dicom_out",
            study_uid_col="study_instance_uid", download_full_study=True,
            results_csv="results/dicom.csv",
        )
    if results.empty or results["error"].notna().any():
        raise RuntimeError("Some DICOM downloads failed; inspect results/dicom.csv")
    return results


if __name__ == "__main__":
    with make_auth("device_code", cache_name="dicom-demo.json") as auth:
        results = download_images(auth)
```

Run the device-flow version:

```bash
uv run python download_images.py
```

Approve access when prompted. **Check your result:** `results/dicom.csv` should describe the two batch studies; the single-study call is checked separately. Open the local `dicom_out` folder and confirm the expected studies/series are present. Do not infer completeness from the number of attempted studies. Rerun the same script to exercise verified skips, then inspect the `skipped` and `error` columns.

For a service account, replace the final entrypoint block with this complete alternative, keeping the imports and function above:

```python
if __name__ == "__main__":
    with make_auth("client_credentials") as auth:
        results = download_images(auth)
```

Configure the helper with the imaging service's approved registration. For selected series rather than whole studies, supply `series_instance_uid` and use `download_full_study=False`. Preserve completion records and inspect both `error` and `skipped`; a skip should represent verified prior output. Consult the [DICOM downloader guide](../modules/dicom/downloader.md) for layouts and recovery. An empty result is not evidence that an expected study was downloaded.

## Use your reviewed CSV

Replace the synthetic `studies` assignment inside `download_images` with:

```python
studies = pd.read_csv("studies.csv", dtype="string")
required = "study_instance_uid"
if required not in studies or studies[required].isna().any():
    raise ValueError("Provide a StudyInstanceUID for every selected row")
studies = studies[[required]].drop_duplicates().reset_index(drop=True)
if studies.empty:
    raise ValueError("The study manifest is empty; nothing will be downloaded")
```

```csv
study_instance_uid
2.25.1001
2.25.1002
```

These UIDs are invented. Replace them with reviewed values before running. If your manifest comes from FHIR, first follow the [resource-to-file mapping notes](fhir-rest.md#from-fhir-resources-to-download-inputs). The results table may contain multiple series rows for a study, so row counts need not equal input study counts.

**Next:** [Documents](documents.md), or return to the [onboarding overview](index.md).

## Choose your output names and sidecars

Current source supports `append_study_hash=False` with an exact unique
`study_folder_name_col`, plus `write_completion_record=False` on the constructor
and `save_study_manifest=False` on full-study calls. These options are included in Beta 5. See [exact study folders](../modules/dicom/downloader.md#exact-study-folders-and-optional-json-records).

## Reliability in current source

For unattended jobs, consider `request_timeout=90` and `parallel_job_timeout=600`. Batch `return_report=True` separates requested study tasks from returned series rows. These options are included in Beta 5.
