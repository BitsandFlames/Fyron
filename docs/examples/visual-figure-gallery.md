# Visual Figure Gallery

This page shows generated Fyron figure examples from synthetic data. The images demonstrate layout, annotation style, and manuscript-ready visual language; they are not clinical results.

Use this gallery to choose a plot family, then follow the linked module guide for parameters, return values, and export patterns.

## Gallery Coverage

The gallery is representative, not exhaustive. It covers the main clinical plotting families and uses synthetic data only, so the images demonstrate layout and style rather than clinical results.

## Survival

<div class="bf-figure-gallery">
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-km-at-risk.png" alt="Kaplan-Meier curve with at-risk table">
<figcaption><strong>Kaplan-Meier with at-risk counts</strong>Use for time-to-event group comparisons, censoring review, and log-rank summaries. See <a href="../../modules/survival/">Survival Analysis</a> and <a href="../../modules/plotting/#kaplan-meier-curves">Clinical Plotting</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-km-reference-bands.png" alt="Kaplan-Meier curves over survival reference bands">
<figcaption><strong>Kaplan-Meier reference bands</strong>Use for historical survival corridors, bootstrap percentile zones, or clinically defined favorable/intermediate/poor regions. See <a href="../../modules/plotting/#kaplan-meier-curves">Clinical Plotting</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-forest-estimates.png" alt="Forest plot with hazard ratio estimates">
<figcaption><strong>Forest estimates and hazard ratios</strong>Use for Cox terms, subgroup effects, odds ratios, or manuscript effect-size tables. See <a href="../../modules/plotting/#forest-plots-and-hazard-ratios">Forest Plots</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-directional-ratio-rows.png" alt="Directional ratio rows with protective and hazardous bands">
<figcaption><strong>Directional ratio rows</strong>Use for odds or hazard ratios when readers should see protective effects left of one and hazardous effects right of one. See <a href="../../modules/plotting/#directional-ratio-rows">Directional Ratio Rows</a>.</figcaption>
</figure>
</div>

## Model Discrimination

<div class="bf-figure-gallery">
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-roc-curve.png" alt="ROC curve">
<figcaption><strong>ROC curve</strong>Use for binary discrimination when predicted probabilities or scores rank patients. See <a href="../../modules/plotting/#model-evaluation-plot-set">Model Evaluation Plot Set</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-cv-roc.png" alt="Cross-validated ROC curves">
<figcaption><strong>Cross-validated ROC</strong>Use out-of-fold predictions to show fold-level ROC curves, mean AUC, and variability. See <a href="../../modules/plotting/#model-evaluation-plot-set">Model Evaluation Plot Set</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-precision-recall.png" alt="Precision-recall curve">
<figcaption><strong>Precision-recall curve</strong>Use when the endpoint is imbalanced and positive predictive value matters. See <a href="../../modules/plotting/#model-evaluation-plot-set">Model Evaluation Plot Set</a>.</figcaption>
</figure>
</div>

## Calibration And Thresholds

<div class="bf-figure-gallery">
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-calibration.png" alt="Calibration curve">
<figcaption><strong>Calibration curve</strong>Use to inspect whether predicted probabilities match observed risk. See <a href="../../modules/plotting/#model-evaluation-plot-set">Model Evaluation Plot Set</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-confusion-matrix.png" alt="Confusion matrix">
<figcaption><strong>Confusion matrix</strong>Use to explain thresholded model errors with TP, FP, FN, and TN counts. See <a href="../../modules/plotting/#model-evaluation-plot-set">Model Evaluation Plot Set</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-survival-calibration.png" alt="Survival calibration plot">
<figcaption><strong>Survival calibration</strong>Use for fixed-horizon survival or event-risk calibration checks. See <a href="../../modules/plotting/#validation-and-qc-plots">Validation And QC Plots</a>.</figcaption>
</figure>
</div>

## Validation And Decision Curves

<div class="bf-figure-gallery">
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-metric-bars.png" alt="Grouped model validation metric bars">
<figcaption><strong>Metric bars</strong>Use to compare AUC, sensitivity, specificity, F1, or external validation metrics across models. See <a href="../../modules/plotting/#model-and-validation-plots">Model And Validation Plots</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-external-validation.png" alt="External validation metric bars">
<figcaption><strong>External validation</strong>Use for compact external validation metric summaries. See <a href="../../modules/plotting/#validation-and-qc-plots">Validation And QC Plots</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-decision-curve.png" alt="Decision curve">
<figcaption><strong>Decision curve</strong>Use to compare net benefit across clinically meaningful thresholds. See <a href="../../modules/plotting/#validation-and-qc-plots">Validation And QC Plots</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-time-dependent-auc.png" alt="Time-dependent AUC curve">
<figcaption><strong>Time-dependent AUC</strong>Use for precomputed AUC values across follow-up horizons. See <a href="../../modules/plotting/#validation-and-qc-plots">Validation And QC Plots</a>.</figcaption>
</figure>
</div>

