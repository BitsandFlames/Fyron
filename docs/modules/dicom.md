# DICOM

For site-specific access setup, see [DICOMweb authentication](../authentication/dicomweb.md). Choose the method and permissions approved by your administrator.

`fyron.dicom` is the DICOM-native boundary for imaging projects: DICOMweb acquisition, generated synthetic image export, and standards-compliant DICOM SEG writing. Keep protocol-specific work here, then hand local files to [Imaging](imaging.md) for array/NIfTI/QC operations.

Requests-based FHIR, DICOMweb, document, and LLM clients follow redirects only within the same scheme, host, and port. Cross-origin redirects, HTTPS downgrades, and URLs containing user credentials are blocked before forwarding request bodies or custom authentication headers. Configure the approved final endpoint directly when a service redirects elsewhere. This guard is also installed on supplied sessions, while preserving existing response hooks.

## DICOM Submodules

| Chapter | Use it for |
| --- | --- |
| [DICOMDownloader](dicom/downloader.md) | Download DICOMweb studies or series and write manifests. |
| [Synthetic DICOM/NIfTI export](dicom/synthetic.md) | Write generated or GAN-derived volumes with synthetic identifiers. |
| [DICOM SEG export](dicom/seg.md) | Write segmentation masks as source-referenced DICOM SEG objects. |

## Choose The Right Path

| Need | Prefer |
| --- | --- |
| Download one study or series | [DICOMDownloader](dicom/downloader.md) |
| Batch-download imaging rows from a cohort table | [DICOMDownloader](dicom/downloader.md) |
| Export generated CT/MR-like volumes | [Synthetic Export](dicom/synthetic.md) |
| Export model/manual segmentation masks to DICOM viewers | [DICOM SEG](dicom/seg.md) |
| Read local headers, series, NIfTI, geometry, or mask QC | [Imaging](imaging.md) |

## Typical Workflow

1. Configure DICOMweb endpoint credentials.
2. Download one test series and inspect the result.
3. Scale to a DataFrame-driven batch download.
4. Store manifests beside the cohort.
5. Run local imaging QC before segmentation, radiomics, or DICOM SEG export.

## Imports

```python
from fyron import DICOMDownloader
from fyron.dicom.synthetic import write_synthetic_dicom_series
from fyron.dicom.seg import write_dicom_seg
```

## Minimal Acquisition Example

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
```

## CLI Examples

```bash
fyron dicom-download \
  --dicom-web-url https://pacs.example.org/dicomweb \
  --study-uid 1.2.3 \
  --series-uid 1.2.3.4 \
  --output-dir dicom_out \
  --output-format dicom
```

```bash
fyron dicom-seg \
  --mask total.nii.gz \
  --source-dicom original_dicom/case_001 \
  --segments segments.json \
  --output segmentations/case_001.seg.dcm \
  --validate
```

## Common Pitfalls

- Use `output_format="dicom"` if later writing DICOM SEG; SEG needs original source images.
- Keep download manifests with the study cohort for reproducibility.
- Do not use synthetic DICOM export for segmentation masks; use DICOM SEG.
- Confirm UID columns before large batch downloads.

## Related Modules

- [Imaging](imaging.md) for local DICOM/NIfTI I/O and QC.
- [BOA](boa.md) for body-composition extraction, radiomics, and visualization.
- [Audit & Provenance](audit.md) for reproducibility manifests.
