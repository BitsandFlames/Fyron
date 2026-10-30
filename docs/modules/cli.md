# Unified CLI

For site-specific access setup, see [Authentication methods and CLI support](../authentication/index.md). Choose the method and permissions approved by your administrator.

The `fyron` command line interface wraps the repeatable parts of clinical data science: API extraction, DICOM downloads, imaging QC, Curate preview preparation, BOA feature extraction, radiomics, DICOM SEG export, synthetic DICOM export, audit manifests, and documentation builds.

Use the Python API when you are exploring. Use notebooks when you need narrative analysis. Use the CLI when a step should be rerun exactly the same way by you, a collaborator, or a compute job.

## Install

```bash
uv add "fyron[all]"
```

For a smaller CLI-focused environment, install only the extras behind the commands you use, for example `uv add "fyron[ml,survival,visualization,radiomics,dicom-seg]"`.

The base command is installed as:

```bash
fyron --help
```

Global output flags work before every subcommand:

```bash
fyron --verbose docs-build
fyron --quiet imaging-qc --nifti ct.nii.gz --output qc.csv
fyron --no-color banner
fyron --json-log fhir-rest --resource Patient --output patients.csv
fyron --no-progress boa-extract --cohort-folder data/boa --output boa.csv
```

## Console Easter Eggs

The banner is a deliberate brand moment, not automatic package output:

```bash
fyron banner
fyron spark
fyron banner --theme mono --no-version
```

Normal commands do not print the banner on startup, which keeps notebooks, CI logs, and scheduled jobs clean.

## Command Map

| Command | Use it for | Main output |
| --- | --- | --- |
| `fyron banner` | Print the colored Fyron terminal banner | terminal text |
| `fyron spark` | Print the same banner as a playful easter egg | terminal text |
| `fyron docs-build` | Build the local BF documentation site | `site/` |
| `fyron fhir-rest` | Query FHIR REST resources or row-wise resource lookups | CSV or JSON |
| `fyron fhir-build-bundle` | Build FHIR bundles from reviewed CSV tables | FHIR JSON bundle and validation reports |
| `fyron dicom-download` | Download DICOMweb series or studies | DICOM/NIfTI files and manifests |
| `fyron document-download` | Download documents with OIDC device or service-account auth | Files and sensitive results CSV |
| `fyron synthetic-dicom` | Export generated NIfTI volumes as synthetic DICOM series | DICOM files and manifest CSV |
| `fyron dicom-seg` | Write source-referenced DICOM SEG objects | `.seg.dcm` |
| `fyron dataset-curate-previews` | Prepare CT/MRI/X-ray PNG previews for Fyron Curate | PNG folder and manifest CSV |
| `fyron dataset-nnunetv2` | Prepare nnU-Net v2 segmentation folders | NIfTI dataset folder and manifest |
| `fyron dataset-yolo-classify` | Prepare YOLO classification folders | split/class image folders |
| `fyron dataset-yolo-detect` | Prepare YOLO detection folders and labels | images, labels, `data.yaml` |
| `fyron boa-extract` | Extract BOA measurement and experimental feature tables | CSV |
| `fyron boa-radiomics` | Extract BOA PyRadiomics tables | CSV |
| `fyron imaging-qc` | Summarize DICOM/NIfTI geometry, mask volumes, and intensities | CSV or JSON |
| `fyron audit-manifest` | Write reproducibility manifests | JSON |

## Curate Preview And Review Workflow

Use `dataset-curate-previews` when CT/MRI folders, DICOM series, X-rays, or topograms need to become ordinary PNG files for Fyron Curate. The command scans nested folders by default, writes preview PNGs, and creates a manifest that maps each preview back to its source.

```bash
uv add "fyron[visualization,curate]"

fyron dataset-curate-previews \
  --input-dir ct_exports/ \
  --output-dir curate_previews/

fyron curate
```

Drop `curate_previews/` into the Curate **Add cohort** dialog. Three-dimensional volumes produce middle axial, coronal, and sagittal images. Two-dimensional images produce one preview image.

Useful options:

```bash
fyron dataset-curate-previews --input-dir ct_exports/ --output-dir curate_previews/ --panel-width 512
fyron dataset-curate-previews --input-dir ct_exports/ --output-dir curate_previews/ --window-center 40 --window-width 400
fyron dataset-curate-previews --input-dir ct_exports/ --output-dir curate_previews/ --overwrite
```

## Console Output And Logging

Fyron uses a small dependency-free console layer for terminal output. Normal CLI output is human-readable, colored with the Bits & Flames palette when the terminal supports ANSI colors, and automatically plain in non-TTY logs or when `NO_COLOR` is set.

| Mode | Use it when | Example |
| --- | --- | --- |
| normal | interactive terminal jobs | `fyron docs-build` |
| quiet | CI jobs where only files matter | `fyron --quiet boa-extract ...` |
| verbose | debugging endpoints, mappings, or batch behavior | `fyron --verbose fhir-rest ...` |
| no color | plain logs, copied output, Windows shells without ANSI | `fyron --no-color banner` |
| JSON log | pipeline logs that should be parsed downstream | `fyron --json-log docs-build` |
| no progress | batch systems where progress bars make logs noisy | `fyron --no-progress boa-extract ...` |

