# BOA Reference

Body-and-Organ-Analysis feature extraction, radiomics, experimental aortic calcification, and visual collages.

For workflow context, see [BOA module guide](../modules/boa.md).

## Functions And Classes

- [`fyron.boa_extraction.experimental_aortic_calcification.extract_experimental_aortic_calcification_features`](#fyronboaextractionexperimentalaorticcalcificationextractexperimentalaorticcalcificationfeatures)
- [`fyron.boa_extraction.experimental_aortic_calcification.extract_experimental_cohort_aortic_calcification_features`](#fyronboaextractionexperimentalaorticcalcificationextractexperimentalcohortaorticcalcificationfeatures)
- [`fyron.boa_extraction.features.discover_boa_cases`](#fyronboaextractionfeaturesdiscoverboacases)
- [`fyron.boa_extraction.features.extract_boa_features`](#fyronboaextractionfeaturesextractboafeatures)
- [`fyron.boa_extraction.features.extract_body_region_features`](#fyronboaextractionfeaturesextractbodyregionfeatures)
- [`fyron.boa_extraction.features.extract_cohort_body_region_features`](#fyronboaextractionfeaturesextractcohortbodyregionfeatures)
- [`fyron.boa_extraction.features.extract_cohort_total_features`](#fyronboaextractionfeaturesextractcohorttotalfeatures)
- [`fyron.boa_extraction.features.extract_total_segmentation_features`](#fyronboaextractionfeaturesextracttotalsegmentationfeatures)
- [`fyron.boa_extraction.features.read_json_file`](#fyronboaextractionfeaturesreadjsonfile)
- [`fyron.boa_radiomics.features.discover_boa_radiomics_cases`](#fyronboaradiomicsfeaturesdiscoverboaradiomicscases)
- [`fyron.boa_radiomics.features.extract_boa_radiomics_features`](#fyronboaradiomicsfeaturesextractboaradiomicsfeatures)
- [`fyron.boa_radiomics.features.extract_case_radiomics_features`](#fyronboaradiomicsfeaturesextractcaseradiomicsfeatures)
- [`fyron.visualization.boa.create_boa_segmentation_collage`](#fyronvisualizationboacreateboasegmentationcollage)
- [`fyron.visualization.curate_previews.PreviewSource`](#fyronvisualizationcuratepreviewspreviewsource)
- [`fyron.visualization.curate_previews.discover_preview_sources`](#fyronvisualizationcuratepreviewsdiscoverpreviewsources)
- [`fyron.visualization.curate_previews.prepare_curate_image_previews`](#fyronvisualizationcuratepreviewspreparecurateimagepreviews)
- [`fyron.visualization.segmentation_collage.create_segmentation_collage`](#fyronvisualizationsegmentationcollagecreatesegmentationcollage)
- [`fyron.visualization.segmentation_collage.create_segmentation_collages_from_cases`](#fyronvisualizationsegmentationcollagecreatesegmentationcollagesfromcases)
- [`fyron.visualization.volume_difference.plot_volume_difference_heatmap`](#fyronvisualizationvolumedifferenceplotvolumedifferenceheatmap)

## `fyron.boa_extraction.experimental_aortic_calcification.extract_experimental_aortic_calcification_features`

Extract experimental aortic calcification burden from BOA-style masks.

**Import path:** `fyron.boa_extraction.experimental_aortic_calcification.extract_experimental_aortic_calcification_features`

```python
extract_experimental_aortic_calcification_features(case_folder_or_masks_dir: str | Path, *, ct_path: str | Path | None = None, masks_dir: str | Path | None = None, download_id: str | None = None, hu_threshold: float = 130.0, prefix: str = 'aortic_calcification', aorta_mask_filenames: str | Sequence[str] = DEFAULT_AORTA_MASK_FILENAMES, total_mask_filenames: str | Sequence[str] = DEFAULT_TOTAL_MASK_FILENAMES, total_aorta_labels: Sequence[int] = DEFAULT_TOTAL_AORTA_LABELS, thoracic_mask_filename: str = 'thoracic_cavity.nii.gz', abdominal_mask_filename: str = 'abdominal_cavity.nii.gz', body_region_mask_filename: str = DEFAULT_BODY_REGION_MASK_FILENAME, body_region_labels: Mapping[str, int] | None = DEFAULT_BODY_REGION_LABELS, iliac_glob: str = '*iliac*.nii.gz', include_iliac: bool = True, missing_value: float | None = np.nan) -> dict[str, Any] | None
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `case_folder_or_masks_dir` | yes | `str  or  Path` |  | Patient folder or mask folder. |
| `ct_path` | no | `str  or  Path  or  None` | `None` | CT NIfTI in Hounsfield units. If omitted, common filenames are searched in the case folder. |
| `masks_dir` | no | `str  or  Path  or  None` | `None` | Folder containing BOA masks. Defaults to ``case_folder_or_masks_dir``. |
| `download_id` | no | `str  or  None` | `None` | Optional explicit case identifier. Defaults to the folder name. |
| `hu_threshold` | no | `float` | `130.0` | Voxels inside the vascular mask with HU >= this value are counted as calcification. |
| `prefix` | no | `str` | `'aortic_calcification'` | Prefix for all generated feature columns. |
| `aorta_mask_filenames` | no | `str  or  Sequence[str]` | `DEFAULT_AORTA_MASK_FILENAMES` | Binary aorta mask filenames to try first. |
| `total_mask_filenames` | no | `str  or  Sequence[str]` | `DEFAULT_TOTAL_MASK_FILENAMES` | Fallback multiclass total segmentation filenames. |
| `total_aorta_labels` | no | `Sequence[int]` | `DEFAULT_TOTAL_AORTA_LABELS` | Label values counted as aorta in ``total.nii.gz``. Defaults to ``52`` and should be verified against the local label map. |
| `thoracic_mask_filename` | no | `str` | `'thoracic_cavity.nii.gz'` | See signature. |
| `abdominal_mask_filename` | no | `str` | `'abdominal_cavity.nii.gz'` | Optional binary body-region masks used to split the aorta. |
| `body_region_mask_filename` | no | `str` | `DEFAULT_BODY_REGION_MASK_FILENAME` | Optional multiclass body-region mask fallback. |
| `body_region_labels` | no | `Mapping[str, int]  or  None` | `DEFAULT_BODY_REGION_LABELS` | Mapping of output region names to labels in ``body_region_mask_filename``. |
| `iliac_glob` | no | `str` | `'*iliac*.nii.gz'` | Glob used to discover iliac masks for aortoiliac burden. |
| `include_iliac` | no | `bool` | `True` | Whether to include iliac-extension and total-aortoiliac features. |
| `missing_value` | no | `float  or  None` | `np.nan` | Value used for unavailable optional regions. |

### Returns

`dict or None` - One flat feature row, or ``None`` when CT/aorta inputs are unavailable.

**See also:** [BOA module guide](../modules/boa.md).

## `fyron.boa_extraction.experimental_aortic_calcification.extract_experimental_cohort_aortic_calcification_features`

Extract experimental aortic calcification features for many BOA cases.

**Import path:** `fyron.boa_extraction.experimental_aortic_calcification.extract_experimental_cohort_aortic_calcification_features`

```python
extract_experimental_cohort_aortic_calcification_features(cohort_folder_or_cases: str | Path | Iterable[str | Path], *, num_workers: int = 1, show_progress: bool = True, return_report: bool = False, **kwargs: Any) -> pd.DataFrame | dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `cohort_folder_or_cases` | yes | `str  or  Path  or  Iterable[str  or  Path]` |  | Case path, cohort directory, or iterable of case paths; names must be unique. |
| `num_workers` | no | `int` | `1` | Number of extraction processes; use one for sequential execution. |
| `show_progress` | no | `bool` | `True` | Display completed case progress. |
| `return_report` | no | `bool` | `False` | If True, return data plus rows and summary report tables; otherwise return the DataFrame. |
| `kwargs` | yes | `Any` |  | Additional keyword arguments passed to the corresponding single-case extractor. |

### Returns

`pd.DataFrame | dict[str, Any]`

**See also:** [BOA module guide](../modules/boa.md).

## `fyron.boa_extraction.features.discover_boa_cases`

Discover BOA patient folders below a cohort directory.

**Import path:** `fyron.boa_extraction.features.discover_boa_cases`

```python
discover_boa_cases(cohort_folder: str | Path, *, measurement_filename: str = 'bca-measurements.json') -> list[Path]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `cohort_folder` | yes | `str  or  Path` |  | Root folder containing patient subfolders such as ``patient0001``. |
| `measurement_filename` | no | `str` | `'bca-measurements.json'` | File used to identify completed BOA cases. |

### Returns

`list[pathlib.Path]` - Sorted patient folders that contain the measurement file.

**See also:** [BOA module guide](../modules/boa.md).

## `fyron.boa_extraction.features.extract_boa_features`

Extract and merge available BOA feature families by ``download_id``.

**Import path:** `fyron.boa_extraction.features.extract_boa_features`

```python
extract_boa_features(cohort_folder_or_cases: str | Path | Iterable[str | Path], *, include_body_regions: bool = True, include_total: bool = True, num_workers: int = 1, show_progress: bool = True, body_region_kwargs: Mapping[str, Any] | None = None, total_kwargs: Mapping[str, Any] | None = None, return_report: bool = False) -> pd.DataFrame | dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `cohort_folder_or_cases` | yes | `str  or  Path  or  Iterable[str  or  Path]` |  | Case path, cohort directory, or iterable of case paths; names must be unique. |
| `include_body_regions` | no | `bool` | `True` | Include body-composition measurements. |
| `include_total` | no | `bool` | `True` | Include total-organ measurements. |
| `num_workers` | no | `int` | `1` | Number of extraction processes; use one for sequential execution. |
| `show_progress` | no | `bool` | `True` | Display completed case progress. |
| `body_region_kwargs` | no | `Mapping[str, Any]  or  None` | `None` | Options forwarded to body-region extraction. |
| `total_kwargs` | no | `Mapping[str, Any]  or  None` | `None` | Options forwarded to total-organ extraction. |
| `return_report` | no | `bool` | `False` | If True, return data plus rows and summary report tables; otherwise return the DataFrame. |

### Returns

`pd.DataFrame | dict[str, Any]`

**See also:** [BOA module guide](../modules/boa.md).

## `fyron.boa_extraction.features.extract_body_region_features`

Extract body-region tissue volumes and vertebral SMA features.

**Import path:** `fyron.boa_extraction.features.extract_body_region_features`

```python
extract_body_region_features(case_folder_or_measurements: str | Path, *, body_regions: Sequence[str] = BODY_REGIONS, tissues: Sequence[str] = TISSUES, vertebrae: Sequence[str] = VERTEBRAE, measurement_filename: str = 'bca-measurements.json', sma_segmentation_filename: str | Sequence[str] = ('tissues.nii.gz',), sma_label: int | None = None, slice_levels: Sequence[str] = ('l3',), slice_tissue_labels: Mapping[str, int] | None = None, height_m: float | None = None, include_derived_markers: bool = True, derived_markers: Sequence[Mapping[str, Any]] = DEFAULT_BODY_REGION_DERIVED_MARKERS, download_id: str | None = None, include_sma: bool = True, missing_value: float | None = np.nan) -> dict[str, Any] | None
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `case_folder_or_measurements` | yes | `str  or  Path` |  | Patient folder or path to ``bca-measurements.json``. |
| `body_regions` | no | `Sequence[str]` | `BODY_REGIONS` | Body-region keys expected in the BOA aggregated measurements. |
| `tissues` | no | `Sequence[str]` | `TISSUES` | Tissue keys read from ``measurements_no_extremities``. |
| `vertebrae` | no | `Sequence[str]` | `VERTEBRAE` | Vertebral level keys used to select the middle axial slice. |
| `measurement_filename` | no | `str` | `'bca-measurements.json'` | Measurement filename when a patient folder is passed. |
| `sma_segmentation_filename` | no | `str  or  Sequence[str]` | `('tissues.nii.gz',)` | Segmentation file used for skeletal muscle area calculation. Pass a sequence to try multiple filenames in order. |
| `sma_label` | no | `int  or  None` | `None` | Explicit muscle label override. By default, use label 1 in BOA tissues. Custom masks require explicit labels; anatomical body-region masks are not a substitute for HU-filtered tissue masks. |
| `slice_levels` | no | `Sequence[str]` | `('l3',)` | Vertebral levels used for richer axial area markers, e.g. ``("l3",)``. |
| `slice_tissue_labels` | no | `Mapping[str, int]  or  None` | `None` | Mapping from marker names to segmentation label values. Defaults to ``{"sma": 1, "imat": 5, "vat": 4, "sat": 3}`` for ``tissues.nii.gz``. For other filenames, only explicitly supplied labels are measured. |
| `height_m` | no | `float  or  None` | `None` | Optional patient height in meters. Area-based ``smi``, ``imati``, ``vati``, and ``sati`` do not require height. When height is provided, additional ``*_cm2_per_m2`` columns are calculated. |
| `include_derived_markers` | no | `bool` | `True` | Calculate body-region volume ratios such as muscle/bone and IMAT/TAT. |
| `derived_markers` | no | `Sequence[Mapping[str, Any]]` | `DEFAULT_BODY_REGION_DERIVED_MARKERS` | Marker definitions with ``name``, ``numerator``, ``denominator``, and optional ``regions`` keys. |
| `download_id` | no | `str  or  None` | `None` | Optional explicit case identifier. Defaults to the patient folder name. |
| `include_sma` | no | `bool` | `True` | Calculate ``<vertebra>_sma`` when the segmentation file is present. |
| `missing_value` | no | `float  or  None` | `np.nan` | Value used when a measurement key is missing. |

### Returns

`dict or None` - One row of features. ``None`` is returned when the JSON file is missing or malformed.

**See also:** [BOA module guide](../modules/boa.md).

## `fyron.boa_extraction.features.extract_cohort_body_region_features`

Extract body-region features for all completed BOA cases in a cohort.

**Import path:** `fyron.boa_extraction.features.extract_cohort_body_region_features`

```python
extract_cohort_body_region_features(cohort_folder_or_cases: str | Path | Iterable[str | Path], *, num_workers: int = 1, show_progress: bool = True, measurement_filename: str = 'bca-measurements.json', return_report: bool = False, **kwargs: Any) -> pd.DataFrame | dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `cohort_folder_or_cases` | yes | `str  or  Path  or  Iterable[str  or  Path]` |  | Case path, cohort directory, or iterable of case paths; names must be unique. |
| `num_workers` | no | `int` | `1` | Number of extraction processes; use one for sequential execution. |
| `show_progress` | no | `bool` | `True` | Display completed case progress. |
| `measurement_filename` | no | `str` | `'bca-measurements.json'` | Measurement JSON filename used for discovery and extraction. |
| `return_report` | no | `bool` | `False` | If True, return data plus rows and summary report tables; otherwise return the DataFrame. |
| `kwargs` | yes | `Any` |  | Additional keyword arguments passed to the corresponding single-case extractor. |

### Returns

`pd.DataFrame | dict[str, Any]`

**See also:** [BOA module guide](../modules/boa.md).

## `fyron.boa_extraction.features.extract_cohort_total_features`

Extract total-segmentation features for all BOA cases in a cohort.

**Import path:** `fyron.boa_extraction.features.extract_cohort_total_features`

```python
extract_cohort_total_features(cohort_folder_or_cases: str | Path | Iterable[str | Path], *, num_workers: int = 1, show_progress: bool = True, measurement_filename: str = 'total-measurements.json', return_report: bool = False, **kwargs: Any) -> pd.DataFrame | dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `cohort_folder_or_cases` | yes | `str  or  Path  or  Iterable[str  or  Path]` |  | Case path, cohort directory, or iterable of case paths; names must be unique. |
| `num_workers` | no | `int` | `1` | Number of extraction processes; use one for sequential execution. |
| `show_progress` | no | `bool` | `True` | Display completed case progress. |
| `measurement_filename` | no | `str` | `'total-measurements.json'` | Measurement JSON filename used for discovery and extraction. |
| `return_report` | no | `bool` | `False` | If True, return data plus rows and summary report tables; otherwise return the DataFrame. |
| `kwargs` | yes | `Any` |  | Additional keyword arguments passed to the corresponding single-case extractor. |

### Returns

`pd.DataFrame | dict[str, Any]`

**See also:** [BOA module guide](../modules/boa.md).

## `fyron.boa_extraction.features.extract_total_segmentation_features`

Extract organ volume, HU, CNR, and ratio features from total measurements.

**Import path:** `fyron.boa_extraction.features.extract_total_segmentation_features`

```python
extract_total_segmentation_features(case_folder: str | Path, *, labels: Mapping[str, int] = TOTAL_LABELS, ratios: Sequence[tuple[str, str]] = TOTAL_RATIOS, measurement_filename: str = 'total-measurements.json', download_id: str | None = None, round_digits: int | None = 2, missing_value: float | None = np.nan) -> dict[str, Any] | None
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `case_folder` | yes | `str  or  Path` |  | Patient folder containing ``total-measurements.json``. |
| `labels` | no | `Mapping[str, int]` | `TOTAL_LABELS` | Organ labels to extract from ``segmentations.total``. |
| `ratios` | no | `Sequence[tuple[str, str]]` | `TOTAL_RATIOS` | Organ volume ratios to compute as ``organ_a / organ_b``. |
| `measurement_filename` | no | `str` | `'total-measurements.json'` | Total segmentation measurements filename. |
| `download_id` | no | `str  or  None` | `None` | Optional explicit case identifier. Defaults to the patient folder name. |
| `round_digits` | no | `int  or  None` | `2` | Number of digits used for rounded numeric features. Set to ``None`` to keep original precision. |
| `missing_value` | no | `float  or  None` | `np.nan` | Value used when a metric or organ is missing. |

### Returns

`dict or None` - One row of total-segmentation features, or ``None`` when no valid JSON is available.

**See also:** [BOA module guide](../modules/boa.md).

## `fyron.boa_extraction.features.read_json_file`

Read a JSON file and return parsed content.

**Import path:** `fyron.boa_extraction.features.read_json_file`

```python
read_json_file(file_path: str | Path) -> dict[str, Any] | list[Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `file_path` | yes | `str  or  Path` |  | JSON file path. |

### Returns

`dict or list` - Parsed JSON content.

**See also:** [BOA module guide](../modules/boa.md).

## `fyron.boa_radiomics.features.discover_boa_radiomics_cases`

Discover BOA patient folders with a target segmentation file.

**Import path:** `fyron.boa_radiomics.features.discover_boa_radiomics_cases`

```python
discover_boa_radiomics_cases(cohort_folder: str | Path, *, segmentation_filename: str | Path = 'total.nii.gz') -> list[Path]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `cohort_folder` | yes | `str  or  Path` |  | See signature. |
| `segmentation_filename` | no | `str  or  Path` | `'total.nii.gz'` | See signature. |

### Returns

`list[Path]`

**See also:** [BOA module guide](../modules/boa.md).

## `fyron.boa_radiomics.features.extract_boa_radiomics_features`

Extract BOA radiomics features for a cohort of patient folders.

**Import path:** `fyron.boa_radiomics.features.extract_boa_radiomics_features`

```python
extract_boa_radiomics_features(cohort_folder_or_cases: str | Path | Iterable[str | Path], *, image_filename: str | Path | Sequence[str | Path] = DEFAULT_IMAGE_FILENAMES, segmentation_kind: SegmentationKind = 'total', segmentation_filename: str | Path | None = None, labels: Mapping[str, int] | Sequence[int] | None = None, extractor_settings: Mapping[str, Any] | None = None, feature_prefix: str = 'radiomics', include_paths: bool = True, exclude_diagnostics: bool = True, minimum_voxels: int = 1, resample_mask: bool = True, on_error: OnError = 'skip', num_workers: int = 1, show_progress: bool = True, return_report: bool = False) -> pd.DataFrame | dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `cohort_folder_or_cases` | yes | `str  or  Path  or  Iterable[str  or  Path]` |  | Case path, cohort directory, or iterable of case paths; names must be unique. |
| `image_filename` | no | `str  or  Path  or  Sequence[str  or  Path]` | `DEFAULT_IMAGE_FILENAMES` | Image filename or ordered candidate filenames. |
| `segmentation_kind` | no | `SegmentationKind` | `'total'` | Label convention: total or body_regions. |
| `segmentation_filename` | no | `str  or  Path  or  None` | `None` | Explicit mask filename; defaults to the selected convention. |
| `labels` | no | `Mapping[str, int]  or  Sequence[int]  or  None` | `None` | Mapping of label names to integer values, or a sequence of integers. |
| `extractor_settings` | no | `Mapping[str, Any]  or  None` | `None` | Settings passed to the PyRadiomics extractor. |
| `feature_prefix` | no | `str` | `'radiomics'` | Prefix for extracted feature columns. |
| `include_paths` | no | `bool` | `True` | Include sensitive source paths in the feature table. |
| `exclude_diagnostics` | no | `bool` | `True` | Omit PyRadiomics diagnostic feature columns. |
| `minimum_voxels` | no | `int` | `1` | Skip feature extraction for masks smaller than this voxel count. |
| `resample_mask` | no | `bool` | `True` | Resample masks to the image grid when needed; this is not registration. |
| `on_error` | no | `OnError` | `'skip'` | Use skip to retain partial results, or raise to propagate extraction failures. |
| `num_workers` | no | `int` | `1` | Number of extraction processes; use one for sequential execution. |
| `show_progress` | no | `bool` | `True` | Display completed case progress. |
| `return_report` | no | `bool` | `False` | If True, return data plus rows and summary report tables; otherwise return the DataFrame. |

### Returns

`pd.DataFrame | dict[str, Any]`

**See also:** [BOA module guide](../modules/boa.md).

## `fyron.boa_radiomics.features.extract_case_radiomics_features`

Extract PyRadiomics features for one BOA case folder.

**Import path:** `fyron.boa_radiomics.features.extract_case_radiomics_features`

```python
extract_case_radiomics_features(case_folder: str | Path, *, image_filename: str | Path | Sequence[str | Path] = DEFAULT_IMAGE_FILENAMES, segmentation_kind: SegmentationKind = 'total', segmentation_filename: str | Path | None = None, labels: Mapping[str, int] | Sequence[int] | None = None, extractor: Any | None = None, extractor_settings: Mapping[str, Any] | None = None, feature_prefix: str = 'radiomics', download_id: str | None = None, include_paths: bool = True, exclude_diagnostics: bool = True, minimum_voxels: int = 1, resample_mask: bool = True, on_error: OnError = 'skip') -> dict[str, Any] | None
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `case_folder` | yes | `str  or  Path` |  | See signature. |
| `image_filename` | no | `str  or  Path  or  Sequence[str  or  Path]` | `DEFAULT_IMAGE_FILENAMES` | See signature. |
| `segmentation_kind` | no | `SegmentationKind` | `'total'` | See signature. |
| `segmentation_filename` | no | `str  or  Path  or  None` | `None` | See signature. |
| `labels` | no | `Mapping[str, int]  or  Sequence[int]  or  None` | `None` | See signature. |
| `extractor` | no | `Any  or  None` | `None` | See signature. |
| `extractor_settings` | no | `Mapping[str, Any]  or  None` | `None` | See signature. |
| `feature_prefix` | no | `str` | `'radiomics'` | See signature. |
| `download_id` | no | `str  or  None` | `None` | See signature. |
| `include_paths` | no | `bool` | `True` | See signature. |
| `exclude_diagnostics` | no | `bool` | `True` | See signature. |
| `minimum_voxels` | no | `int` | `1` | See signature. |
| `resample_mask` | no | `bool` | `True` | See signature. |
| `on_error` | no | `OnError` | `'skip'` | See signature. |

### Returns

`dict[str, Any] | None`

**See also:** [BOA module guide](../modules/boa.md).

## `fyron.visualization.boa.create_boa_segmentation_collage`

Create a multi-patient BOA collage with OpenCV.

**Import path:** `fyron.visualization.boa.create_boa_segmentation_collage`

```python
create_boa_segmentation_collage(boa_folders: Sequence[StrPath], output_path: StrPath, *, orientation: Orientation = 'axial', segmentation_layers: Sequence[SegmentationLayer | SegmentationKind | str] | None = None, patient_labels: Sequence[str] | None = None, slice_index: int | None = None, slice_indices: Sequence[int] | None = None, slice_fraction: float | None = None, ct_filename: str | None = None, window_center: float = 40.0, window_width: float = 400.0, segmentation_opacity: float = 0.45, overlay_alpha: float | None = None, panel_width: int = 320, row_label_prefix: str | None = None, crop_body_region: int | str | None = None, body_region_padding_mm: float = 15.0, body_region_slices: BodyRegionSliceMode = 'best') -> CollageResult
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `boa_folders` | yes | `Sequence[StrPath]` |  | One BOA output directory per patient. |
| `output_path` | yes | `StrPath` |  | Destination image path (``.png`` recommended). |
| `orientation` | no | `Orientation` | `'axial'` | ``axial``, ``sagittal``, or ``coronal``. |
| `segmentation_layers` | no | `Sequence[SegmentationLayer  or  SegmentationKind  or  str]  or  None` | `None` | Which masks to show and how. Pass kinds (``"body_regions"``, ``"tissues"``, ``"total"``) or ``SegmentationLayer`` objects with ``display_mode`` of ``ct``, ``ct_overlay``, or ``segmentation``. |
| `patient_labels` | no | `Sequence[str]  or  None` | `None` | Patient ID shown rotated at the start of each row (e.g. ``Patient A``). |
| `slice_index` | no | `int  or  None` | `None` | Absolute slice index along the orientation axis. |
| `slice_indices` | no | `Sequence[int]  or  None` | `None` | Multiple slice rows (absolute indices). Not combined with ``slice_fraction``. |
| `slice_fraction` | no | `float  or  None` | `None` | Relative slice position in ``[0, 1]`` per patient (handles different volume depths). Ignored when ``slice_indices`` is set. |
| `ct_filename` | no | `str  or  None` | `None` | Optional explicit CT filename inside each folder. |
| `window_center` | no | `float` | `40.0` | See signature. |
| `window_width` | no | `float` | `400.0` | CT window for grayscale / overlay backgrounds. |
| `segmentation_opacity` | no | `float` | `0.45` | Opacity of segmentation colors in ``ct_overlay`` and ``segmentation`` panels, in ``[0, 1]``. Per-layer override via ``SegmentationLayer(opacity=...)``. |
| `overlay_alpha` | no | `float  or  None` | `None` | Deprecated alias for ``segmentation_opacity``. |
| `panel_width` | no | `int` | `320` | Panel width in pixels; height follows voxel spacing. |
| `row_label_prefix` | no | `str  or  None` | `None` | See signature. |
| `crop_body_region` | no | `int  or  str  or  None` | `None` | BOA body-region label id or name (e.g. ``3`` or ``"Abdominal Cavity"``). Selects only slices containing this region and crops each panel to its bounding box (plus ``body_region_padding_mm``). |
| `body_region_padding_mm` | no | `float` | `15.0` | Padding around the cropped body region in millimetres. |
| `body_region_slices` | no | `BodyRegionSliceMode` | `'best'` | ``best`` (default): slice with largest in-plane region area; ``center``: middle slice of the region extent; ``all``: every slice that contains the region. |

### Returns

`dict` - ``output_path``, ``patient_paths``, ``segmentation_layers``, ``slice_indices_used``, ``orientation``, ``image_shape``, and when cropping is enabled ``crop_body_region``.

**See also:** [BOA module guide](../modules/boa.md).

## `fyron.visualization.curate_previews.PreviewSource`

Input source resolved from a directory scan.

**Import path:** `fyron.visualization.curate_previews.PreviewSource`

```python
PreviewSource()
```

### Parameters

No parameters documented.

### Returns

Class constructor.

**See also:** [BOA module guide](../modules/boa.md).

## `fyron.visualization.curate_previews.discover_preview_sources`

Discover DICOM series and image files below a directory.

**Import path:** `fyron.visualization.curate_previews.discover_preview_sources`

```python
discover_preview_sources(input_dir: StrPath, *, recursive: bool = True, include_dicom: bool = True, include_image_files: bool = True) -> list[PreviewSource]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `input_dir` | yes | `StrPath` |  | See signature. |
| `recursive` | no | `bool` | `True` | See signature. |
| `include_dicom` | no | `bool` | `True` | See signature. |
| `include_image_files` | no | `bool` | `True` | See signature. |

### Returns

`list[PreviewSource]`

**See also:** [BOA module guide](../modules/boa.md).

## `fyron.visualization.curate_previews.prepare_curate_image_previews`

Write Curate-ready PNG previews from medical image folders.

**Import path:** `fyron.visualization.curate_previews.prepare_curate_image_previews`

```python
prepare_curate_image_previews(input_dir: StrPath, output_dir: StrPath, *, recursive: bool = True, include_dicom: bool = True, include_image_files: bool = True, panel_width: int = 384, window_center: float | None = None, window_width: float | None = None, percentile_clip: tuple[float, float] = (1.0, 99.0), overwrite: bool = False, manifest_csv: StrPath | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `input_dir` | yes | `StrPath` |  | Directory containing CT/MRI volumes, DICOM files, or 2-D images. |
| `output_dir` | yes | `StrPath` |  | Destination folder for PNG previews. |
| `recursive` | no | `bool` | `True` | If True, scan nested folders. |
| `include_dicom` | no | `bool` | `True` | If True, read DICOM series from directories containing DICOM files. |
| `include_image_files` | no | `bool` | `True` | If True, read NIfTI/MHA/NRRD and common 2-D raster image files. |
| `panel_width` | no | `int` | `384` | Output width per PNG. Height follows physical spacing for 3-D slices. |
| `window_center` | no | `float  or  None` | `None` | See signature. |
| `window_width` | no | `float  or  None` | `None` | Optional fixed grayscale window, useful for CT. If omitted, robust percentile normalization is used, which also works for MRI. |
| `percentile_clip` | no | `tuple[float, float]` | `(1.0, 99.0)` | Low/high percentiles for automatic normalization when no fixed window is supplied. |
| `overwrite` | no | `bool` | `False` | If False, existing PNG files are left untouched. |
| `manifest_csv` | no | `StrPath  or  None` | `None` | Optional manifest path. Defaults to ``output_dir / "manifest.csv"``. |

### Returns

`dict` - ``input_dir``, ``output_dir``, ``manifest_csv``, ``sources_found``, ``images_written``, ``images_skipped``, and ``rows``.

**See also:** [BOA module guide](../modules/boa.md).

## `fyron.visualization.segmentation_collage.create_segmentation_collage`

Create a generic OpenCV CT/segmentation overlay collage.

**Import path:** `fyron.visualization.segmentation_collage.create_segmentation_collage`

```python
create_segmentation_collage(image: VolumeInput, segmentation: VolumeInput, output_path: StrPath, *, labels: Sequence[int] | int | None = None, orientation: Orientation = 'axial', slice_strategy: SliceStrategy = 'segmentation_extent', slice_indices: Sequence[int] | None = None, every_n_slices: int | None = None, max_slices: int | None = None, n_cols: int | None = None, window_center: float = 40.0, window_width: float = 400.0, segmentation_opacity: float = 0.4, label_colors: Mapping[int, tuple[int, int, int]] | Sequence[tuple[int, int, int]] | None = None, title: str | None = None, show_slice_labels: bool = True, panel_width: int = 256, spacing: tuple[float, float, float] = (1.0, 1.0, 1.0)) -> CollageResult
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `image` | yes | `VolumeInput` |  | Image volume as NIfTI path, ``SimpleITK.Image``, or 3-D NumPy array in ``(z, y, x)`` order. |
| `segmentation` | yes | `VolumeInput` |  | Segmentation volume as NIfTI path, ``SimpleITK.Image``, or matching 3-D NumPy array in ``(z, y, x)`` order. |
| `output_path` | yes | `StrPath` |  | Destination image path, usually ``.png``. |
| `labels` | no | `Sequence[int]  or  int  or  None` | `None` | Label ids to display. ``None`` displays all non-zero labels. |
| `orientation` | no | `Orientation` | `'axial'` | ``axial``, ``sagittal``, or ``coronal``. |
| `slice_strategy` | no | `SliceStrategy` | `'segmentation_extent'` | ``segmentation_extent`` selects slices containing the requested labels; ``full_extent`` samples the complete volume. |
| `slice_indices` | no | `Sequence[int]  or  None` | `None` | Explicit absolute slice indices along the selected orientation axis. |
| `every_n_slices` | no | `int  or  None` | `None` | Step size over the selected extent. The last selected extent slice is included for ``segmentation_extent``. |
| `max_slices` | no | `int  or  None` | `None` | Optional maximum number of selected slices after slice sampling. |
| `n_cols` | no | `int  or  None` | `None` | Number of columns in the output grid. When omitted, a near-square grid is chosen automatically. |
| `window_center` | no | `float` | `40.0` | CT window center used for grayscale background rendering. |
| `window_width` | no | `float` | `400.0` | CT window width used for grayscale background rendering. |
| `segmentation_opacity` | no | `float` | `0.4` | Opacity of the colored segmentation overlay in ``[0, 1]``. |
| `label_colors` | no | `Mapping[int, tuple[int, int, int]]  or  Sequence[tuple[int, int, int]]  or  None` | `None` | RGB colors either as ``{label: (r, g, b)}`` mapping or sequence matched to ``labels`` order. |
| `title` | no | `str  or  None` | `None` | Optional title bar shown above the collage. |
| `show_slice_labels` | no | `bool` | `True` | If True, add a small label bar with the orientation axis and slice index to each panel. |
| `panel_width` | no | `int` | `256` | Width of each rendered slice panel in pixels. |
| `spacing` | no | `tuple[float, float, float]` | `(1.0, 1.0, 1.0)` | Fallback voxel spacing ``(sx, sy, sz)`` for NumPy array inputs. |

### Returns

`dict` - Metadata including ``output_path``, ``slice_indices_used``, ``labels``, ``image_shape``, and ``orientation``.

**See also:** [BOA module guide](../modules/boa.md).

## `fyron.visualization.segmentation_collage.create_segmentation_collages_from_cases`

Create one segmentation collage per case folder and return a summary table.

**Import path:** `fyron.visualization.segmentation_collage.create_segmentation_collages_from_cases`

```python
create_segmentation_collages_from_cases(input_root: StrPath, output_dir: StrPath, *, case_glob: str = 'case-*', image_relpath: StrPath = 'A/image.nii.gz', segmentation_relpath: StrPath = 'A/segmentation.nii.gz', output_suffix: str = '.png', labels: Sequence[int] | int | None = None, orientation: Orientation = 'axial', slice_strategy: SliceStrategy = 'segmentation_extent', every_n_slices: int | None = None, max_slices: int | None = None, n_cols: int | None = None, window_center: float = 40.0, window_width: float = 400.0, segmentation_opacity: float = 0.4, label_colors: Mapping[int, tuple[int, int, int]] | Sequence[tuple[int, int, int]] | None = None, panel_width: int = 256, continue_on_error: bool = True) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `input_root` | yes | `StrPath` |  | Folder containing case directories. |
| `output_dir` | yes | `StrPath` |  | Destination folder for generated collage PNGs. |
| `case_glob` | no | `str` | `'case-*'` | Glob pattern used to discover case directories below ``input_root``. |
| `image_relpath` | no | `StrPath` | `'A/image.nii.gz'` | Image path relative to each case directory. |
| `segmentation_relpath` | no | `StrPath` | `'A/segmentation.nii.gz'` | Segmentation path relative to each case directory. |
| `output_suffix` | no | `str` | `'.png'` | Suffix for output files; filenames use the case directory name. |
| `labels` | no | `Sequence[int]  or  int  or  None` | `None` | Label id or ids to display. ``None`` displays all non-zero labels. |
| `orientation` | no | `Orientation` | `'axial'` | ``axial``, ``sagittal``, or ``coronal``. |
| `slice_strategy` | no | `SliceStrategy` | `'segmentation_extent'` | ``segmentation_extent`` selects slices containing the requested labels; ``full_extent`` samples the complete volume. |
| `every_n_slices` | no | `int  or  None` | `None` | Step size over the selected extent. |
| `max_slices` | no | `int  or  None` | `None` | Optional maximum number of selected slices per case. |
| `n_cols` | no | `int  or  None` | `None` | Number of columns in each output grid. |
| `window_center` | no | `float` | `40.0` | CT window center used for grayscale background rendering. |
| `window_width` | no | `float` | `400.0` | CT window width used for grayscale background rendering. |
| `segmentation_opacity` | no | `float` | `0.4` | Opacity of the colored segmentation overlay in ``[0, 1]``. |
| `label_colors` | no | `Mapping[int, tuple[int, int, int]]  or  Sequence[tuple[int, int, int]]  or  None` | `None` | RGB colors either as mapping by label id or sequence matched to labels. |
| `panel_width` | no | `int` | `256` | Width of each rendered slice panel in pixels. |
| `continue_on_error` | no | `bool` | `True` | If True, failed cases are recorded with ``status="error"``; otherwise the first failure is raised. |

### Returns

`pandas.DataFrame` - One row per case with paths, status, message, selected slices, and slice count.

**See also:** [BOA module guide](../modules/boa.md).

## `fyron.visualization.volume_difference.plot_volume_difference_heatmap`

Plot aligned CT/MR slices with a zero-centered difference heatmap.

**Import path:** `fyron.visualization.volume_difference.plot_volume_difference_heatmap`

```python
plot_volume_difference_heatmap(volume_a: VolumeInput, volume_b: VolumeInput, *, data_type: DataType = 'ct_hu', orientation: Orientation = 'axial', slice_index: int | None = None, slice_indices: Sequence[int] | None = None, slice_fraction: float | None = None, label_a: str = 'Volume A', label_b: str = 'Volume B', window_center: float = 40.0, window_width: float = 400.0, rescale_slope: float = 1.0, rescale_intercept: float = -1024.0, mr_normalization: str = 'percentile', mr_percentile: float = 99.0, diff_vmax: float | None = None, diff_percentile: float = 99.0, diff_cmap: str = 'fyron_diverging_blue_red', figsize: tuple[float, float] | None = None, title: str | None = None, save_path: StrPath | None = None) -> tuple[plt.Figure, np.ndarray, pd.DataFrame]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `volume_a` | yes | `VolumeInput` |  | See signature. |
| `volume_b` | yes | `VolumeInput` |  | NIfTI path, ``SimpleITK.Image``, or NumPy array in ``(z, y, x)`` order. Path and SimpleITK inputs are checked for matching spacing, origin, and direction. NumPy arrays are checked for shape only. |
| `data_type` | no | `DataType` | `'ct_hu'` | ``"ct_hu"`` assumes arrays are already Hounsfield units. ``"ct_uint16"`` converts stored values with ``arr * rescale_slope + rescale_intercept``. ``"mr"`` normalizes each volume to a ``[0, 1]`` scale before comparison. |
| `orientation` | no | `Orientation` | `'axial'` | Slice plane: ``"axial"``, ``"coronal"``, or ``"sagittal"``. |
| `slice_index` | no | `int  or  None` | `None` | See signature. |
| `slice_indices` | no | `Sequence[int]  or  None` | `None` | See signature. |
| `slice_fraction` | no | `float  or  None` | `None` | Select one absolute slice, several absolute slices, or one relative slice location in ``[0, 1]``. If none is provided, the center slice is shown. |
| `label_a` | no | `str` | `'Volume A'` | See signature. |
| `label_b` | no | `str` | `'Volume B'` | Column labels for the first two panels. |
| `window_center` | no | `float` | `40.0` | See signature. |
| `window_width` | no | `float` | `400.0` | CT display window for ``ct_hu`` and ``ct_uint16`` inputs. |
| `rescale_slope` | no | `float` | `1.0` | See signature. |
| `rescale_intercept` | no | `float` | `-1024.0` | Conversion from stored CT values to HU for ``data_type="ct_uint16"``. |
| `mr_normalization` | no | `str` | `'percentile'` | See signature. |
| `mr_percentile` | no | `float` | `99.0` | MR normalization mode and percentile passed to ``normalize_mr``. |
| `diff_vmax` | no | `float  or  None` | `None` | Symmetric absolute limit for the difference map. When omitted, it is estimated from ``diff_percentile`` of the absolute full-volume difference. |
| `diff_percentile` | no | `float` | `99.0` | Percentile used for automatic ``diff_vmax``. |
| `diff_cmap` | no | `str` | `'fyron_diverging_blue_red'` | Matplotlib colormap name or Fyron named diverging colormap. |
| `figsize` | no | `tuple[float, float]  or  None` | `None` | Optional figure size. Defaults to a readable size based on slice count. |
| `title` | no | `str  or  None` | `None` | Optional figure title. |
| `save_path` | no | `StrPath  or  None` | `None` | Optional output image path. Parent directories are created. |

### Returns

`tuple` - ``(fig, axes, table)`` where ``axes`` is an ``n_slices x 3`` array and ``table`` contains slice-level difference summary statistics.

**See also:** [BOA module guide](../modules/boa.md).
