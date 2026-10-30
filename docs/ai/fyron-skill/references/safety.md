# Fyron Safety Rules For Agents

Fyron is research software. It is not a medical device, clinical decision support product, compliance platform, or replacement for statistical review.

Always:

- Keep examples synthetic or de-identified.
- Avoid private endpoint URLs, credentials, accessions, MRNs, and patient-linked dates in prompts, comments, logs, screenshots, and generated docs.
- Ask for endpoint definitions when event coding, censoring, or time windows are unclear.
- Validate inputs before fitting models or drawing conclusions.
- Save outputs in inspectable formats: CSV, JSON, PNG/SVG, Markdown, notebooks, and provenance manifests.
- Warn before sending any real clinical text, FHIR bundle, DICOM metadata, or table rows to a commercial/non-local LLM.

Pause for human review when:

- inclusion/exclusion criteria are ambiguous,
- model output might influence patient care,
- PHI could leave the local machine,
- a workflow writes to a live FHIR endpoint,
- FHIR implementation guides or regulatory validation are required,
- DICOM SEG validity matters for downstream clinical systems,
- a statistical test depends on assumptions not visible in the data.

