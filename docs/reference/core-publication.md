# Core, Publication, And Utility Reference

Core I/O, documents, LLM helpers, reporting, audit manifests, console utilities, and banner helpers.

For workflow context, see [Core, Publication, And Utility module guide](../modules/core.md).

## Functions And Classes

- [`fyron.audit.manifest.analysis_run_manifest`](#fyronauditmanifestanalysisrunmanifest)
- [`fyron.audit.manifest.create_provenance_manifest`](#fyronauditmanifestcreateprovenancemanifest)
- [`fyron.audit.manifest.hash_file`](#fyronauditmanifesthashfile)
- [`fyron.audit.manifest.write_manifest`](#fyronauditmanifestwritemanifest)
- [`fyron.banner.get_banner`](#fyronbannergetbanner)
- [`fyron.banner.get_run_footer`](#fyronbannergetrunfooter)
- [`fyron.banner.get_run_header`](#fyronbannergetrunheader)
- [`fyron.banner.print_banner`](#fyronbannerprintbanner)
- [`fyron.clinical_codes.charlson.add_charlson_comorbidity_columns`](#fyronclinicalcodescharlsonaddcharlsoncomorbiditycolumns)
- [`fyron.clinical_codes.charlson.charlson_comorbidity_index`](#fyronclinicalcodescharlsoncharlsoncomorbidityindex)
- [`fyron.clinical_codes.charlson.classify_charlson_comorbidities`](#fyronclinicalcodescharlsonclassifycharlsoncomorbidities)
- [`fyron.clinical_codes.charlson.derive_charlson_category`](#fyronclinicalcodescharlsonderivecharlsoncategory)
- [`fyron.clinical_codes.encounter.add_encounter_type_features`](#fyronclinicalcodesencounteraddencountertypefeatures)
- [`fyron.clinical_codes.encounter.classify_elective_status`](#fyronclinicalcodesencounterclassifyelectivestatus)
- [`fyron.clinical_codes.icd10.add_icd10_disease_groups`](#fyronclinicalcodesicd10addicd10diseasegroups)
- [`fyron.clinical_codes.icd10.classify_icd10`](#fyronclinicalcodesicd10classifyicd10)
- [`fyron.clinical_codes.icd10.classify_icd10_string`](#fyronclinicalcodesicd10classifyicd10string)
- [`fyron.clinical_codes.icd10.icd10_group_prevalence`](#fyronclinicalcodesicd10icd10groupprevalence)
- [`fyron.clinical_codes.ops.add_mdc_partition`](#fyronclinicalcodesopsaddmdcpartition)
- [`fyron.clinical_codes.ops.add_ops_categories`](#fyronclinicalcodesopsaddopscategories)
- [`fyron.clinical_codes.ops.aggregate_ops_by_encounter`](#fyronclinicalcodesopsaggregateopsbyencounter)
- [`fyron.clinical_codes.ops.classify_mdc_partition`](#fyronclinicalcodesopsclassifymdcpartition)
- [`fyron.clinical_codes.ops.classify_ops`](#fyronclinicalcodesopsclassifyops)
- [`fyron.clinical_codes.ops.classify_ops_string`](#fyronclinicalcodesopsclassifyopsstring)
- [`fyron.clinical_codes.ops.get_ops_chapter`](#fyronclinicalcodesopsgetopschapter)
- [`fyron.clinical_codes.ops.normalize_ops_codes`](#fyronclinicalcodesopsnormalizeopscodes)
- [`fyron.clinical_codes.ops.ops_category_prevalence`](#fyronclinicalcodesopsopscategoryprevalence)
- [`fyron.clinical_codes.utils.aggregate_code_rows`](#fyronclinicalcodesutilsaggregatecoderows)
- [`fyron.clinical_codes.utils.explode_code_column`](#fyronclinicalcodesutilsexplodecodecolumn)
- [`fyron.clinical_codes.utils.normalize_code`](#fyronclinicalcodesutilsnormalizecode)
- [`fyron.clinical_codes.utils.split_code_string`](#fyronclinicalcodesutilssplitcodestring)
- [`fyron.console.configure_logging`](#fyronconsoleconfigurelogging)
- [`fyron.console.console_message`](#fyronconsoleconsolemessage)
- [`fyron.console.error`](#fyronconsoleerror)
- [`fyron.console.format_count`](#fyronconsoleformatcount)
- [`fyron.console.format_duration`](#fyronconsoleformatduration)
- [`fyron.console.format_path`](#fyronconsoleformatpath)
- [`fyron.console.get_logger`](#fyronconsolegetlogger)
- [`fyron.console.get_timer`](#fyronconsolegettimer)
- [`fyron.console.info`](#fyronconsoleinfo)
- [`fyron.console.success`](#fyronconsolesuccess)
- [`fyron.console.supports_color`](#fyronconsolesupportscolor)
- [`fyron.console.warning`](#fyronconsolewarning)
- [`fyron.core.env.load_env`](#fyroncoreenvloadenv)
- [`fyron.core.io.DataIO`](#fyroncoreiodataio)
- [`fyron.core.io.DataIO.read_csv`](#fyroncoreiodataioreadcsv)
- [`fyron.core.io.DataIO.write_csv`](#fyroncoreiodataiowritecsv)
- [`fyron.core.io.DataIO.read_excel`](#fyroncoreiodataioreadexcel)
- [`fyron.core.io.DataIO.write_excel`](#fyroncoreiodataiowriteexcel)
- [`fyron.core.io.DataIO.read_json`](#fyroncoreiodataioreadjson)
- [`fyron.core.io.DataIO.write_json`](#fyroncoreiodataiowritejson)
- [`fyron.core.io.DataIO.read_table`](#fyroncoreiodataioreadtable)
- [`fyron.core.io.DataIO.write_table`](#fyroncoreiodataiowritetable)
- [`fyron.core.io.DataIO.summarize_table`](#fyroncoreiodataiosummarizetable)
- [`fyron.core.io.DataIO.describe_file`](#fyroncoreiodataiodescribefile)
- [`fyron.core.io.TeableClient`](#fyroncoreioteableclient)
- [`fyron.core.io.TeableClient.list_records`](#fyroncoreioteableclientlistrecords)
- [`fyron.core.io.TeableClient.list_spaces`](#fyroncoreioteableclientlistspaces)
- [`fyron.core.io.TeableClient.list_bases`](#fyroncoreioteableclientlistbases)
- [`fyron.core.io.TeableClient.create_base`](#fyroncoreioteableclientcreatebase)
- [`fyron.core.io.TeableClient.get_or_create_base`](#fyroncoreioteableclientgetorcreatebase)
- [`fyron.core.io.TeableClient.list_tables`](#fyroncoreioteableclientlisttables)
- [`fyron.core.io.TeableClient.create_table`](#fyroncoreioteableclientcreatetable)
- [`fyron.core.io.TeableClient.get_or_create_table`](#fyroncoreioteableclientgetorcreatetable)
- [`fyron.core.io.TeableClient.read_table`](#fyroncoreioteableclientreadtable)
- [`fyron.core.io.TeableClient.create_records`](#fyroncoreioteableclientcreaterecords)
- [`fyron.core.io.TeableClient.delete_records`](#fyroncoreioteableclientdeleterecords)
- [`fyron.core.io.TeableClient.clear_table`](#fyroncoreioteableclientcleartable)
- [`fyron.core.io.TeableClient.write_dataframe`](#fyroncoreioteableclientwritedataframe)
- [`fyron.core.io.TeableClient.overwrite_table`](#fyroncoreioteableclientoverwritetable)
- [`fyron.core.io.TeableClient.read_cohort`](#fyroncoreioteableclientreadcohort)
- [`fyron.core.io.TeableClient.write_research_cohort`](#fyroncoreioteableclientwriteresearchcohort)
- [`fyron.core.io.TeableClient.create_research_cohort_table`](#fyroncoreioteableclientcreateresearchcohorttable)
- [`fyron.core.io.TeableClient.summarize_teable_table`](#fyroncoreioteableclientsummarizeteabletable)
- [`fyron.core.io.TeableConfig`](#fyroncoreioteableconfig)
- [`fyron.core.io.describe_file`](#fyroncoreiodescribefile)
- [`fyron.core.io.ensure_parent_dir`](#fyroncoreioensureparentdir)
- [`fyron.core.io.read_csv`](#fyroncoreioreadcsv)
- [`fyron.core.io.read_excel`](#fyroncoreioreadexcel)
- [`fyron.core.io.read_json`](#fyroncoreioreadjson)
- [`fyron.core.io.read_table`](#fyroncoreioreadtable)
- [`fyron.core.io.summarize_table`](#fyroncoreiosummarizetable)
- [`fyron.core.io.write_csv`](#fyroncoreiowritecsv)
- [`fyron.core.io.write_excel`](#fyroncoreiowriteexcel)
- [`fyron.core.io.write_json`](#fyroncoreiowritejson)
- [`fyron.core.io.write_table`](#fyroncoreiowritetable)
- [`fyron.core.s3.S3Storage`](#fyroncores3s3storage)
- [`fyron.core.s3.S3Storage.key`](#fyroncores3s3storagekey)
- [`fyron.core.s3.S3Storage.exists`](#fyroncores3s3storageexists)
- [`fyron.core.s3.S3Storage.list`](#fyroncores3s3storagelist)
- [`fyron.core.s3.S3Storage.read_bytes`](#fyroncores3s3storagereadbytes)
- [`fyron.core.s3.S3Storage.write_bytes`](#fyroncores3s3storagewritebytes)
- [`fyron.core.s3.S3Storage.read_json`](#fyroncores3s3storagereadjson)
- [`fyron.core.s3.S3Storage.write_json`](#fyroncores3s3storagewritejson)
- [`fyron.core.s3.S3Storage.read_table`](#fyroncores3s3storagereadtable)
- [`fyron.core.s3.S3Storage.write_table`](#fyroncores3s3storagewritetable)
- [`fyron.core.s3.S3Storage.download_file`](#fyroncores3s3storagedownloadfile)
- [`fyron.core.s3.S3Storage.upload_file`](#fyroncores3s3storageuploadfile)
- [`fyron.core.s3.parse_s3_uri`](#fyroncores3parses3uri)
- [`fyron.core.s3.read_s3_table`](#fyroncores3reads3table)
- [`fyron.core.s3.write_s3_table`](#fyroncores3writes3table)
- [`fyron.curate.build_compose_command`](#fyroncuratebuildcomposecommand)
- [`fyron.curate.default_app_dir`](#fyroncuratedefaultappdir)
- [`fyron.curate.start_curator`](#fyroncuratestartcurator)
- [`fyron.datasets.make_boa_like_folder`](#fyrondatasetsmakeboalikefolder)
- [`fyron.datasets.make_classification_cohort`](#fyrondatasetsmakeclassificationcohort)
- [`fyron.datasets.make_clinical_cohort`](#fyrondatasetsmakeclinicalcohort)
- [`fyron.datasets.make_dicom_series`](#fyrondatasetsmakedicomseries)
- [`fyron.datasets.make_nifti_pair`](#fyrondatasetsmakeniftipair)
- [`fyron.datasets.make_survival_cohort`](#fyrondatasetsmakesurvivalcohort)
- [`fyron.datasets.preparation.prepare_nnunetv2_dataset`](#fyrondatasetspreparationpreparennunetv2dataset)
- [`fyron.datasets.preparation.prepare_yolo_classification_dataset`](#fyrondatasetspreparationprepareyoloclassificationdataset)
- [`fyron.datasets.preparation.prepare_yolo_detection_dataset`](#fyrondatasetspreparationprepareyolodetectiondataset)
- [`fyron.datasets.preparation.validate_nnunetv2_dataset`](#fyrondatasetspreparationvalidatennunetv2dataset)
- [`fyron.datasets.preparation.validate_yolo_dataset`](#fyrondatasetspreparationvalidateyolodataset)
- [`fyron.datasets.preparation.write_dataset_manifest`](#fyrondatasetspreparationwritedatasetmanifest)
- [`fyron.documents.client.DocumentDownloader`](#fyrondocumentsclientdocumentdownloader)
- [`fyron.documents.client.DocumentDownloader.close`](#fyrondocumentsclientdocumentdownloaderclose)
- [`fyron.documents.client.DocumentDownloader.download_id`](#fyrondocumentsclientdocumentdownloaderdownloadid)
- [`fyron.documents.client.DocumentDownloader.download_url`](#fyrondocumentsclientdocumentdownloaderdownloadurl)
- [`fyron.documents.client.DocumentDownloader.download_urls`](#fyrondocumentsclientdocumentdownloaderdownloadurls)
- [`fyron.documents.client.DocumentDownloader.download_from_dataframe`](#fyrondocumentsclientdocumentdownloaderdownloadfromdataframe)
- [`fyron.documents.client.DocumentDownloader.download_from_df`](#fyrondocumentsclientdocumentdownloaderdownloadfromdf)
- [`fyron.documents.client.DocumentResult`](#fyrondocumentsclientdocumentresult)
- [`fyron.get_banner`](#fyrongetbanner)
- [`fyron.get_run_footer`](#fyrongetrunfooter)
- [`fyron.get_run_header`](#fyrongetrunheader)
- [`fyron.llm.agent.LLMAgent`](#fyronllmagentllmagent)
- [`fyron.llm.agent.LLMAgent.prompt`](#fyronllmagentllmagentprompt)
- [`fyron.llm.agent.LLMAgent.chat`](#fyronllmagentllmagentchat)
- [`fyron.llm.agent.LLMAgent.run_on_dataframe`](#fyronllmagentllmagentrunondataframe)
- [`fyron.llm.agent.LLMAgent.run_on_documents`](#fyronllmagentllmagentrunondocuments)
- [`fyron.llm.agent.LLMAgent.prompt_documents`](#fyronllmagentllmagentpromptdocuments)
- [`fyron.llm.agent.LLMAgent.prompt_dataframe`](#fyronllmagentllmagentpromptdataframe)
- [`fyron.llm.agent.LLMAgent.prompt_df`](#fyronllmagentllmagentpromptdf)
- [`fyron.llm.agent.LLMAgent.run_prompt_on_dataframe`](#fyronllmagentllmagentrunpromptondataframe)
- [`fyron.llm.agent.LLMAgent.describe_python_file`](#fyronllmagentllmagentdescribepythonfile)
- [`fyron.llm.agent.LLMAgent.run_on_directory`](#fyronllmagentllmagentrunondirectory)
- [`fyron.llm.agent.LLMAgent.prompt_directory`](#fyronllmagentllmagentpromptdirectory)
- [`fyron.llm.agent.LLMConfig`](#fyronllmagentllmconfig)
- [`fyron.plotting_palettes.PaletteSpec`](#fyronplottingpalettespalettespec)
- [`fyron.plotting_palettes.get_colormap`](#fyronplottingpalettesgetcolormap)
- [`fyron.plotting_palettes.get_palette`](#fyronplottingpalettesgetpalette)
- [`fyron.plotting_palettes.list_palettes`](#fyronplottingpaletteslistpalettes)
- [`fyron.plotting_palettes.palette_grayscale_contrast`](#fyronplottingpalettespalettegrayscalecontrast)
- [`fyron.plotting_palettes.palette_luminance_table`](#fyronplottingpalettespaletteluminancetable)
- [`fyron.plotting_palettes.preview_palette`](#fyronplottingpalettespreviewpalette)
- [`fyron.plotting_palettes.resolve_colormap`](#fyronplottingpalettesresolvecolormap)
- [`fyron.plotting_palettes.resolve_palette`](#fyronplottingpalettesresolvepalette)
- [`fyron.plotting_palettes.set_plot_style`](#fyronplottingpalettessetplotstyle)
- [`fyron.print_banner`](#fyronprintbanner)
- [`fyron.reporting.tables.cohort_flow_table`](#fyronreportingtablescohortflowtable)
- [`fyron.reporting.tables.compare_models_table`](#fyronreportingtablescomparemodelstable)
- [`fyron.reporting.tables.dataframe_to_markdown`](#fyronreportingtablesdataframetomarkdown)
- [`fyron.reporting.tables.format_estimate_ci`](#fyronreportingtablesformatestimateci)
- [`fyron.reporting.tables.metrics_table`](#fyronreportingtablesmetricstable)
- [`fyron.reporting.tables.summarize_baseline_table`](#fyronreportingtablessummarizebaselinetable)

## `fyron.audit.manifest.analysis_run_manifest`

Create a provenance manifest for one clinical analysis run.

**Import path:** `fyron.audit.manifest.analysis_run_manifest`

```python
analysis_run_manifest(*, title: str, inputs: Sequence[str | Path] | None = None, outputs: Sequence[str | Path] | None = None, parameters: Mapping[str, Any] | None = None, random_seed: int | None = None, analysis_type: str | None = None, cohort_id: str | None = None, notes: str | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `title` | yes | `str` |  | Human-readable run title. |
| `inputs` | no | `Sequence[str  or  Path]  or  None` | `None` | See signature. |
| `outputs` | no | `Sequence[str  or  Path]  or  None` | `None` | Input and output artifacts. Existing input files are hashed. |
| `parameters` | no | `Mapping[str, Any]  or  None` | `None` | Analysis parameters such as endpoint definition, model choices, and thresholds. |
| `random_seed` | no | `int  or  None` | `None` | Optional seed used for splitting, bootstrapping, or model fitting. |
| `analysis_type` | no | `str  or  None` | `None` | Optional label such as ``"survival"``, ``"classification"``, or ``"boa_features"``. |
| `cohort_id` | no | `str  or  None` | `None` | Optional cohort identifier or version. |
| `notes` | no | `str  or  None` | `None` | Free-text provenance notes. |

### Returns

`dict` - JSON-serializable manifest with Fyron/runtime metadata and analysis context.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.audit.manifest.create_provenance_manifest`

Create a JSON-serializable provenance manifest.

**Import path:** `fyron.audit.manifest.create_provenance_manifest`

```python
create_provenance_manifest(*, title: str | None = None, inputs: Sequence[str | Path] | None = None, outputs: Sequence[str | Path] | None = None, parameters: Mapping[str, Any] | None = None, notes: str | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `title` | no | `str  or  None` | `None` | See signature. |
| `inputs` | no | `Sequence[str  or  Path]  or  None` | `None` | See signature. |
| `outputs` | no | `Sequence[str  or  Path]  or  None` | `None` | See signature. |
| `parameters` | no | `Mapping[str, Any]  or  None` | `None` | See signature. |
| `notes` | no | `str  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.audit.manifest.hash_file`

Hash a file for provenance tracking.

**Import path:** `fyron.audit.manifest.hash_file`

```python
hash_file(path: str | Path, *, algorithm: str = 'sha256', chunk_size: int = 1024 * 1024) -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `str  or  Path` |  | See signature. |
| `algorithm` | no | `str` | `'sha256'` | See signature. |
| `chunk_size` | no | `int` | `1024 * 1024` | See signature. |

### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.audit.manifest.write_manifest`

Write a provenance manifest as pretty JSON.

**Import path:** `fyron.audit.manifest.write_manifest`

```python
write_manifest(manifest: Mapping[str, Any], path: str | Path) -> Path
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `manifest` | yes | `Mapping[str, Any]` |  | See signature. |
| `path` | yes | `str  or  Path` |  | See signature. |

### Returns

`Path`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.banner.get_banner`

Return the Bits & Flames Fyron terminal banner.

**Import path:** `fyron.banner.get_banner`

```python
get_banner(version: str | None = None, *, include_version: bool = True, color: bool = True, theme: str = 'bf') -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `version` | no | `str  or  None` | `None` | Optional version label. If omitted, the installed package version is used. |
| `include_version` | no | `bool` | `True` | Append a version line below the banner when ``True``. |
| `color` | no | `bool` | `True` | Render the pixel logo with ANSI colors when ``True``. |
| `theme` | no | `str` | `'bf'` | Terminal theme: ``"bf"`` for the colored Bits & Flames wordmark, ``"plain"`` for ASCII logs, or ``"mono"`` for minimal monochrome output. |

### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.banner.get_run_footer`

Return a compact Fyron run footer.

**Import path:** `fyron.banner.get_run_footer`

```python
get_run_footer(status: str = 'success', *, duration: float | None = None, outputs: list[str | Path] | tuple[str | Path, ...] | None = None, color: bool = True) -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `status` | no | `str` | `'success'` | See signature. |
| `duration` | no | `float  or  None` | `None` | See signature. |
| `outputs` | no | `list[str  or  Path]  or  tuple[str  or  Path, ...]  or  None` | `None` | See signature. |
| `color` | no | `bool` | `True` | See signature. |

### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.banner.get_run_header`

Return a compact Fyron run header for scripts and CLI jobs.

**Import path:** `fyron.banner.get_run_header`

```python
get_run_header(command: str | None = None, *, version: bool = True, timestamp: bool = True, color: bool = True) -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `command` | no | `str  or  None` | `None` | See signature. |
| `version` | no | `bool` | `True` | See signature. |
| `timestamp` | no | `bool` | `True` | See signature. |
| `color` | no | `bool` | `True` | See signature. |

### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.banner.print_banner`

Print the Bits & Flames Fyron terminal banner to a text stream.

**Import path:** `fyron.banner.print_banner`

```python
print_banner(version: str | None = None, *, include_version: bool = True, color: bool = True, theme: str = 'bf', file: TextIO | None = None) -> None
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `version` | no | `str  or  None` | `None` | See signature. |
| `include_version` | no | `bool` | `True` | See signature. |
| `color` | no | `bool` | `True` | See signature. |
| `theme` | no | `str` | `'bf'` | See signature. |
| `file` | no | `TextIO  or  None` | `None` | See signature. |

### Returns

`None`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.charlson.add_charlson_comorbidity_columns`

Add Charlson Comorbidity Index columns from ICD-10 code strings.

**Import path:** `fyron.clinical_codes.charlson.add_charlson_comorbidity_columns`

```python
add_charlson_comorbidity_columns(df: pd.DataFrame, icd_column: str = 'pni_icd', id_column: str | None = None) -> tuple[pd.DataFrame, str | None]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | DataFrame containing ICD-10 code strings. |
| `icd_column` | no | `str` | `'pni_icd'` | Column containing one or more semicolon-separated ICD-10 codes. |
| `id_column` | no | `str  or  None` | `None` | Optional encounter or patient identifier column. Repeated IDs are scored across all ICD-10 codes observed for that ID. |

### Returns

`tuple[pandas.DataFrame, str or None]` - DataFrame copy with ``charlson_comorbidity_index``, ``charlson_comorbidity_category``, and binary ``charlson_*`` comorbidity indicators. ``skipped_reason`` is None when scoring succeeds.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.charlson.charlson_comorbidity_index`

Calculate a Charlson Comorbidity Index score from ICD-10 codes.

**Import path:** `fyron.clinical_codes.charlson.charlson_comorbidity_index`

```python
charlson_comorbidity_index(icd_codes: Any) -> int | None
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `icd_codes` | yes | `Any` |  | Missing value, semicolon-separated ICD-10 string, or iterable of ICD-10 codes. |

### Returns

`int or None` - Charlson score, or None when no parsable ICD-10 codes are present.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.charlson.classify_charlson_comorbidities`

Classify ICD-10 codes into Charlson comorbidity indicators.

**Import path:** `fyron.clinical_codes.charlson.classify_charlson_comorbidities`

```python
classify_charlson_comorbidities(icd_codes: Any) -> dict[str, int]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `icd_codes` | yes | `Any` |  | Missing value, semicolon-separated ICD-10 string, or iterable of ICD-10 codes. |

### Returns

`dict[str, int]` - Binary Charlson comorbidity indicators using explicit ICD-10 ranges.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.charlson.derive_charlson_category`

Bin Charlson scores into ordered clinical categories.

**Import path:** `fyron.clinical_codes.charlson.derive_charlson_category`

```python
derive_charlson_category(score: pd.Series) -> pd.Categorical
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `score` | yes | `pd.Series` |  | Numeric Charlson Comorbidity Index values. |

### Returns

`pandas.Categorical` - Ordered categories ``"0"``, ``"1-2"``, ``"3-4"``, and ``">=5"``.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.encounter.add_encounter_type_features`

Add normalized encounter type and elective-status columns.

**Import path:** `fyron.clinical_codes.encounter.add_encounter_type_features`

```python
add_encounter_type_features(df: pd.DataFrame, encounter_type_column: str = 'pni_encounter_type') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | DataFrame with an encounter type column. |
| `encounter_type_column` | no | `str` | `'pni_encounter_type'` | Source column containing encounter type codes. |

### Returns

`pandas.DataFrame` - Copy of ``df`` with ``pni_encounter_type_normalized`` and ``pni_encounter_elective_status``.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.encounter.classify_elective_status`

Classify elective status from an encounter type code.

**Import path:** `fyron.clinical_codes.encounter.classify_elective_status`

```python
classify_elective_status(encounter_type: Any) -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `encounter_type` | yes | `Any` |  | Encounter type such as ``"AMB"``, ``"IMP"``, or ``"EMER"``. |

### Returns

`str` - ``"elective"``, ``"non_elective"``, or ``"unknown"``.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.icd10.add_icd10_disease_groups`

Add broad ICD-10 disease-group indicator columns.

**Import path:** `fyron.clinical_codes.icd10.add_icd10_disease_groups`

```python
add_icd10_disease_groups(df: pd.DataFrame, icd_col: str, *, sep: str = ';', prefix: str = 'icd10_group_', summary_col: str = 'icd10_groups', count_col: str = 'n_icd10_groups', groups: Sequence[str] | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | DataFrame containing an ICD-10 code column. |
| `icd_col` | yes | `str` |  | Column with one or more ICD-10 codes per row. |
| `sep` | no | `str` | `';'` | Delimiter between multiple codes in one cell. |
| `prefix` | no | `str` | `'icd10_group_'` | Prefix for generated binary indicator columns. |
| `summary_col` | no | `str` | `'icd10_groups'` | Output column containing human-readable disease groups. |
| `count_col` | no | `str` | `'n_icd10_groups'` | Output column containing the number of disease groups per row. |
| `groups` | no | `Sequence[str]  or  None` | `None` | Optional explicit disease-group order. Defaults to Fyron's built-in broad ICD-10 groups. |

### Returns

`pandas.DataFrame` - Copy of ``df`` with binary disease-group indicators and summary columns.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.icd10.classify_icd10`

Classify one ICD-10 code into a broad disease group.

**Import path:** `fyron.clinical_codes.icd10.classify_icd10`

```python
classify_icd10(code: Any) -> str | None
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `code` | yes | `Any` |  | ICD-10 code such as ``"C34"``, ``"I50.1"``, or ``"Z51"``. |

### Returns

`str or None` - Broad disease group name, ``"Other"`` for malformed non-empty codes, or None for missing values.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.icd10.classify_icd10_string`

Classify a delimited ICD-10 code string into disease groups.

**Import path:** `fyron.clinical_codes.icd10.classify_icd10_string`

```python
classify_icd10_string(value: Any, *, sep: str = ';') -> set[str]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `value` | yes | `Any` |  | Scalar cell containing one or more ICD-10 codes. |
| `sep` | no | `str` | `';'` | Delimiter between codes. |

### Returns

`set[str]` - Disease groups present in the code string.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.icd10.icd10_group_prevalence`

Summarize ICD-10 disease-group indicator prevalence.

**Import path:** `fyron.clinical_codes.icd10.icd10_group_prevalence`

```python
icd10_group_prevalence(df: pd.DataFrame, *, group_cols: Sequence[str] | None = None, prefix: str = 'icd10_group_') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | DataFrame with ICD-10 group indicator columns. |
| `group_cols` | no | `Sequence[str]  or  None` | `None` | Optional explicit indicator columns. If omitted, columns with ``prefix`` are used. |
| `prefix` | no | `str` | `'icd10_group_'` | Prefix used to discover indicator columns. |

### Returns

`pandas.DataFrame` - Prevalence table with group, column, patient count, and percent.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.ops.add_mdc_partition`

Add MDC partition labels from an OPS code column.

**Import path:** `fyron.clinical_codes.ops.add_mdc_partition`

```python
add_mdc_partition(df: pd.DataFrame, ops_column: str | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | DataFrame containing OPS code values. |
| `ops_column` | no | `str  or  None` | `None` | Explicit source column. If omitted, common OPS column names are tried. |

### Returns

`pandas.DataFrame` - Copy of ``df`` with ``mdc_partition`` and ``mdc_partition_source``.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.ops.add_ops_categories`

Add broad German OPS procedure-category indicator columns.

**Import path:** `fyron.clinical_codes.ops.add_ops_categories`

```python
add_ops_categories(df: pd.DataFrame, ops_col: str, *, sep: str = ';', prefix: str = 'ops_category_', summary_col: str = 'ops_categories', count_col: str = 'n_ops_categories', categories: Sequence[str] | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | DataFrame containing an OPS code column. |
| `ops_col` | yes | `str` |  | Column with one or more OPS codes per row. |
| `sep` | no | `str` | `';'` | Delimiter between multiple codes in one cell. |
| `prefix` | no | `str` | `'ops_category_'` | Prefix for generated binary indicator columns. |
| `summary_col` | no | `str` | `'ops_categories'` | Output column containing human-readable OPS categories. |
| `count_col` | no | `str` | `'n_ops_categories'` | Output column containing the number of OPS categories per row. |
| `categories` | no | `Sequence[str]  or  None` | `None` | Optional explicit category order. Defaults to Fyron's broad OPS groups. |

### Returns

`pandas.DataFrame` - Copy of ``df`` with binary OPS category indicators and summary columns.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.ops.aggregate_ops_by_encounter`

Aggregate one-OPS-procedure-per-row data to encounter-level lists.

**Import path:** `fyron.clinical_codes.ops.aggregate_ops_by_encounter`

```python
aggregate_ops_by_encounter(procedures: pd.DataFrame, *, patient_col: str = 'patient_id', encounter_col: str = 'encounter_id', date_col: str = 'performed_date', ops_code_col: str = 'ops_code', ops_display_col: str | None = 'ops_display', complete_encounters: pd.DataFrame | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `procedures` | yes | `pd.DataFrame` |  | Long procedure DataFrame with one OPS code per row. |
| `patient_col` | no | `str` | `'patient_id'` | Patient identifier column. |
| `encounter_col` | no | `str` | `'encounter_id'` | Encounter identifier column. |
| `date_col` | no | `str` | `'performed_date'` | Procedure date column used for first/last performed dates. |
| `ops_code_col` | no | `str` | `'ops_code'` | OPS code column. |
| `ops_display_col` | no | `str  or  None` | `'ops_display'` | Optional OPS display text column. |
| `complete_encounters` | no | `pd.DataFrame  or  None` | `None` | Optional patient/encounter table used to retain encounters without OPS codes. |

### Returns

`pandas.DataFrame` - One row per patient encounter with ``ops_code_list``, ``ops_display_list``, first/last performed dates, and ``n_ops_codes``.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.ops.classify_mdc_partition`

Classify a stay into a broad MDC partition from OPS codes.

**Import path:** `fyron.clinical_codes.ops.classify_mdc_partition`

```python
classify_mdc_partition(ops_codes: Any) -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `ops_codes` | yes | `Any` |  | Missing value, scalar code, delimited string, Python-style list string, or iterable of OPS codes. |

### Returns

`str` - ``"surgical"`` when any chapter-5 OPS code is present, ``"medical"`` when any other valid OPS chapter is present, otherwise ``"other"``.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.ops.classify_ops`

Classify one German OPS code into a broad procedure category.

**Import path:** `fyron.clinical_codes.ops.classify_ops`

```python
classify_ops(code: Any) -> str | None
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `code` | yes | `Any` |  | OPS code such as ``"1-620"``, ``"3-20"``, ``"5-541"``, or ``"8-980"``. |

### Returns

`str or None` - Broad OPS category, ``"Other"`` for malformed non-empty codes, or None for missing values.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.ops.classify_ops_string`

Classify a delimited OPS code string into broad procedure categories.

**Import path:** `fyron.clinical_codes.ops.classify_ops_string`

```python
classify_ops_string(value: Any, *, sep: str = ';') -> set[str]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `value` | yes | `Any` |  | Scalar cell containing one or more OPS codes. |
| `sep` | no | `str` | `';'` | Delimiter between codes. |

### Returns

`set[str]` - OPS categories present in the code string.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.ops.get_ops_chapter`

Extract the one-digit OPS chapter from an OPS code.

**Import path:** `fyron.clinical_codes.ops.get_ops_chapter`

```python
get_ops_chapter(ops_code: Any) -> str | None
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `ops_code` | yes | `Any` |  | OPS code such as ``"5-470.0"``, ``"8-930"``, or ``"1-632"``. |

### Returns

`str or None` - One-digit chapter, or None for missing/malformed values.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.ops.normalize_ops_codes`

Convert different OPS column formats into a clean list of OPS codes.

**Import path:** `fyron.clinical_codes.ops.normalize_ops_codes`

```python
normalize_ops_codes(ops_codes: Any) -> list[str]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `ops_codes` | yes | `Any` |  | Missing value, scalar code, delimited string, Python-style list string, or iterable of OPS codes. |

### Returns

`list[str]` - Normalized OPS code strings.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.ops.ops_category_prevalence`

Summarize OPS procedure-category indicator prevalence.

**Import path:** `fyron.clinical_codes.ops.ops_category_prevalence`

```python
ops_category_prevalence(df: pd.DataFrame, *, category_cols: Sequence[str] | None = None, prefix: str = 'ops_category_') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | DataFrame with OPS category indicator columns. |
| `category_cols` | no | `Sequence[str]  or  None` | `None` | Optional explicit indicator columns. If omitted, columns with ``prefix`` are used. |
| `prefix` | no | `str` | `'ops_category_'` | Prefix used to discover indicator columns. |

### Returns

`pandas.DataFrame` - Prevalence table with category, column, patient count, and percent.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.utils.aggregate_code_rows`

Aggregate one-code-per-row data into list-valued group rows.

**Import path:** `fyron.clinical_codes.utils.aggregate_code_rows`

```python
aggregate_code_rows(df: pd.DataFrame, group_cols: str | Sequence[str], code_col: str, *, display_col: str | None = None, date_col: str | None = None, code_list_col: str | None = None, display_list_col: str | None = None, first_date_col: str | None = None, last_date_col: str | None = None, count_col: str | None = None, complete_groups: pd.DataFrame | None = None, sort_items: bool = True, unique: bool = True, strip_strings: bool = True) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Long DataFrame with one clinical code per row. |
| `group_cols` | yes | `str  or  Sequence[str]` |  | Column or columns defining the output row, such as patient and encounter identifiers. |
| `code_col` | yes | `str` |  | Source column containing the clinical code. |
| `display_col` | no | `str  or  None` | `None` | Optional source column containing code display text. |
| `date_col` | no | `str  or  None` | `None` | Optional date column used for first/last date outputs and sorting. |
| `code_list_col` | no | `str  or  None` | `None` | Output column for code lists. Defaults to ``f"{code_col}_list"``. |
| `display_list_col` | no | `str  or  None` | `None` | Output column for display text lists. Defaults to ``f"{display_col}_list"`` when ``display_col`` is provided. |
| `first_date_col` | no | `str  or  None` | `None` | Output column for the earliest date. Defaults to ``f"{date_col}_first"`` when ``date_col`` is provided. |
| `last_date_col` | no | `str  or  None` | `None` | Output column for the latest date. Defaults to ``f"{date_col}_last"`` when ``date_col`` is provided. |
| `count_col` | no | `str  or  None` | `None` | Output column for the number of distinct codes. Defaults to ``f"n_{code_col}s"``. |
| `complete_groups` | no | `pd.DataFrame  or  None` | `None` | Optional DataFrame with all desired output groups. Groups with no codes are retained with empty lists, missing dates, and a zero count. |
| `sort_items` | no | `bool` | `True` | If True, list outputs are sorted for stable CSV/JSON artifacts. |
| `unique` | no | `bool` | `True` | If True, each code/display appears once per output group. |
| `strip_strings` | no | `bool` | `True` | If True, trim whitespace from string-like group, code, and display columns before aggregation. |

### Returns

`pandas.DataFrame` - One row per group with list-valued code/display columns, optional first/last dates, and a code count.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.utils.explode_code_column`

Explode a delimited clinical code column into one row per code.

**Import path:** `fyron.clinical_codes.utils.explode_code_column`

```python
explode_code_column(df: pd.DataFrame, code_col: str, *, sep: str = ';', output_col: str = 'code', keep_empty: bool = False) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | DataFrame containing a delimited code column. |
| `code_col` | yes | `str` |  | Column with one or more codes per row. |
| `sep` | no | `str` | `';'` | Delimiter between codes. |
| `output_col` | no | `str` | `'code'` | Name of the exploded output code column. |
| `keep_empty` | no | `bool` | `False` | If True, keep rows without codes and set ``output_col`` to missing. |

### Returns

`pandas.DataFrame` - Exploded DataFrame with one row per parsed code.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.utils.normalize_code`

Normalize one clinical code value for matching.

**Import path:** `fyron.clinical_codes.utils.normalize_code`

```python
normalize_code(value: Any, *, uppercase: bool = True, remove_spaces: bool = True, remove_dots: bool = False) -> str | None
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `value` | yes | `Any` |  | Raw code value such as an ICD-10, OPS, medication, or local registry code. |
| `uppercase` | no | `bool` | `True` | If True, convert the returned code to uppercase. |
| `remove_spaces` | no | `bool` | `True` | If True, remove whitespace within the code. |
| `remove_dots` | no | `bool` | `False` | If True, remove dots from the code. |

### Returns

`str or None` - Normalized code string, or None for missing/empty values.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.clinical_codes.utils.split_code_string`

Split one cell containing one or more clinical codes.

**Import path:** `fyron.clinical_codes.utils.split_code_string`

```python
split_code_string(value: Any, *, sep: str = ';', normalize: bool = True) -> list[str]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `value` | yes | `Any` |  | Scalar value containing one or more codes, usually separated by semicolons. |
| `sep` | no | `str` | `';'` | Delimiter used between codes. |
| `normalize` | no | `bool` | `True` | If True, normalize each code with :func:`normalize_code`. |

### Returns

`list[str]` - Ordered list of non-empty codes.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.console.configure_logging`

Configure root Fyron logging and return the ``fyron`` logger.

**Import path:** `fyron.console.configure_logging`

```python
configure_logging(level: str | int = 'INFO', *, color: bool = True, json: bool = False, stream: TextIO | None = None) -> logging.Logger
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `level` | no | `str  or  int` | `'INFO'` | See signature. |
| `color` | no | `bool` | `True` | See signature. |
| `json` | no | `bool` | `False` | See signature. |
| `stream` | no | `TextIO  or  None` | `None` | See signature. |

### Returns

`logging.Logger`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.console.console_message`

Print and return a styled terminal message.

**Import path:** `fyron.console.console_message`

```python
console_message(message: str, *, level: str = 'info', color: bool = True, prefix: str = 'fyron', stream: TextIO | None = None, quiet: bool = False) -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `message` | yes | `str` |  | See signature. |
| `level` | no | `str` | `'info'` | See signature. |
| `color` | no | `bool` | `True` | See signature. |
| `prefix` | no | `str` | `'fyron'` | See signature. |
| `stream` | no | `TextIO  or  None` | `None` | See signature. |
| `quiet` | no | `bool` | `False` | See signature. |

### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.console.error`

See the signature and linked module guide for context.

**Import path:** `fyron.console.error`

```python
error(message: str, **kwargs: Any) -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `message` | yes | `str` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.console.format_count`

See the signature and linked module guide for context.

**Import path:** `fyron.console.format_count`

```python
format_count(label: str, value: int | float) -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `label` | yes | `str` |  | See signature. |
| `value` | yes | `int  or  float` |  | See signature. |

### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.console.format_duration`

See the signature and linked module guide for context.

**Import path:** `fyron.console.format_duration`

```python
format_duration(seconds: float) -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `seconds` | yes | `float` |  | See signature. |

### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.console.format_path`

See the signature and linked module guide for context.

**Import path:** `fyron.console.format_path`

```python
format_path(path: str | Path) -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `str  or  Path` |  | See signature. |

### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.console.get_logger`

Return a logger below the Fyron namespace.

**Import path:** `fyron.console.get_logger`

```python
get_logger(name: str | None = None) -> logging.Logger
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `name` | no | `str  or  None` | `None` | See signature. |

### Returns

`logging.Logger`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.console.get_timer`

See the signature and linked module guide for context.

**Import path:** `fyron.console.get_timer`

```python
get_timer() -> float
```

### Parameters

No parameters documented.

### Returns

`float`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.console.info`

See the signature and linked module guide for context.

**Import path:** `fyron.console.info`

```python
info(message: str, **kwargs: Any) -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `message` | yes | `str` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.console.success`

See the signature and linked module guide for context.

**Import path:** `fyron.console.success`

```python
success(message: str, **kwargs: Any) -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `message` | yes | `str` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.console.supports_color`

Return whether ANSI colors should be emitted for a stream.

**Import path:** `fyron.console.supports_color`

```python
supports_color(stream: TextIO | None = None) -> bool
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `stream` | no | `TextIO  or  None` | `None` | See signature. |

### Returns

`bool`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.console.warning`

See the signature and linked module guide for context.

**Import path:** `fyron.console.warning`

```python
warning(message: str, **kwargs: Any) -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `message` | yes | `str` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.env.load_env`

Load environment variables from a .env file.

**Import path:** `fyron.core.env.load_env`

```python
load_env(path: Optional[str] = None, *, override: bool = False, warn_if_missing: bool = True) -> Optional[str]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | no | `Optional[str]` | `None` | Optional path to a .env file. If None, searches from the current working directory. |
| `override` | no | `bool` | `False` | Whether to override existing environment variables. |
| `warn_if_missing` | no | `bool` | `True` | If True, logs a warning when no .env file is found. |

### Returns

`Optional[str]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.io.DataIO`

Convenience wrappers for local table and JSON IO.

**Import path:** `fyron.core.io.DataIO`

```python
DataIO()
```

### Parameters

No parameters documented.

### Returns

Class constructor.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

### Public Methods

#### `fyron.core.io.DataIO.read_csv`

See the signature and linked module guide for context.

**Import path:** `fyron.core.io.DataIO.read_csv`

```python
DataIO.read_csv(path: str, **kwargs: Any) -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `str` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

#### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.DataIO.write_csv`

See the signature and linked module guide for context.

**Import path:** `fyron.core.io.DataIO.write_csv`

```python
DataIO.write_csv(df: pd.DataFrame, path: str, **kwargs: Any) -> None
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `path` | yes | `str` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

#### Returns

`None`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.DataIO.read_excel`

See the signature and linked module guide for context.

**Import path:** `fyron.core.io.DataIO.read_excel`

```python
DataIO.read_excel(path: str, **kwargs: Any) -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `str` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

#### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.DataIO.write_excel`

See the signature and linked module guide for context.

**Import path:** `fyron.core.io.DataIO.write_excel`

```python
DataIO.write_excel(df: pd.DataFrame, path: str, **kwargs: Any) -> None
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `path` | yes | `str` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

#### Returns

`None`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.DataIO.read_json`

See the signature and linked module guide for context.

**Import path:** `fyron.core.io.DataIO.read_json`

```python
DataIO.read_json(path: str | Path, **kwargs: Any) -> Any
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `str  or  Path` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

#### Returns

`Any`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.DataIO.write_json`

See the signature and linked module guide for context.

**Import path:** `fyron.core.io.DataIO.write_json`

```python
DataIO.write_json(payload: Any, path: str | Path, *, indent: int | None = 2, create_parent: bool = True, **kwargs: Any) -> Path
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `payload` | yes | `Any` |  | See signature. |
| `path` | yes | `str  or  Path` |  | See signature. |
| `indent` | no | `int  or  None` | `2` | See signature. |
| `create_parent` | no | `bool` | `True` | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

#### Returns

`Path`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.DataIO.read_table`

See the signature and linked module guide for context.

**Import path:** `fyron.core.io.DataIO.read_table`

```python
DataIO.read_table(path: str | Path, *, file_format: str | None = None, **kwargs: Any) -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `str  or  Path` |  | See signature. |
| `file_format` | no | `str  or  None` | `None` | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

#### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.DataIO.write_table`

See the signature and linked module guide for context.

**Import path:** `fyron.core.io.DataIO.write_table`

```python
DataIO.write_table(df: pd.DataFrame, path: str | Path, *, file_format: str | None = None, create_parent: bool = True, index: bool = False, **kwargs: Any) -> Path
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `path` | yes | `str  or  Path` |  | See signature. |
| `file_format` | no | `str  or  None` | `None` | See signature. |
| `create_parent` | no | `bool` | `True` | See signature. |
| `index` | no | `bool` | `False` | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

#### Returns

`Path`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.DataIO.summarize_table`

See the signature and linked module guide for context.

**Import path:** `fyron.core.io.DataIO.summarize_table`

```python
DataIO.summarize_table(df: pd.DataFrame, *, name: str | None = None) -> dict[str, Any]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `name` | no | `str  or  None` | `None` | See signature. |

#### Returns

`dict[str, Any]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.DataIO.describe_file`

See the signature and linked module guide for context.

**Import path:** `fyron.core.io.DataIO.describe_file`

```python
DataIO.describe_file(path: str | Path) -> dict[str, Any]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `str  or  Path` |  | See signature. |

#### Returns

`dict[str, Any]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.io.TeableClient`

Minimal Teable table client for reading/writing DataFrames.

**Import path:** `fyron.core.io.TeableClient`

```python
TeableClient(self, base_url: Optional[str] = None, token: Optional[str] = None, timeout: int = 30)
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `base_url` | no | `Optional[str]` | `None` | See signature. |
| `token` | no | `Optional[str]` | `None` | See signature. |
| `timeout` | no | `int` | `30` | See signature. |

### Returns

Class constructor.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

### Public Methods

#### `fyron.core.io.TeableClient.list_records`

See the signature and linked module guide for context.

**Import path:** `fyron.core.io.TeableClient.list_records`

```python
TeableClient.list_records(self, table_id: str, *, view_id: Optional[str] = None, take: int = 1000, skip: int = 0, field_key_type: str = 'name', cell_format: str = 'json', projection: Optional[List[str]] = None, **params: Any) -> Dict[str, Any]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `table_id` | yes | `str` |  | See signature. |
| `view_id` | no | `Optional[str]` | `None` | See signature. |
| `take` | no | `int` | `1000` | See signature. |
| `skip` | no | `int` | `0` | See signature. |
| `field_key_type` | no | `str` | `'name'` | See signature. |
| `cell_format` | no | `str` | `'json'` | See signature. |
| `projection` | no | `Optional[List[str]]` | `None` | See signature. |
| `params` | yes | `Any` |  | See signature. |

#### Returns

`Dict[str, Any]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.TeableClient.list_spaces`

List spaces available to the current token.

**Import path:** `fyron.core.io.TeableClient.list_spaces`

```python
TeableClient.list_spaces(self) -> List[Dict[str, Any]]
```

#### Parameters

No parameters documented.

#### Returns

`List[Dict[str, Any]]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.TeableClient.list_bases`

List bases for a space or all accessible bases.

**Import path:** `fyron.core.io.TeableClient.list_bases`

```python
TeableClient.list_bases(self, *, space_id: Optional[str] = None) -> List[Dict[str, Any]]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `space_id` | no | `Optional[str]` | `None` | See signature. |

#### Returns

`List[Dict[str, Any]]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.TeableClient.create_base`

Create a base in a space.

**Import path:** `fyron.core.io.TeableClient.create_base`

```python
TeableClient.create_base(self, *, space_id: str, name: str, icon: Optional[str] = None) -> Dict[str, Any]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `space_id` | yes | `str` |  | See signature. |
| `name` | yes | `str` |  | See signature. |
| `icon` | no | `Optional[str]` | `None` | See signature. |

#### Returns

`Dict[str, Any]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.TeableClient.get_or_create_base`

Return a base by name, creating it if it doesn't exist.

**Import path:** `fyron.core.io.TeableClient.get_or_create_base`

```python
TeableClient.get_or_create_base(self, *, name: str, space_id: Optional[str] = None, space_name: Optional[str] = None, icon: Optional[str] = None) -> Dict[str, Any]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `name` | yes | `str` |  | See signature. |
| `space_id` | no | `Optional[str]` | `None` | See signature. |
| `space_name` | no | `Optional[str]` | `None` | See signature. |
| `icon` | no | `Optional[str]` | `None` | See signature. |

#### Returns

`Dict[str, Any]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.TeableClient.list_tables`

List tables in a base.

**Import path:** `fyron.core.io.TeableClient.list_tables`

```python
TeableClient.list_tables(self, base_id: str) -> List[Dict[str, Any]]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `base_id` | yes | `str` |  | See signature. |

#### Returns

`List[Dict[str, Any]]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.TeableClient.create_table`

Create a table in a base.

**Import path:** `fyron.core.io.TeableClient.create_table`

```python
TeableClient.create_table(self, *, base_id: str, name: str, db_table_name: Optional[str] = None, description: Optional[str] = None, icon: Optional[str] = None, fields: Optional[List[Dict[str, Any]]] = None, views: Optional[List[Dict[str, Any]]] = None, records: Optional[List[Dict[str, Any]]] = None, order: Optional[int] = None, field_key_type: str = 'name') -> Dict[str, Any]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `base_id` | yes | `str` |  | See signature. |
| `name` | yes | `str` |  | See signature. |
| `db_table_name` | no | `Optional[str]` | `None` | See signature. |
| `description` | no | `Optional[str]` | `None` | See signature. |
| `icon` | no | `Optional[str]` | `None` | See signature. |
| `fields` | no | `Optional[List[Dict[str, Any]]]` | `None` | See signature. |
| `views` | no | `Optional[List[Dict[str, Any]]]` | `None` | See signature. |
| `records` | no | `Optional[List[Dict[str, Any]]]` | `None` | See signature. |
| `order` | no | `Optional[int]` | `None` | See signature. |
| `field_key_type` | no | `str` | `'name'` | See signature. |

#### Returns

`Dict[str, Any]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.TeableClient.get_or_create_table`

Return a table by name (or db_table_name), creating it if missing.

**Import path:** `fyron.core.io.TeableClient.get_or_create_table`

```python
TeableClient.get_or_create_table(self, *, base_id: str, name: str, db_table_name: Optional[str] = None, description: Optional[str] = None, icon: Optional[str] = None, fields: Optional[List[Dict[str, Any]]] = None, views: Optional[List[Dict[str, Any]]] = None, records: Optional[List[Dict[str, Any]]] = None, order: Optional[int] = None, field_key_type: str = 'name') -> Dict[str, Any]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `base_id` | yes | `str` |  | See signature. |
| `name` | yes | `str` |  | See signature. |
| `db_table_name` | no | `Optional[str]` | `None` | See signature. |
| `description` | no | `Optional[str]` | `None` | See signature. |
| `icon` | no | `Optional[str]` | `None` | See signature. |
| `fields` | no | `Optional[List[Dict[str, Any]]]` | `None` | See signature. |
| `views` | no | `Optional[List[Dict[str, Any]]]` | `None` | See signature. |
| `records` | no | `Optional[List[Dict[str, Any]]]` | `None` | See signature. |
| `order` | no | `Optional[int]` | `None` | See signature. |
| `field_key_type` | no | `str` | `'name'` | See signature. |

#### Returns

`Dict[str, Any]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.TeableClient.read_table`

See the signature and linked module guide for context.

**Import path:** `fyron.core.io.TeableClient.read_table`

```python
TeableClient.read_table(self, table_id: str, *, view_id: Optional[str] = None, field_key_type: str = 'name', cell_format: str = 'json', projection: Optional[List[str]] = None, take: int = 1000, max_records: Optional[int] = None) -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `table_id` | yes | `str` |  | See signature. |
| `view_id` | no | `Optional[str]` | `None` | See signature. |
| `field_key_type` | no | `str` | `'name'` | See signature. |
| `cell_format` | no | `str` | `'json'` | See signature. |
| `projection` | no | `Optional[List[str]]` | `None` | See signature. |
| `take` | no | `int` | `1000` | See signature. |
| `max_records` | no | `Optional[int]` | `None` | See signature. |

#### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.TeableClient.create_records`

See the signature and linked module guide for context.

**Import path:** `fyron.core.io.TeableClient.create_records`

```python
TeableClient.create_records(self, table_id: str, records: Iterable[Dict[str, Any]], *, field_key_type: str = 'name', typecast: bool = True, order: Optional[Dict[str, Any]] = None) -> Dict[str, Any]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `table_id` | yes | `str` |  | See signature. |
| `records` | yes | `Iterable[Dict[str, Any]]` |  | See signature. |
| `field_key_type` | no | `str` | `'name'` | See signature. |
| `typecast` | no | `bool` | `True` | See signature. |
| `order` | no | `Optional[Dict[str, Any]]` | `None` | See signature. |

#### Returns

`Dict[str, Any]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.TeableClient.delete_records`

Delete records by ID.

**Import path:** `fyron.core.io.TeableClient.delete_records`

```python
TeableClient.delete_records(self, table_id: str, record_ids: List[str]) -> None
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `table_id` | yes | `str` |  | See signature. |
| `record_ids` | yes | `List[str]` |  | See signature. |

#### Returns

`None`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.TeableClient.clear_table`

Delete all records in a table and return deleted count.

**Import path:** `fyron.core.io.TeableClient.clear_table`

```python
TeableClient.clear_table(self, table_id: str, *, batch_size: int = 200, take: int = 1000) -> int
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `table_id` | yes | `str` |  | See signature. |
| `batch_size` | no | `int` | `200` | See signature. |
| `take` | no | `int` | `1000` | See signature. |

#### Returns

`int`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.TeableClient.write_dataframe`

See the signature and linked module guide for context.

**Import path:** `fyron.core.io.TeableClient.write_dataframe`

```python
TeableClient.write_dataframe(self, table_id: str, df: pd.DataFrame, *, field_key_type: str = 'name', typecast: bool = True, chunk_size: int = 200) -> List[str]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `table_id` | yes | `str` |  | See signature. |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `field_key_type` | no | `str` | `'name'` | See signature. |
| `typecast` | no | `bool` | `True` | See signature. |
| `chunk_size` | no | `int` | `200` | See signature. |

#### Returns

`List[str]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.TeableClient.overwrite_table`

Delete all records in a table, then write the DataFrame.

**Import path:** `fyron.core.io.TeableClient.overwrite_table`

```python
TeableClient.overwrite_table(self, table_id: str, df: pd.DataFrame, *, delete_batch_size: int = 200, create_chunk_size: int = 200, field_key_type: str = 'name', typecast: bool = True) -> List[str]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `table_id` | yes | `str` |  | See signature. |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `delete_batch_size` | no | `int` | `200` | See signature. |
| `create_chunk_size` | no | `int` | `200` | See signature. |
| `field_key_type` | no | `str` | `'name'` | See signature. |
| `typecast` | no | `bool` | `True` | See signature. |

#### Returns

`List[str]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.TeableClient.read_cohort`

Read a reviewed Teable cohort and validate basic cohort shape.

**Import path:** `fyron.core.io.TeableClient.read_cohort`

```python
TeableClient.read_cohort(self, table_id: str, *, id_col: str | None = None, required_columns: list[str] | None = None, view_id: str | None = None, max_records: int | None = None) -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `table_id` | yes | `str` |  | See signature. |
| `id_col` | no | `str  or  None` | `None` | See signature. |
| `required_columns` | no | `list[str]  or  None` | `None` | See signature. |
| `view_id` | no | `str  or  None` | `None` | See signature. |
| `max_records` | no | `int  or  None` | `None` | See signature. |

#### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.TeableClient.write_research_cohort`

Write a finished research cohort to Teable and return an audit summary.

**Import path:** `fyron.core.io.TeableClient.write_research_cohort`

```python
TeableClient.write_research_cohort(self, table_id: str, df: pd.DataFrame, *, mode: str = 'append', cohort_name: str | None = None, version: str | None = None, metadata: dict[str, Any] | None = None, id_col: str | None = None, field_key_type: str = 'name', typecast: bool = True, chunk_size: int = 200) -> dict[str, Any]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `table_id` | yes | `str` |  | See signature. |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `mode` | no | `str` | `'append'` | See signature. |
| `cohort_name` | no | `str  or  None` | `None` | See signature. |
| `version` | no | `str  or  None` | `None` | See signature. |
| `metadata` | no | `dict[str, Any]  or  None` | `None` | See signature. |
| `id_col` | no | `str  or  None` | `None` | See signature. |
| `field_key_type` | no | `str` | `'name'` | See signature. |
| `typecast` | no | `bool` | `True` | See signature. |
| `chunk_size` | no | `int` | `200` | See signature. |

#### Returns

`dict[str, Any]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.TeableClient.create_research_cohort_table`

Create a Teable table for a research cohort.

**Import path:** `fyron.core.io.TeableClient.create_research_cohort_table`

```python
TeableClient.create_research_cohort_table(self, *, base_id: str, name: str, df: pd.DataFrame | None = None, description: str | None = None, fields: list[dict[str, Any]] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `base_id` | yes | `str` |  | See signature. |
| `name` | yes | `str` |  | See signature. |
| `df` | no | `pd.DataFrame  or  None` | `None` | See signature. |
| `description` | no | `str  or  None` | `None` | See signature. |
| `fields` | no | `list[dict[str, Any]]  or  None` | `None` | See signature. |
| `metadata` | no | `dict[str, Any]  or  None` | `None` | See signature. |

#### Returns

`dict[str, Any]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.io.TeableClient.summarize_teable_table`

Return a compact summary for a Teable table.

**Import path:** `fyron.core.io.TeableClient.summarize_teable_table`

```python
TeableClient.summarize_teable_table(self, table_id: str, *, view_id: str | None = None, projection: list[str] | None = None, max_records: int | None = None) -> dict[str, Any]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `table_id` | yes | `str` |  | See signature. |
| `view_id` | no | `str  or  None` | `None` | See signature. |
| `projection` | no | `list[str]  or  None` | `None` | See signature. |
| `max_records` | no | `int  or  None` | `None` | See signature. |

#### Returns

`dict[str, Any]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.io.TeableConfig`

See the signature and linked module guide for context.

**Import path:** `fyron.core.io.TeableConfig`

```python
TeableConfig()
```

### Parameters

No parameters documented.

### Returns

Class constructor.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.io.describe_file`

Return file metadata without reading the payload.

**Import path:** `fyron.core.io.describe_file`

```python
describe_file(path: str | Path) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `str  or  Path` |  | See signature. |

### Returns

`dict[str, Any]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.io.ensure_parent_dir`

Create the parent directory for a file path and return the path.

**Import path:** `fyron.core.io.ensure_parent_dir`

```python
ensure_parent_dir(path: str | Path) -> Path
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `str  or  Path` |  | See signature. |

### Returns

`Path`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.io.read_csv`

Read a CSV file (shortcut for DataIO.read_csv).

**Import path:** `fyron.core.io.read_csv`

```python
read_csv(path: str, **kwargs: Any) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `str` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.io.read_excel`

Read an Excel file (shortcut for DataIO.read_excel).

**Import path:** `fyron.core.io.read_excel`

```python
read_excel(path: str, **kwargs: Any) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `str` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.io.read_json`

Read a UTF-8 JSON file.

**Import path:** `fyron.core.io.read_json`

```python
read_json(path: str | Path, **kwargs: Any) -> Any
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `str  or  Path` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

`Any`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.io.read_table`

Read a table from CSV, TSV, Excel, JSON, or JSONL.

**Import path:** `fyron.core.io.read_table`

```python
read_table(path: str | Path, *, file_format: str | None = None, **kwargs: Any) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `path` | yes | `str  or  Path` |  | See signature. |
| `file_format` | no | `str  or  None` | `None` | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.io.summarize_table`

Return compact metadata for a DataFrame.

**Import path:** `fyron.core.io.summarize_table`

```python
summarize_table(df: pd.DataFrame, *, name: str | None = None) -> dict[str, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `name` | no | `str  or  None` | `None` | See signature. |

### Returns

`dict[str, Any]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.io.write_csv`

Write a DataFrame to CSV (shortcut for DataIO.write_csv).

**Import path:** `fyron.core.io.write_csv`

```python
write_csv(df: pd.DataFrame, path: str, **kwargs: Any) -> None
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `path` | yes | `str` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

`None`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.io.write_excel`

Write a DataFrame to Excel (shortcut for DataIO.write_excel).

**Import path:** `fyron.core.io.write_excel`

```python
write_excel(df: pd.DataFrame, path: str, **kwargs: Any) -> None
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `path` | yes | `str` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

`None`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.io.write_json`

Write a UTF-8 JSON file and return the output path.

**Import path:** `fyron.core.io.write_json`

```python
write_json(payload: Any, path: str | Path, *, indent: int | None = 2, create_parent: bool = True, **kwargs: Any) -> Path
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `payload` | yes | `Any` |  | See signature. |
| `path` | yes | `str  or  Path` |  | See signature. |
| `indent` | no | `int  or  None` | `2` | See signature. |
| `create_parent` | no | `bool` | `True` | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

`Path`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.io.write_table`

Write a table to CSV, TSV, Excel, JSON, or JSONL and return the path.

**Import path:** `fyron.core.io.write_table`

```python
write_table(df: pd.DataFrame, path: str | Path, *, file_format: str | None = None, create_parent: bool = True, index: bool = False, **kwargs: Any) -> Path
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `path` | yes | `str  or  Path` |  | See signature. |
| `file_format` | no | `str  or  None` | `None` | See signature. |
| `create_parent` | no | `bool` | `True` | See signature. |
| `index` | no | `bool` | `False` | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

`Path`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.s3.S3Storage`

Small S3 wrapper for clinical data science tables and sidecar files.

**Import path:** `fyron.core.s3.S3Storage`

```python
S3Storage(self, bucket: str | None = None, *, prefix: str = '', endpoint_url: str | None = None, region_name: str | None = None, profile_name: str | None = None, access_key_id: str | None = None, secret_access_key: str | None = None, session_token: str | None = None)
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `bucket` | no | `str  or  None` | `None` | Bucket name. Defaults to ``S3_BUCKET``. |
| `prefix` | no | `str` | `''` | Optional key prefix prepended to reads and writes. Defaults to ``S3_PREFIX`` when omitted. |
| `endpoint_url` | no | `str  or  None` | `None` | Optional S3-compatible endpoint URL such as MinIO. Defaults to ``S3_ENDPOINT_URL``. |
| `region_name` | no | `str  or  None` | `None` | AWS region name. Defaults to ``AWS_REGION`` or ``AWS_DEFAULT_REGION``. |
| `profile_name` | no | `str  or  None` | `None` | Optional boto3 profile name for local credential resolution. |
| `access_key_id` | no | `str  or  None` | `None` | Optional explicit access key ID for S3-compatible deployments. |
| `secret_access_key` | no | `str  or  None` | `None` | Optional explicit secret access key. Prefer environment variables or a profile for shared research environments. |
| `session_token` | no | `str  or  None` | `None` | Optional temporary session token. |

### Returns

Class constructor.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

### Public Methods

#### `fyron.core.s3.S3Storage.key`

Return a key with the configured prefix applied.

**Import path:** `fyron.core.s3.S3Storage.key`

```python
S3Storage.key(self, key: str) -> str
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `key` | yes | `str` |  | See signature. |

#### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.s3.S3Storage.exists`

Return false only for an explicit not-found response; other errors raise.

**Import path:** `fyron.core.s3.S3Storage.exists`

```python
S3Storage.exists(self, key: str) -> bool
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `key` | yes | `str` |  | See signature. |

#### Returns

`bool`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.s3.S3Storage.list`

List all pages; max_keys limits returned items after suffix filtering.

**Import path:** `fyron.core.s3.S3Storage.list`

```python
S3Storage.list(self, prefix: str | None = None, *, suffix: str | None = None, max_keys: int | None = None) -> list[dict[str, Any]]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `prefix` | no | `str  or  None` | `None` | See signature. |
| `suffix` | no | `str  or  None` | `None` | See signature. |
| `max_keys` | no | `int  or  None` | `None` | See signature. |

#### Returns

`list[dict[str, Any]]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.s3.S3Storage.read_bytes`

Read an object as bytes.

**Import path:** `fyron.core.s3.S3Storage.read_bytes`

```python
S3Storage.read_bytes(self, key: str) -> bytes
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `key` | yes | `str` |  | See signature. |

#### Returns

`bytes`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.s3.S3Storage.write_bytes`

Write bytes to S3 and return the s3 URI.

**Import path:** `fyron.core.s3.S3Storage.write_bytes`

```python
S3Storage.write_bytes(self, key: str, data: bytes, *, content_type: str | None = None) -> str
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `key` | yes | `str` |  | See signature. |
| `data` | yes | `bytes` |  | See signature. |
| `content_type` | no | `str  or  None` | `None` | See signature. |

#### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.s3.S3Storage.read_json`

Read a JSON object.

**Import path:** `fyron.core.s3.S3Storage.read_json`

```python
S3Storage.read_json(self, key: str) -> Any
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `key` | yes | `str` |  | See signature. |

#### Returns

`Any`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.s3.S3Storage.write_json`

Write a JSON object.

**Import path:** `fyron.core.s3.S3Storage.write_json`

```python
S3Storage.write_json(self, key: str, payload: Any, *, indent: int | None = 2) -> str
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `key` | yes | `str` |  | See signature. |
| `payload` | yes | `Any` |  | See signature. |
| `indent` | no | `int  or  None` | `2` | See signature. |

#### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.s3.S3Storage.read_table`

Read a table from S3.

**Import path:** `fyron.core.s3.S3Storage.read_table`

```python
S3Storage.read_table(self, key: str, *, file_format: str | None = None, **kwargs: Any) -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `key` | yes | `str` |  | See signature. |
| `file_format` | no | `str  or  None` | `None` | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

#### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.s3.S3Storage.write_table`

Write a table to S3.

**Import path:** `fyron.core.s3.S3Storage.write_table`

```python
S3Storage.write_table(self, key: str, df: pd.DataFrame, *, file_format: str | None = None, index: bool = False, **kwargs: Any) -> str
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `key` | yes | `str` |  | See signature. |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `file_format` | no | `str  or  None` | `None` | See signature. |
| `index` | no | `bool` | `False` | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

#### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.s3.S3Storage.download_file`

Download an object to a local file.

**Import path:** `fyron.core.s3.S3Storage.download_file`

```python
S3Storage.download_file(self, key: str, local_path: str | Path, *, create_parent: bool = True) -> Path
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `key` | yes | `str` |  | See signature. |
| `local_path` | yes | `str  or  Path` |  | See signature. |
| `create_parent` | no | `bool` | `True` | See signature. |

#### Returns

`Path`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.core.s3.S3Storage.upload_file`

Upload a local file and return the s3 URI.

**Import path:** `fyron.core.s3.S3Storage.upload_file`

```python
S3Storage.upload_file(self, local_path: str | Path, key: str | None = None, *, content_type: str | None = None) -> str
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `local_path` | yes | `str  or  Path` |  | See signature. |
| `key` | no | `str  or  None` | `None` | See signature. |
| `content_type` | no | `str  or  None` | `None` | See signature. |

#### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.s3.parse_s3_uri`

Parse an s3://bucket/key URI.

**Import path:** `fyron.core.s3.parse_s3_uri`

```python
parse_s3_uri(uri: str) -> dict[str, str]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `uri` | yes | `str` |  | See signature. |

### Returns

`dict[str, str]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.s3.read_s3_table`

Read a table from an s3:// URI.

**Import path:** `fyron.core.s3.read_s3_table`

```python
read_s3_table(uri: str, **kwargs: Any) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `uri` | yes | `str` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.core.s3.write_s3_table`

Write a DataFrame to an s3:// URI.

**Import path:** `fyron.core.s3.write_s3_table`

```python
write_s3_table(df: pd.DataFrame, uri: str, **kwargs: Any) -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `uri` | yes | `str` |  | See signature. |
| `kwargs` | yes | `Any` |  | See signature. |

### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.curate.build_compose_command`

Build the Docker Compose command used to run the curator stack.

**Import path:** `fyron.curate.build_compose_command`

```python
build_compose_command(*, build: bool = True, detached: bool = True) -> list[str]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `build` | no | `bool` | `True` | Whether to include ``--build`` so Docker rebuilds the Curate images. |
| `detached` | no | `bool` | `True` | Whether to include ``-d`` so the stack runs in the background. |

### Returns

`list[str]` - Command tokens suitable for :func:`subprocess.run`.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.curate.default_app_dir`

Return the best available path for the bundled image curator app.

**Import path:** `fyron.curate.default_app_dir`

```python
default_app_dir() -> Path
```

### Parameters

No parameters documented.

### Returns

`Path`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.curate.start_curator`

Start the local Fyron image curator Docker Compose app.

**Import path:** `fyron.curate.start_curator`

```python
start_curator(*, app_dir: str | Path | None = None, build: bool = True, detached: bool = True, open_browser: bool = False, color: bool = True, quiet: bool = False) -> int
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `app_dir` | no | `str  or  Path  or  None` | `None` | Optional path to an ``apps/image-curator`` directory. When omitted, Fyron uses the bundled app from the installed package or source tree. |
| `build` | no | `bool` | `True` | Whether Docker Compose should rebuild service images. |
| `detached` | no | `bool` | `True` | Whether Docker Compose should run the stack in the background. |
| `open_browser` | no | `bool` | `False` | Whether to open the local Curate URL in the default browser. |
| `color` | no | `bool` | `True` | Whether status messages may use ANSI color. |
| `quiet` | no | `bool` | `False` | Whether to suppress nonessential status messages. |

### Returns

`int` - Process-style exit code, where ``0`` means Curate started.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.datasets.make_boa_like_folder`

Create a minimal BOA-like cohort folder with one synthetic case.

**Import path:** `fyron.datasets.make_boa_like_folder`

```python
make_boa_like_folder(output_dir: str | Path) -> Path
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `output_dir` | yes | `str  or  Path` |  | See signature. |

### Returns

`Path`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.datasets.make_classification_cohort`

Create a tiny tabular classification dataset.

**Import path:** `fyron.datasets.make_classification_cohort`

```python
make_classification_cohort(n: int = 80, *, random_state: int = 42) -> tuple[pd.DataFrame, pd.Series]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `n` | no | `int` | `80` | See signature. |
| `random_state` | no | `int` | `42` | See signature. |

### Returns

`tuple[pd.DataFrame, pd.Series]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.datasets.make_clinical_cohort`

Create a deterministic synthetic clinical cohort.

**Import path:** `fyron.datasets.make_clinical_cohort`

```python
make_clinical_cohort(n: int = 40, *, random_state: int = 42) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `n` | no | `int` | `40` | See signature. |
| `random_state` | no | `int` | `42` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.datasets.make_dicom_series`

Write a tiny synthetic CT DICOM series.

**Import path:** `fyron.datasets.make_dicom_series`

```python
make_dicom_series(output_dir: str | Path, *, shape: tuple[int, int, int] = (3, 8, 8), patient_id: str = 'SYNTHETIC') -> list[Path]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `output_dir` | yes | `str  or  Path` |  | See signature. |
| `shape` | no | `tuple[int, int, int]` | `(3, 8, 8)` | See signature. |
| `patient_id` | no | `str` | `'SYNTHETIC'` | See signature. |

### Returns

`list[Path]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.datasets.make_nifti_pair`

Write a tiny synthetic image/mask NIfTI pair.

**Import path:** `fyron.datasets.make_nifti_pair`

```python
make_nifti_pair(output_dir: str | Path, *, shape: tuple[int, int, int] = (4, 8, 8)) -> dict[str, Path]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `output_dir` | yes | `str  or  Path` |  | See signature. |
| `shape` | no | `tuple[int, int, int]` | `(4, 8, 8)` | See signature. |

### Returns

`dict[str, Path]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.datasets.make_survival_cohort`

Create a deterministic survival-ready cohort with time and event.

**Import path:** `fyron.datasets.make_survival_cohort`

```python
make_survival_cohort(n: int = 40, *, random_state: int = 42) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `n` | no | `int` | `40` | See signature. |
| `random_state` | no | `int` | `42` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.datasets.preparation.prepare_nnunetv2_dataset`

Prepare an nnU-Net v2 segmentation dataset from a tabular manifest.

**Import path:** `fyron.datasets.preparation.prepare_nnunetv2_dataset`

```python
prepare_nnunetv2_dataset(manifest: pd.DataFrame | str | Path, output_dir: str | Path, dataset_id: int, dataset_name: str, image_col: str = 'image_path', label_col: str = 'label_path', case_id_col: str = 'case_id', split_col: str = 'split', channel_names: dict[int | str, str] | Sequence[str] | None = None, labels: dict[int | str, str] | None = None, copy_mode: CopyMode = 'copy', overwrite: bool = False, validate: bool = True) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `manifest` | yes | `pd.DataFrame  or  str  or  Path` |  | See signature. |
| `output_dir` | yes | `str  or  Path` |  | See signature. |
| `dataset_id` | yes | `int` |  | See signature. |
| `dataset_name` | yes | `str` |  | See signature. |
| `image_col` | no | `str` | `'image_path'` | See signature. |
| `label_col` | no | `str` | `'label_path'` | See signature. |
| `case_id_col` | no | `str` | `'case_id'` | See signature. |
| `split_col` | no | `str` | `'split'` | See signature. |
| `channel_names` | no | `dict[int  or  str, str]  or  Sequence[str]  or  None` | `None` | See signature. |
| `labels` | no | `dict[int  or  str, str]  or  None` | `None` | See signature. |
| `copy_mode` | no | `CopyMode` | `'copy'` | See signature. |
| `overwrite` | no | `bool` | `False` | See signature. |
| `validate` | no | `bool` | `True` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.datasets.preparation.prepare_yolo_classification_dataset`

Prepare a YOLO classification dataset from images, DICOM, or NIfTI.

**Import path:** `fyron.datasets.preparation.prepare_yolo_classification_dataset`

```python
prepare_yolo_classification_dataset(manifest: pd.DataFrame | str | Path, output_dir: str | Path, image_col: str = 'image_path', class_col: str = 'class', split_col: str = 'split', sample_id_col: str | None = None, image_format: str = 'png', copy_mode: CopyMode = 'copy', dicom_window: tuple[float, float] | None = None, nifti_slice: int | Literal['middle', 'all'] = 'middle', overwrite: bool = False, validate: bool = True) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `manifest` | yes | `pd.DataFrame  or  str  or  Path` |  | See signature. |
| `output_dir` | yes | `str  or  Path` |  | See signature. |
| `image_col` | no | `str` | `'image_path'` | See signature. |
| `class_col` | no | `str` | `'class'` | See signature. |
| `split_col` | no | `str` | `'split'` | See signature. |
| `sample_id_col` | no | `str  or  None` | `None` | See signature. |
| `image_format` | no | `str` | `'png'` | See signature. |
| `copy_mode` | no | `CopyMode` | `'copy'` | See signature. |
| `dicom_window` | no | `tuple[float, float]  or  None` | `None` | See signature. |
| `nifti_slice` | no | `int  or  Literal['middle', 'all']` | `'middle'` | See signature. |
| `overwrite` | no | `bool` | `False` | See signature. |
| `validate` | no | `bool` | `True` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.datasets.preparation.prepare_yolo_detection_dataset`

Prepare an Ultralytics-compatible YOLO object-detection dataset.

**Import path:** `fyron.datasets.preparation.prepare_yolo_detection_dataset`

```python
prepare_yolo_detection_dataset(manifest: pd.DataFrame | str | Path, output_dir: str | Path, image_col: str = 'image_path', split_col: str = 'split', class_col: str = 'class', bbox_cols: Sequence[str] = ('x_min', 'y_min', 'x_max', 'y_max'), image_width_col: str | None = None, image_height_col: str | None = None, coord_format: Literal['xyxy_pixels'] = 'xyxy_pixels', sample_id_col: str | None = None, image_format: str = 'png', copy_mode: CopyMode = 'copy', dicom_window: tuple[float, float] | None = None, nifti_slice: int | Literal['middle', 'all'] = 'middle', overwrite: bool = False, validate: bool = True) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `manifest` | yes | `pd.DataFrame  or  str  or  Path` |  | See signature. |
| `output_dir` | yes | `str  or  Path` |  | See signature. |
| `image_col` | no | `str` | `'image_path'` | See signature. |
| `split_col` | no | `str` | `'split'` | See signature. |
| `class_col` | no | `str` | `'class'` | See signature. |
| `bbox_cols` | no | `Sequence[str]` | `('x_min', 'y_min', 'x_max', 'y_max')` | See signature. |
| `image_width_col` | no | `str  or  None` | `None` | See signature. |
| `image_height_col` | no | `str  or  None` | `None` | See signature. |
| `coord_format` | no | `Literal['xyxy_pixels']` | `'xyxy_pixels'` | See signature. |
| `sample_id_col` | no | `str  or  None` | `None` | See signature. |
| `image_format` | no | `str` | `'png'` | See signature. |
| `copy_mode` | no | `CopyMode` | `'copy'` | See signature. |
| `dicom_window` | no | `tuple[float, float]  or  None` | `None` | See signature. |
| `nifti_slice` | no | `int  or  Literal['middle', 'all']` | `'middle'` | See signature. |
| `overwrite` | no | `bool` | `False` | See signature. |
| `validate` | no | `bool` | `True` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.datasets.preparation.validate_nnunetv2_dataset`

Validate the expected files and names in an nnU-Net v2 dataset folder.

**Import path:** `fyron.datasets.preparation.validate_nnunetv2_dataset`

```python
validate_nnunetv2_dataset(dataset_dir: str | Path) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `dataset_dir` | yes | `str  or  Path` |  | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.datasets.preparation.validate_yolo_dataset`

Validate a prepared YOLO classification or detection dataset.

**Import path:** `fyron.datasets.preparation.validate_yolo_dataset`

```python
validate_yolo_dataset(dataset_dir: str | Path, task: Literal['detect', 'classify'] = 'detect') -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `dataset_dir` | yes | `str  or  Path` |  | See signature. |
| `task` | no | `Literal['detect', 'classify']` | `'detect'` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.datasets.preparation.write_dataset_manifest`

Write a dataset preparation manifest as CSV or JSON.

**Import path:** `fyron.datasets.preparation.write_dataset_manifest`

```python
write_dataset_manifest(df: pd.DataFrame, output_path: str | Path) -> Path
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `output_path` | yes | `str  or  Path` |  | See signature. |

### Returns

`Path`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.documents.client.DocumentDownloader`

Download documents from URLs into a deterministic folder structure.

**Import path:** `fyron.documents.client.DocumentDownloader`

```python
DocumentDownloader(self, auth: Optional[Union[Auth, requests.Session]] = None, base_url: Optional[str] = None, output_dir: Union[str, pathlib.Path] = 'documents_out', timeout: int = 30, skip_existing: bool = True, log_downloads: bool = False, max_workers: int = 4, retries: Optional[Retry] = None, save_mode: str = 'auto', force_extension: Optional[str] = None, basic_auth: Optional[Tuple[str, str]] = None, *, require_pdf: bool = False, allow_redirects: bool = True, write_completion_record: bool = True, flat_output: bool = False)
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `auth` | no | `Optional[Union[Auth, requests.Session]]` | `None` | Optional Auth or requests.Session to reuse. |
| `base_url` | no | `Optional[str]` | `None` | Optional base URL to prefix relative paths. |
| `output_dir` | no | `Union[str, pathlib.Path]` | `'documents_out'` | Parent folder where documents are stored. |
| `timeout` | no | `int` | `30` | Request timeout in seconds. |
| `skip_existing` | no | `bool` | `True` | Skip downloads if the target file already exists. |
| `log_downloads` | no | `bool` | `False` | If True, logs each download. |
| `max_workers` | no | `int` | `4` | See signature. |
| `retries` | no | `Optional[Retry]` | `None` | See signature. |
| `save_mode` | no | `str` | `'auto'` | See signature. |
| `force_extension` | no | `Optional[str]` | `None` | See signature. |
| `basic_auth` | no | `Optional[Tuple[str, str]]` | `None` | Optional (user, password) tuple for basic auth (standalone). |
| `require_pdf` | no | `bool` | `False` | Require HTTP 200, application/pdf content type, and a PDF header. |
| `allow_redirects` | no | `bool` | `True` | Follow only same-origin redirects when True; reject redirects when False. |
| `write_completion_record` | no | `bool` | `True` | Write a hidden JSON record for verified restarts. If False, newly saved files cannot be skipped on subsequent runs without an existing valid record. |
| `flat_output` | no | `bool` | `False` | Save documents directly in output_dir using URL-hash filenames. Results contain absolute paths. Explicit output_path takes precedence. |

### Returns

Class constructor.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

### Public Methods

#### `fyron.documents.client.DocumentDownloader.close`

Close the underlying session if owned.

**Import path:** `fyron.documents.client.DocumentDownloader.close`

```python
DocumentDownloader.close(self) -> None
```

#### Parameters

No parameters documented.

#### Returns

`None`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.documents.client.DocumentDownloader.download_id`

Return a deterministic download ID for a URL.

**Import path:** `fyron.documents.client.DocumentDownloader.download_id`

```python
DocumentDownloader.download_id(url: str) -> str
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `url` | yes | `str` |  | See signature. |

#### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.documents.client.DocumentDownloader.download_url`

Download a document with staged publication and verified restarts.

**Import path:** `fyron.documents.client.DocumentDownloader.download_url`

```python
DocumentDownloader.download_url(self, url: str, *, output_path: Optional[Union[str, pathlib.Path]] = None, document_id: Optional[Union[str, int]] = None) -> DocumentResult
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `url` | yes | `str` |  | Absolute document URL or a path relative to base_url. |
| `output_path` | no | `Optional[Union[str, pathlib.Path]]` | `None` | Exact destination file, bypassing automatic naming. When omitted, use automatic naming below output_dir. |
| `document_id` | no | `Optional[Union[str, int]]` | `None` | Optional filename-safe string or integer ID used for automatic naming. Defaults to the URL hash; output_path overrides automatic naming. |

#### Returns

`DocumentResult`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.documents.client.DocumentDownloader.download_urls`

Download a list of URLs and return results as a DataFrame.

**Import path:** `fyron.documents.client.DocumentDownloader.download_urls`

```python
DocumentDownloader.download_urls(self, urls: Iterable[str], results_csv: Optional[Union[str, pathlib.Path]] = None) -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `urls` | yes | `Iterable[str]` |  | See signature. |
| `results_csv` | no | `Optional[Union[str, pathlib.Path]]` | `None` | See signature. |

#### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.documents.client.DocumentDownloader.download_from_dataframe`

Download all URLs from a DataFrame column.

**Import path:** `fyron.documents.client.DocumentDownloader.download_from_dataframe`

```python
DocumentDownloader.download_from_dataframe(self, df: pd.DataFrame, url_col: str = 'document_url', results_csv: Optional[Union[str, pathlib.Path]] = None, *, id_col: Optional[str] = None) -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Input table with unique column names. |
| `url_col` | no | `str` | `'document_url'` | Column containing document URLs. |
| `results_csv` | no | `Optional[Union[str, pathlib.Path]]` | `None` | Optional results CSV destination, separate from document paths. |
| `id_col` | no | `Optional[str]` | `None` | Optional column of unique filename-safe string or integer IDs. Omit to retain URL-hash naming. IDs are validated before requests. |

#### Returns

`pd.DataFrame` - Download outcomes with URL-hash download_id, effective document_id, actual path, status, hash, and controlled errors. Parallel results may arrive in completion order.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.documents.client.DocumentDownloader.download_from_df`

Short alias for download_from_dataframe.

**Import path:** `fyron.documents.client.DocumentDownloader.download_from_df`

```python
DocumentDownloader.download_from_df(self, df: pd.DataFrame, url_col: str = 'document_url', results_csv: Optional[Union[str, pathlib.Path]] = None, *, id_col: Optional[str] = None) -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Input table with unique column names. |
| `url_col` | no | `str` | `'document_url'` | Column containing document URLs. |
| `results_csv` | no | `Optional[Union[str, pathlib.Path]]` | `None` | Optional results CSV destination, separate from document paths. |
| `id_col` | no | `Optional[str]` | `None` | Optional column of unique filename-safe string or integer IDs. Omit to retain URL-hash naming. IDs are validated before requests. |

#### Returns

`pd.DataFrame` - Download outcomes with URL-hash download_id, effective document_id, actual path, status, hash, and controlled errors. Parallel results may arrive in completion order.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.documents.client.DocumentResult`

See the signature and linked module guide for context.

**Import path:** `fyron.documents.client.DocumentResult`

```python
DocumentResult()
```

### Parameters

No parameters documented.

### Returns

Class constructor.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.get_banner`

Return the Bits & Flames Fyron banner as text.

**Import path:** `fyron.get_banner`

```python
get_banner(version: str | None = None, *, include_version: bool = True, color: bool = True, theme: str = 'bf') -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `version` | no | `str  or  None` | `None` | Optional version label to show instead of the installed Fyron version. |
| `include_version` | no | `bool` | `True` | Whether to include the version label in the banner. |
| `color` | no | `bool` | `True` | Whether to include ANSI color escape sequences. |
| `theme` | no | `str` | `'bf'` | Banner color theme passed to :mod:`fyron.banner`. |

### Returns

`str` - Rendered banner text.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.get_run_footer`

Return a formatted run footer for CLI and workflow logs.

**Import path:** `fyron.get_run_footer`

```python
get_run_footer(*args, **kwargs) -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `args` | yes |  |  | Positional arguments forwarded to :func:`fyron.banner.get_run_footer`. |
| `kwargs` | yes |  |  | Keyword arguments forwarded to :func:`fyron.banner.get_run_footer`. |

### Returns

`str` - Footer text suitable for terminal or log output.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.get_run_header`

Return a formatted run header for CLI and workflow logs.

**Import path:** `fyron.get_run_header`

```python
get_run_header(*args, **kwargs) -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `args` | yes |  |  | Positional arguments forwarded to :func:`fyron.banner.get_run_header`. |
| `kwargs` | yes |  |  | Keyword arguments forwarded to :func:`fyron.banner.get_run_header`. |

### Returns

`str` - Header text suitable for terminal or log output.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.llm.agent.LLMAgent`

Simple LLM agent for DataFrame and document directory workflows.

**Import path:** `fyron.llm.agent.LLMAgent`

```python
LLMAgent(self, provider: Optional[str] = None, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None, timeout: Optional[int] = None, extra_headers: Optional[Dict[str, str]] = None, auth_required: Optional[bool] = None, verify_ssl: bool = True)
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `provider` | no | `Optional[str]` | `None` | Provider mode: ``openai``, ``anyllm``, or ``custom``. Defaults to ``LLM_PROVIDER`` or ``openai``. |
| `base_url` | no | `Optional[str]` | `None` | Provider base URL or custom endpoint. Defaults to ``LLM_BASE_URL``. |
| `api_key` | no | `Optional[str]` | `None` | Optional API key. Defaults to ``LLM_API_KEY`` and is sent as a bearer token when present. |
| `model` | no | `Optional[str]` | `None` | Model name for the provider. Defaults to ``LLM_MODEL``. |
| `timeout` | no | `Optional[int]` | `None` | Request timeout in seconds. Defaults to ``LLM_TIMEOUT`` or 30. |
| `extra_headers` | no | `Optional[Dict[str, str]]` | `None` | Additional HTTP headers merged into the session. |
| `auth_required` | no | `Optional[bool]` | `None` | Whether an API key is required. Defaults to true for ``openai`` and ``anyllm`` and false for ``custom``. |
| `verify_ssl` | no | `bool` | `True` | Whether HTTPS certificate verification is enabled for requests. |

### Returns

Class constructor.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

### Public Methods

#### `fyron.llm.agent.LLMAgent.prompt`

Send a single prompt and return the model response.

**Import path:** `fyron.llm.agent.LLMAgent.prompt`

```python
LLMAgent.prompt(self, user_prompt: str, *, image_path: Optional[str] = None, file_path: Optional[str] = None, mode: str = 'text') -> str
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `user_prompt` | yes | `str` |  | See signature. |
| `image_path` | no | `Optional[str]` | `None` | See signature. |
| `file_path` | no | `Optional[str]` | `None` | See signature. |
| `mode` | no | `str` | `'text'` | See signature. |

#### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.llm.agent.LLMAgent.chat`

Alias for prompt (kept for convenience).

**Import path:** `fyron.llm.agent.LLMAgent.chat`

```python
LLMAgent.chat(self, user_prompt: str, *, image_path: Optional[str] = None, file_path: Optional[str] = None, mode: str = 'text') -> str
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `user_prompt` | yes | `str` |  | See signature. |
| `image_path` | no | `Optional[str]` | `None` | See signature. |
| `file_path` | no | `Optional[str]` | `None` | See signature. |
| `mode` | no | `str` | `'text'` | See signature. |

#### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.llm.agent.LLMAgent.run_on_dataframe`

Run a prompt over a DataFrame column and append results.

**Import path:** `fyron.llm.agent.LLMAgent.run_on_dataframe`

```python
LLMAgent.run_on_dataframe(self, df: pd.DataFrame, text_col: str, prompt: str, output_col: str = 'llm_output', format_func: Optional[Callable[[str, Dict[str, Any]], str]] = None, image_col: Optional[str] = None, file_col: Optional[str] = None, mode: str = 'text') -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Input DataFrame. |
| `text_col` | yes | `str` |  | Column containing text to analyze. |
| `prompt` | yes | `str` |  | Prompt template. If format_func is not provided, text is appended. |
| `output_col` | no | `str` | `'llm_output'` | Name of output column. |
| `format_func` | no | `Optional[Callable[[str, Dict[str, Any]], str]]` | `None` | Optional function (text, row_dict) -> prompt string. |
| `image_col` | no | `Optional[str]` | `None` | Optional column with image file paths or URLs. |
| `file_col` | no | `Optional[str]` | `None` | Optional column with PDF file paths (OpenAI Responses only). |
| `mode` | no | `str` | `'text'` | "text", "image", "pdf", or "auto". |

#### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.llm.agent.LLMAgent.run_on_documents`

Run a prompt over a list of documents (paths or raw strings).

**Import path:** `fyron.llm.agent.LLMAgent.run_on_documents`

```python
LLMAgent.run_on_documents(self, documents: List[str], prompt: str, output_csv: Optional[str] = None, mode: str = 'text') -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `documents` | yes | `List[str]` |  | List of file paths or raw text strings. |
| `prompt` | yes | `str` |  | Prompt to apply to each document. |
| `output_csv` | no | `Optional[str]` | `None` | Optional path to write results as CSV. |
| `mode` | no | `str` | `'text'` | "text", "image", "pdf", or "auto". |

#### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.llm.agent.LLMAgent.prompt_documents`

Short alias for run_on_documents.

**Import path:** `fyron.llm.agent.LLMAgent.prompt_documents`

```python
LLMAgent.prompt_documents(self, documents: List[str], prompt: str, output_csv: Optional[str] = None, mode: str = 'text') -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `documents` | yes | `List[str]` |  | See signature. |
| `prompt` | yes | `str` |  | See signature. |
| `output_csv` | no | `Optional[str]` | `None` | See signature. |
| `mode` | no | `str` | `'text'` | See signature. |

#### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.llm.agent.LLMAgent.prompt_dataframe`

Run a prompt over a DataFrame column and optionally save results.

**Import path:** `fyron.llm.agent.LLMAgent.prompt_dataframe`

```python
LLMAgent.prompt_dataframe(self, df: pd.DataFrame, text_col: str, prompt: str, output_col: str = 'llm_output', output_csv: Optional[str] = None, format_func: Optional[Callable[[str, Dict[str, Any]], str]] = None, image_col: Optional[str] = None, file_col: Optional[str] = None, mode: str = 'text') -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `text_col` | yes | `str` |  | See signature. |
| `prompt` | yes | `str` |  | See signature. |
| `output_col` | no | `str` | `'llm_output'` | See signature. |
| `output_csv` | no | `Optional[str]` | `None` | See signature. |
| `format_func` | no | `Optional[Callable[[str, Dict[str, Any]], str]]` | `None` | See signature. |
| `image_col` | no | `Optional[str]` | `None` | See signature. |
| `file_col` | no | `Optional[str]` | `None` | See signature. |
| `mode` | no | `str` | `'text'` | See signature. |

#### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.llm.agent.LLMAgent.prompt_df`

Short alias for prompt_dataframe.

**Import path:** `fyron.llm.agent.LLMAgent.prompt_df`

```python
LLMAgent.prompt_df(self, df: pd.DataFrame, text_col: str, prompt: str, output_col: str = 'llm_output', output_csv: Optional[str] = None, format_func: Optional[Callable[[str, Dict[str, Any]], str]] = None, image_col: Optional[str] = None, file_col: Optional[str] = None, mode: str = 'text') -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `text_col` | yes | `str` |  | See signature. |
| `prompt` | yes | `str` |  | See signature. |
| `output_col` | no | `str` | `'llm_output'` | See signature. |
| `output_csv` | no | `Optional[str]` | `None` | See signature. |
| `format_func` | no | `Optional[Callable[[str, Dict[str, Any]], str]]` | `None` | See signature. |
| `image_col` | no | `Optional[str]` | `None` | See signature. |
| `file_col` | no | `Optional[str]` | `None` | See signature. |
| `mode` | no | `str` | `'text'` | See signature. |

#### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.llm.agent.LLMAgent.run_prompt_on_dataframe`

Backward-compatible alias for prompt_dataframe.

**Import path:** `fyron.llm.agent.LLMAgent.run_prompt_on_dataframe`

```python
LLMAgent.run_prompt_on_dataframe(self, df: pd.DataFrame, text_col: str, prompt: str, output_col: str = 'llm_output', output_csv: Optional[str] = None, format_func: Optional[Callable[[str, Dict[str, Any]], str]] = None, image_col: Optional[str] = None, file_col: Optional[str] = None, mode: str = 'text') -> pd.DataFrame
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | See signature. |
| `text_col` | yes | `str` |  | See signature. |
| `prompt` | yes | `str` |  | See signature. |
| `output_col` | no | `str` | `'llm_output'` | See signature. |
| `output_csv` | no | `Optional[str]` | `None` | See signature. |
| `format_func` | no | `Optional[Callable[[str, Dict[str, Any]], str]]` | `None` | See signature. |
| `image_col` | no | `Optional[str]` | `None` | See signature. |
| `file_col` | no | `Optional[str]` | `None` | See signature. |
| `mode` | no | `str` | `'text'` | See signature. |

#### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.llm.agent.LLMAgent.describe_python_file`

Generate a scientific-methods style description of a Python file.

**Import path:** `fyron.llm.agent.LLMAgent.describe_python_file`

```python
LLMAgent.describe_python_file(self, file_path: str | pathlib.Path, output_md: str | pathlib.Path, prompt: Optional[str] = None) -> str
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `file_path` | yes | `str  or  pathlib.Path` |  | Path to the Python file to analyze. |
| `output_md` | yes | `str  or  pathlib.Path` |  | Path to write the markdown summary. |
| `prompt` | no | `Optional[str]` | `None` | Optional prompt override. |

#### Returns

`str`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.llm.agent.LLMAgent.run_on_directory`

Run a prompt over all files in a directory.

**Import path:** `fyron.llm.agent.LLMAgent.run_on_directory`

```python
LLMAgent.run_on_directory(self, input_dir: str | pathlib.Path, prompt: str, glob: str = '*.txt', mode: str = 'text') -> Dict[str, str]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `input_dir` | yes | `str  or  pathlib.Path` |  | See signature. |
| `prompt` | yes | `str` |  | See signature. |
| `glob` | no | `str` | `'*.txt'` | See signature. |
| `mode` | no | `str` | `'text'` | See signature. |

#### Returns

`Dict[str, str]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

#### `fyron.llm.agent.LLMAgent.prompt_directory`

Short alias for run_on_directory.

**Import path:** `fyron.llm.agent.LLMAgent.prompt_directory`

```python
LLMAgent.prompt_directory(self, input_dir: str | pathlib.Path, prompt: str, glob: str = '*.txt', mode: str = 'text') -> Dict[str, str]
```

#### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `input_dir` | yes | `str  or  pathlib.Path` |  | See signature. |
| `prompt` | yes | `str` |  | See signature. |
| `glob` | no | `str` | `'*.txt'` | See signature. |
| `mode` | no | `str` | `'text'` | See signature. |

#### Returns

`Dict[str, str]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.llm.agent.LLMConfig`

See the signature and linked module guide for context.

**Import path:** `fyron.llm.agent.LLMConfig`

```python
LLMConfig()
```

### Parameters

No parameters documented.

### Returns

Class constructor.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.plotting_palettes.PaletteSpec`

Metadata for one named scientific color palette.

**Import path:** `fyron.plotting_palettes.PaletteSpec`

```python
PaletteSpec()
```

### Parameters

No parameters documented.

### Returns

Class constructor.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.plotting_palettes.get_colormap`

Return a Matplotlib colormap from a named sequential/diverging palette.

**Import path:** `fyron.plotting_palettes.get_colormap`

```python
get_colormap(name: str = 'fyron_sequential_blue', *, reverse: bool = False) -> LinearSegmentedColormap
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `name` | no | `str` | `'fyron_sequential_blue'` | See signature. |
| `reverse` | no | `bool` | `False` | See signature. |

### Returns

`LinearSegmentedColormap`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.plotting_palettes.get_palette`

Return a named scientific palette as hex colors.

**Import path:** `fyron.plotting_palettes.get_palette`

```python
get_palette(name: str = 'okabe_ito', n: int | None = None, *, reverse: bool = False) -> list[str]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `name` | no | `str` | `'okabe_ito'` | See signature. |
| `n` | no | `int  or  None` | `None` | See signature. |
| `reverse` | no | `bool` | `False` | See signature. |

### Returns

`list[str]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.plotting_palettes.list_palettes`

List available Fyron scientific palettes.

**Import path:** `fyron.plotting_palettes.list_palettes`

```python
list_palettes(kind: str | None = None) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `kind` | no | `str  or  None` | `None` | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.plotting_palettes.palette_grayscale_contrast`

Return adjacent luminance differences for grayscale readability checks.

**Import path:** `fyron.plotting_palettes.palette_grayscale_contrast`

```python
palette_grayscale_contrast(name_or_colors: str | Sequence[str]) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `name_or_colors` | yes | `str  or  Sequence[str]` |  | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.plotting_palettes.palette_luminance_table`

Return luminance and text-color guidance for a palette.

**Import path:** `fyron.plotting_palettes.palette_luminance_table`

```python
palette_luminance_table(name_or_colors: str | Sequence[str]) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `name_or_colors` | yes | `str  or  Sequence[str]` |  | See signature. |

### Returns

`pd.DataFrame`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.plotting_palettes.preview_palette`

Preview a named palette as labeled swatches.

**Import path:** `fyron.plotting_palettes.preview_palette`

```python
preview_palette(name: str, n: int | None = None, *, save_path: str | Path | None = None) -> tuple[Any, Any]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `name` | yes | `str` |  | See signature. |
| `n` | no | `int  or  None` | `None` | See signature. |
| `save_path` | no | `str  or  Path  or  None` | `None` | See signature. |

### Returns

`tuple[Any, Any]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.plotting_palettes.resolve_colormap`

Resolve a Fyron colormap name or pass through any Matplotlib colormap.

**Import path:** `fyron.plotting_palettes.resolve_colormap`

```python
resolve_colormap(cmap: str | Any) -> Any
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `cmap` | yes | `str  or  Any` |  | See signature. |

### Returns

`Any`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.plotting_palettes.resolve_palette`

Resolve a named or explicit palette to ``n`` colors.

**Import path:** `fyron.plotting_palettes.resolve_palette`

```python
resolve_palette(palette: str | Sequence[str] | None, n: int, *, default: str = 'okabe_ito') -> list[str]
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `palette` | yes | `str  or  Sequence[str]  or  None` |  | See signature. |
| `n` | yes | `int` |  | See signature. |
| `default` | no | `str` | `'okabe_ito'` | See signature. |

### Returns

`list[str]`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.plotting_palettes.set_plot_style`

Set Fyron Matplotlib defaults for publication figures.

**Import path:** `fyron.plotting_palettes.set_plot_style`

```python
set_plot_style(style: str = 'paper', palette: str = 'okabe_ito') -> None
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `style` | no | `str` | `'paper'` | See signature. |
| `palette` | no | `str` | `'okabe_ito'` | See signature. |

### Returns

`None`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.print_banner`

Print the Bits & Flames Fyron banner.

**Import path:** `fyron.print_banner`

```python
print_banner(version: str | None = None, *, include_version: bool = True, color: bool = True, theme: str = 'bf', file: TextIO | None = None) -> None
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `version` | no | `str  or  None` | `None` | Optional version label to show instead of the installed Fyron version. |
| `include_version` | no | `bool` | `True` | Whether to include the version label in the banner. |
| `color` | no | `bool` | `True` | Whether to include ANSI color escape sequences. |
| `theme` | no | `str` | `'bf'` | Banner color theme passed to :mod:`fyron.banner`. |
| `file` | no | `TextIO  or  None` | `None` | Optional text stream to receive the banner. |

### Returns

`None`

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.reporting.tables.cohort_flow_table`

Create a simple cohort flow table from named analysis steps.

**Import path:** `fyron.reporting.tables.cohort_flow_table`

```python
cohort_flow_table(steps: Sequence[Mapping[str, Any]] | pd.DataFrame) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `steps` | yes | `Sequence[Mapping[str, Any]]  or  pd.DataFrame` |  | Ordered step records with at least ``step`` or ``label`` and ``n``. Optional ``excluded`` and ``reason`` values are preserved or derived. |

### Returns

`pandas.DataFrame` - Ordered flow table with step number, label, count, excluded count, and exclusion reason.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.reporting.tables.compare_models_table`

Combine multiple model result objects into one paper-ready metrics table.

**Import path:** `fyron.reporting.tables.compare_models_table`

```python
compare_models_table(results: Mapping[str, Any] | Sequence[Mapping[str, Any]], *, model_col: str = 'model', metrics_key: str = 'metrics', digits: int = 3) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `results` | yes | `Mapping[str, Any]  or  Sequence[Mapping[str, Any]]` |  | Either ``{"model name": result}`` or a sequence of result dictionaries. Each result may contain a ``metrics`` dictionary or metric keys at top level. |
| `model_col` | no | `str` | `'model'` | Name of the output model column. |
| `metrics_key` | no | `str` | `'metrics'` | Key containing the metric dictionary when present. |
| `digits` | no | `int` | `3` | Decimal places for numeric metric columns. |

### Returns

`pandas.DataFrame` - One row per model/result with rounded metric columns.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.reporting.tables.dataframe_to_markdown`

Render a DataFrame as a plain Markdown table.

**Import path:** `fyron.reporting.tables.dataframe_to_markdown`

```python
dataframe_to_markdown(df: pd.DataFrame, *, index: bool = False) -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | DataFrame to render. |
| `index` | no | `bool` | `False` | If True, include the DataFrame index as the first column. |

### Returns

`str` - Markdown table string suitable for notes, reports, documentation, or pull-request review.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.reporting.tables.format_estimate_ci`

Format an estimate and confidence interval for manuscript tables.

**Import path:** `fyron.reporting.tables.format_estimate_ci`

```python
format_estimate_ci(estimate: float, lower: float, upper: float, *, digits: int = 2, separator: str = ' to ') -> str
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `estimate` | yes | `float` |  | Point estimate, such as beta, odds ratio, hazard ratio, or metric value. |
| `lower` | yes | `float` |  | Lower confidence interval bound. |
| `upper` | yes | `float` |  | Upper confidence interval bound. |
| `digits` | no | `int` | `2` | Decimal places used for all numeric values. |
| `separator` | no | `str` | `' to '` | Text placed between lower and upper confidence interval bounds. |

### Returns

`str` - Formatted string such as ``"1.24 (1.02 to 1.51)"``.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.reporting.tables.metrics_table`

Normalize model metrics into a rounded report table.

**Import path:** `fyron.reporting.tables.metrics_table`

```python
metrics_table(metrics: Mapping[str, Mapping[str, Any]] | pd.DataFrame, *, model_col: str = 'model', digits: int = 3) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `metrics` | yes | `Mapping[str, Mapping[str, Any]]  or  pd.DataFrame` |  | Either a DataFrame that already contains metric columns, or a nested mapping such as ``{"RF": {"auc": 0.82}}``. |
| `model_col` | no | `str` | `'model'` | Name of the output column containing model names. |
| `digits` | no | `int` | `3` | Decimal places used for numeric metric columns. |

### Returns

`pandas.DataFrame` - One row per model or metric source with rounded numeric metric columns.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).

## `fyron.reporting.tables.summarize_baseline_table`

Create a compact baseline characteristics table.

**Import path:** `fyron.reporting.tables.summarize_baseline_table`

```python
summarize_baseline_table(df: pd.DataFrame, *, group_col: str | None = None, continuous: Sequence[str] | None = None, categorical: Sequence[str] | None = None, digits: int = 1) -> pd.DataFrame
```

### Parameters

| Parameter | Required | Type | Default | Description |
| --- | --- | --- | --- | --- |
| `df` | yes | `pd.DataFrame` |  | Patient-level cohort or analysis table. |
| `group_col` | no | `str  or  None` | `None` | Optional column used to stratify summaries, such as treatment arm, risk group, cohort, or center. |
| `continuous` | no | `Sequence[str]  or  None` | `None` | Continuous variables to summarize as mean and standard deviation. If omitted, numeric columns are selected automatically. |
| `categorical` | no | `Sequence[str]  or  None` | `None` | Categorical variables to summarize as count and percent. If omitted, non-continuous columns are selected automatically. |
| `digits` | no | `int` | `1` | Decimal places used in formatted summary strings. |

### Returns

`pandas.DataFrame` - Long baseline table with variable, level, summary type, and one column per group or an overall column.

**See also:** [Core, Publication, And Utility module guide](../modules/core.md).