CLI commands print concise completion messages with created files, rows, validation status, and elapsed time where useful. Machine-readable outputs such as JSON bundles, validation reports, manifests, CSV tables, and DICOM files are unchanged by console flags.

For Python scripts and notebooks, use the same helpers directly:

```python
from fyron.console import configure_logging, get_logger, success, warning

configure_logging("INFO")
log = get_logger("fyron.analysis")
log.info("starting cohort build")
success("Wrote cohort_features.csv")
warning("External validation cohort has 12 missing BMI values")
```

For CI, combine `--quiet` for artifact-only commands or `--json-log` when a runner should collect structured logs.

## FHIR REST Extraction

Simple resource extraction:

```bash
fyron fhir-rest \
  --base-url https://fhir.example.org/fhir \
  --resource Patient \
  --param _count=100 \
  --max-pages 2 \
  --output patients.csv
```

Row-wise extraction from a cohort table:

```bash
fyron fhir-rest \
  --base-url https://fhir.example.org/fhir \
  --resource Observation \
  --input cohort.csv \
  --column-map subject=patient_id \
  --param 'code=http://loinc.org|718-7' \
  --max-pages 1 \
  --output observations.csv
```

FHIRPath-style projection from JSON:

```json
[
  ["observation_id", "id"],
  ["patient_ref", "subject.reference"],
  ["value", "valueQuantity.value"],
  ["unit", "valueQuantity.unit"]
]
```

```bash
fyron fhir-rest \
  --base-url "$FHIR_BASE_URL" \
  --resource Observation \
  --params-json observation_params.json \
  --fhir-paths observation_paths.json \
  --output hemoglobin.csv
```

Credentials can come from arguments or environment variables: `FHIR_BASE_URL`, `FHIR_AUTH_URL`, and `FHIR_TOKEN`.

## FHIR Bundle Building

```bash
fyron fhir-build-bundle \
  --input extracted_observations.csv \
  --mapping observation_mapping.json \
  --resource Observation \
  --subject-col patient_id \
  --id-col observation_id \
  --bundle-type transaction \
  --transaction-method PUT \
  --output bundle.json \
  --summary-json bundle_summary.json \
  --validation-json validation_report.json
```

Use `--submit` only for reviewed transaction bundles:

```bash
fyron fhir-build-bundle \
  --input extracted_observations.csv \
  --mapping observation_mapping.json \
  --resource Observation \
  --subject-col patient_id \
  --bundle-type transaction \
  --output bundle.json \
  --submit \
  --base-url "$FHIR_BASE_URL"
```

## Document Downloads

```bash
fyron document-download \
  --url 'https://documents.example.org/reports/synthetic-001/pdf' \
  --output documents_out/report.pdf --pdf \
  --auth-type device_code \
  --auth-url 'https://identity.example.org/realms/research' \
  --client-id research-documents-cli \
  --scope 'openid user/DocumentReference.rs' \
  --results-csv document-results.csv
```

These are fictional endpoints. Use a registered client and approved scopes from
your provider. See [DocumentDownloader](documents/downloader.md) for Python usage,
plain-text downloads, mixed text/PDF batches, and verified restart behavior.

Both `text/plain` and `application/pdf` are supported. Omit `--pdf` for plain text
or mixed batches; add it only when every response must pass strict PDF checks.
The downloader saves bytes without converting text into PDF or PDF into text.

| Options | Behavior |
| --- | --- |
| `--url` / `--csv` | Exactly one source; CSV defaults to column `document_url`. |
| `--document-id` / `--id-col` | Exact ID for a single URL or ID column for a CSV; invalid or duplicate IDs fail before authentication. |
| `--url-col`, `--base-url` | Select a CSV URL column and optionally resolve relative paths. |
| `--output` / `--output-dir` | Exact single-file destination, or URL-hash folders (parent defaults to `documents_out`). |
| `--auth-type` | `none` (default), `device_code`, or `client_credentials`; anonymous mode ignores FHIR auth environment variables. |
| `--auth-url`, `--client-id`, `--scope` | Issuer, registered client, and approved scopes. Device scopes default to `openid`; service-account scopes default to empty. |
| `--client-secret-env` | Environment variable name holding the secret; required for service accounts. |
| `--device-authorization-endpoint`, `--token-endpoint` | Supply both to bypass device discovery; service accounts can use a token endpoint alone. |
| `--authorization-endpoint` | Optional device-login endpoint for shared authentication challenge handling. |
| `--token-cache`, `--no-reauthentication` | Opt-in sensitive plaintext device cache; prohibit interactive approval for unattended use. |
| `--pdf` | Require HTTP 200, PDF content type, and `%PDF-` signature. |
| `--timeout`, `--workers` | Request timeout (default 90 seconds) and batch threads (default four). |
| `--overwrite` | Permit replacement; otherwise only verified downloads can be skipped. |
| `--no-completion-record` | Omit per-document JSON completion records. Newly saved files cannot be verified for later skips; intentional replacement requires `--overwrite`. |
| `--flat-output` | Save directly in `--output-dir` with URL-hash filenames; `path` in results contains the absolute document path. Explicit `--output` takes precedence. |
| `--allow-redirects` | Enable same-origin redirects. All redirects are rejected by default. |
| `--results-csv` | Sensitive per-document URLs, paths, hashes, and outcomes. |

