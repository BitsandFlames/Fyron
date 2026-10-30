# About Fyron

**A fireplace for research. A place for ideas to become working tools.**

Fyron is an source-available Python toolkit by [Bits & Flames](https://bitsandflames.ai/) for healthcare researchers, clinical data scientists, and imaging AI teams. It brings together practical tools for accessing data, preparing cohorts, reviewing images, analysing results, and documenting how you got there.

## Why we built it

A research question can start with a spark. Getting to the first experiment often means sorting files, rewriting a downloader, or finding a script from an earlier study. We have spent plenty of time there ourselves.

We built Fyron to share the useful parts of that work. A helper that saved one project a day might give another project its start. An example might answer a question, reveal a better approach, or inspire something we never imagined.

Whether Fyron helps you build your next study or simply gives you an idea, we hope it helps you bring that idea to life sooner. Take what helps, adapt it, and share what you learn.

## What you can do with it

| Research task | Start here |
| --- | --- |
| Access healthcare data | [FHIR REST and SQL](modules/fhir.md), [DICOM downloads](modules/dicom.md), [document downloads](modules/documents/downloader.md) |
| Prepare a study cohort | [Cohort construction](modules/cohort.md), [phenotyping](modules/phenotyping.md), [preprocessing](modules/preprocessing.md) |
| Work with images | [CT/MRI normalization and image I/O](modules/imaging.md), [Body and Organ Analysis](modules/boa.md), [dataset preparation](modules/datasets.md) |
| Review and select images locally | [Fyron Curate](applications/curate.md) |
| Explore and evaluate results | [Descriptive analysis](modules/descriptive.md), [survival analysis](modules/survival.md), [machine learning](modules/ml.md), [validation](modules/validation.md) |
| Communicate and document your work | [Plotting](modules/plotting.md), [reporting](modules/reporting.md), [provenance](modules/audit.md) |

Use one function or connect several modules. Fyron works with familiar Python tables and arrays, so you can inspect intermediate results and keep using the libraries you already know. Heavier optional tools are available through [dependency extras](getting-started.md).

## Built close to research

Bits & Flames brings together experience in healthcare, software development, and AI. Our tools grow from questions and recurring problems in our own work.

In Fyron, that means explicit inputs, visible assumptions, and outputs you can review. You choose the cohort definition, model, thresholds, and interpretation. Examples help you get started, while [API documentation](reference/index.md) explains the individual tools.

Fyron is in **public beta**. APIs and behaviour can change, so pin the version used for a study and read the [release history](releases/index.md) before upgrading. For citation, privacy, and reproducibility guidance, see [Using Fyron in Research](repository-trust.md).

## Bring your ideas

A contribution can be a small example, a clearer explanation, a reproducible bug, or a research problem that deserves a better tool. Share it through [GitHub issues](https://github.com/BitsandFlames/Fyron/issues) or the [contribution guide](https://github.com/BitsandFlames/Fyron/blob/main/CONTRIBUTING.md). Please use synthetic examples and keep patient data and credentials private.

[Get started](getting-started.md) · [Explore examples](example-gallery.md) · [Meet Bits & Flames](https://bitsandflames.ai/team)

**{ From Research. For Research. Built by Bits. Shaped by Flames. }**
