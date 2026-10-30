# DICOM And Imaging Agent Notes

Use `fyron.dicom` for DICOMweb and DICOM SEG. Use `fyron.imaging` for local images, NIfTI, normalization, and QC.

DICOMweb:

```python
from fyron import DICOMDownloader

downloader = DICOMDownloader(base_url=dicom_web_url, bearer_token=token)
downloader.download_study(study_uid, output_dir="dicom_out")
```

Image QC:

```python
from fyron.imaging import qc

summary = qc.summarize_image_geometry("image.nii.gz", mask_path="mask.nii.gz")
```

DICOM SEG requires source DICOM:

```python
from fyron.dicom.seg import load_source_dicom_series, read_segment_descriptions, write_dicom_seg

source_images = load_source_dicom_series("dicom/")
segments = read_segment_descriptions("segments.json")
write_dicom_seg(mask, source_images, "mask.seg.dcm", segments)
```

Rules:

- Do not claim valid DICOM SEG export from a NIfTI file alone.
- Check orientation, spacing, shape, and mask alignment before comparing images.
- Keep DICOM identifiers and private tags out of prompts and examples unless explicitly de-identified.
- Use synthetic or toy images in assistant-generated demos.
- For CT/MRI review folders, prefer Curate preview generation before manual screening.