Inputs are validated before authentication. Summaries contain counts;
`--json-log` emits structured diagnostic records. Browser approval instructions
remain visible with `--quiet`. Exit codes: 0 for success/verified skips, 1 for
download or authentication failure, 2 for invalid inputs, 130 for interruption.

## DICOMweb Downloads

Single series:

```bash
fyron dicom-download \
  --dicom-web-url https://pacs.example.org/dicomweb \
  --study-uid 1.2.3 \
  --series-uid 1.2.3.4 \
  --output-dir dicom_out \
  --output-format nifti
```

Batch from a table:

```bash
fyron dicom-download \
  --csv imaging.csv \
  --study-col study_instance_uid \
  --series-col series_instance_uid \
  --output-dir dicom_out \
  --results-csv dicom_results.csv
```

Full-study mode:

```bash
fyron dicom-download \
  --csv imaging.csv \
  --full-study \
  --study-layout hierarchical \
  --study-folder-col download_id \
  --manifest \
  --output-format dicom
```

Endpoint credentials can come from `DICOM_WEB_URL`, `DICOM_USER`, and `DICOM_PASSWORD`.

## Synthetic DICOM Export

Use this for generated images, GAN outputs, augmentation studies, or benchmark volumes that need DICOM geometry and synthetic identifiers.

```bash
fyron synthetic-dicom \
  --volume generated_ct.nii.gz \
  --reference-dicom original_dicom/case_001 \
  --output-dir synthetic/case_001 \
  --patient-id SYN001 \
  --manifest synthetic/case_001_manifest.csv
```

The command creates new UIDs by default and does not copy patient-identifying tags.

## DICOM SEG Export

DICOM SEG needs original source DICOM images because segmentations reference source frames and geometry.

```json
[
  {"label": "liver", "label_value": 5},
  {"label": "spleen", "label_value": 1}
]
```

```bash
fyron dicom-seg \
  --mask total.nii.gz \
  --source-dicom original_dicom/case_001 \
  --segments segments.json \
  --output segmentations/case_001.seg.dcm \
  --algorithm-name "Fyron organ model" \
  --validate \
  --summary-json segmentations/case_001.seg.summary.json
```

Install `fyron[dicom-seg]` for the `highdicom` dependency.

`--source-dicom` is loaded in geometry order, with fallback to `InstanceNumber` and then file path. Use `--summary-json` when a batch job should leave an inspectable validation artifact next to the SEG object.

## BOA Feature Tables

```bash
fyron boa-extract \
  --cohort-folder data/boa \
  --output body_regions.csv \
  --include-body-regions \
  --include-total \
  --include-aortic-experimental \
  --num-workers 8
```

Radiomics:

```bash
fyron boa-radiomics \
  --cohort-folder data/boa \
  --segmentation total \
  --output radiomics.csv \
  --num-workers 8
```

Use `boa-extract` for BOA JSON measurements, SMA/IMATI/VATI markers, organ volumes, and experimental aortic calcification. Use `boa-radiomics` for PyRadiomics features from `total.nii.gz` or `body-regions.nii.gz`.

## Imaging QC

```bash
fyron imaging-qc \
  --dicom-dir dicom/case_001 \
  --nifti ct.nii.gz \
  --mask liver_mask.nii.gz \
  --output qc.csv
```

The output table can include DICOM geometry summaries, NIfTI geometry, image-mask alignment checks, mask volumes, and intensity ranges. This is a good pre-flight step before radiomics, BOA extraction, or DICOM SEG export.

## Audit Manifest

```bash
fyron audit-manifest \
  --title "BOA survival analysis" \
  --input data/boa_features.csv \
  --input data/outcomes.csv \
  --output results/metrics.csv \
  --param duration_col=time \
  --param event_col=event \
  --write results/provenance.json
```

Store the manifest beside tables and figures so reruns remain traceable.

## Dataset Preparation

Use the dataset commands when image and label manifests should be turned into framework-ready training folders.

```bash
fyron dataset-nnunetv2 \
  --manifest cohort.csv \
  --output-dir datasets/nnunet \
  --dataset-id 501 \
  --dataset-name LungTumor
```

```bash
fyron dataset-yolo-classify \
  --manifest cohort.csv \
  --output-dir datasets/yolo_cls \
  --image-col image_path \
  --class-col label \
  --split-col split
```

```bash
fyron dataset-yolo-detect \
  --manifest boxes.csv \
  --output-dir datasets/yolo_det \
  --image-col image_path \
  --class-col class \
  --bbox-cols x_min,y_min,x_max,y_max
```

See [Datasets](datasets.md) for folder layouts, DICOM/NIfTI conversion behavior, and validation helpers.

## Documentation Build

```bash
fyron docs-build
```

This runs the custom BF documentation generator and writes the static site under `site/`.
