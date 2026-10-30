# DICOM And Imaging Reference

DICOMweb downloads, synthetic DICOM/NIfTI export, DICOM SEG, image I/O, normalization, QC, and segmentation metrics.

For workflow context, see [DICOM And Imaging module guide](../modules/dicom.md).

## Functions And Classes

- [`fyron.dicom.client.DICOMDownloader`](#fyrondicomclientdicomdownloader)
- [`fyron.dicom.client.DICOMDownloader.close`](#fyrondicomclientdicomdownloaderclose)
- [`fyron.dicom.client.DICOMDownloader.download_id`](#fyrondicomclientdicomdownloaderdownloadid)
- [`fyron.dicom.client.DICOMDownloader.download_series`](#fyrondicomclientdicomdownloaderdownloadseries)
- [`fyron.dicom.client.DICOMDownloader.download_study`](#fyrondicomclientdicomdownloaderdownloadstudy)
- [`fyron.dicom.client.DICOMDownloader.download_from_dataframe`](#fyrondicomclientdicomdownloaderdownloadfromdataframe)
- [`fyron.dicom.client.DICOMDownloader.download_from_df`](#fyrondicomclientdicomdownloaderdownloadfromdf)
- [`fyron.dicom.client.DicomResult`](#fyrondicomclientdicomresult)
- [`fyron.dicom.seg.label_map_to_segments`](#fyrondicomseglabelmaptosegments)
- [`fyron.dicom.seg.load_source_dicom_series`](#fyrondicomsegloadsourcedicomseries)
- [`fyron.dicom.seg.read_segment_descriptions`](#fyrondicomsegreadsegmentdescriptions)
- [`fyron.dicom.seg.summarize_dicom_seg`](#fyrondicomsegsummarizedicomseg)
- [`fyron.dicom.seg.validate_dicom_seg`](#fyrondicomsegvalidatedicomseg)
- [`fyron.dicom.seg.validate_segment_descriptions`](#fyrondicomsegvalidatesegmentdescriptions)
- [`fyron.dicom.seg.write_dicom_seg`](#fyrondicomsegwritedicomseg)
- [`fyron.dicom.synthetic.write_synthetic_dicom_series`](#fyrondicomsyntheticwritesyntheticdicomseries)
- [`fyron.dicom.synthetic.write_synthetic_nifti`](#fyrondicomsyntheticwritesyntheticnifti)
- [`fyron.imaging.dicom_io.get_dicom_series_ids`](#fyronimagingdicomiogetdicomseriesids)
- [`fyron.imaging.dicom_io.read_dicom_header`](#fyronimagingdicomioreaddicomheader)
- [`fyron.imaging.dicom_io.read_dicom_series`](#fyronimagingdicomioreaddicomseries)
- [`fyron.imaging.nifti_io.read_nifti`](#fyronimagingniftiioreadnifti)
- [`fyron.imaging.nifti_io.write_nifti`](#fyronimagingniftiiowritenifti)
- [`fyron.imaging.normalize.normalize_ct`](#fyronimagingnormalizenormalizect)
- [`fyron.imaging.normalize.normalize_mr`](#fyronimagingnormalizenormalizemr)
- [`fyron.imaging.qc.check_image_mask_alignment`](#fyronimagingqccheckimagemaskalignment)
- [`fyron.imaging.qc.summarize_dicom_series_geometry`](#fyronimagingqcsummarizedicomseriesgeometry)
- [`fyron.imaging.qc.summarize_intensity_range`](#fyronimagingqcsummarizeintensityrange)
- [`fyron.imaging.qc.summarize_mask_volume`](#fyronimagingqcsummarizemaskvolume)
- [`fyron.imaging.qc.summarize_nifti_geometry`](#fyronimagingqcsummarizeniftigeometry)
- [`fyron.imaging.segmentation.dice_score`](#fyronimagingsegmentationdicescore)
- [`fyron.imaging.segmentation.hausdorff_distance`](#fyronimagingsegmentationhausdorffdistance)
- [`fyron.imaging.segmentation.label_overlap_table`](#fyronimagingsegmentationlabeloverlaptable)
- [`fyron.imaging.segmentation.segmentation_metric_table`](#fyronimagingsegmentationsegmentationmetrictable)
- [`fyron.imaging.segmentation.surface_dice`](#fyronimagingsegmentationsurfacedice)
- [`fyron.imaging.segmentation.volume_difference`](#fyronimagingsegmentationvolumedifference)

## `fyron.dicom.client.DICOMDownloader`

Download DICOM studies/series via DICOMweb and optionally convert to NIfTI.

**Import path:** `fyron.dicom.client.DICOMDownloader`

```python
DICOMDownloader(self, auth: Optional[Union[Auth, requests.Session]] = None, dicom_web_url: Optional[str] = None, dicom_user: Optional[str] = None, dicom_password: Optional[str] = None, basic_auth: Optional[Tuple[str, str]] = None, output_format: str = 'nifti', use_compression: bool = False, num_processes: int = 1, log_downloads: bool = False, save_reference_dicom: bool = False, reference_dicom_name: str = 'reference.dcm', *, worker_auth_timeout: float = 120)
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `auth` | no | `Optional[Union[Auth, requests.Session]]` | `None` | Optional Auth or requests.Session to reuse. |
| `dicom_web_url` | no | `Optional[str]` | `None` | Base DICOMweb endpoint (e.g., https://pacs.example.org/dicomweb). If omitted, uses DICOM_WEB_URL env. |
| `dicom_user` | no | `Optional[str]` | `None` | Optional username for HTTP basic authentication. If omitted, uses ``DICOM_USER`` from the environment. |
| `dicom_password` | no | `Optional[str]` | `None` | Optional password for HTTP basic authentication. If omitted, uses ``DICOM_PASSWORD`` from the environment. |
| `basic_auth` | no | `Optional[Tuple[str, str]]` | `None` | Optional (user, password) tuple for basic auth (standalone). |
| `output_format` | no | `str` | `'nifti'` | "dicom" or "nifti" (default: nifti). |
| `use_compression` | no | `bool` | `False` | Whether to compress NIfTI output. |
| `num_processes` | no | `int` | `1` | Number of worker processes for DataFrame downloads. |
| `log_downloads` | no | `bool` | `False` | Emit progress-oriented log messages through the DICOM logger. |
| `save_reference_dicom` | no | `bool` | `False` | When writing NIfTI output, keep one original DICOM slice beside the NIfTI as lightweight metadata/provenance. |
| `reference_dicom_name` | no | `str` | `'reference.dcm'` | File name for the retained metadata DICOM. |
| `worker_auth_timeout` | no | `float` | `120` | Positive worker token-wait timeout in seconds (default 120). |

### Returns

Class constructor.

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

### Public Methods

#### `fyron.dicom.client.DICOMDownloader.close`

Close the underlying session if owned.

**Import path:** `fyron.dicom.client.DICOMDownloader.close`

```python
DICOMDownloader.close(self) -> None
```

#### Parameters

No parameters documented.

#### Returns

`None`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

#### `fyron.dicom.client.DICOMDownloader.download_id`

Compute the deterministic output identifier for a study or series.

**Import path:** `fyron.dicom.client.DICOMDownloader.download_id`

```python
DICOMDownloader.download_id(study_uid: str, series_uid: Optional[str] = None) -> str
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `study_uid` | yes | `str` |  | DICOM ``StudyInstanceUID``. |
| `series_uid` | no | `Optional[str]` | `None` | Optional DICOM ``SeriesInstanceUID``. When provided, the identifier is based on ``"{study_uid}_{series_uid}"``; otherwise it is based on the study UID alone. |

#### Returns

`str` - SHA-256 hex digest used by Fyron as the default download folder name.

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

#### `fyron.dicom.client.DICOMDownloader.download_series`

Download one DICOM series into a deterministic output folder.

**Import path:** `fyron.dicom.client.DICOMDownloader.download_series`

```python
DICOMDownloader.download_series(self, study_uid: str, series_uid: str, output_dir: Union[str, pathlib.Path], skip_existing: bool = True) -> DicomResult
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `study_uid` | yes | `str` |  | DICOM ``StudyInstanceUID`` containing the requested series. |
| `series_uid` | yes | `str` |  | DICOM ``SeriesInstanceUID`` to download. |
| `output_dir` | yes | `Union[str, pathlib.Path]` |  | Root output directory. Fyron writes the series under ``output_dir / download_id(study_uid, series_uid)``. |
| `skip_existing` | no | `bool` | `True` | If True, return the existing output when a DICOM or NIfTI series already exists in the target folder. |

#### Returns

`DicomResult`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

#### `fyron.dicom.client.DICOMDownloader.download_study`

Download all series in a study under one study folder.

**Import path:** `fyron.dicom.client.DICOMDownloader.download_study`

```python
DICOMDownloader.download_study(self, study_uid: str, output_dir: Union[str, pathlib.Path], skip_existing: bool = True, write_manifest: bool = True, study_layout: Literal['hierarchical', 'flat'] = 'hierarchical', study_folder_name: Optional[object] = None, save_study_manifest: Optional[bool] = None) -> List[DicomResult]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `study_uid` | yes | `str` |  | DICOM ``StudyInstanceUID`` to download. |
| `output_dir` | yes | `Union[str, pathlib.Path]` |  | Root directory where the study folder is created. |
| `skip_existing` | no | `bool` | `True` | If True, skip series whose output already exists. |
| `write_manifest` | no | `bool` | `True` | Write ``study_manifest.json`` after a successful full-study download. |
| `study_layout` | no | `Literal['hierarchical', 'flat']` | `'hierarchical'` | ``"hierarchical"`` (default): ``{study_dir}/{series_uid}/`` holds that series (DICOM slices or one ``{series_uid}.nii.gz``). ``"flat"``: all DICOM files or all per-series NIfTI volumes live directly under ``study_dir`` (DICOM filenames are ``{SOPInstanceUID}.dcm``; NIfTI files are ``{series_uid}.nii.gz``). |
| `study_folder_name` | no | `Optional[object]` | `None` | Optional readable prefix for the study directory. The sanitized label is followed by ``__{download_id(study_uid)}``, so different studies never share a directory merely because their patient label matches. Existing label-only directories are not reused or moved. |
| `save_study_manifest` | no | `Optional[bool]` | `None` | If not ``None``, overrides ``write_manifest`` for whether ``study_manifest.json`` is written (use ``False`` to skip the manifest without changing ``write_manifest``). |

#### Returns

`list[DicomResult]` - One result per downloaded or skipped series. A study-level failure is raised as ``DicomDownloadError``.

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

#### `fyron.dicom.client.DICOMDownloader.download_from_dataframe`

Download studies/series defined by a DataFrame.

**Import path:** `fyron.dicom.client.DICOMDownloader.download_from_dataframe`

```python
DICOMDownloader.download_from_dataframe(self, df: pd.DataFrame, output_dir: Union[str, pathlib.Path], study_uid_col: str = 'study_instance_uid', series_uid_col: str = 'series_instance_uid', download_full_study: bool = False, skip_existing: bool = True, write_manifest: bool = True, study_layout: Literal['hierarchical', 'flat'] = 'hierarchical', study_folder_name_col: Optional[str] = None, save_study_manifest: Optional[bool] = None, results_csv: Optional[Union[str, pathlib.Path]] = None, save_reference_dicom: Optional[bool] = None, reference_dicom_name: Optional[str] = None, keep_reference_dicom: Optional[bool] = None) -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Input manifest with one row per requested series, or one row per study when ``download_full_study=True``. |
| `output_dir` | yes | `Union[str, pathlib.Path]` |  | Root directory for downloaded outputs. |
| `study_uid_col` | no | `str` | `'study_instance_uid'` | Column containing DICOM ``StudyInstanceUID`` values. |
| `series_uid_col` | no | `str` | `'series_instance_uid'` | Column containing DICOM ``SeriesInstanceUID`` values for series-level downloads. Not required in full-study mode. |
| `download_full_study` | no | `bool` | `False` | If True, download all series in each study using WADO-RS study retrieval. |
| `skip_existing` | no | `bool` | `True` | If True, skip rows whose expected DICOM or NIfTI outputs already exist. |
| `write_manifest` | no | `bool` | `True` | Write full-study manifests when ``download_full_study=True``. |
| `study_layout` | no | `Literal['hierarchical', 'flat']` | `'hierarchical'` | Full-study layout: ``"hierarchical"`` for per-series folders or ``"flat"`` for all series directly under the study folder. |
| `study_folder_name_col` | no | `Optional[str]` | `None` | Optional DataFrame column used as a readable prefix before the study hash. |
| `save_study_manifest` | no | `Optional[bool]` | `None` | Optional override for ``write_manifest`` in full-study downloads. |
| `results_csv` | no | `Optional[Union[str, pathlib.Path]]` | `None` | Optional CSV path where the returned result table is also saved. |
| `save_reference_dicom` | no | `Optional[bool]` | `None` | One-call override for the constructor setting. When True and ``output_format="nifti"``, retain one source DICOM slice beside each NIfTI output. |
| `reference_dicom_name` | no | `Optional[str]` | `None` | One-call override for the retained metadata DICOM file name. |
| `keep_reference_dicom` | no | `Optional[bool]` | `None` | Deprecated alias for ``save_reference_dicom`` kept for older scripts. |

#### Returns

`pandas.DataFrame` - One row per result with study UID, series UID, deterministic ``download_id``, output path, output format, and error text.

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

#### `fyron.dicom.client.DICOMDownloader.download_from_df`

Short alias for :meth:`download_from_dataframe`.

**Import path:** `fyron.dicom.client.DICOMDownloader.download_from_df`

```python
DICOMDownloader.download_from_df(self, df: pd.DataFrame, output_dir: Union[str, pathlib.Path], study_uid_col: str = 'study_instance_uid', series_uid_col: str = 'series_instance_uid', download_full_study: bool = False, skip_existing: bool = True, write_manifest: bool = True, study_layout: Literal['hierarchical', 'flat'] = 'hierarchical', study_folder_name_col: Optional[str] = None, save_study_manifest: Optional[bool] = None, results_csv: Optional[Union[str, pathlib.Path]] = None, save_reference_dicom: Optional[bool] = None, reference_dicom_name: Optional[str] = None, keep_reference_dicom: Optional[bool] = None) -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Input manifest with study and optionally series UID columns. |
| `output_dir` | yes | `Union[str, pathlib.Path]` |  | Root directory for downloaded outputs. |
| `study_uid_col` | no | `str` | `'study_instance_uid'` | Column containing DICOM ``StudyInstanceUID`` values. |
| `series_uid_col` | no | `str` | `'series_instance_uid'` | Column containing DICOM ``SeriesInstanceUID`` values. |
| `download_full_study` | no | `bool` | `False` | If True, download all series for each study row. |
| `skip_existing` | no | `bool` | `True` | If True, skip outputs that already exist. |
| `write_manifest` | no | `bool` | `True` | Write full-study manifests when applicable. |
| `study_layout` | no | `Literal['hierarchical', 'flat']` | `'hierarchical'` | Full-study output layout. |
| `study_folder_name_col` | no | `Optional[str]` | `None` | Optional DataFrame column for human-readable study folder names. |
| `save_study_manifest` | no | `Optional[bool]` | `None` | Optional full-study manifest override. |
| `results_csv` | no | `Optional[Union[str, pathlib.Path]]` | `None` | Optional path for saving the returned result table. |
| `save_reference_dicom` | no | `Optional[bool]` | `None` | One-call override for retaining a source DICOM beside NIfTI outputs. |
| `reference_dicom_name` | no | `Optional[str]` | `None` | One-call override for the retained metadata DICOM file name. |
| `keep_reference_dicom` | no | `Optional[bool]` | `None` | Deprecated alias for ``save_reference_dicom``. |

#### Returns

`pandas.DataFrame` - Same result table returned by ``download_from_dataframe``.

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.dicom.client.DicomResult`

Result metadata for one DICOM series download.

**Import path:** `fyron.dicom.client.DicomResult`

```python
DicomResult()
```

### Parameters

No parameters documented.

### Returns

Class constructor.

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.dicom.seg.label_map_to_segments`

Convert an integer label map to a binary segment stack.

**Import path:** `fyron.dicom.seg.label_map_to_segments`

```python
label_map_to_segments(label_map: np.ndarray, labels: Sequence[int]) -> np.ndarray
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `label_map` | yes | `np.ndarray` |  | Array in ``(z, y, x)`` order. |
| `labels` | yes | `Sequence[int]` |  | Integer label values to convert. |

### Returns

`numpy.ndarray` - Boolean array in ``(segment, z, y, x)`` order.

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.dicom.seg.load_source_dicom_series`

Load source DICOM slices from a directory in deterministic SEG order.

**Import path:** `fyron.dicom.seg.load_source_dicom_series`

```python
load_source_dicom_series(source_dicom_dir: StrPath, sort_by: str = 'geometry') -> list[pydicom.Dataset]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `source_dicom_dir` | yes | `StrPath` |  | Directory containing source ``.dcm`` files. |
| `sort_by` | no | `str` | `'geometry'` | ``"geometry"`` sorts by ``ImagePositionPatient`` when available, falling back to ``InstanceNumber`` and then path. ``"instance"`` and ``"path"`` are also supported for explicit workflows. |

### Returns

`list[pydicom.Dataset]`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.dicom.seg.read_segment_descriptions`

Read and validate a JSON list of DICOM SEG segment descriptions.

**Import path:** `fyron.dicom.seg.read_segment_descriptions`

```python
read_segment_descriptions(path: StrPath) -> list[dict[str, Any]]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `StrPath` |  | See signature. |

### Returns

`list[dict[str, Any]]`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.dicom.seg.summarize_dicom_seg`

Return a lightweight metadata summary for a DICOM SEG object.

**Import path:** `fyron.dicom.seg.summarize_dicom_seg`

```python
summarize_dicom_seg(path: StrPath, source_images: Sequence[pydicom.Dataset | StrPath] | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `StrPath` |  | See signature. |
| `source_images` | no | `Sequence[pydicom.Dataset  or  StrPath]  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.dicom.seg.validate_dicom_seg`

Read a DICOM SEG and return lightweight validation metadata.

**Import path:** `fyron.dicom.seg.validate_dicom_seg`

```python
validate_dicom_seg(path: StrPath, source_images: Sequence[pydicom.Dataset | StrPath] | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `StrPath` |  | See signature. |
| `source_images` | no | `Sequence[pydicom.Dataset  or  StrPath]  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.dicom.seg.validate_segment_descriptions`

Validate and normalize DICOM SEG segment description dictionaries.

**Import path:** `fyron.dicom.seg.validate_segment_descriptions`

```python
validate_segment_descriptions(segment_descriptions: Sequence[dict[str, Any]]) -> list[dict[str, Any]]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `segment_descriptions` | yes | `Sequence[dict[str, Any]]` |  | See signature. |

### Returns

`list[dict[str, Any]]`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.dicom.seg.write_dicom_seg`

Write a standards-oriented DICOM SEG object using highdicom.

**Import path:** `fyron.dicom.seg.write_dicom_seg`

```python
write_dicom_seg(mask: np.ndarray, source_images: Sequence[pydicom.Dataset | StrPath], output_path: StrPath, segment_descriptions: Sequence[dict[str, Any]], *, series_description: str = 'Fyron DICOM SEG', manufacturer: str = 'Bits & Flames', algorithm_type: str = 'AUTOMATIC', algorithm_name: str = 'Fyron') -> Path
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `mask` | yes | `np.ndarray` |  | See signature. |
| `source_images` | yes | `Sequence[pydicom.Dataset  or  StrPath]` |  | See signature. |
| `output_path` | yes | `StrPath` |  | See signature. |
| `segment_descriptions` | yes | `Sequence[dict[str, Any]]` |  | See signature. |
| `series_description` | no | `str` | `'Fyron DICOM SEG'` | See signature. |
| `manufacturer` | no | `str` | `'Bits & Flames'` | See signature. |
| `algorithm_type` | no | `str` | `'AUTOMATIC'` | See signature. |
| `algorithm_name` | no | `str` | `'Fyron'` | See signature. |

### Returns

`Path`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.dicom.synthetic.write_synthetic_dicom_series`

Write a synthetic 3D volume as one DICOM file per slice.

**Import path:** `fyron.dicom.synthetic.write_synthetic_dicom_series`

```python
write_synthetic_dicom_series(volume: np.ndarray | sitk.Image, output_dir: StrPath, *, reference_dicom_dir: StrPath | None = None, reference_datasets: Sequence[pydicom.Dataset | StrPath] | None = None, patient_id: str = 'SYNTHETIC', study_instance_uid: str | None = None, series_instance_uid: str | None = None, modality: str = 'CT', series_description: str = 'Synthetic Fyron volume', intensity_mode: str = 'hu', rescale_intercept: float = -1024.0, rescale_slope: float = 1.0, copy_patient_tags: bool = False) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `volume` | yes | `np.ndarray  or  sitk.Image` |  | See signature. |
| `output_dir` | yes | `StrPath` |  | See signature. |
| `reference_dicom_dir` | no | `StrPath  or  None` | `None` | See signature. |
| `reference_datasets` | no | `Sequence[pydicom.Dataset  or  StrPath]  or  None` | `None` | See signature. |
| `patient_id` | no | `str` | `'SYNTHETIC'` | See signature. |
| `study_instance_uid` | no | `str  or  None` | `None` | See signature. |
| `series_instance_uid` | no | `str  or  None` | `None` | See signature. |
| `modality` | no | `str` | `'CT'` | See signature. |
| `series_description` | no | `str` | `'Synthetic Fyron volume'` | See signature. |
| `intensity_mode` | no | `str` | `'hu'` | See signature. |
| `rescale_intercept` | no | `float` | `-1024.0` | See signature. |
| `rescale_slope` | no | `float` | `1.0` | See signature. |
| `copy_patient_tags` | no | `bool` | `False` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.dicom.synthetic.write_synthetic_nifti`

Write a synthetic volume to NIfTI while preserving inspectable geometry.

**Import path:** `fyron.dicom.synthetic.write_synthetic_nifti`

```python
write_synthetic_nifti(volume: sitk.Image | np.ndarray, output_path: StrPath, *, reference_image: sitk.Image | StrPath | None = None, spacing: Sequence[float] | None = None, origin: Sequence[float] | None = None, direction: Sequence[float] | None = None, dtype: str | np.dtype = 'float32', compress: bool = True, metadata: dict[str, Any] | None = None) -> Path
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `volume` | yes | `sitk.Image  or  np.ndarray` |  | See signature. |
| `output_path` | yes | `StrPath` |  | See signature. |
| `reference_image` | no | `sitk.Image  or  StrPath  or  None` | `None` | See signature. |
| `spacing` | no | `Sequence[float]  or  None` | `None` | See signature. |
| `origin` | no | `Sequence[float]  or  None` | `None` | See signature. |
| `direction` | no | `Sequence[float]  or  None` | `None` | See signature. |
| `dtype` | no | `str  or  np.dtype` | `'float32'` | See signature. |
| `compress` | no | `bool` | `True` | See signature. |
| `metadata` | no | `dict[str, Any]  or  None` | `None` | See signature. |

### Returns

`Path`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.imaging.dicom_io.get_dicom_series_ids`

List DICOM series IDs under a directory using GDCM (via SimpleITK).

**Import path:** `fyron.imaging.dicom_io.get_dicom_series_ids`

```python
get_dicom_series_ids(dicom_dir: StrPath, *, include_metadata: bool = False, recursive: bool = False) -> Union[list[str], 'pd.DataFrame']
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `dicom_dir` | yes | `StrPath` |  | Directory containing DICOM files (or subdirectories when ``recursive``). |
| `include_metadata` | no | `bool` | `False` | If True, return a ``pandas.DataFrame`` summary; otherwise a list of series UIDs. |
| `recursive` | no | `bool` | `False` | If True, scan subfolders for ``*.dcm`` files and aggregate series IDs found in each directory that contains DICOM (can be slower on large trees). |

### Returns

`list[str] or pandas.DataFrame` - Series instance UIDs, or a metadata table when ``include_metadata`` is True. Empty input yields ``[]`` or an empty DataFrame with the expected columns.

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.imaging.dicom_io.read_dicom_header`

Read a DICOM file header with pydicom.

**Import path:** `fyron.imaging.dicom_io.read_dicom_header`

```python
read_dicom_header(dicom_path: StrPath, *, stop_before_pixels: bool = True, force: bool = False, as_dict: bool = False, selected_tags: list[str] | None = None) -> Union[pydicom.Dataset, dict[str, Any]]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `dicom_path` | yes | `StrPath` |  | Path to a DICOM part-10 file. |
| `stop_before_pixels` | no | `bool` | `True` | If True (default), skip loading pixel data for faster IO. |
| `force` | no | `bool` | `False` | If True, attempt to read non-standard files (passed to ``dcmread``). |
| `as_dict` | no | `bool` | `False` | If True, return a flat ``dict`` of tag keyword (or string tag) to value. |
| `selected_tags` | no | `list[str]  or  None` | `None` | Optional list of DICOM keywords (e.g. ``"PatientID"``) or hex tags (``"0010,0020"`` / ``"00100020"``). |

### Returns

`pydicom.dataset.Dataset or dict` - Full dataset, a subset dataset (only when ``selected_tags`` is set and ``as_dict`` is False), or a dict view.

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.imaging.dicom_io.read_dicom_series`

Read a DICOM series as a ``SimpleITK.Image``.

**Import path:** `fyron.imaging.dicom_io.read_dicom_series`

```python
read_dicom_series(study_path: StrPath, series_id: str, *, return_array: bool = False) -> Union[sitk.Image, tuple[sitk.Image, np.ndarray]]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `study_path` | yes | `StrPath` |  | Directory passed to ``GetGDCMSeriesFileNames`` (must contain the series). |
| `series_id` | yes | `str` |  | Series instance UID as returned by ``get_dicom_series_ids``. |
| `return_array` | no | `bool` | `False` | If True, also return ``numpy`` array in **Z, Y, X** order (``GetArrayFromImage``). |

### Returns

`SimpleITK.Image or tuple` - Image, or ``(image, array)`` when ``return_array`` is True.

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.imaging.nifti_io.read_nifti`

Read a NIfTI volume with SimpleITK.

**Import path:** `fyron.imaging.nifti_io.read_nifti`

```python
read_nifti(nifti_path: StrPath, *, return_array: bool = False) -> Union[sitk.Image, tuple[sitk.Image, np.ndarray]]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `nifti_path` | yes | `StrPath` |  | Path ending in ``.nii`` or ``.nii.gz``. |
| `return_array` | no | `bool` | `False` | If True, also return a NumPy array in **Z, Y, X** order (``GetArrayFromImage``). |

### Returns

`SimpleITK.Image or tuple` - Image, or ``(image, array)`` when ``return_array`` is True.

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.imaging.nifti_io.write_nifti`

Write a ``SimpleITK.Image`` or NumPy array to NIfTI.

**Import path:** `fyron.imaging.nifti_io.write_nifti`

```python
write_nifti(image: sitk.Image | np.ndarray, output_path: StrPath, *, reference_image: sitk.Image | None = None, compress: bool = True) -> Path
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `image` | yes | `sitk.Image  or  np.ndarray` |  | ``SimpleITK.Image`` or array in **Z, Y, X** order (as produced by ``GetArrayFromImage``). |
| `output_path` | yes | `StrPath` |  | Destination ``.nii`` or ``.nii.gz`` (parent directories are created). |
| `reference_image` | no | `sitk.Image  or  None` | `None` | When ``image`` is a NumPy array, copy spacing, origin, and direction from this image. When ``image`` is already a ``SimpleITK.Image`` and ``reference_image`` is set, geometry is overwritten from the reference before writing. |
| `compress` | no | `bool` | `True` | If True, request compression (always on for ``.nii.gz``; for plain ``.nii`` uses SimpleITK's writer compression flag when supported). |

### Returns

`pathlib.Path` - Resolved output path.

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.imaging.normalize.normalize_ct`

Clip CT Hounsfield units and scale linearly to ``[0, 1]`` as float32.

**Import path:** `fyron.imaging.normalize.normalize_ct`

```python
normalize_ct(image: sitk.Image | np.ndarray, hu_min: float = -1000.0, hu_max: float = 3000.0) -> sitk.Image | np.ndarray
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `image` | yes | `sitk.Image  or  np.ndarray` |  | ``SimpleITK.Image`` (HU) or NumPy array in **Z, Y, X** order. |
| `hu_min` | no | `float` | `-1000.0` | See signature. |
| `hu_max` | no | `float` | `3000.0` | HU window; ``hu_max`` must be greater than ``hu_min``. |

### Returns

`SimpleITK.Image or numpy.ndarray` - Same container type as input; float32 intensities in ``[0, 1]``. For ``SimpleITK`` input, spacing, origin, and direction are preserved.

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.imaging.normalize.normalize_mr`

Normalize MR intensities to a ``[0, 1]`` float scale (default: high percentile).

**Import path:** `fyron.imaging.normalize.normalize_mr`

```python
normalize_mr(image: sitk.Image | np.ndarray, *, mode: str = 'percentile', percentile: float = 99.0, value: float | None = None, ignore_zeros: bool = True, clip: bool = True) -> sitk.Image | np.ndarray
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `image` | yes | `sitk.Image  or  np.ndarray` |  | ``SimpleITK.Image`` or NumPy array in **Z, Y, X** order. |
| `mode` | no | `str` | `'percentile'` | ``"percentile"`` (divide by given percentile), ``"max"`` (divide by max), or ``"value"`` (divide by fixed ``value``). |
| `percentile` | no | `float` | `99.0` | Used when ``mode="percentile"`` (e.g. 95 or 99). |
| `value` | no | `float  or  None` | `None` | Required positive divisor when ``mode="value"``. |
| `ignore_zeros` | no | `bool` | `True` | If True, zeros are excluded when computing percentile or max statistics. |
| `clip` | no | `bool` | `True` | If True, clip output to ``[0, 1]``. |

### Returns

`SimpleITK.Image or numpy.ndarray` - Same container type as input; float32. Geometry preserved for ``SimpleITK``.

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.imaging.qc.check_image_mask_alignment`

Check whether image and mask share shape, spacing, origin, and direction.

**Import path:** `fyron.imaging.qc.check_image_mask_alignment`

```python
check_image_mask_alignment(image: sitk.Image | StrPath, mask: sitk.Image | StrPath) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `image` | yes | `sitk.Image  or  StrPath` |  | See signature. |
| `mask` | yes | `sitk.Image  or  StrPath` |  | See signature. |

### Returns

`dict[str, Any]`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.imaging.qc.summarize_dicom_series_geometry`

Summarize DICOM series geometry under a directory.

**Import path:** `fyron.imaging.qc.summarize_dicom_series_geometry`

```python
summarize_dicom_series_geometry(dicom_dir: StrPath, *, recursive: bool = False) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `dicom_dir` | yes | `StrPath` |  | See signature. |
| `recursive` | no | `bool` | `False` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.imaging.qc.summarize_intensity_range`

Summarize intensity distribution, optionally inside a mask.

**Import path:** `fyron.imaging.qc.summarize_intensity_range`

```python
summarize_intensity_range(image: sitk.Image | np.ndarray | StrPath, *, mask: sitk.Image | np.ndarray | StrPath | None = None, percentiles: Sequence[float] = (0.5, 99.5)) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `image` | yes | `sitk.Image  or  np.ndarray  or  StrPath` |  | See signature. |
| `mask` | no | `sitk.Image  or  np.ndarray  or  StrPath  or  None` | `None` | See signature. |
| `percentiles` | no | `Sequence[float]` | `(0.5, 99.5)` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.imaging.qc.summarize_mask_volume`

Return label-wise mask voxel counts and volumes in ml.

**Import path:** `fyron.imaging.qc.summarize_mask_volume`

```python
summarize_mask_volume(mask: sitk.Image | np.ndarray | StrPath, *, labels: Sequence[int] | None = None, spacing: Sequence[float] | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `mask` | yes | `sitk.Image  or  np.ndarray  or  StrPath` |  | See signature. |
| `labels` | no | `Sequence[int]  or  None` | `None` | See signature. |
| `spacing` | no | `Sequence[float]  or  None` | `None` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.imaging.qc.summarize_nifti_geometry`

Summarize shape and geometry for one or more NIfTI files.

**Import path:** `fyron.imaging.qc.summarize_nifti_geometry`

```python
summarize_nifti_geometry(paths: StrPath | Sequence[StrPath]) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `paths` | yes | `StrPath  or  Sequence[StrPath]` |  | See signature. |

### Returns

`pd.DataFrame`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.imaging.segmentation.dice_score`

Return Dice score for binary masks or one label in label maps.

**Import path:** `fyron.imaging.segmentation.dice_score`

```python
dice_score(mask_true: Any, mask_pred: Any, *, label: int | None = None) -> float
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `mask_true` | yes | `Any` |  | See signature. |
| `mask_pred` | yes | `Any` |  | See signature. |
| `label` | no | `int  or  None` | `None` | See signature. |

### Returns

`float`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.imaging.segmentation.hausdorff_distance`

Return symmetric Hausdorff distance between mask surfaces.

**Import path:** `fyron.imaging.segmentation.hausdorff_distance`

```python
hausdorff_distance(mask_true: Any, mask_pred: Any, *, label: int | None = None, spacing: Sequence[float] | None = None, percentile: float | None = None) -> float
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `mask_true` | yes | `Any` |  | See signature. |
| `mask_pred` | yes | `Any` |  | See signature. |
| `label` | no | `int  or  None` | `None` | See signature. |
| `spacing` | no | `Sequence[float]  or  None` | `None` | See signature. |
| `percentile` | no | `float  or  None` | `None` | See signature. |

### Returns

`float`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.imaging.segmentation.label_overlap_table`

Return label-wise overlap and volume metrics.

**Import path:** `fyron.imaging.segmentation.label_overlap_table`

```python
label_overlap_table(mask_true: Any, mask_pred: Any, *, labels: Sequence[int] | Mapping[int, str] | None = None, spacing: Sequence[float] | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `mask_true` | yes | `Any` |  | See signature. |
| `mask_pred` | yes | `Any` |  | See signature. |
| `labels` | no | `Sequence[int]  or  Mapping[int, str]  or  None` | `None` | See signature. |
| `spacing` | no | `Sequence[float]  or  None` | `None` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.imaging.segmentation.segmentation_metric_table`

Return label-wise Dice, Hausdorff, surface Dice, and volume metrics.

**Import path:** `fyron.imaging.segmentation.segmentation_metric_table`

```python
segmentation_metric_table(mask_true: Any, mask_pred: Any, *, labels: Sequence[int] | Mapping[int, str] | None = None, spacing: Sequence[float] | None = None, surface_tolerance: float = 1.0) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `mask_true` | yes | `Any` |  | See signature. |
| `mask_pred` | yes | `Any` |  | See signature. |
| `labels` | no | `Sequence[int]  or  Mapping[int, str]  or  None` | `None` | See signature. |
| `spacing` | no | `Sequence[float]  or  None` | `None` | See signature. |
| `surface_tolerance` | no | `float` | `1.0` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.imaging.segmentation.surface_dice`

Return surface Dice at a distance tolerance.

**Import path:** `fyron.imaging.segmentation.surface_dice`

```python
surface_dice(mask_true: Any, mask_pred: Any, *, label: int | None = None, tolerance: float = 1.0, spacing: Sequence[float] | None = None) -> float
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `mask_true` | yes | `Any` |  | See signature. |
| `mask_pred` | yes | `Any` |  | See signature. |
| `label` | no | `int  or  None` | `None` | See signature. |
| `tolerance` | no | `float` | `1.0` | See signature. |
| `spacing` | no | `Sequence[float]  or  None` | `None` | See signature. |

### Returns

`float`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).

## `fyron.imaging.segmentation.volume_difference`

Return absolute and relative volume differences.

**Import path:** `fyron.imaging.segmentation.volume_difference`

```python
volume_difference(mask_true: Any, mask_pred: Any, *, label: int | None = None, spacing: Sequence[float] | None = None) -> dict[str, float]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `mask_true` | yes | `Any` |  | See signature. |
| `mask_pred` | yes | `Any` |  | See signature. |
| `label` | no | `int  or  None` | `None` | See signature. |
| `spacing` | no | `Sequence[float]  or  None` | `None` | See signature. |

### Returns

`dict[str, float]`

**See also:** [DICOM And Imaging module guide](../modules/dicom.md).
