#!/usr/bin/env python3
"""Build the BF-native Fyron documentation site.

The generator intentionally uses only the Python standard library. Markdown
files stay as the source of truth, while the rendered site uses a small custom
layout that matches the Bits & Flames application style.
"""

from __future__ import annotations

import html
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SITE = ROOT / "site"


@dataclass(frozen=True)
class Page:
    title: str
    source: str
    output: str
    group: str
    parent: str | None = None


def release_sort_key(source: Path) -> tuple[int, int, int, int, int]:
    """Order release pages numerically, with prereleases before the final release."""
    match = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)(?:(a|b|rc)(\d+))?", source.stem)
    if match is None:
        raise ValueError(f"Unsupported release page version: {source.name}")
    major, minor, patch, stage, sequence = match.groups()
    return (int(major), int(minor), int(patch),
            {"a": 0, "b": 1, "rc": 2, None: 3}[stage], int(sequence or 0))


PAGES = [
    Page("Home", "index.md", "index.html", "Start"),
    Page("About Fyron", "about.md", "about/index.html", "Start"),
    Page("Getting Started", "getting-started.md", "getting-started/index.html", "Start"),
    Page("Release History", "releases/index.md", "releases/index.html", "Start"),
    Page("Public Beta", "public-beta.md", "public-beta/index.html", "Start", parent="about/index.html"),
    Page("API Design", "api-design.md", "api-design/index.html", "Start", parent="about/index.html"),
    Page("Installation & Extras", "installation.md", "installation/index.html", "Start", parent="getting-started/index.html"),
    Page("Modules Overview", "modules/index.md", "modules/index.html", "Start", parent="getting-started/index.html"),
    Page("Workflow Guide", "workflow.md", "workflow/index.html", "Start", parent="getting-started/index.html"),
    Page("Clinical AI Study Workflow", "clinical-ai-study-workflow.md", "clinical-ai-study-workflow/index.html", "Start", parent="getting-started/index.html"),
    Page("Survival Workflow", "survival-workflow.md", "survival-workflow/index.html", "Start", parent="getting-started/index.html"),
    Page("FHIR To DataFrame Quickstart", "quickstarts/fhir-rest-to-dataframe.md", "quickstarts/fhir-rest-to-dataframe/index.html", "Start", parent="getting-started/index.html"),
    Page("Curate Review Quickstart", "quickstarts/curate-image-review.md", "quickstarts/curate-image-review/index.html", "Start", parent="getting-started/index.html"),
    Page("Survival Quickstart", "quickstarts/survival-analysis.md", "quickstarts/survival-analysis/index.html", "Start", parent="getting-started/index.html"),
    Page("Plotting Gallery Quickstart", "quickstarts/plotting-gallery.md", "quickstarts/plotting-gallery/index.html", "Start", parent="getting-started/index.html"),
    *[
        Page(f"Release {source.stem[1:]}", f"releases/{source.name}", f"releases/{source.stem}/index.html", "Start", parent="releases/index.html")
        for source in sorted(
            (DOCS / "releases").glob("v[0-9]*.md"),
            key=release_sort_key,
            reverse=True,
        )
    ],
    Page("Unified CLI", "modules/cli.md", "modules/cli/index.html", "CLI"),
    Page("Choose your authentication", "authentication/index.md", "authentication/index.html", "Authentication"),
    Page("FHIR REST", "authentication/fhir-rest.md", "authentication/fhir-rest/index.html", "Authentication"),
    Page("DICOMweb", "authentication/dicomweb.md", "authentication/dicomweb/index.html", "Authentication"),
    Page("Documents", "authentication/documents.md", "authentication/documents/index.html", "Authentication"),
    Page("SQL", "authentication/sql.md", "authentication/sql/index.html", "Authentication"),
    Page("Core I/O", "modules/core.md", "modules/core/index.html", "Clinical Data"),
    Page("FHIR", "modules/fhir.md", "modules/fhir/index.html", "Clinical Data"),
    Page("FHIR REST", "modules/fhir/rest.md", "modules/fhir/rest/index.html", "Clinical Data", parent="modules/fhir/index.html"),
    Page("FHIR SQL", "modules/fhir/sql.md", "modules/fhir/sql/index.html", "Clinical Data", parent="modules/fhir/index.html"),
    Page("FHIR Builder", "modules/fhir/builder.md", "modules/fhir/builder/index.html", "Clinical Data", parent="modules/fhir/index.html"),
    Page("FHIR Mapping", "modules/fhir/mapping.md", "modules/fhir/mapping/index.html", "Clinical Data", parent="modules/fhir/index.html"),
    Page("DICOM", "modules/dicom.md", "modules/dicom/index.html", "Clinical Data"),
    Page("DICOMDownloader", "modules/dicom/downloader.md", "modules/dicom/downloader/index.html", "Clinical Data", parent="modules/dicom/index.html"),
    Page("Synthetic Export", "modules/dicom/synthetic.md", "modules/dicom/synthetic/index.html", "Clinical Data", parent="modules/dicom/index.html"),
    Page("DICOM SEG", "modules/dicom/seg.md", "modules/dicom/seg/index.html", "Clinical Data", parent="modules/dicom/index.html"),
    Page("Documents", "modules/documents.md", "modules/documents/index.html", "Clinical Data"),
    Page("DocumentDownloader", "modules/documents/downloader.md", "modules/documents/downloader/index.html", "Clinical Data", parent="modules/documents/index.html"),
    Page("Cohort Tables", "modules/cohort.md", "modules/cohort/index.html", "Clinical Data"),
    Page("Phenotyping", "modules/phenotyping.md", "modules/phenotyping/index.html", "Clinical Data"),
    Page("Clinical Codes", "modules/clinical-codes.md", "modules/clinical-codes/index.html", "Clinical Data"),
    Page("DataFrame Operations", "modules/dataframe.md", "modules/dataframe/index.html", "Clinical Data"),
    Page("Imaging", "modules/imaging.md", "modules/imaging/index.html", "Imaging"),
    Page("Body and Organ Analysis", "modules/boa.md", "modules/boa/index.html", "Body and Organ Analysis"),
    Page("Extraction", "modules/boa-extraction.md", "modules/boa-extraction/index.html", "Body and Organ Analysis", parent="modules/boa/index.html"),
    Page("Radiomics", "modules/boa-radiomics.md", "modules/boa-radiomics/index.html", "Body and Organ Analysis", parent="modules/boa/index.html"),
    Page("Visualization", "modules/visualization.md", "modules/visualization/index.html", "Body and Organ Analysis", parent="modules/boa/index.html"),
    Page("Datasets", "modules/datasets.md", "modules/datasets/index.html", "Datasets"),
    Page("Preprocessing QC", "modules/preprocessing.md", "modules/preprocessing/index.html", "Analysis"),
    Page("Descriptive Analysis", "modules/descriptive.md", "modules/descriptive/index.html", "Analysis"),
    Page("Statistics", "modules/statistics.md", "modules/statistics/index.html", "Analysis"),
    Page("Survival Analysis", "modules/survival.md", "modules/survival/index.html", "Analysis"),
    Page("Machine Learning", "modules/ml.md", "modules/ml/index.html", "Analysis"),
    Page("Feature Selection", "modules/feature-selection.md", "modules/feature-selection/index.html", "Analysis"),
    Page("Model Validation", "modules/validation.md", "modules/validation/index.html", "Analysis"),
    Page("Explainability", "modules/explainability.md", "modules/explainability/index.html", "Analysis"),
    Page("Cohort Flow Tracking", "modules/flow.md", "modules/flow/index.html", "Analysis"),
    Page("LLM", "modules/llm.md", "modules/llm/index.html", "LLMs/Agents"),
    Page("Skills", "agent-skill.md", "agent-skill/index.html", "LLMs/Agents"),
    Page("SKILL.md", "ai/fyron-skill/SKILL.md", "agents/skill/index.html", "LLMs/Agents"),
    Page("AI Assistant Guide", "agents.md", "agents/index.html", "LLMs/Agents"),
    Page("Clinical Plotting", "modules/plotting.md", "modules/plotting/index.html", "Publication"),
    Page("Colors & Styles", "colors.md", "colors/index.html", "Publication"),
    Page("Reporting", "modules/reporting.md", "modules/reporting/index.html", "Publication"),
    Page("Provenance Manifests", "modules/audit.md", "modules/audit/index.html", "Audit & Provenance"),
    Page("Safe Network Diagnostics", "diagnostics.md", "diagnostics/index.html", "Audit & Provenance"),
    Page("Research Reliability", "reliability.md", "reliability/index.html", "Audit & Provenance"),
    Page("Using Fyron in Research", "repository-trust.md", "repository-trust/index.html", "Audit & Provenance"),
    Page("Overview", "applications/curate.md", "applications/curate/index.html", "Curate"),
    Page("Start the app", "applications/curate/start.md", "applications/curate/start/index.html", "Curate"),
    Page("Prepare your data", "applications/curate/prepare-data.md", "applications/curate/prepare-data/index.html", "Curate"),
    Page("Review & export", "applications/curate/review-export.md", "applications/curate/review-export/index.html", "Curate"),
    Page("Example Gallery", "example-gallery.md", "example-gallery/index.html", "Examples"),
    Page("Clinical Data Science", "examples/clinical-data-science.md", "examples/clinical-data-science/index.html", "Examples", parent="example-gallery/index.html"),
    Page("FHIR to Cohort", "examples/fhir-to-cohort.md", "examples/fhir-to-cohort/index.html", "Examples", parent="example-gallery/index.html"),
    Page("FHIR To Table One", "examples/fhir-to-table-one.md", "examples/fhir-to-table-one/index.html", "Examples", parent="example-gallery/index.html"),
    Page("DICOM BOA Validation", "examples/dicom-boa-validation.md", "examples/dicom-boa-validation/index.html", "Examples", parent="example-gallery/index.html"),
    Page("Manuscript Workflow", "examples/manuscript-workflow.md", "examples/manuscript-workflow/index.html", "Examples", parent="example-gallery/index.html"),
    Page("Manuscript Statistics Workflow", "examples/manuscript-statistics-workflow.md", "examples/manuscript-statistics-workflow/index.html", "Examples", parent="example-gallery/index.html"),
    Page("Survival PH Diagnostics Guide", "examples/survival-ph-diagnostics-guide.md", "examples/survival-ph-diagnostics-guide/index.html", "Examples", parent="example-gallery/index.html"),
    Page("Manuscript Plotting Workflow", "examples/manuscript-plotting-workflow.md", "examples/manuscript-plotting-workflow/index.html", "Examples", parent="example-gallery/index.html"),
    Page("Filled KDE Plot", "examples/filled-kde-plot.md", "examples/filled-kde-plot/index.html", "Examples", parent="example-gallery/index.html"),
    Page("Visual Figure Gallery", "examples/visual-figure-gallery.md", "examples/visual-figure-gallery/index.html", "Examples", parent="example-gallery/index.html"),
    Page("Dataset Preparation", "examples/dataset-preparation.md", "examples/dataset-preparation/index.html", "Examples", parent="example-gallery/index.html"),
    Page("Cohort Flow Explainability", "examples/cohort-flow-explainability.md", "examples/cohort-flow-explainability/index.html", "Examples", parent="example-gallery/index.html"),
    Page("FHIR Paths & Custom Extraction", "examples/fhir-paths-custom-extraction.md", "examples/fhir-paths-custom-extraction/index.html", "Examples", parent="example-gallery/index.html"),
    Page("FHIR LLM Evidence", "examples/fhir-llm-extracted-evidence.md", "examples/fhir-llm-extracted-evidence/index.html", "Examples", parent="example-gallery/index.html"),
    Page("FHIR Imaging Measurements", "examples/fhir-imaging-measurement-bundle.md", "examples/fhir-imaging-measurement-bundle/index.html", "Examples", parent="example-gallery/index.html"),
    Page("FHIR DataFrame Observations", "examples/fhir-dataframe-to-observations.md", "examples/fhir-dataframe-to-observations/index.html", "Examples", parent="example-gallery/index.html"),
    Page("FHIR LLM Table Bundle", "examples/fhir-llm-table-to-bundle.md", "examples/fhir-llm-table-to-bundle/index.html", "Examples", parent="example-gallery/index.html"),
    Page("FHIR BOA Measurements", "examples/fhir-boa-measurements-to-bundle.md", "examples/fhir-boa-measurements-to-bundle/index.html", "Examples", parent="example-gallery/index.html"),
    Page("BOA Collages", "examples/boa-collage.md", "examples/boa-collage/index.html", "Examples", parent="example-gallery/index.html"),
    Page("Volume Difference Heatmaps", "examples/volume-difference-heatmap.md", "examples/volume-difference-heatmap/index.html", "Examples", parent="example-gallery/index.html"),
    Page("Synthetic GAN Volume", "examples/synthetic-gan-volume.md", "examples/synthetic-gan-volume/index.html", "Examples", parent="example-gallery/index.html"),
    Page("DICOM SEG Export", "examples/dicom-seg-export.md", "examples/dicom-seg-export/index.html", "Examples", parent="example-gallery/index.html"),
    Page("Function Reference", "function-reference.md", "function-reference/index.html", "Reference"),
    Page("Complete Function Reference", "reference/index.md", "reference/index.html", "Reference"),
    Page("Docstring Coverage", "reference/docstring-coverage.md", "reference/docstring-coverage/index.html", "Reference", parent="reference/index.html"),
    Page("FHIR Reference", "reference/fhir.md", "reference/fhir/index.html", "Reference", parent="reference/index.html"),
    Page("DICOM And Imaging Reference", "reference/dicom-imaging.md", "reference/dicom-imaging/index.html", "Reference", parent="reference/index.html"),
    Page("BOA Reference", "reference/boa.md", "reference/boa/index.html", "Reference", parent="reference/index.html"),
    Page("Cohort And Analysis Reference", "reference/cohort-analysis.md", "reference/cohort-analysis/index.html", "Reference", parent="reference/index.html"),
    Page("Survival Reference", "reference/survival.md", "reference/survival/index.html", "Reference", parent="reference/index.html"),
    Page("ML, Validation, And Explainability Reference", "reference/ml-validation.md", "reference/ml-validation/index.html", "Reference", parent="reference/index.html"),
    Page("Core, Publication, And Utility Reference", "reference/core-publication.md", "reference/core-publication/index.html", "Reference", parent="reference/index.html"),
]


