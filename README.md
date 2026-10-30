![Fyron: a fireplace for research. Pixel-art researchers and developers gathered around a campfire.](https://fyron.bitsandflames.ai/assets/fyron-banner.png?v=0.3.20b4)

<p align="center">
  <a href="https://github.com/BitsandFlames/Fyron/releases/tag/v0.3.20b4"><img alt="Fyron 0.3.20b4 · beta" src="https://img.shields.io/badge/release-0.3.20b4%20%C2%B7%20beta-FF6A1A" /></a>
  <img alt="Supported Python versions" src="https://img.shields.io/pypi/pyversions/fyron?color=3776AB" />
  <img alt="CC BY-NC 4.0 license" src="https://img.shields.io/badge/license-CC_BY--NC_4.0-8B5CF6" />
</p>

<h3 align="center">Fyron</h3>
<p align="center"><strong>{ Built by bits. Shaped by Flames }</strong></p>

<p align="center">
  <a href="https://fyron.bitsandflames.ai/">[ Documentation ]</a>
  &nbsp; <a href="https://fyron.bitsandflames.ai/getting-started/">[ Getting Started ]</a>
  &nbsp; <a href="https://pypi.org/project/fyron/">[ PyPI ]</a>
  &nbsp; <a href="https://github.com/BitsandFlames/Fyron/blob/main/CITATION.cff">[ Citation ]</a>
  &nbsp; <a href="https://github.com/BitsandFlames/Fyron/blob/main/LICENSE">[ License ]</a>
</p>

---

## What it is

Fyron is a Python toolkit by **Bits & Flames**, built from our everyday work in healthcare research, clinical data science, and imaging AI. It is where we share the code, tools, and lessons we wish we had when we started. We hope they help you take an idea you care about and turn it into something you can explore, test, and share.

## Why we built it

We love the moment a research question starts to become a real project. We also know how much work sits between the two: connecting data, sorting files, preparing cohorts, and writing a script you are almost certain someone else has written before.

Fyron grew out of a simple wish: let's share more of that work. A useful function from one study might save someone days on the next. An example might suggest a new approach. Sometimes, seeing how someone else solved a problem is enough to get you moving again.

Whether Fyron helps you build your next project or simply gives you an idea, we hope it sparks something. Take what helps, make it your own, and spend more of your time exploring the questions that excite you. That is what our shared fireplace is for.

## What you can build

Fyron covers the journey from accessing healthcare data to sharing research results. Use it to prepare a study, review images, explore a question, or bring your findings together for a paper.

- **FHIR (`fhir`):** Query REST and SQL sources, build FHIR resources, and map reviewed tables to bundles.
- **DICOM (`dicom`):** Download DICOMweb studies, export synthetic imaging, and write DICOM SEG files.
- **Documents (`documents`):** Download PDFs and text reports with shared authentication, CSV batches, and custom document IDs.
- **Core I/O (`core`):** Read and write tables and files, load environment settings, and work with Teable and S3 storage.
- **Imaging (`imaging`):** Read DICOM and NIfTI, normalize CT and MRI, check geometry, and evaluate segmentation masks.
- **Datasets (`datasets`):** Generate synthetic examples and prepare nnU-Net v2 and YOLO training folders.
- **Body and Organ Analysis (`boa_extraction`):** Extract cohort measurements from existing BOA outputs with case-level reports.
- **BOA radiomics (`boa_radiomics`):** Calculate radiomic features from images and BOA segmentation masks.
- **Image visualization (`visualization`):** Create segmentation collages, aligned CT/MR difference maps, and previews for Curate.
- **Fyron Curate (`curate`):** Review images locally, accept or reject cases, save decisions, and export selected datasets.
- **Clinical codes (`clinical_codes`):** Work with ICD-10, OPS, MDC, Charlson comorbidity scores, and encounter indicators.
- **DataFrame helpers (`dataframe`):** Derive code indicators, date intervals, age, and time-window features.
- **Cohorts (`cohort`):** Join patient tables, construct endpoints, and audit joins and follow-up definitions.
- **Cohort flow (`flow`):** Track inclusion, exclusion, and query activity with inspectable counts and tables.
- **Phenotyping (`phenotyping`):** Define and combine explicit clinical rules for patient-level phenotypes.
- **Preprocessing (`preprocessing`):** Inspect missingness, impute and encode features, and check for leakage and split imbalance.
- **Descriptive analysis (`descriptive`):** Summarize cohorts with Table 1, standardized differences, and endpoint summaries.
- **Statistics (`statistics`):** Run statistical comparisons and estimate uncertainty with bootstrap confidence intervals.
- **Survival analysis (`survival`):** Fit Kaplan–Meier, Cox, AFT, and survival boosting models, with RMST and diagnostics.
- **Machine learning (`ml`):** Train classifiers, compare predictions, and produce performance metrics and figures.
- **Feature selection (`feature_selection`):** Compare univariate, correlation, model, permutation, Boruta, and stability methods.
- **Validation (`validation`):** Evaluate thresholds, calibration, subgroups, decision curves, and survival predictions.
- **Explainability (`explainability`):** Inspect models with permutation importance, partial dependence, and SHAP outputs.
- **LLM workflows (`llm`):** Apply prompts to text, files, images, DataFrames, and directories for reviewable annotations.
- **Scientific plotting (`plotting`):** Create figures for exploratory analysis, survival, model evaluation, and manuscripts.
- **Plot palettes (`plotting_palettes`):** Choose consistent scientific color schemes for figures.
- **Reporting (`reporting`):** Assemble baseline, metric, and cohort-flow tables for research reports.
- **Audit and provenance (`audit`):** Record file hashes and manifests to trace inputs, parameters, and outputs.
- **Command line (`cli`):** Run repeatable extraction, preparation, imaging, and audit workflows from the terminal.

Some workflows require optional dependency extras. The documentation explains what to install for each module.

Start with a single helper or put together a whole workflow. The synthetic examples give you somewhere to begin, with methods you can inspect and adapt as your project grows.

## Get started

Add Fyron to your project with **Python 3.11+**:

```bash
uv add "fyron @ https://github.com/BitsandFlames/Fyron/releases/download/v0.3.20b4/fyron-0.3.20b4-py3-none-any.whl"
```

This release is **0.3.20 Beta 4**. Pin your study's version and review methods and outputs for your research question. Software checks do not replace scientific validation.

Current Fyron and Curate source is **available under CC BY-NC 4.0** for noncommercial use with attribution. Commercial use beyond existing permissions requires separate permission. Previously published MIT versions, including Beta 3, retain their MIT permissions. See [licensing details](https://fyron.bitsandflames.ai/repository-trust/#license).

## Cite Fyron

If Fyron supports your research, including image selection with Curate, please acknowledge the people behind it:

> René Hosch, Katarzyna Borys, Sina Warmer, Jannis Straus, Kamyar Hartmann, and Justin Woolley (2026).
> **Fyron** (Version 0.3.20b4) [Computer software]. Bits & Flames.

```bibtex
@software{hosch_fyron_2026,
  author = {Hosch, Ren{\'e} and Borys, Katarzyna and Warmer, Sina and Straus, Jannis and Hartmann, Kamyar and Woolley, Justin},
  title = {Fyron: An Open Research Companion for Healthcare Interoperability, Data Science and AI},
  year = {2026},
  version = {0.3.20b4},
  url = {https://github.com/bitsandflames/fyron}
}
```