## Risk And Endpoint Bars

<div class="bf-figure-gallery">
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-risk-score-distribution.png" alt="Risk score distribution by event status">
<figcaption><strong>Risk score distribution</strong>Use to show how predicted risk separates event and non-event groups while preserving distribution shape. See <a href="../../modules/plotting/#risk-score-distribution">Risk Score Distribution</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-likert-scale.png" alt="Likert scale plot">
<figcaption><strong>Likert scale</strong>Use for reader studies, clinical expert surveys, usability ratings, and ordered response summaries. See <a href="../../modules/plotting/#likert-scale-plots">Likert Scale Plots</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-waffle.png" alt="Waffle plot">
<figcaption><strong>Waffle plot</strong>Use for cohort composition, class balance, endpoint mix, or review status summaries. See <a href="../../modules/plotting/#waffle-plots">Waffle Plots</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-patterned-bar.png" alt="Patterned endpoint rate bar plot">
<figcaption><strong>Patterned bar plot</strong>Use hatches with a named palette when endpoint or model bars must remain readable in grayscale. See <a href="../../modules/plotting/#patterned-bar-plot">Patterned Bar Plot</a>.</figcaption>
</figure>
</div>

## Feature Selection And Importance

<div class="bf-figure-gallery">
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-feature-importance.png" alt="Feature importance bar plot">
<figcaption><strong>Feature importance</strong>Use for top-N model importance summaries from tree or tabular models. See <a href="../../modules/plotting/#function-summary">Function Summary</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-feature-selection-summary.png" alt="Feature selection summary plot">
<figcaption><strong>Feature selection summary</strong>Use to show selected and rejected features from a selection table. See <a href="../../modules/plotting/#function-summary">Function Summary</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-stability-selection.png" alt="Stability selection frequency plot">
<figcaption><strong>Stability selection</strong>Use to show feature-selection frequencies and the chosen stability threshold. See <a href="../../modules/plotting/#function-summary">Function Summary</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-volcano.png" alt="Multi-group volcano plot">
<figcaption><strong>Volcano plot</strong>Use for omics, radiomics, or biomarker screening by effect size and p-value. See <a href="../../modules/plotting/#function-summary">Function Summary</a>.</figcaption>
</figure>
</div>

## Distributions

<div class="bf-figure-gallery">
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-reference-band-grid.png" alt="Reference band grid for body composition features by age and sex">
<figcaption><strong>Reference band grid</strong>Use for body composition, biological age, lab, imaging, or radiomics reference ranges across a continuous axis. See <a href="../../modules/plotting/#reference-band-grids">Reference Band Grids</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-qq-plot.png" alt="Q-Q plot comparing residual quantiles by cohort">
<figcaption><strong>Q-Q plot</strong>Use for checking whether residuals, biomarkers, or scores follow the expected normal-theory quantiles. See <a href="../../modules/plotting/#q-q-plots">Q-Q Plots</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-grouped-boxplot.png" alt="Grouped boxplot with statistical annotation">
<figcaption><strong>Grouped boxplot with annotation</strong>Use for compact group comparisons with patient-level points and statistical brackets. See <a href="../../modules/plotting/#grouped-boxplots-with-statistics">Grouped Boxplots</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-swarmplot.png" alt="Swarmplot with points by group and hue">
<figcaption><strong>Swarmplot</strong>Use when individual patient-level values should remain visible, especially in smaller cohorts. See <a href="../../modules/plotting/#density-histogram-and-swarm-plots">Distribution Plots</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-density.png" alt="Density curves grouped by event status">
<figcaption><strong>Density plot</strong>Use when a boxplot hides distribution shape or multimodality. See <a href="../../modules/plotting/#density-histogram-and-swarm-plots">Density Plots</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-filled-kde.png" alt="Filled two-dimensional KDE plot grouped by kind">
<figcaption><strong>Filled KDE plot</strong>Use when two continuous variables form dense clusters by group. See <a href="../../modules/plotting/#density-plots">Filled KDE Plot</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-histogram.png" alt="Histogram grouped by event status">
<figcaption><strong>Histogram</strong>Use when absolute counts or percentages across numeric bins matter for interpretation. See <a href="../../modules/plotting/#density-histogram-and-swarm-plots">Histograms</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-raincloud.png" alt="Raincloud distribution plot">
<figcaption><strong>Raincloud plot</strong>Use when distribution shape, summary interval, and patient-level values all need to remain visible. See <a href="../../modules/plotting/#function-summary">Function Summary</a>.</figcaption>
</figure>
</div>