# Curated workflow shortcuts keep long module pages reachable without putting
# their complete heading lists in the sidebar. Anchors are checked at build time.
SECTION_NAV = {
    "modules/llm/index.html": (
        ("Configure LLMAgent", "llmagent"),
        ("Prompts & chat", "prompt-chat"),
        ("DataFrame prompts", "promptdataframe"),
        ("Document prompts", "promptdocuments"),
        ("Directory prompts", "promptdirectory"),
    ),
    "agent-skill/index.html": (
        ("Download skill package", "download"),
        ("Choose your assistant", "choose-your-assistant"),
        ("Example prompt", "example-prompt"),
    ),
    "agents/skill/index.html": (
        ("Coding rules", "coding-rules"),
        ("Canonical patterns", "canonical-patterns"),
        ("Reference files", "reference-files"),
    ),
    "agents/index.html": (
        ("Quick-start prompt", "quick-start-prompt"),
        ("Prompt recipes", "hands-on-prompt-recipes"),
        ("Review generated code", "review-checklist"),
    ),
    "modules/audit/index.html": (
        ("Create a manifest", "minimal-example"),
        ("CLI workflow", "cli-workflow"),
        ("What to record", "what-to-record"),
        ("Publication summaries", "internal-records-and-publication-summaries"),
    ),
    "diagnostics/index.html": (
        ("Errors & sensitive outputs", "errors-and-sensitive-outputs"),
        ("Batch completion", "batch-completion"),
    ),
    "modules/datasets/index.html": (
        ("nnU-Net v2", "nnu-net-v2-preparation"),
        ("YOLO classification", "yolo-classification-preparation"),
        ("YOLO detection", "yolo-object-detection-preparation"),
        ("Validate datasets", "validation"),
        ("Tools & repositories", "tools-and-repositories"),
    ),
    "modules/boa/index.html": (
        ("BOA CT & BOA MR", "upstream-tools-and-repositories"),
        ("Input folders", "boa-folder-pattern"),
        ("Extraction reports", "check-coverage-before-joining"),
    ),
    "modules/boa-extraction/index.html": (
        ("Cohort extraction", "extract-a-cohort-table"),
        ("Labels & feature families", "customize-labels-and-feature-families"),
        ("Derived markers", "customize-derived-markers"),
        ("Clinical joins", "join-with-clinical-data"),
    ),
    "modules/boa-radiomics/index.html": (
        ("Organ radiomics", "extract-total-segmentation-radiomics"),
        ("Body-region radiomics", "extract-body-region-radiomics"),
        ("Custom extractor", "custom-pyradiomics-extractor"),
    ),
    "modules/visualization/index.html": (
        ("Segmentation collages", "generic-segmentation-collage"),
        ("Curate previews", "curate-preview-preparation"),
        ("Body-region cropping", "body-region-cropping"),
        ("CT/MR difference maps", "volume-difference-heatmaps"),
    ),
    "modules/imaging/index.html": (
        ("CT normalization · normalize_ct", "normalizect"),
        ("MRI normalization · normalize_mr", "normalizemr"),
        ("DICOM headers · read_dicom_header", "readdicomheader"),
        ("Find series · get_dicom_series_ids", "getdicomseriesids"),
        ("Read DICOM · read_dicom_series", "readdicomseries"),
        ("Read NIfTI · read_nifti", "readnifti"),
        ("Write NIfTI · write_nifti", "writenifti"),
        ("Imaging QC", "imaging-qc-helpers"),
        ("Segmentation metrics", "segmentation-metrics"),
    ),
    "modules/preprocessing/index.html": (
        ("Imputation", "imputation"),
        ("Encoding", "encoding"),
        ("Train/evaluation example", "executable-trainevaluation-example"),
    ),
    "modules/survival/index.html": (
        ("Kaplan–Meier", "kaplan-meier-curves"),
        ("Restricted mean survival", "restricted-mean-survival-time"),
        ("Cox regression", "cox-regression"),
        ("PH diagnostics", "proportional-hazards-diagnostics"),
        ("Weibull AFT", "weibull-aft"),
        ("Survival boosting", "gradient-survival-boosting"),
    ),
    "modules/ml/index.html": (
        ("Train/test split", "traintest-split"),
        ("Random forest", "random-forest"),
        ("XGBoost", "xgboost"),
        ("Cross-validation", "cross-validation"),
        ("External validation", "external-validation-and-calibration"),
    ),
    "applications/curate/index.html": (
        ("Example gallery", "explore-curate-with-example-data"),
        ("Try the example cohort", "try-the-example-cohort"),
        ("Citation", "citation"),
    ),
    "applications/curate/start/index.html": (
        ("Install", "install"),
        ("Stop and restart", "stop-and-restart-safely"),
        ("Troubleshooting", "troubleshooting"),
    ),
    "applications/curate/prepare-data/index.html": (
        ("Accepted formats", "accepted-uploads-and-preview-limits"),
        ("Folder layout", "organize-an-image-folder"),
        ("Bash", "bash"),
        ("Python", "python"),
        ("Preview decisions", "understand-what-a-preview-decision-means"),
    ),
    "applications/curate/review-export/index.html": (
        ("Review", "create-and-review-a-cohort"),
        ("Exports", "choose-an-export"),
        ("Find files", "locate-exported-files"),
    ),
}


def slugify(value: str) -> str:
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = value.lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"\s+", "-", value).strip("-")
    return value or "section"


def page_dir(page: Page) -> Path:
    return Path(page.output).parent


def url_to(from_page: Page, target_output: str) -> str:
    start = SITE / page_dir(from_page)
    dest = SITE / target_output
    return path_relative(dest, start)


def asset_url(from_page: Page, asset: str) -> str:
    return path_relative(SITE / "assets" / asset, SITE / page_dir(from_page))


def path_relative(dest: Path, start: Path) -> str:
    return Path(os.path.relpath(dest, start)).as_posix()


OUTPUT_BY_SOURCE = {page.source: page.output for page in PAGES}


def rewrite_href(href: str, current: Page) -> str:
    if href.startswith(("http://", "https://", "#", "mailto:")):
        return href
    clean = href
    anchor = ""
    if "#" in clean:
        clean, anchor = clean.split("#", 1)
        anchor = f"#{anchor}"
    if clean.startswith("../assets/"):
        asset = clean.removeprefix("../assets/")
        return f"{asset_url(current, asset)}{anchor}"
    if clean.startswith("assets/"):
        asset = clean.removeprefix("assets/")
        return f"{asset_url(current, asset)}{anchor}"
    source_path = os.path.normpath(Path(current.source).parent / clean).replace("\\", "/")
    if source_path.startswith("assets/"):
        return f"{asset_url(current, source_path.removeprefix('assets/'))}{anchor}"
    if source_path in OUTPUT_BY_SOURCE:
        return f"{url_to(current, OUTPUT_BY_SOURCE[source_path])}{anchor}"
    clean = clean.lstrip("./")
    if clean.endswith(".md") and clean in OUTPUT_BY_SOURCE:
        return f"{url_to(current, OUTPUT_BY_SOURCE[clean])}{anchor}"
    return href


def inline(text: str, current: Page) -> str:
    placeholders: list[str] = []

    def keep_code(match: re.Match[str]) -> str:
        placeholders.append(f"<code>{html.escape(match.group(1))}</code>")
        return f"\u0000{len(placeholders) - 1}\u0000"

    def keep_image(match: re.Match[str]) -> str:
        alt = html.escape(match.group(1))
        src = html.escape(rewrite_href(match.group(2), current))
        placeholders.append(f'<img class="bf-doc-image" src="{src}" alt="{alt}">')
        return f"\u0000{len(placeholders) - 1}\u0000"

    text = re.sub(r"`([^`]+)`", keep_code, text)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", keep_image, text)
    text = html.escape(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)

    def link(match: re.Match[str]) -> str:
        label = match.group(1)
        href = rewrite_href(match.group(2), current)
        return f'<a href="{html.escape(href)}">{label}</a>'

    text = re.sub(r"(?<!!)\[([^\]]+)\]\(([^)]+)\)", link, text)
    for index, value in enumerate(placeholders):
        text = text.replace(f"\u0000{index}\u0000", value)
    return text


