# Fyron Module Map

Use this table to choose the first public API to inspect.

| Task | Python/API | CLI or docs |
| --- | --- | --- |
| FHIR REST search, paging, auth, bundle flattening | `fyron.FHIRRestClient`, `fyron.fhir.rest` | `fyron fhir-rest`, `/modules/fhir/rest/` |
| SQL-backed FHIR tables | `fyron.FHIRSQLClient`, `fyron.fhir.sql` | `/modules/fhir/sql/` |
| FHIR resources and bundles | `fyron.fhir.builder` | `fyron fhir-build-bundle`, `/modules/fhir/builder/` |
| Reviewed table to FHIR | `fyron.fhir.mapping` | `/modules/fhir/mapping/` |
| DICOMweb download | `fyron.DICOMDownloader`, `fyron.dicom` | `fyron dicom-download`, `/modules/dicom/` |
| DICOM SEG | `fyron.dicom.seg` | `fyron dicom-seg`, `/modules/dicom/seg/` |
| Local DICOM/NIfTI image I/O | `fyron.imaging` | `/modules/imaging/` |
| Image geometry and mask QC | `fyron.imaging.qc`, `fyron.imaging.segmentation` | `fyron imaging-qc` |
| Curate preview PNGs | `fyron.visualization.prepare_curate_image_previews` | `fyron dataset-curate-previews` |
| Curate app | `fyron.curate` launcher | `fyron curate`, `/applications/curate/` |
| BOA feature extraction | `fyron.boa_extraction` | `fyron boa-extract` |
| BOA radiomics | `fyron.boa_radiomics` | `fyron boa-radiomics` |
| BOA figures and collages | `fyron.visualization` | `/modules/visualization/` |
| CSV, Excel, JSON, env, S3 | `fyron.core`, `fyron.core.s3` | `/modules/core/` |
| ICD/OPS groups, MDC partitions, Charlson scores | `fyron.clinical_codes` | `/modules/clinical-codes/` |
| Dates and local code flags | `fyron.dataframe` | `/modules/dataframe/` |
| Cohort joins and endpoints | `fyron.cohort` | `/modules/cohort/` |
| Rule-based phenotypes | `fyron.phenotyping` | `/modules/phenotyping/` |
| Missingness, imputation, encoding, leakage | `fyron.preprocessing` | `/modules/preprocessing/` |
| Descriptive summaries and Table 1 | `fyron.descriptive`, `fyron.reporting` | `/modules/descriptive/` |
| Inclusion/exclusion flows | `fyron.flow` | `/modules/flow/` |
| Statistical tests and effect sizes | `fyron.statistics` | `/modules/statistics/` |
| Survival analysis | `fyron.survival` | `/modules/survival/` |
| Machine learning | `fyron.ml` | `/modules/ml/` |
| Feature selection | `fyron.feature_selection` | `/modules/feature-selection/` |
| Model validation | `fyron.validation` | `/modules/validation/` |
| Explainability | `fyron.explainability` | `/modules/explainability/` |
| Clinical figures | `fyron.plotting` | `/modules/plotting/`, `/examples/visual-figure-gallery/` |
| Provenance | `fyron.audit` | `fyron audit-manifest`, `/modules/audit/` |
| LLM wrappers | `fyron.llm` | `/modules/llm/` |

Default to DataFrame-first workflows where possible. Prefer named outputs and saved artifacts over implicit side effects.
