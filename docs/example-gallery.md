# Example Gallery

Use this gallery to find a runnable synthetic workflow before adapting Fyron to private data.

The checkout also includes `examples/ingestion_workflow.py`: synthetic FHIR
bundles to an audited cohort without a server. It and the survival workflow run
against fresh wheel installations in the [reliability gates](reliability.md).

`examples/research_contracts.py` adds training-only preprocessing, explicit
phenotype populations, physical mask volumes, and separate internal/publication
provenance artifacts. Run it with `--output-dir /tmp/fyron-contracts`; it also runs
against installed wheels and requires no external services.

| Example | Shows | Main artifacts |
| --- | --- | --- |
| [Complete Survival Workflow](survival-workflow.md) | synthetic endpoints, predictor exclusions, Cox/AFT, PH diagnostics, and held-out validation | coefficient and calibration tables, KM figure |
| [FHIR To Cohort](examples/fhir-to-cohort.md) | public FHIR query to patient-level cohort shape | cohort DataFrame |
| [FHIR To Table One](examples/fhir-to-table-one.md) | FHIR-like rows to descriptive baseline table | Table 1 |
| [FHIR Paths & Custom Extraction](examples/fhir-paths-custom-extraction.md) | FHIRPath presets and custom extraction functions | flattened resource table |
| [DICOM BOA Validation](examples/dicom-boa-validation.md) | imaging-derived feature validation shape | feature table and validation metrics |
| [BOA Collages](examples/boa-collage.md) | CT/mask review collage | PNG review figure |
| [Volume Difference Heatmap](examples/volume-difference-heatmap.md) | aligned CT/MR slice difference visualization | figure and difference summary table |
| [Dataset Preparation](examples/dataset-preparation.md) | nnU-Net v2, YOLO classification, YOLO detection folder builders | dataset folders and manifests |
| [Cohort Flow Explainability](examples/cohort-flow-explainability.md) | decorated filters, joins, flow exports, model explanation | flow table, Markdown, figure |
| [Manuscript Statistics Workflow](examples/manuscript-statistics-workflow.md) | Table 1, FDR correction, regression, Cox diagnostics | manuscript-ready tables |
| [Survival PH Diagnostics Guide](examples/survival-ph-diagnostics-guide.md) | KM curves, Cox PH checks, Schoenfeld diagnostics, RMST, Weibull AFT | survival model diagnostics |
| [Manuscript Plotting Workflow](examples/manuscript-plotting-workflow.md) | statistical annotations, KM, forest plots, palettes | paper-ready figures |
| [Filled KDE Plot](examples/filled-kde-plot.md) | 2D filled KDE contours by group | Matplotlib figure |
| [Visual Figure Gallery](examples/visual-figure-gallery.md) | generated manuscript-style plot examples, including reference-band grids | PNG figure gallery |
| [Synthetic GAN Volume](examples/synthetic-gan-volume.md) | generated CT export to NIfTI and DICOM | image files and manifest |
| [DICOM SEG Export](examples/dicom-seg-export.md) | source-referenced segmentation export | DICOM SEG object |
| [FHIR Imaging Measurements](examples/fhir-imaging-measurement-bundle.md) | imaging-derived measurements as FHIR | FHIR JSON bundle |

## Visual Figure Examples

The generated figure previews now live on the [Visual Figure Gallery](examples/visual-figure-gallery.md). Use it to scan manuscript-style plots before choosing the right plotting helper.

## Choosing A Starting Point

| Goal | Start here |
| --- | --- |
| Understand the whole study shape | [Clinical AI Study Workflow](clinical-ai-study-workflow.md) |
| Prepare image folders for review | [Fyron Curate](applications/curate.md) |
| Compare module responsibilities | [Modules Overview](modules/index.md) |
| Learn function arguments quickly | [Function Reference](function-reference.md) |
| Prepare repository or manuscript trust material | [Using Fyron In Research](repository-trust.md) |
