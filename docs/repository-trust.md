# Using Fyron in Research

**Make your methods understandable, your results traceable, and your data protected.**

Fyron supports research workflows, including image review with Curate. This page explains what to record for a study, how to cite the software, and what to consider before sharing results or asking for help.

## Record the version and methods

Fyron is in public beta. Pin the version used for your study and keep the analysis code, environment, and parameters together. Check the [release history](releases/index.md) before upgrading an ongoing project.

| Keep with your study | What to record |
| --- | --- |
| Software environment | Fyron version, Python version, dependencies, and your analysis code revision |
| Cohort definition | Source selection, inclusion and exclusion rules, joins, and endpoint definitions |
| Analysis settings | Feature preparation, model parameters, random seeds, thresholds, and validation design |
| Results | Tables, figures, uncertainty estimates, and relevant QC or extraction reports |
| Provenance | Input/output references and hashes, stored under the same access controls as the study data |

Use [cohort flow tracking](modules/flow.md) to document selection steps and [audit manifests](modules/audit.md) to record provenance. Review manifests and reports before sharing them: paths, identifiers, and metadata can reveal sensitive information. These tools do not automatically anonymize an artifact.

## Cite Fyron, including Curate

If Fyron contributes to a paper, thesis, or dataset, please cite the version you used. Curate uses the same software citation. In Methods, describe its role and the criteria used to accept or reject images.

> René Hosch, Katarzyna Borys, Sina Warmer, Jannis Straus, Kamyar Hartmann, and Justin Woolley. *Fyron: An Open Research Companion for Healthcare Interoperability, Data Science and AI.* Bits & Flames. Include the version and release year used in your study.

[Copy the current citation and BibTeX](index.md#citation) · [Download citation metadata](https://github.com/BitsandFlames/Fyron/blob/main/CITATION.cff) · [Curate citation guidance](applications/curate.md#citation)

If your release has a verified Zenodo record, use its version-specific DOI. A Git tag or citation file alone does not create a DOI. Citation is a scholarly request, not an additional license requirement.

## Know where your data goes

Local file and analysis workflows run on your machine. Configured clients can send requests to services such as FHIR, DICOMweb, S3, Teable, and LLM providers. Before using them with study data, check the destination, credentials, data handling, and your institution's requirements.

Curate is a local image review app. It supports dataset selection, but it is not a regulated clinical audit system. Fyron is not a medical device or a substitute for study approvals, privacy controls, or clinical validation.

Keep token caches and credentials outside shared datasets. Treat downloaded documents, clinical tables, images, and review exports as sensitive until reviewed under your study's data policy.

## Share a reproducible example safely

For public issues, pull requests, and screenshots, use a small **synthetic example** that reproduces the problem. Include the Fyron version, command or code, expected result, and observed behaviour.

Remove credentials, private endpoints, patient identifiers, clinical free text, identifying image metadata, and local paths that expose private projects. Do not attach real FHIR payloads, DICOM files, or provenance manifests without an appropriate review.

[Example Gallery](example-gallery.md) · [Report a bug](https://github.com/BitsandFlames/Fyron/issues) · [Report a security issue privately](https://github.com/BitsandFlames/Fyron/security/policy)

## Check the assumptions behind a result

FHIR profiles, imaging geometry, segmentation labels, and endpoint definitions vary between studies. Inspect extraction reports, missing values, units, and cohort counts before analysing the output. Choose statistical methods and validation designs that fit your research question.

Passing software tests does not establish clinical validity or guarantee that a method is appropriate for your data. See the [clinical study workflow](clinical-ai-study-workflow.md) for an example of keeping these decisions explicit.

## License

Current Fyron source, Curate's frontend and backend, and associated project documentation are available under **Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**. You may share and adapt the material for noncommercial purposes with appropriate credit, a license link, and an indication of changes. Noncommercial is not the same as research-only: research can be commercial, and noncommercial use can extend beyond research.

Because this license restricts commercial use, we describe the current source as **source available**, not OSI open source. For commercial permission beyond existing grants, contact [Bits & Flames](mailto:hello@bitsandflames.ai). Creative Commons recommends software-specific licenses for software; this project has chosen CC BY-NC 4.0, whose legal text governs this grant.

This change applies to the current development source and future distributions carrying the new license. **Previously published MIT versions, including v0.3.20b3, retain their MIT permissions.** Changing the current license cannot withdraw rights already granted for that material. Consult the license shipped with the exact version you use; resetting repository history does not change those permissions. Beta 4 is the first release carrying this license change.

Third-party dependencies, fonts, and separately licensed components retain their own licenses. Licensing does not imply clinical approval or grant trademark rights. The original MIT notice for previously licensed material is retained in NOTICE.

[Read CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) · [Full project license](https://github.com/BitsandFlames/Fyron/blob/main/LICENSE) · [Notices](https://github.com/BitsandFlames/Fyron/blob/main/NOTICE)
