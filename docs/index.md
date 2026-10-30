<section class="bf-shared-hero" aria-label="Fyron introduction">
  <h1 class="bf-sr-only">Fyron</h1>
  <img class="bf-shared-banner" src="assets/fyron-banner.svg" width="1600" height="600" alt="Fyron. A fireplace for research. Reusable tools. Shared knowledge. More time for the questions that matter. { Built by bits. Shaped by flames. } Pixel-art researchers and developers gathered around a campfire." fetchpriority="high">
  <div class="bf-shared-hero-tools">
    <div class="bf-fireplace-actions">
      <a class="bf-hero-button" href="getting-started/">Get started <span class="bf-pixel-arrow" aria-hidden="true"></span></a>
      <a class="bf-hero-link" href="reference/">Explore the API</a>
    </div>
    <div class="bf-code bf-hero-install">
      <div class="bf-code__bar"><strong>Bash</strong><span>Python 3.11+</span></div>
      <pre><code class="language-bash">uv add &quot;fyron @ https://github.com/BitsandFlames/Fyron/releases/download/v0.3.20b4/fyron-0.3.20b4-py3-none-any.whl&quot;</code></pre>
    </div>
  </div>

<aside class="bf-release-note" aria-label="Latest release">
  <a href="releases/v0.3.20b4/">v0.3.20b4 <span class="bf-pixel-arrow" aria-hidden="true"></span></a>
  <p>CC BY-NC 4.0 licensing for current Fyron and Curate source, authentication guides, and Curate dependency security updates. Earlier MIT permissions remain valid. Python 3.11+ is required. Read the release notes for changes and upgrade guidance.</p>
</aside>

<p class="bf-shared-intro">Fyron is a modular Python toolkit for healthcare data, medical imaging, and scientific analysis. Work with familiar DataFrames, arrays, and file paths to build workflows whose inputs, assumptions, and results remain inspectable.</p>
</section>

## Start Here

<div class="bf-docs-grid bf-docs-grid--featured bf-docs-grid--intro">
  <a class="bf-docs-card" href="getting-started/"><strong>Get started</strong><span>Install Fyron, choose the extras you need, and run your first workflow.</span></a>
  <a class="bf-docs-card" href="example-gallery/"><strong>Explore examples</strong><span>Learn from synthetic workflows before adapting them to your own research.</span></a>
  <a class="bf-docs-card" href="reference/"><strong>Find an API</strong><span>Look up function signatures, parameters, return values, and examples.</span></a>
</div>

## Choose Your Workflow

<div class="bf-docs-grid bf-docs-grid--featured">
  <a class="bf-docs-card" href="modules/fhir/"><strong>Work with clinical data</strong><span>Query FHIR endpoints and SQL tables, build resources, and map reviewed data to bundles.</span></a>
  <a class="bf-docs-card" href="modules/imaging/"><strong>Prepare medical images</strong><span>Read DICOM and NIfTI volumes, check geometry, and evaluate segmentation alignment.</span></a>
  <a class="bf-docs-card" href="applications/curate/"><strong>Curate image datasets</strong><span>Review images locally, record selection decisions, and export curated datasets.</span></a>
  <a class="bf-docs-card" href="modules/boa/"><strong>Extract BOA features</strong><span>Build body-composition and radiomics tables from existing BOA outputs.</span></a>
  <a class="bf-docs-card" href="clinical-ai-study-workflow/"><strong>Analyze and validate</strong><span>Connect cohort preparation, statistical analysis, survival models, and model validation.</span></a>
  <a class="bf-docs-card" href="examples/visual-figure-gallery/"><strong>Create scientific figures</strong><span>Explore plots for cohort summaries, survival, model performance, and imaging quality.</span></a>
</div>

See the [Modules Overview](modules/index.md) for the full toolkit, use the [Unified CLI](modules/cli.md) for repeatable terminal jobs, or install the [Fyron skill](agent-skill.md) for your AI assistant.

## The Scientific Workflow

| Stage | Fyron modules | Output |
| --- | --- | --- |
| Connect | `fhir`, `dicom`, `documents`, `core` | resources, files, and tables |
| Structure | `cohort`, `phenotyping`, `preprocessing` | analysis tables with explicit cohort and feature definitions |
| Extract | `imaging`, `boa_extraction`, `boa_radiomics` | imaging-derived measurements and feature tables |
| Analyze | `descriptive`, `statistics`, `survival`, `ml`, `feature_selection` | estimates, models, and summaries |
| Validate | `validation`, `explainability`, `imaging.segmentation` | model evaluation, explanations, and segmentation metrics |
| Report | `plotting`, `reporting`, `audit` | figures, tables, and provenance manifests |

The [Workflow Guide](workflow.md) explains how these steps fit together. Each module documents its inputs, outputs, assumptions, and common pitfalls.

## Research Use

Fyron is in [public beta](public-beta.md). Pin the version used for a study, preserve the analysis parameters, and review [Release History](releases/index.md) before upgrading. [Research Reliability](reliability.md) describes the available verification evidence and its limits.

Fyron supports research; it does not replace clinical validation, privacy review, or institutional approval. See [Using Fyron in Research](repository-trust.md) for reproducibility, data handling, and citation guidance, and [About Fyron](about.md) for the project's purpose.

## Citation

Please cite the version used in your work, including studies using **Fyron Curate**.

<div class="bf-citation">
<p>René Hosch, Katarzyna Borys, Sina Warmer, Jannis Straus, Kamyar Hartmann, and Justin Woolley (2026). <em>Fyron: An Open Research Companion for Healthcare Interoperability, Data Science and AI.</em> Version 0.3.20b4 [Computer software].</p>
<details class="bf-citation-bibtex">
<summary>BibTeX</summary>

```bibtex
@software{hosch_fyron_2026,
  author = {Hosch, Ren{\'e} and Borys, Katarzyna and Warmer, Sina and Straus, Jannis and Hartmann, Kamyar and Woolley, Justin},
  title = {Fyron: An Open Research Companion for Healthcare Interoperability, Data Science and AI},
  year = {2026},
  version = {0.3.20b4},
  url = {https://github.com/bitsandflames/fyron}
}
```

</details>
</div>

[Citation metadata](https://github.com/bitsandflames/fyron/blob/main/CITATION.cff) · [Research and citation guidance](repository-trust.md)

Citation is appreciated, not a license requirement.