def render_table(lines: list[str], current: Page) -> str:
    headers = [cell.strip() for cell in lines[0].strip().strip("|").split("|")]
    rows = []
    for line in lines[2:]:
        rows.append([cell.strip() for cell in line.strip().strip("|").split("|")])
    out = ["<div class=\"bf-table-wrap\"><table>"]
    out.append("<thead><tr>")
    out.extend(f"<th>{inline(cell, current)}</th>" for cell in headers)
    out.append("</tr></thead><tbody>")
    for row in rows:
        out.append("<tr>")
        out.extend(f"<td>{inline(cell, current)}</td>" for cell in row)
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


def is_table_start(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    return "|" in lines[index] and re.match(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$", lines[index + 1]) is not None


def render_markdown(markdown: str, current: Page) -> tuple[str, list[dict[str, str]], str]:
    lines = markdown.splitlines()
    if lines and lines[0] == "---":
        # Skill metadata stays in the downloadable source, outside the article.
        metadata_end = lines.index("---", 1)
        lines = lines[metadata_end + 1:]
    out: list[str] = []
    toc: list[dict[str, str]] = []
    plain_parts: list[str] = []
    i = 0
    used_ids: set[str] = set()

    while i < len(lines):
        line = lines[i]

        if not line.strip():
            i += 1
            continue

        if line.startswith("```"):
            language = line.strip().strip("`") or "text"
            i += 1
            code: list[str] = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            out.append(
                f'<div class="bf-code"><div class="bf-code__bar"><div class="bf-code__dots" aria-hidden="true"><span></span><span></span><span></span></div><div class="bf-code__actions"><strong>{html.escape(language)}</strong>'
                '<button class="bf-code__copy" type="button" aria-label="Copy code" title="Copy code" data-copy-code>'
                '<svg aria-hidden="true" viewBox="0 0 24 24" width="16" height="16">'
                '<path data-copy-icon fill="currentColor" d="M16 1H5a2 2 0 0 0-2 2v13h2V3h11V1Zm3 4H9a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2Zm0 16H9V7h10v14Z"/>'
                '</svg><span class="bf-code__copy-label">Copy</span></button></div></div>'
                f'<pre><code>{html.escape(chr(10).join(code))}</code></pre></div>'
            )
            plain_parts.append(" ".join(code))
            continue

        if is_table_start(lines, i):
            table_lines = [line, lines[i + 1]]
            i += 2
            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                table_lines.append(lines[i])
                i += 1
            out.append(render_table(table_lines, current))
            plain_parts.append(" ".join(table_lines))
            continue

        heading = re.match(r"^(#{1,4})\s+(.+)$", line)
        if heading:
            level = len(heading.group(1))
            title = heading.group(2).strip()
            base_id = slugify(title)
            element_id = base_id
            suffix = 2
            while element_id in used_ids:
                element_id = f"{base_id}-{suffix}"
                suffix += 1
            used_ids.add(element_id)
            if level in (2, 3):
                toc.append({"level": str(level), "title": re.sub(r"`", "", title), "id": element_id})
            out.append(f'<h{level} id="{element_id}">{inline(title, current)}</h{level}>')
            plain_parts.append(title)
            i += 1
            continue

        if re.match(r"^\s*[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                text = re.sub(r"^\s*[-*]\s+", "", lines[i])
                items.append(f"<li>{inline(text, current)}</li>")
                plain_parts.append(text)
                i += 1
            out.append(f"<ul>{''.join(items)}</ul>")
            continue

        if re.match(r"^\s*\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                text = re.sub(r"^\s*\d+\.\s+", "", lines[i])
                items.append(f"<li>{inline(text, current)}</li>")
                plain_parts.append(text)
                i += 1
            out.append(f"<ol>{''.join(items)}</ol>")
            continue

        if line.lstrip().startswith("<"):
            out.append(line.replace(' markdown', ""))
            i += 1
            continue

        paragraph = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,4})\s+", lines[i]) and not lines[i].startswith("```") and not is_table_start(lines, i) and not re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]) and not lines[i].lstrip().startswith("<"):
            paragraph.append(lines[i])
            i += 1
        text = " ".join(part.strip() for part in paragraph)
        out.append(f"<p>{inline(text, current)}</p>")
        plain_parts.append(text)

    return "\n".join(out), toc, " ".join(plain_parts)


def grouped_nav(current: Page) -> str:
    groups: dict[str, list[Page]] = {}
    by_output = {page.output: page for page in PAGES}
    active_path = {current.output}
    ancestor = current
    while ancestor.parent:
        active_path.add(ancestor.parent)
        ancestor = by_output[ancestor.parent]
    for page in PAGES:
        groups.setdefault(page.group, []).append(page)

    def page_links(page: Page, pages: list[Page], *, nested: bool = False, flatten_sections: bool = False) -> str:
        # Gallery and release entries are browsed on their index pages.
        children = [
            child for child in pages
            if child.parent == page.output
            and page.group != "Examples"
            and page.output != "releases/index.html"
        ]
        sections = SECTION_NAV.get(page.output, ())
        expanded = page.output in active_path
        active = ' aria-current="page"' if page.output == current.output else ""
        link_class = "bf-nav-child" if nested else "bf-nav-parent"
        if expanded:
            link_class += " bf-nav-parent--active"
        title = "Overview" if flatten_sections and sections and page.title == page.group else page.title
        parts = [
            '<div class="bf-nav-row">',
            f'<a class="{link_class}"{active} href="{url_to(current, page.output)}">{html.escape(title)}</a>',
        ]
        subnav_id = f"nav-{slugify(page.output)}"
        if (children or sections) and not flatten_sections:
            parts.append(
                f'<button class="bf-nav-expand" type="button" data-nav-expand '
                f'aria-label="Toggle {html.escape(page.title)} pages" '
                f'aria-expanded="{str(expanded).lower()}" aria-controls="{subnav_id}">'
                f'<span aria-hidden="true">{"−" if expanded else "+"}</span></button>'
            )
        parts.append("</div>")
        if children or sections:
            hidden = "" if expanded or flatten_sections else " hidden"
            parts.append(f'<div class="bf-nav-children" id="{subnav_id}"{hidden}>')
            parts.extend(page_links(child, pages, nested=True) for child in children)
            for title, anchor in sections:
                target = "" if page.output == current.output else url_to(current, page.output)
                parts.append(
                    f'<a class="bf-nav-child bf-nav-section" href="{target}#{anchor}">{html.escape(title)}</a>'
                )
            parts.append("</div>")
        return "\n".join(parts)

    parts = []
    for group, pages in groups.items():
        if group == "Start":
            parts.append(f'<section class="bf-nav-group"><h2>{html.escape(group)}</h2>')
        else:
            expanded = " open" if group == current.group else ""
            parts.append(
                f'<details class="bf-nav-group bf-nav-category"{expanded}>'
                f'<summary>{html.escape(group)}</summary><div class="bf-nav-category__items">'
            )
        parts.extend(page_links(page, pages, flatten_sections=len(pages) == 1) for page in pages if not page.parent)
        parts.append("</section>" if group == "Start" else "</div></details>")
    return "\n".join(parts)


def related_section_html(current: Page) -> str:
    if current.group != "Examples":
        return ""
    examples = [
        page
        for page in PAGES
        if page.group == "Examples" and page.parent == "example-gallery/index.html"
    ]
    if not examples:
        return ""
    links = ['<section class="bf-toc-section"><h2>Examples</h2>']
    links.append(
        f'<a class="bf-toc-link" href="{url_to(current, "example-gallery/index.html")}">Example Gallery</a>'
    )
    for page in examples:
        active = ' aria-current="true"' if page.output == current.output else ""
        links.append(
            f'<a class="bf-toc-link bf-toc-link--sub"{active} href="{url_to(current, page.output)}">{html.escape(page.title)}</a>'
        )
    links.append("</section>")
    return "\n".join(links)


def toc_html(toc: list[dict[str, str]]) -> str:
    if not toc:
        return '<p class="bf-muted">No sections on this page.</p>'
    links = []
    for item in toc:
        cls = "bf-toc-link" if item["level"] == "2" else "bf-toc-link bf-toc-link--sub"
        links.append(f'<a class="{cls}" href="#{item["id"]}">{html.escape(item["title"])}</a>')
    return "\n".join(links)


def render_page(page: Page, body: str, toc: list[dict[str, str]]) -> str:
    css = asset_url(page, "bf-docs.css")
    js = asset_url(page, "bf-docs.js")
    logo = asset_url(page, "bits-and-flames-logo.png")
    search_index = asset_url(page, "search-index.json")
    root_url = path_relative(SITE, SITE / page_dir(page))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(page.title)} · Fyron</title>
  <link rel="icon" type="image/svg+xml" sizes="any" href="{asset_url(page, 'bf-favicon.svg')}">
  <link rel="stylesheet" href="{css}">
</head>
<body data-search-index="{search_index}" data-root="{root_url}">
  <a class="bf-skip-link" href="#main-content">Skip to content</a>
  <header class="bf-header">
    <a class="bf-brand" href="{url_to(page, 'index.html')}" aria-label="Fyron documentation home">
      <img src="{logo}" alt="Bits & Flames">
      <span class="bf-brand__divider" aria-hidden="true">|</span>
      <span class="bf-brand__name">Fyron <span>Documentation</span></span>
    </a>
    <div class="bf-search" data-search>
      <label class="bf-search__label" for="bf-search-input">Search</label>
      <input id="bf-search-input" type="search" placeholder="Search docs, modules, functions..." autocomplete="off">
      <div class="bf-search__results" data-search-results hidden></div>
    </div>
    <a class="bf-repo" href="https://github.com/bitsandflames/fyron" aria-label="Open Fyron on GitHub">
      <svg aria-hidden="true" viewBox="0 0 16 16" width="16" height="16">
        <path fill="currentColor" d="M8 0C3.58 0 0 3.67 0 8.2c0 3.62 2.29 6.69 5.47 7.78.4.08.55-.18.55-.4v-1.52c-2.23.5-2.7-.98-2.7-.98-.36-.95-.89-1.2-.89-1.2-.73-.51.06-.5.06-.5.81.06 1.23.85 1.23.85.72 1.26 1.88.9 2.34.69.07-.53.28-.9.51-1.1-1.78-.21-3.64-.91-3.64-4.05 0-.89.31-1.62.82-2.2-.08-.2-.36-1.04.08-2.16 0 0 .68-.22 2.2.84A7.47 7.47 0 0 1 8 3.96c.68 0 1.36.09 2 .28 1.52-1.06 2.2-.84 2.2-.84.44 1.12.16 1.96.08 2.16.51.58.82 1.31.82 2.2 0 3.15-1.87 3.83-3.65 4.04.29.26.55.76.55 1.53v2.25c0 .22.15.48.55.4A8.13 8.13 0 0 0 16 8.2C16 3.67 12.42 0 8 0Z"/>
      </svg>
      <span>GitHub</span>
    </a>
    <button class="bf-menu-button" type="button" data-nav-toggle aria-controls="bf-docs-navigation" aria-expanded="false">
      <span class="bf-sr-only">Open documentation navigation</span>
      <span class="bf-menu-button__line" aria-hidden="true"></span>
      <span class="bf-menu-button__line" aria-hidden="true"></span>
      <span class="bf-menu-button__line" aria-hidden="true"></span>
    </button>
  </header>
  <button class="bf-nav-backdrop" type="button" data-nav-close aria-label="Close documentation navigation" hidden></button>
  <div class="bf-shell">
    <aside class="bf-sidebar" id="bf-docs-navigation" data-nav-drawer>
      <div class="bf-sidebar__mobile-header">
        <span>Documentation</span>
        <button class="bf-nav-close" type="button" data-nav-close aria-label="Close documentation navigation">Close</button>
      </div>
      <nav aria-label="Documentation navigation">
        {grouped_nav(page)}
      </nav>
    </aside>
    <main class="bf-content" id="main-content" tabindex="-1">
      <div class="bf-page-context"><a href="{url_to(page, 'index.html')}">Docs</a><span aria-hidden="true">/</span><span>{html.escape(page.group if page.output == 'index.html' else page.title)}</span></div>
      <article class="bf-article">
        {body}
      </article>
    </main>
    <aside class="bf-toc">
      <section class="bf-toc-section">
        <h2>On This Page</h2>
        <nav>{toc_html(toc)}</nav>
      </section>
      {related_section_html(page)}
    </aside>
  </div>
  <footer class="bf-footer">
    <div class="bf-footer__inner">
      <div class="bf-footer__brand">
        <img src="{logo}" alt="Bits & Flames">
        <p><span>Built by bits.</span><span>Shaped by flames.</span></p>
      </div>
      <p class="bf-footer__note">Fyron documentation. Everything starts with a spark.</p>
    </div>
  </footer>
  <script src="{js}"></script>
</body>
</html>
"""


def extract_code_blocks(markdown: str) -> list[str]:
    blocks = []
    for match in re.finditer(r"```[^\n]*\n(.*?)\n```", markdown, flags=re.DOTALL):
        block = match.group(1).strip()
        if block:
            blocks.append(block)
    return blocks[:12]


CSS = r'''@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap");

:root {
  --bf-page-bg: var(--bf-cream-surface);
  --bf-text: #191817;
  --bf-card-bg: #fffcf6;
  --bf-card-border: #dcd5c9;
  --bf-card-shadow: 3px 3px 0 rgba(25, 24, 23, 0.04);
  --bf-field-bg: #fffcf6;
  --bf-field-border: #dcd5c9;
  --bf-text-muted: #726b62;
  --bf-text-subtle: #514e49;
  --bf-surface-hover: #eee6da;
  --bf-divider: #dfd8cc;
  --bf-cream-surface: #fffaf1;
  --bf-primary: #0b0b0c;
  --bf-primary-hover: #15110f;
  --bf-ember: #ff6a1a;
  --bf-ember-soft: #ffeadb;
  --bf-link: #ad400e;
  --bf-violet: #7550b5;
  --bf-radius-button: 4px;
  --bf-radius-card: 6px;
  --bf-font-body: "Inter", ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --bf-font-display: "Space Grotesk", "Inter", ui-sans-serif, system-ui, sans-serif;
  --bf-font-code: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 6rem; }
::selection { background: #ffcfad; color: var(--bf-text); }
:focus-visible { outline: 2px solid var(--bf-violet); outline-offset: 4px; }
.bf-skip-link {
  background: var(--bf-primary);
  color: #fff;
  left: 1rem;
  padding: 0.8rem 1rem;
  position: fixed;
  top: -6rem;
  z-index: 60;
}
.bf-skip-link:focus { top: 0.5rem; }
body {
  margin: 0;
  background: var(--bf-page-bg);
  color: var(--bf-text);
  font-family: var(--bf-font-body);
  font-size: 15px;
}

.bf-header {
  align-items: center;
  background: var(--bf-cream-surface);
  box-shadow: 0 3px 0 rgba(25, 24, 23, 0.025);
  border-bottom: 1px solid var(--bf-divider);
  display: grid;
  grid-template-columns: minmax(15rem, 1fr) minmax(18rem, 36rem) minmax(7rem, 1fr);
  gap: 1rem;
  height: 4.5rem;
  padding: 0 clamp(1rem, 2vw, 2rem);
  position: sticky;
  top: 0;
  z-index: 20;
}

.bf-header > * { min-width: 0; }
.bf-brand {
  align-items: center;
  color: var(--bf-text);
  display: inline-flex;
  gap: 0.85rem;
  text-decoration: none;
  width: max-content;
}
.bf-brand img {
  display: block;
  height: 2.5rem;
  width: auto;
}
.bf-brand__divider {
  color: #000000;
  display: inline-block;
  font-family: var(--bf-font-code);
  font-size: 1.35rem;
  font-weight: 400;
  line-height: 1;
}
.bf-brand__name {
  color: #000000;
  font-family: var(--bf-font-code);
  font-size: 1.08rem;
  font-weight: 600;
  letter-spacing: -0.04em;
  line-height: 1;
}
.bf-brand__name span {
  color: var(--bf-text-muted);
  display: block;
  font: 500 0.58rem/1 var(--bf-font-code);
  letter-spacing: 0.04em;
  margin-top: 0.45rem;
  text-transform: uppercase;
}
.bf-sr-only {
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  height: 1px;
  overflow: hidden;
  position: absolute;
  white-space: nowrap;
  width: 1px;
}
.bf-repo {
  align-items: center;
  background: var(--bf-primary);
  border: 1px solid var(--bf-primary);
  border-radius: var(--bf-radius-button);
  color: #fff;
  display: inline-flex;
  font-size: 0.78rem;
  font-weight: 700;
  gap: 0.5rem;
  justify-self: end;
  padding: 0.72rem 0.9rem;
  text-decoration: none;
}
.bf-repo svg {
  display: block;
  flex: 0 0 auto;
}
.bf-repo:hover { background: var(--bf-primary-hover); }
.bf-menu-button {
  align-items: center;
  background: var(--bf-primary);
  border: 1px solid var(--bf-primary);
  border-radius: var(--bf-radius-button);
  color: #fff;
  cursor: pointer;
  display: none;
  flex-direction: column;
  gap: 0.24rem;
  height: 2.65rem;
  justify-content: center;
  justify-self: end;
  padding: 0;
  width: 2.65rem;
}
.bf-menu-button__line {
  background: currentColor;
  border-radius: 999px;
  display: block;
  height: 2px;
  transition: transform 160ms ease, opacity 160ms ease;
  width: 1.05rem;
}
.bf-menu-button[aria-expanded="true"] .bf-menu-button__line:nth-of-type(2) {
  transform: translateY(0.38rem) rotate(45deg);
}
.bf-menu-button[aria-expanded="true"] .bf-menu-button__line:nth-of-type(3) {
  opacity: 0;
}
.bf-menu-button[aria-expanded="true"] .bf-menu-button__line:nth-of-type(4) {
  transform: translateY(-0.38rem) rotate(-45deg);
}
.bf-nav-backdrop {
  background: rgba(11, 11, 12, 0.46);
  border: 0;
  inset: 0;
  position: fixed;
  z-index: 30;
}
.bf-nav-backdrop[hidden] { display: none; }
.bf-sidebar__mobile-header {
  display: none;
}
.bf-nav-close {
  background: var(--bf-primary);
  border: 1px solid var(--bf-primary);
  border-radius: var(--bf-radius-button);
  color: #fff;
  cursor: pointer;
  font: 800 0.72rem var(--bf-font-body);
  padding: 0.55rem 0.7rem;
}

.bf-search { position: relative; width: 100%; }
.bf-search__label {
  height: 1px;
  overflow: hidden;
  position: absolute;
  white-space: nowrap;
  width: 1px;
}
.bf-search input {
  background: var(--bf-field-bg);
  border: 1px solid var(--bf-field-border);
  border-radius: var(--bf-radius-button);
  color: var(--bf-text);
  font: 400 0.78rem var(--bf-font-code);
  height: 2.65rem;
  outline: none;
  padding: 0 1rem;
  width: 100%;
}
.bf-search input:focus {
  border-color: var(--bf-primary);
  box-shadow: 0 0 0 2px var(--bf-primary);
}
.bf-search__results {
  background: var(--bf-card-bg);
  border: 1px solid var(--bf-card-border);
  border-radius: var(--bf-radius-card);
  box-shadow: 5px 5px 0 rgba(25, 24, 23, 0.1);
  left: 0;
  max-height: min(30rem, calc(100vh - 6rem));
  overflow: auto;
  position: absolute;
  right: 0;
  top: calc(100% + 0.5rem);
  z-index: 40;
}
.bf-search__meta {
  border-bottom: 1px solid var(--bf-divider);
  color: var(--bf-text-muted);
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  padding: 0.72rem 0.9rem;
  text-transform: uppercase;
}
.bf-search__result {
  border-bottom: 1px solid var(--bf-divider);
  color: var(--bf-text);
  display: block;
  padding: 0.8rem 0.9rem;
  text-decoration: none;
}
.bf-search__result:last-child { border-bottom: 0; }
.bf-search__result:hover,
.bf-search__result:focus { background: var(--bf-surface-hover); outline: none; }
.bf-search__result strong {
  display: block;
  font-family: var(--bf-font-display);
  font-size: 0.82rem;
  line-height: 1.25;
}
.bf-search__result span {
  color: var(--bf-text-subtle);
  display: block;
  font-size: 0.72rem;
  line-height: 1.45;
  margin-top: 0.25rem;
}

.bf-shell {
  display: grid;
  grid-template-columns: 13rem minmax(0, 1fr) 11rem;
  gap: clamp(1.5rem, 3vw, 3rem);
  margin: 0 auto;
  max-width: 104rem;
  padding: 2rem clamp(1rem, 2vw, 2rem) 0;
  width: 100%;
}
.bf-sidebar,
.bf-toc {
  align-self: start;
  max-height: calc(100vh - 7rem);
  scrollbar-width: thin;
  scrollbar-color: var(--bf-card-border) transparent;
  overflow: auto;
  position: sticky;
  top: 6rem;
}
.bf-sidebar { padding-right: 0.65rem; }
.bf-toc { border-left: 1px solid var(--bf-divider); padding-left: 1rem; }
.bf-nav-group { margin-bottom: 1.15rem; }
.bf-nav-category { margin-bottom: 0.3rem; }
.bf-nav-category > summary {
  align-items: center;
  color: var(--bf-text-subtle);
  cursor: pointer;
  display: flex;
  font: 600 0.68rem/1.4 var(--bf-font-code);
  justify-content: space-between;
  letter-spacing: 0.04em;
  list-style: none;
  padding: 0.45rem 0.65rem;
}
.bf-nav-category > summary::-webkit-details-marker { display: none; }
.bf-nav-category > summary::after { content: "+"; font-size: 1rem; line-height: 1; }
.bf-nav-category[open] > summary::after { content: "−"; }
.bf-nav-category > summary:hover { background: var(--bf-surface-hover); color: var(--bf-text); }
.bf-nav-category[open] > summary { color: var(--bf-violet); }
.bf-nav-category__items { padding: 0.15rem 0 0.65rem; }
.bf-nav-row { align-items: stretch; display: flex; }
.bf-nav-row > a { flex: 1; min-width: 0; }
.bf-nav-expand {
  background: transparent;
  border: 0;
  border-radius: 2px;
  color: var(--bf-text-muted);
  cursor: pointer;
  flex: 0 0 2.25rem;
  font: 500 1rem/1 var(--bf-font-code);
  margin-bottom: 0.18rem;
  padding: 0;
}
.bf-nav-expand:hover { background: var(--bf-surface-hover); color: var(--bf-text); }
.bf-nav-expand[aria-expanded="true"] { color: var(--bf-violet); }
.bf-nav-children[hidden] { display: none; }
.bf-toc-section { margin-bottom: 1.25rem; }
.bf-nav-group h2,
.bf-toc h2 {
  color: var(--bf-text-muted);
  font-family: var(--bf-font-code);
  font-size: 0.64rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  margin: 0 0 0.45rem;
  text-transform: uppercase;
}
.bf-nav-group a,
.bf-toc a {
  border-radius: 2px;
  border-left: 2px solid transparent;
  color: var(--bf-text-subtle);
  display: block;
  font-size: 0.78rem;
  font-weight: 500;
  line-height: 1.25;
  margin-bottom: 0.18rem;
  padding: 0.55rem 0.65rem;
  text-decoration: none;
}
.bf-nav-group a:hover,
.bf-toc a:hover { background: var(--bf-surface-hover); color: var(--bf-text); }
.bf-nav-group a[aria-current="page"] {
  background: var(--bf-ember-soft);
  border-left-color: var(--bf-ember);
  color: #8f350e;
  font-weight: 700;
}
.bf-nav-parent.bf-nav-parent--active {
  color: var(--bf-text);
}
.bf-nav-children {
  border-left: 1px solid var(--bf-divider);
  margin: 0.1rem 0 0.45rem 0.75rem;
  padding-left: 0.45rem;
}
.bf-nav-group a.bf-nav-child {
  font-size: 0.72rem;
  margin-bottom: 0.12rem;
  padding: 0.5rem 0.65rem;
}
.bf-nav-section[aria-current="location"] {
  background: var(--bf-surface-hover);
  border-left-color: var(--bf-violet);
  color: var(--bf-violet);
}
.bf-toc .bf-toc-link--sub { font-size: 0.72rem; padding-left: 1.35rem; }
.bf-toc a[aria-current="true"] {
  background: transparent;
  border-left-color: var(--bf-violet);
  color: var(--bf-violet);
}
.bf-muted { color: var(--bf-text-muted); font-size: 0.78rem; }

.bf-content { min-width: 0; }
.bf-content:focus { outline: none; }
.bf-page-context {
  align-items: center;
  color: var(--bf-text-muted);
  display: flex;
  flex-wrap: wrap;
  font: 400 0.69rem/1.6 var(--bf-font-code);
  gap: 0.65rem;
  margin: 0 0 1.6rem;
}
.bf-page-context a { color: var(--bf-violet); text-decoration: none; }
.bf-page-context a:hover { text-decoration: underline; }
.bf-article {
  color: var(--bf-text-subtle);
  font-size: 0.96rem;
  line-height: 1.75;
  max-width: none;
}
.bf-article h1,
.bf-article h2,
.bf-article h3,
.bf-article h4 {
  color: var(--bf-text);
  font-family: var(--bf-font-display);
  letter-spacing: 0;
}
.bf-article h1 {
  font-size: clamp(2.35rem, 5vw, 4rem);
  line-height: 1;
  margin: 0 0 1rem;
}
.bf-article h2 {
  border-top: 1px solid var(--bf-divider);
  font-size: 1.45rem;
  margin: 2.8rem 0 0.9rem;
  padding-top: 1.35rem;
}
.bf-article h3 { font-size: 1.05rem; margin-top: 2rem; }
.bf-article a { color: var(--bf-link); font-weight: 600; text-underline-offset: 3px; }
.bf-article a:hover { text-decoration-thickness: 2px; }
.bf-article > p { max-width: 78ch; }
.bf-article code {
  background: var(--bf-field-bg);
  border: 1px solid var(--bf-field-border);
  border-radius: 3px;
  color: var(--bf-text);
  font-family: var(--bf-font-code);
  font-size: 0.84em;
  padding: 0.08rem 0.3rem;
}
.bf-code {
  background: #080a0f;
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: var(--bf-radius-card);
  box-shadow: 4px 4px 0 rgba(25, 24, 23, 0.1);
  margin: 1.35rem 0;
  overflow: hidden;
}
.bf-code__bar {
  align-items: center;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  display: flex;
  gap: 0.4rem;
  height: 2.1rem;
  justify-content: space-between;
  min-width: 0;
  padding: 0 0.9rem;
}
.bf-code__dots {
  display: inline-flex;
  flex: 0 0 auto;
  gap: 0.4rem;
}
.bf-code__dots span {
  background: var(--bf-ember);
  border-radius: 0;
  height: 0.45rem;
  width: 0.45rem;
}
.bf-code__dots span:nth-child(2) { background: #fdba3b; }
.bf-code__dots span:nth-child(3) { background: #a78bfa; }
.bf-code__actions {
  align-items: center;
  display: flex;
  flex: 1 1 auto;
  gap: 0.5rem;
  justify-content: flex-end;
  min-width: 0;
}
.bf-code__bar strong {
  color: rgba(248,250,252,0.58);
  flex: 1 1 auto;
  font-family: var(--bf-font-code);
  font-size: 0.62rem;
  min-width: 0;
  overflow: hidden;
  text-align: right;
  text-overflow: ellipsis;
  text-transform: uppercase;
  white-space: nowrap;
}
.bf-code__copy {
  align-items: center;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 3px;
  color: rgba(248,250,252,0.76);
  cursor: pointer;
  display: inline-flex;
  flex: 0 0 auto;
  font: 700 0.64rem var(--bf-font-body);
  gap: 0.35rem;
  height: 1.55rem;
  padding: 0 0.48rem;
  transition: background 160ms ease, border-color 160ms ease, color 160ms ease, transform 160ms ease;
}
.bf-code__copy:hover,
.bf-code__copy:focus {
  background: rgba(255,255,255,0.12);
  border-color: rgba(255,255,255,0.28);
  color: #fff;
  outline: none;
}
.bf-code__copy:focus-visible {
  box-shadow: 0 0 0 2px var(--bf-ember);
}
.bf-code__copy svg {
  display: block;
}
.bf-code__copy.is-copied {
  background: var(--bf-ember);
  border-color: var(--bf-ember);
  color: #fff;
  animation: bf-copy-pop 360ms ease;
}
.bf-code__copy.is-error {
  background: rgba(255, 106, 26, 0.2);
  border-color: rgba(255, 106, 26, 0.7);
  color: #fff;
}
.bf-code__copy-label {
  line-height: 1;
}
@keyframes bf-copy-pop {
  0% { transform: scale(1); }
  45% { transform: scale(1.06); }
  100% { transform: scale(1); }
}
@media (prefers-reduced-motion: reduce) {
  .bf-code__copy { transition: none; }
  .bf-code__copy.is-copied { animation: none; }
}
.bf-code pre {
  margin: 0;
  overflow: auto;
  padding: 1rem;
}
.bf-code code {
  background: transparent;
  border: 0;
  color: #f8fafc;
  display: block;
  font-size: 0.82rem;
  line-height: 1.55;
  padding: 0;
  tab-size: 4;
  white-space: pre;
}
.bf-table-wrap {
  border: 1px solid var(--bf-card-border);
  background: var(--bf-card-bg);
  border-radius: var(--bf-radius-card);
  box-shadow: none;
  margin: 1.3rem 0;
  overflow: auto;
}
table { border-collapse: collapse; min-width: 100%; }
th, td {
  border-bottom: 1px solid var(--bf-divider);
  padding: 0.72rem 0.85rem;
  text-align: left;
  vertical-align: top;
}
th {
  background: #efe8dc;
  font-family: var(--bf-font-code);
  color: var(--bf-text);
  font-size: 0.68rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
td { color: var(--bf-text-subtle); font-size: 0.82rem; }
tr:last-child td { border-bottom: 0; }

/* The homepage shares the warm paper and pixel accents of Bits & Flames. */
.bf-docs-hero {
  background: var(--bf-cream-surface);
  border: 1px solid var(--bf-card-border);
  border-radius: var(--bf-radius-card);
  margin-bottom: 1.6rem;
  padding: clamp(1.2rem, 3vw, 2rem);
}
.bf-docs-hero--home {
  align-items: center;
  background: #f3edf7;
  border: 0;
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(0, 0.95fr) minmax(0, 1.05fr);
  padding: 1.8rem clamp(1.2rem, 3vw, 2rem) 2.5rem;
  position: relative;
}
.bf-docs-fireplace-cta { margin: 0 0 1rem; min-height: 28rem; }
.bf-docs-hero--home .bf-eyebrow {
  color: var(--bf-violet);
  font: 600 0.62rem/1.6 var(--bf-font-code);
  letter-spacing: 0.13em;
  margin: 0 0 1.5rem;
}
.bf-docs-hero--home h1 {
  font-size: clamp(3.8rem, 6.8vw, 6.25rem);
  letter-spacing: -0.075em;
  line-height: 0.95;
  margin: 0 0 1.2rem;
}

.bf-hero-statement {
  color: var(--bf-text);
  font: 700 clamp(1.55rem, 2.6vw, 2.4rem)/1.12 var(--bf-font-display);
  letter-spacing: -0.04em;
  margin: 0 0 1.2rem;
}
.bf-hero-statement span { color: #c54b12; }
.bf-hero-lead { font-size: 0.95rem; line-height: 1.7; margin: 0; }
.bf-fireplace-actions {
  align-items: center;
  display: flex;
  flex-wrap: wrap;
  gap: 1.1rem;
  margin-top: 1.6rem;
}
.bf-article .bf-hero-button {
  align-items: center;
  background: var(--bf-primary);
  border: 1px solid var(--bf-primary);
  border-radius: var(--bf-radius-button);
  color: #fffaf1;
  display: inline-flex;
  font-size: 0.8rem;
  gap: 1rem;
  min-height: 2.8rem;
  padding: 0.65rem 1rem;
  text-decoration: none;
}
.bf-hero-button:hover { box-shadow: 3px 3px 0 #d8b996; transform: translate(-1px, -1px); }
.bf-article .bf-hero-link { color: var(--bf-text); font-size: 0.78rem; }
.bf-pixel-arrow {
  background: currentColor;
  clip-path: polygon(0 40%, 57.143% 40%, 57.143% 0, 71.429% 0, 71.429% 20%, 85.714% 20%, 85.714% 40%, 100% 40%, 100% 60%, 85.714% 60%, 85.714% 80%, 71.429% 80%, 71.429% 100%, 57.143% 100%, 57.143% 60%, 0 60%);
  display: inline-block;
  flex: 0 0 auto;
  height: 10px;
  width: 14px;
}
.bf-hero-install {
  margin: 1.5rem 0 0;
  max-width: 22rem;
}
.bf-hero-install .bf-code__bar strong { text-align: left; }
.bf-hero-install .bf-code__bar > span { color: #b9b6c5; font: 400 0.66rem var(--bf-font-code); }
.bf-hero-install pre { padding: 0.8rem 0.9rem; }
.bf-hero-install code::before { color: var(--bf-ember); content: "$ "; }
.bf-fireplace-visual { margin: 0; min-width: 0; position: relative; text-align: center; }
.bf-fireplace-visual::before {
  background: #dfcced;
  box-shadow: 10px -10px 0 #eee4f3, 20px 0 0 #e5d7ed, -10px 10px 0 #eadff1;
  content: "";
  height: 10px;
  position: absolute;
  right: 15%;
  top: 7%;
  width: 10px;
}
.bf-fireplace-visual img {
  border-radius: 6px;
  height: auto;
  image-rendering: pixelated;
  max-height: 28rem;
  object-fit: contain;
  width: 100%;
}
.bf-fireplace-visual figcaption { color: var(--bf-violet); font: 400 0.59rem/1.7 var(--bf-font-code); letter-spacing: 0.01em; margin-top: 0.5rem; }
.bf-release-note {
  align-items: start;
  background: var(--bf-card-bg);
  border: 1px solid var(--bf-divider);
  border-left: 3px solid var(--bf-ember);
  border-radius: 0 var(--bf-radius-button) var(--bf-radius-button) 0;
  display: grid;
  gap: 1rem;
  grid-template-columns: auto 1fr;
  margin: 0 0 2rem;
  padding: 1rem 1.1rem;
}
.bf-release-note > a { align-items: center; display: inline-flex; font: 600 0.75rem/1.8 var(--bf-font-code); gap: 0.6rem; text-decoration: none; }
.bf-release-note p { font-size: 0.77rem; line-height: 1.65; margin: 0; }
.bf-install-card {
  background: #0b0b0c;
  border: 1px solid rgba(11, 11, 12, 0.16);
  border-radius: 1.2rem;
  box-shadow: 0 22px 60px rgba(11, 11, 12, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1);
  margin-top: 0.4rem;
  max-width: 46rem;
  overflow: hidden;
}
.bf-install-card__header {
  align-items: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  gap: 1rem;
  justify-content: space-between;
  padding: 0.75rem 0.85rem;
}
.bf-install-card__header > span {
  color: rgba(255, 255, 255, 0.74);
  font-family: var(--bf-font-code);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.bf-install-tabs {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 0.75rem;
  display: flex;
  gap: 0.2rem;
  padding: 0.2rem;
}
.bf-install-tabs button {
  appearance: none;
  background: transparent;
  border: 0;
  border-radius: 0.55rem;
  color: rgba(255, 255, 255, 0.72);
  cursor: pointer;
  font-family: var(--bf-font-code);
  font-size: 0.68rem;
  font-weight: 800;
  padding: 0.42rem 0.62rem;
}
.bf-install-tabs button.is-active {
  background: #fffaf1;
  color: #080a0f;
}
.bf-install-tabs button:focus-visible {
  outline: 2px solid #ffcf67;
  outline-offset: 2px;
}
.bf-install-card pre {
  margin: 0;
  overflow-x: auto;
  padding: 1.05rem 1.15rem 1.2rem;
}
.bf-install-card code {
  background: transparent;
  border: 0;
  border-radius: 0;
  color: #fff;
  display: block;
  font-family: var(--bf-font-code);
  font-size: clamp(0.88rem, 1.55vw, 1.05rem);
  font-weight: 400;
  line-height: 1.4;
  padding: 0;
  white-space: pre;
}
.bf-install-card code::before {
  color: #ff6a1a;
  content: "$ ";
}
.bf-docs-actions--hero {
  grid-template-columns: repeat(2, minmax(10rem, 1fr));
  margin-top: 1.35rem;
  max-width: 34rem;
}
.bf-docs-hero--home .bf-docs-button {
  backdrop-filter: blur(12px);
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.18);
  box-shadow: none;
  color: #fff;
}
.bf-docs-hero--home .bf-docs-button:hover {
  background: rgba(255, 255, 255, 0.15);
}
.bf-docs-hero--home .bf-docs-button--primary {
  background: #fff;
  border-color: #fff;
  color: #080a0f;
}
.bf-spark-card {
  align-self: center;
  background: rgba(8, 10, 15, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 1.5rem;
  box-shadow: 0 28px 80px rgba(0, 0, 0, 0.32), inset 0 1px 0 rgba(255, 255, 255, 0.12);
  min-height: 23rem;
  overflow: hidden;
  padding: 1rem;
  position: relative;
}
.bf-spark-card::before {
  background: linear-gradient(135deg, rgba(255, 106, 26, 0.25), rgba(142, 124, 195, 0.22), rgba(9, 17, 31, 0));
  content: "";
  inset: 0;
  pointer-events: none;
  position: absolute;
}
.bf-spark-card > * {
  position: relative;
  z-index: 1;
}
.bf-spark-card__bar {
  display: flex;
  gap: 0.4rem;
  padding: 0.15rem 0.1rem 0.9rem;
}
.bf-spark-card__bar span {
  background: rgba(255, 255, 255, 0.56);
  border-radius: 999px;
  height: 0.55rem;
  width: 0.55rem;
}
.bf-spark-card__bar span:first-child { background: #ff6a1a; }
.bf-spark-card__bar span:nth-child(2) { background: #ffcf67; }
.bf-spark-card__bar span:nth-child(3) { background: #8e7cc3; }
.bf-spark-mark {
  display: grid;
  gap: 0.55rem;
  grid-template-columns: repeat(3, 1fr);
  margin: 1.9rem auto 1.45rem;
  max-width: 16rem;
}
.bf-spark-mark span {
  aspect-ratio: 1;
  background: linear-gradient(135deg, #ffcf67 0%, #ff6a1a 46%, #8e7cc3 100%);
  border: 1px solid rgba(255, 255, 255, 0.22);
  box-shadow: 0 12px 26px rgba(255, 106, 26, 0.18);
}
.bf-spark-mark span:nth-child(2),
.bf-spark-mark span:nth-child(4),
.bf-spark-mark span:nth-child(6) {
  background: linear-gradient(135deg, #8e7cc3 0%, #172140 52%, #ff6a1a 140%);
}
.bf-spark-card__prompt {
  color: #ffcf67;
  font-family: var(--bf-font-code);
  font-size: 0.9rem;
  font-weight: 800;
  margin: 0 0 1rem;
}
.bf-spark-card__prompt::before {
  color: #ff6a1a;
  content: "$ ";
}
.bf-spark-flow {
  display: grid;
  gap: 0.45rem;
  grid-template-columns: repeat(5, minmax(0, 1fr));
}
.bf-spark-flow span {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.14);
  color: rgba(255, 255, 255, 0.84);
  font-family: var(--bf-font-code);
  font-size: 0.62rem;
  font-weight: 800;
  overflow: hidden;
  padding: 0.55rem 0.35rem;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bf-eyebrow {
  color: var(--bf-ember);
  font-family: var(--bf-font-code);
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.bf-docs-actions,
.bf-docs-grid {
  display: grid;
  gap: 0.85rem;
  grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr));
  margin: 1rem 0;
}
.bf-docs-button,
.bf-docs-card {
  background: var(--bf-card-bg);
  border: 1px solid var(--bf-card-border);
  border-radius: var(--bf-radius-card);
  box-shadow: none;
  color: var(--bf-text);
  display: block;
  padding: 1rem;
  text-decoration: none;
}
.bf-docs-button { text-align: center; }
.bf-docs-button:hover,
.bf-docs-card:hover {
  border-color: rgba(255, 106, 26, 0.42);
  transform: translateY(-1px);
}
.bf-docs-card,
.bf-docs-button {
  transition: background 160ms ease, border-color 160ms ease, transform 160ms ease;
}
.bf-docs-grid--featured { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.bf-docs-grid--intro { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.bf-docs-grid--featured .bf-docs-card {
  border-top: 2px solid #d9cbed;
  min-height: 8rem;
  padding: 1.1rem 1.1rem 1rem;
  position: relative;
}
.bf-docs-grid--featured .bf-docs-card:nth-child(3n + 2) { border-top-color: #edbd94; }
.bf-docs-grid--featured .bf-docs-card::after {
  color: var(--bf-violet);
  content: "↗";
  font-family: var(--bf-font-code);
  position: absolute;
  right: 1rem;
  top: 0.8rem;
}
.bf-docs-grid--featured .bf-docs-card:hover {
  background: var(--bf-cream-surface);
  border-color: #ac947a;
  box-shadow: 3px 3px 0 #e4d9c9;
  transform: translate(-1px, -1px);
}
.bf-docs-card strong {
  color: var(--bf-text);
  display: block;
  font-family: var(--bf-font-display);
  font-size: 1rem;
  line-height: 1.25;
  margin-bottom: 0.55rem;
  padding-right: 1rem;
}
.bf-docs-card span { color: var(--bf-text-subtle); display: block; font-size: 0.8rem; font-weight: 400; line-height: 1.65; }
.bf-doc-image {
  background: #fff;
  border: 1px solid var(--bf-card-border);
  border-radius: var(--bf-radius-card);
  box-shadow: var(--bf-card-shadow);
  display: block;
  margin: 1.35rem 0;
  max-width: 100%;
  padding: 0.35rem;
}
.bf-figure-gallery {
  display: grid;
  gap: 1.25rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin: 1.4rem 0 2.1rem;
}
.bf-figure-card {
  background: var(--bf-card-bg);
  border: 1px solid var(--bf-card-border);
  border-radius: var(--bf-radius-card);
  box-shadow: none;
  display: flex;
  flex-direction: column;
  margin: 0;
  min-width: 0;
  overflow: hidden;
}
.bf-figure-card img {
  background: #ffffff;
  border-bottom: 1px solid var(--bf-divider);
  display: block;
  height: auto;
  max-width: 100%;
  object-fit: contain;
  width: 100%;
}
.bf-figure-card figcaption {
  color: var(--bf-text-subtle);
  display: block;
  font-size: 0.82rem;
  line-height: 1.55;
  min-width: 0;
  overflow-wrap: anywhere;
  padding: 0.85rem 0.95rem 1rem;
}
.bf-figure-card figcaption strong {
  color: var(--bf-text);
  display: block;
  font-size: 0.9rem;
  line-height: 1.35;
  margin-bottom: 0.25rem;
}
.bf-footer {
  background: var(--bf-cream-surface);
  border-top: 1px solid var(--bf-divider);
  color: var(--bf-text-subtle);
  margin-top: 4rem;
  padding: 1.65rem 1.25rem 1.9rem;
}
.bf-footer__inner {
  align-items: center;
  display: grid;
  gap: 1.2rem;
  grid-template-columns: minmax(0, 1fr) minmax(16rem, auto);
  margin: 0 auto;
  max-width: 96rem;
}
.bf-footer__brand {
  align-items: center;
  display: flex;
  gap: 0.9rem;
  min-width: 0;
}
.bf-footer__brand img {
  display: block;
  height: 2.65rem;
  width: auto;
}
.bf-footer__brand p {
  color: var(--bf-primary);
  font-family: var(--bf-font-display);
  font-size: 0.95rem;
  font-weight: 700;
  line-height: 1.15;
  margin: 0;
  min-width: 0;
}
.bf-footer__brand p span:first-child { color: var(--bf-primary); }
.bf-footer__brand p span:last-child { color: var(--bf-ember); display: block; }
.bf-footer__note {
  color: var(--bf-text-subtle);
  font-family: var(--bf-font-code);
  font-size: 0.76rem;
  justify-self: end;
  line-height: 1.5;
  margin: 0;
  max-width: 34rem;
  text-align: right;
}

.bf-search__code {
  background: #080a0f;
  border-radius: 3px;
  color: #f8fafc;
  display: block;
  font-family: var(--bf-font-code);
  font-size: 0.68rem;
  line-height: 1.45;
  margin-top: 0.48rem;
  overflow-x: auto;
  padding: 0.55rem 0.65rem;
  white-space: pre;
}
.bf-search mark {
  background: var(--bf-ember-soft);
  border-radius: 0.25rem;
  color: inherit;
  padding: 0 0.12rem;
}

@media (max-width: 1100px) {
  .bf-header { grid-template-columns: auto minmax(12rem, 1fr) auto; }
  .bf-shell { grid-template-columns: 14rem minmax(0,1fr); }
  .bf-toc { display: none; }
  .bf-docs-hero--home { grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); }
  .bf-docs-fireplace-cta { min-height: auto; }
  .bf-fireplace-visual { justify-content: center; }
  .bf-fireplace-visual img { max-height: 28rem; max-width: min(100%, 35rem); }
  .bf-spark-card { min-height: auto; }
}
@media (max-width: 920px) {
  .bf-header {
    grid-template-columns: auto minmax(0, 1fr) auto;
    height: auto;
    padding: 0.75rem 1rem;
  }
  .bf-brand img { height: 3rem; }
  .bf-repo { display: none; }
  .bf-menu-button { display: inline-flex; }
  .bf-shell {
    display: block;
    padding: 0 1rem;
  }
  .bf-sidebar {
    background: var(--bf-page-bg);
    border-right: 1px solid var(--bf-divider);
    box-shadow: 24px 0 70px rgba(11, 11, 12, 0.18);
    bottom: 0;
    left: 0;
    margin: 0;
    max-height: none;
    max-width: min(22rem, calc(100vw - 3rem));
    overflow: auto;
    padding: 1rem;
    position: fixed;
    top: 0;
    transform: translateX(-105%);
    transition: transform 190ms ease;
    visibility: hidden;
    width: 21rem;
    z-index: 40;
  }
  body.bf-nav-open { overflow: hidden; }
  body.bf-nav-open .bf-sidebar { transform: translateX(0); visibility: visible; }
  .bf-sidebar__mobile-header {
    align-items: center;
    border-bottom: 1px solid var(--bf-divider);
    display: flex;
    gap: 1rem;
    justify-content: space-between;
    margin: -0.15rem 0 1rem;
    padding-bottom: 0.85rem;
  }
  .bf-sidebar__mobile-header span {
    color: var(--bf-text);
    font-family: var(--bf-font-display);
    font-size: 1rem;
    font-weight: 800;
  }
  .bf-sidebar::-webkit-scrollbar { width: 0.45rem; }
  .bf-nav-group {
    display: block;
    margin: 0 0 1rem;
    max-width: none;
    width: auto;
  }
  .bf-nav-category { margin-bottom: 0.3rem; }
  .bf-nav-category > summary { min-height: 2.75rem; }
  .bf-nav-group h2 {
    margin-bottom: 0.35rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .bf-nav-group a {
    font-size: 0.8rem;
    margin-bottom: 0.16rem;
    padding: 0.62rem 0.7rem;
  }
  .bf-nav-children {
    margin: 0.1rem 0 0.35rem 0.4rem;
    padding-left: 0.35rem;
  }
  .bf-content { margin-top: 1.2rem; }
  .bf-docs-fireplace-cta {
    margin-left: 0;
    margin-right: 0;
  }
  .bf-docs-hero--home {
    gap: 1.2rem;
    padding: 1.6rem 1.2rem 2rem;
  }
  .bf-docs-hero--home h1 {
    font-size: clamp(2.8rem, 11vw, 5rem);
    max-width: 8ch;
  }
  .bf-fireplace-visual img {
    max-height: 24rem;
    max-width: min(100%, 30rem);
  }
}
@media (max-width: 760px) {
  .bf-header {
    grid-template-columns: minmax(0, 1fr) auto;
    height: auto;
    padding: 0.8rem 1rem;
  }
  .bf-search {
    grid-column: 1 / -1;
    grid-row: 2;
  }
  .bf-brand img { height: 2.75rem; }
  .bf-footer__brand img { height: 2.5rem; }
  .bf-repo { display: none; }
  .bf-shell {
    display: block;
    padding: 0 1rem 1rem;
  }
  .bf-sidebar {
    max-width: min(21rem, calc(100vw - 2.5rem));
    width: 20rem;
  }
  .bf-content { margin-top: 1.5rem; }
  .bf-article {
    font-size: 0.9rem;
    line-height: 1.62;
  }
  .bf-article h1 { font-size: clamp(2rem, 12vw, 2.7rem); }
  .bf-article h2 { font-size: 1.25rem; margin-top: 2.1rem; }
  .bf-figure-gallery { grid-template-columns: 1fr; }
  .bf-docs-hero--home {
    grid-template-columns: 1fr;
    margin-left: 0;
    margin-right: 0;
    padding: 1.4rem 1.2rem 1.7rem;
  }
  .bf-docs-hero--home .bf-eyebrow {
    font-size: 0.56rem;
    letter-spacing: 0.28em;
    margin-bottom: 1.1rem;
  }
  .bf-docs-hero--home h1 {
    font-size: clamp(3.8rem, 18vw, 5rem);
    letter-spacing: -0.045em;
    line-height: 0.94;
  }
  .bf-hero-lead { font-size: 0.9rem; }
  .bf-fireplace-visual img { max-height: 18rem; }
  .bf-fireplace-actions { gap: 1.1rem; }
  .bf-hero-statement { font-size: 1.9rem; }
  .bf-fireplace-visual { margin-top: 1rem; }
  .bf-release-note { grid-template-columns: 1fr; gap: 0.5rem; }
  .bf-page-context { margin-bottom: 1.25rem; }
  .bf-docs-actions--hero { grid-template-columns: 1fr; }
  .bf-spark-flow { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .bf-install-card__header {
    align-items: flex-start;
    flex-direction: column;
  }
  .bf-install-tabs { width: 100%; }
  .bf-install-tabs button { flex: 1; }
  .bf-footer {
    margin-top: 2.5rem;
    padding: 1.65rem 1rem 1.8rem;
  }
  .bf-footer__inner {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    justify-content: center;
    max-width: 24rem;
    text-align: center;
  }
  .bf-footer__brand {
    align-items: center;
    flex-direction: column;
    gap: 0.65rem;
    justify-content: center;
    text-align: center;
  }
  .bf-footer__note {
    max-width: 22rem;
    text-align: center;
  }
}
@media (max-width: 520px) {
  .bf-search__results {
    left: 1rem;
    max-height: min(24rem, calc(100vh - 8.5rem));
    position: fixed;
    right: 1rem;
    top: 7.1rem;
  }
  .bf-sidebar {
    max-width: min(20rem, calc(100vw - 2rem));
    width: 19rem;
  }
  .bf-nav-group {
    max-width: none;
    width: auto;
  }
  .bf-docs-grid { grid-template-columns: 1fr; }
  .bf-table-wrap {
    border-radius: var(--bf-radius-card);
    margin-left: 0;
    margin-right: 0;
  }
  th, td { padding: 0.62rem 0.68rem; }
  .bf-code { border-radius: var(--bf-radius-card); margin-left: 0; margin-right: 0; }
  .bf-code pre { padding: 0.85rem; }
  .bf-docs-hero--home h1 { max-width: 7.5ch; }
  .bf-fireplace-visual img { max-height: 14.5rem; }
}
@media (max-width: 760px) {
  html { scroll-padding-top: 9rem; }
  .bf-docs-grid--intro { grid-template-columns: 1fr; }
}
.bf-citation { border-left: 2px solid var(--bf-divider); padding-left: 1rem; margin: 1rem 0; }
.bf-citation > p { font-size: 0.88rem; line-height: 1.65; margin: 0 0 0.5rem; }
.bf-citation-bibtex > summary { cursor: pointer; width: fit-content; padding: 0.6rem 0; min-height: 2.75rem; color: var(--bf-violet); font: 600 0.8rem/1.6 var(--bf-font-code); }
.bf-citation-bibtex > summary:hover { color: var(--bf-text); }
.bf-citation-bibtex .bf-code { margin: 0.5rem 0 0; }
.bf-shared-hero {
  border: 1px solid var(--bf-divider);
  border-radius: 8px;
  margin-bottom: 2rem;
  overflow: hidden;
}
.bf-shared-banner { display: block; width: 100%; height: auto; }
.bf-shared-hero-tools {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  align-items: center;
  gap: 1rem;
  padding: 1.25rem;
}
.bf-shared-hero-tools .bf-fireplace-actions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); margin: 0; gap: 0.65rem; }
.bf-shared-hero-tools .bf-fireplace-actions > a {
  justify-content: center;
  text-align: center;
  min-height: 2.8rem;
  flex: 1;
  white-space: nowrap;
}
.bf-shared-hero-tools .bf-hero-link {
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--bf-divider);
  border-radius: var(--bf-radius-button);
  padding: 0.65rem 0.75rem;
  text-decoration: none;
}
.bf-shared-hero-tools .bf-hero-link:hover { background: var(--bf-cream-surface); }
.bf-shared-hero-tools .bf-hero-install { margin: 0; max-width: none; width: 100%; box-shadow: none; }
.bf-shared-hero .bf-release-note {
  margin: 0;
  padding: 1rem 1.25rem;
  border: 0;
  border-top: 1px solid var(--bf-divider);
  border-radius: 0;
  background: var(--bf-cream-surface);
  gap: 1.25rem;
  align-items: baseline;
}
.bf-shared-hero .bf-release-note p { font-size: 0.82rem; }
.bf-shared-hero .bf-shared-intro { margin: 0; padding: 1.25rem; font-size: 0.92rem; line-height: 1.75; border-top: 1px solid var(--bf-divider); }
@media (max-width: 760px) {
  .bf-shared-hero-tools { padding: 1rem; }
  .bf-shared-hero .bf-release-note { grid-template-columns: minmax(0, 1fr); gap: 0.4rem; padding: 1rem; }
  .bf-shared-hero .bf-shared-intro { padding: 1rem; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after { animation: none !important; transition: none !important; }
}

'''


JS = r'''(() => {
  const input = document.querySelector("[data-search] input");
  const results = document.querySelector("[data-search-results]");
  const tocLinks = Array.from(document.querySelectorAll(".bf-toc a[href^='#'], .bf-nav-section[href^='#']"));
  const navToggle = document.querySelector("[data-nav-toggle]");
  const navDrawer = document.querySelector("[data-nav-drawer]");
  const navBackdrop = document.querySelector("[data-nav-close].bf-nav-backdrop");
  const navCloseButtons = Array.from(document.querySelectorAll("[data-nav-close]"));

  document.querySelectorAll("[data-nav-expand]").forEach((button) => {
    button.addEventListener("click", () => {
      const children = document.getElementById(button.getAttribute("aria-controls"));
      if (!children) return;
      const expanded = button.getAttribute("aria-expanded") !== "true";
      button.setAttribute("aria-expanded", String(expanded));
      button.querySelector("span").textContent = expanded ? "−" : "+";
      children.hidden = !expanded;
    });
  });

  function setNavOpen(open) {
    if (!navToggle || !navDrawer || !navBackdrop) return;
    document.body.classList.toggle("bf-nav-open", open);
    navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    navBackdrop.hidden = !open;
    if (open) {
      navDrawer.querySelector("a, button")?.focus({ preventScroll: true });
    } else {
      navToggle.focus({ preventScroll: true });
    }
  }

  if (navToggle && navDrawer && navBackdrop) {
    navToggle.addEventListener("click", () => {
      setNavOpen(navToggle.getAttribute("aria-expanded") !== "true");
    });
    navCloseButtons.forEach((button) => {
      button.addEventListener("click", () => setNavOpen(false));
    });
    navDrawer.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        if (window.matchMedia("(max-width: 920px)").matches) setNavOpen(false);
      });
    });
    window.addEventListener("resize", () => {
      if (!window.matchMedia("(max-width: 920px)").matches) setNavOpen(false);
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && document.body.classList.contains("bf-nav-open")) {
        setNavOpen(false);
      }
    });
  }

  function fallbackCopy(text) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "");
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.select();
    try {
      document.execCommand("copy");
    } finally {
      textarea.remove();
    }
  }

  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text).catch(() => {
        fallbackCopy(text);
      });
    }
    fallbackCopy(text);
    return Promise.resolve();
  }

  document.querySelectorAll("[data-copy-code]").forEach((button) => {
    const icon = button.querySelector("[data-copy-icon]");
    const label = button.querySelector(".bf-code__copy-label");
    const defaultIcon = icon ? icon.getAttribute("d") : "";
    const copiedIcon = "M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2Z";
    const errorIcon = "M11 7h2v7h-2V7Zm0 9h2v2h-2v-2Zm1-14 10 18H2L12 2Z";
    let resetTimer = null;

    function resetButton() {
      button.classList.remove("is-copied", "is-error");
      button.setAttribute("aria-label", "Copy code");
      button.setAttribute("title", "Copy code");
      if (label) label.textContent = "Copy";
      if (icon && defaultIcon) icon.setAttribute("d", defaultIcon);
    }

    button.addEventListener("click", async () => {
      const code = button.closest(".bf-code")?.querySelector("pre code");
      if (!code) return;
      if (resetTimer) window.clearTimeout(resetTimer);
      try {
        await copyText(code.textContent || "");
        button.classList.remove("is-error");
        button.classList.add("is-copied");
        button.setAttribute("aria-label", "Copied code");
        button.setAttribute("title", "Copied");
        if (label) label.textContent = "Copied";
        if (icon) icon.setAttribute("d", copiedIcon);
        resetTimer = window.setTimeout(resetButton, 1400);
      } catch {
        button.classList.remove("is-copied");
        button.classList.add("is-error");
        button.setAttribute("aria-label", "Could not copy code");
        button.setAttribute("title", "Could not copy");
        if (label) label.textContent = "Failed";
        if (icon) icon.setAttribute("d", errorIcon);
        resetTimer = window.setTimeout(resetButton, 1800);
      }
    });
  });

  document.querySelectorAll("[data-install-switcher]").forEach((switcher) => {
    const output = switcher.querySelector("[data-install-output]");
    const buttons = Array.from(switcher.querySelectorAll("[data-install-command]"));
    buttons.forEach((button) => {
      button.addEventListener("click", () => {
        buttons.forEach((item) => item.classList.remove("is-active"));
        button.classList.add("is-active");
        if (output) output.textContent = button.dataset.installCommand || "";
      });
    });
  });

  if (!input || !results) return;

  const indexUrl = document.body.dataset.searchIndex;
  let records = [];

  fetch(indexUrl)
    .then((response) => response.json())
    .then((data) => {
      records = data;
    })
    .catch(() => {
      records = [];
    });

  function closeResults() {
    results.hidden = true;
    results.innerHTML = "";
  }

  function excerpt(text, query) {
    const lower = text.toLowerCase();
    const position = lower.indexOf(query.toLowerCase());
    const start = Math.max(0, position - 80);
    return text.slice(start, start + 180).replace(/\s+/g, " ").trim();
  }

  function escapeHtml(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function highlight(text, query) {
    const escaped = escapeHtml(text);
    const safeQuery = query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    if (!safeQuery) return escaped;
    return escaped.replace(new RegExp(`(${safeQuery})`, "ig"), "<mark>$1</mark>");
  }

  function codeSnippet(record, query) {
    const lowerQuery = query.toLowerCase();
    const snippet = (record.code || []).find((block) => block.toLowerCase().includes(lowerQuery));
    if (!snippet) return "";
    const lines = snippet.split("\n").filter(Boolean).slice(0, 7).join("\n");
    return `<code class="bf-search__code">${highlight(lines, query)}</code>`;
  }

  function render(query) {
    const value = query.trim().toLowerCase();
    if (value.length < 2) {
      closeResults();
      return;
    }

    const matches = records
      .map((record) => {
        const haystack = `${record.title} ${record.text}`.toLowerCase();
        const score = haystack.includes(value) ? (record.title.toLowerCase().includes(value) ? 2 : 1) : 0;
        return { record, score };
      })
      .filter((item) => item.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 12);

    results.hidden = false;
    if (!matches.length) {
      results.innerHTML = '<div class="bf-search__meta">No matching documents</div>';
      return;
    }

    const root = document.body.dataset.root || ".";
    const meta = `<div class="bf-search__meta">${matches.length} matching result${matches.length === 1 ? "" : "s"}</div>`;
    const rows = matches
      .map(({ record }) => {
        const snippet = excerpt(record.text, value);
        return `<a class="bf-search__result" href="${root}/${record.url}"><strong>${highlight(record.title, value)}</strong><span>${highlight(snippet, value)}</span>${codeSnippet(record, value)}</a>`;
      })
      .join("");
    results.innerHTML = meta + rows;
  }

  input.addEventListener("input", () => render(input.value));
  input.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeResults();
  });
  document.addEventListener("click", (event) => {
    if (!event.target.closest("[data-search]")) closeResults();
  });

  if (tocLinks.length) {
    const headings = Array.from(document.querySelectorAll(".bf-article h2[id], .bf-article h3[id]"));
    const sectionIds = new Set(tocLinks
      .filter((link) => link.classList.contains("bf-nav-section"))
      .map((link) => decodeURIComponent(link.hash.slice(1))));
    const setActive = (id) => {
      const headingIndex = headings.findIndex((heading) => heading.id === id);
      const section = headings.slice(0, headingIndex + 1).reverse()
        .find((heading) => sectionIds.has(heading.id));
      tocLinks.forEach((link) => {
        const isSection = link.classList.contains("bf-nav-section");
        if (decodeURIComponent(link.hash.slice(1)) === (isSection ? section?.id : id)) {
          link.setAttribute("aria-current", isSection ? "location" : "true");
        } else {
          link.removeAttribute("aria-current");
        }
      });
    };

    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)[0];
        if (visible) setActive(visible.target.id);
      },
      { rootMargin: "-18% 0px -72% 0px", threshold: [0, 1] },
    );

    headings.forEach((heading) => observer.observe(heading));
    if (headings[0]) setActive(headings[0].id);
  }
})();
'''


def copy_assets() -> None:
    assets_dir = SITE / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    for source in (DOCS / "assets").glob("*"):
        if source.is_file():
            shutil.copy2(source, assets_dir / source.name)
    skill_source = DOCS / "ai" / "fyron-skill"
    if skill_source.exists():
        skill_dest = assets_dir / "fyron-skill"
        if skill_dest.exists():
            shutil.rmtree(skill_dest)
        shutil.copytree(
            skill_source,
            skill_dest,
            ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"),
        )
        archive_base = assets_dir / "fyron-skill"
        shutil.make_archive(str(archive_base), "zip", root_dir=skill_source)
    (assets_dir / "bf-docs.css").write_text(CSS, encoding="utf-8")
    (assets_dir / "bf-docs.js").write_text(JS, encoding="utf-8")


def write_search_indexes(records: list[dict[str, Any]]) -> None:
    """Write docs search indexes for the website."""
    payload = json.dumps(records, indent=2)
    (SITE / "assets" / "search-index.json").write_text(payload, encoding="utf-8")
    (SITE / "search-index.json").write_text(payload, encoding="utf-8")


def generate_reference_pages() -> None:
    """Generate exhaustive API reference Markdown before rendering."""
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "generate_function_reference.py")],
        check=True,
        cwd=ROOT,
    )


def build() -> None:
    generate_reference_pages()

    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)

    search_records = []
    rendered: dict[str, tuple[str, list[dict[str, str]], str]] = {}
    for page in PAGES:
        markdown = (DOCS / page.source).read_text(encoding="utf-8")
        rendered[page.output] = render_markdown(markdown, page)
        heading_ids = {item["id"] for item in rendered[page.output][1]}
        for _, anchor in SECTION_NAV.get(page.output, ()):
            if anchor not in heading_ids:
                raise ValueError(f"Sidebar section #{anchor} is missing in {page.source}")

    copy_assets()

    for page in PAGES:
        body, toc, plain_text = rendered[page.output]
        markdown = (DOCS / page.source).read_text(encoding="utf-8")
        output_path = SITE / page.output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_page(page, body, toc), encoding="utf-8")
        search_records.append(
            {
                "title": page.title,
                "group": page.group,
                "source": page.source,
                "url": page.output.replace("index.html", ""),
                "text": re.sub(r"\s+", " ", plain_text)[:5000],
                "code": extract_code_blocks(markdown),
            }
        )

    write_search_indexes(search_records)


if __name__ == "__main__":
    build()