## Agreement And Response

<div class="bf-figure-gallery">
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-bland-altman.png" alt="Bland-Altman agreement plot">
<figcaption><strong>Bland-Altman</strong>Use for agreement review between two measurement methods or model outputs. See <a href="../../modules/plotting/#function-summary">Function Summary</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-waterfall.png" alt="Waterfall response plot">
<figcaption><strong>Waterfall plot</strong>Use for ordered patient-level response, percent change, or risk-score change. See <a href="../../modules/plotting/#function-summary">Function Summary</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-swimmer.png" alt="Swimmer treatment timeline plot">
<figcaption><strong>Swimmer plot</strong>Use for patient-level treatment duration, response events, and oncology timelines. See <a href="../../modules/plotting/#function-summary">Function Summary</a>.</figcaption>
</figure>
</div>

## Missingness And Table Summaries

<div class="bf-figure-gallery">
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-missingness-bar.png" alt="Missingness bar plot">
<figcaption><strong>Missingness bar</strong>Use to communicate variable-level missingness before modeling or imputation. See <a href="../../modules/plotting/#function-summary">Function Summary</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-table-one-summary.png" alt="Table one p-value summary plot">
<figcaption><strong>Table 1 summary</strong>Use for a compact visual overview of Table 1 p-values. See <a href="../../modules/plotting/#function-summary">Function Summary</a>.</figcaption>
</figure>
</div>

## Statistical Annotations

<div class="bf-figure-gallery">
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-significance-bars.png" alt="Significance bars showing negative log p-values">
<figcaption><strong>Significance bars</strong>Use for p-value screening summaries, log-rank tests, or univariate feature checks. See <a href="../../modules/plotting/#significance-bars">Significance Bars</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-signed-feature-weights.png" alt="Signed feature weights with direction">
<figcaption><strong>Signed feature weights</strong>Use for model coefficients, risk direction, and compact feature contribution summaries. See <a href="../../modules/plotting/#signed-feature-weights">Signed Feature Weights</a>.</figcaption>
</figure>
</div>

## Segmentation QC

<div class="bf-figure-gallery">
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-dice-by-label.png" alt="Dice by label bar plot">
<figcaption><strong>Dice by label</strong>Use to summarize segmentation overlap metrics per organ, tissue, or label. See <a href="../../modules/plotting/#validation-and-qc-plots">Validation And QC Plots</a>.</figcaption>
</figure>
</div>

## Correlation And Cohort QC

<div class="bf-figure-gallery">
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-correlation-heatmap.png" alt="Correlation heatmap for clinical features">
<figcaption><strong>Correlation heatmap</strong>Use for exploratory feature correlation, leakage review, and manuscript supplement QC. See <a href="../../modules/plotting/#correlation-heatmaps">Correlation Heatmaps</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-cohort-flow.png" alt="Cohort flow bar plot">
<figcaption><strong>Cohort flow</strong>Use to report inclusion and exclusion counts from source cohort to final analysis set. See <a href="../../modules/flow/">Flow Explainability</a> and <a href="../../modules/plotting/#validation-cohort-and-imaging-qc-plots">Cohort Flow Plots</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-alluvial-flow.png" alt="Alluvial categorical flow plot">
<figcaption><strong>Alluvial flow</strong>Use for phenotype transitions, treatment sequences, or curation-state paths. See <a href="../../modules/plotting/#function-summary">Function Summary</a>.</figcaption>
</figure>
<figure class="bf-figure-card">
<img src="../../assets/figure-gallery-binned-marker-heatmap.png" alt="Binned marker heatmap">
<figcaption><strong>Binned marker heatmap</strong>Use for patient-feature marker panels with discrete risk or value bins. See <a href="../../modules/plotting/#function-summary">Function Summary</a>.</figcaption>
</figure>
</div>

## Regenerate The Gallery

The gallery assets are generated from code:

```bash
uv run python scripts/generate_plot_examples.py
uv run python scripts/build_docs.py
```

Keep the generated PNGs with the documentation source so the rendered site stays stable across environments.
