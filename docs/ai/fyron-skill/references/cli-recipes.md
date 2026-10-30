# Fyron CLI Recipes

Use the unified `fyron` command for repeatable workflows.

FHIR REST:

```bash
fyron fhir-rest --base-url "$FHIR_BASE_URL" --resource Patient --output patients.csv
```

FHIR bundle from table:

```bash
fyron fhir-build-bundle \
  --input observations.csv \
  --mapping mapping.json \
  --resource Observation \
  --subject-col patient_id \
  --output bundle.json
```

DICOMweb download:

```bash
fyron dicom-download \
  --dicom-web-url "$DICOM_WEB_URL" \
  --study-uid "$STUDY_UID" \
  --output-dir dicom_out
```

Document download with browser-approved OIDC authentication:

```bash
fyron document-download \
  --url 'https://documents.example.org/reports/synthetic-001/pdf' \
  --output documents_out/report.pdf --pdf \
  --auth-type device_code \
  --auth-url 'https://identity.example.org/realms/research' \
  --client-id research-documents-cli \
  --scope 'openid user/DocumentReference.rs'
```

These endpoints and identifiers are fictional. Omit `--pdf` for `text/plain`
or mixed PDF/text batches. Use `--csv documents.csv --output-dir documents_out`
instead of `--url` and `--output` for batches. Client secrets belong in an
environment variable named by `--client-secret-env`, never in command-line values.

DICOM SEG:

```bash
fyron dicom-seg \
  --mask mask.nii.gz \
  --source-dicom dicom/ \
  --segments segments.json \
  --output mask.seg.dcm \
  --validate
```

Curate previews and app:

```bash
fyron dataset-curate-previews --input-dir imaging_exports/ --output-dir curate_previews/
fyron curate
```

BOA:

```bash
fyron boa-extract --cohort-folder boa/ --output body_regions.csv --include-body-regions --include-total
fyron boa-radiomics --cohort-folder boa/ --segmentation total --output radiomics.csv
```

Imaging QC:

```bash
fyron imaging-qc --nifti image.nii.gz --mask mask.nii.gz --output qc.csv
```

Provenance:

```bash
fyron audit-manifest \
  --title "Analysis" \
  --input data/features.csv \
  --output results/metrics.csv \
  --write results/provenance.json
```

Global flags:

```bash
fyron --quiet ...
fyron --verbose ...
fyron --no-color ...
fyron --json-log ...
fyron --no-progress ...
```
