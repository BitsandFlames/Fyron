#!/usr/bin/env python3
"""Generate exhaustive Fyron function reference Markdown from source AST."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "fyron"
OUT = ROOT / "docs" / "reference"
MISSING_DESCRIPTION = "See the signature and linked module guide for context."
MISSING_RETURN = "See the function signature and module guide."
MISSING_PARAM = "See signature."
PRIORITY_DOCSTRING_MODULES = (
    "fyron",
    "fyron.core.io",
    "fyron.curate",
    "fyron.dicom.client",
    "fyron.fhir.rest",
    "fyron.imaging.",
    "fyron.ml.evaluation",
    "fyron.ml.metrics",
    "fyron.ml.pipeline",
    "fyron.ml.plots",
    "fyron.ml.training",
    "fyron.plotting",
    "fyron.plotting_palettes",
    "fyron.survival.",
)
PRIORITY_DOCSTRING_GUIDANCE = (
    "`fyron`, `core`, `fhir`, `dicom`, `imaging`, `survival`, `ml`, `plotting`, and `curate` "
    "are the first public-beta documentation surfaces. Treat the priority backlog as the milestone "
    "for first external users; the full backlog below remains useful for long-tail polishing."
)


@dataclass(frozen=True)
class ReferenceGroup:
    slug: str
    title: str
    prefixes: tuple[str, ...]
    guide: str
    description: str


GROUPS = (
    ReferenceGroup(
        "fhir",
        "FHIR Reference",
        ("fyron.fhir.",),
        "../modules/fhir.md",
        "FHIR REST, SQL, authentication, resource builders, mapping, and defensive extraction helpers.",
    ),
    ReferenceGroup(
        "dicom-imaging",
        "DICOM And Imaging Reference",
        ("fyron.dicom.", "fyron.imaging."),
        "../modules/dicom.md",
        "DICOMweb downloads, synthetic DICOM/NIfTI export, DICOM SEG, image I/O, normalization, QC, and segmentation metrics.",
    ),
    ReferenceGroup(
        "boa",
        "BOA Reference",
        ("fyron.boa_extraction.", "fyron.boa_radiomics.", "fyron.visualization."),
        "../modules/boa.md",
        "Body-and-Organ-Analysis feature extraction, radiomics, experimental aortic calcification, and visual collages.",
    ),
    ReferenceGroup(
        "cohort-analysis",
        "Cohort And Analysis Reference",
        (
            "fyron.cohort.",
            "fyron.dataframe",
            "fyron.preprocessing.",
            "fyron.descriptive.",
            "fyron.statistics.",
            "fyron.phenotyping.",
        ),
        "../modules/cohort.md",
        "Cohort construction, preprocessing, descriptive tables, statistical tests, effects, bootstrap intervals, and phenotype rules.",
    ),
    ReferenceGroup(
        "survival",
        "Survival Reference",
        ("fyron.survival.",),
        "../modules/survival.md",
        "Kaplan-Meier curves, RMST, Cox models, proportional hazards diagnostics, AFT models, and survival boosting.",
    ),
    ReferenceGroup(
        "ml-validation",
        "ML, Validation, And Explainability Reference",
        (
            "fyron.ml.",
            "fyron.feature_selection.",
            "fyron.validation.",
            "fyron.explainability.",
            "fyron.flow.",
        ),
        "../modules/ml.md",
        "Classification pipelines, metrics, plotting wrappers, feature selection, validation, model interpretation, and filter-flow explainability.",
    ),
    ReferenceGroup(
        "core-publication",
        "Core, Publication, And Utility Reference",
        (
            "fyron.core.",
            "fyron.datasets",
            "fyron.documents.",
            "fyron.llm.",
            "fyron.plotting.",
            "fyron.reporting.",
            "fyron.audit.",
            "fyron.console",
            "fyron.banner",
        ),
        "../modules/core.md",
        "Core I/O, documents, LLM helpers, reporting, audit manifests, console utilities, and banner helpers.",
    ),
)


@dataclass
class ParameterDoc:
    name: str
    annotation: str = ""
    default: str = ""
    required: bool = True
    description: str = ""


@dataclass
class ApiDoc:
    kind: str
    name: str
    qualname: str
    module: str
    import_path: str
    signature: str
    description: str
    returns: str
    params: list[ParameterDoc] = field(default_factory=list)
    methods: list["ApiDoc"] = field(default_factory=list)


def module_name(path: Path) -> str:
    rel = path.relative_to(ROOT / "src").with_suffix("")
    if rel.name == "__init__":
        rel = rel.parent
    return ".".join(rel.parts)


def clean_doc(text: str) -> str:
    text = " ".join(line.strip() for line in text.strip().splitlines() if line.strip())
    return text.replace("|", " or ")


def first_paragraph(docstring: str | None) -> str:
    if not docstring:
        return MISSING_DESCRIPTION
    lines = [line.rstrip() for line in docstring.strip().splitlines()]
    paragraph: list[str] = []
    for line in lines:
        if not line.strip():
            if paragraph:
                break
            continue
        stripped = line.strip()
        if stripped.lower() in {"parameters", "args", "arguments", "returns", "return"}:
            break
        if set(stripped) <= {"-"}:
            continue
        paragraph.append(stripped)
    return clean_doc(" ".join(paragraph)) if paragraph else MISSING_DESCRIPTION


def parse_docstring_sections(docstring: str | None) -> tuple[dict[str, str], str]:
    if not docstring:
        return {}, ""
    lines = docstring.expandtabs().splitlines()
    params: dict[str, str] = {}
    returns: list[str] = []
    section = ""
    current_param: str | None = None
    i = 0
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        lower = stripped.lower()
        next_stripped = lines[i + 1].strip() if i + 1 < len(lines) else ""
        is_section_heading = not section or (set(next_stripped) <= {"-"} and bool(next_stripped))
        if lower in {"parameters", "args", "arguments"} and is_section_heading:
            section = "params"
            current_param = None
            if set(next_stripped) <= {"-"} and next_stripped:
                i += 2
                continue
            i += 1
            continue
        if lower in {"returns", "return"} and is_section_heading:
            section = "returns"
            current_param = None
            if set(next_stripped) <= {"-"} and next_stripped:
                i += 2
                continue
            i += 1
            continue
        if re.match(r"^[A-Z][A-Za-z ]+$", stripped) and section and not raw.startswith((" ", "\t")):
            section = ""
            current_param = None
        if section == "params":
            if not stripped:
                i += 1
                continue
            match = re.match(r"^([A-Za-z_][\w]*(?:\s*,\s*[A-Za-z_][\w]*)*)(?:\s*:\s*(.*))?$", stripped)
            if match and not raw.startswith((" ", "\t")):
                names = [name.strip() for name in match.group(1).split(",")]
                current_param = names[-1]
                desc = match.group(2) or ""
                for name in names:
                    params[name] = clean_doc(desc)
            elif current_param:
                params[current_param] = clean_doc(f"{params[current_param]} {stripped}".strip())
        elif section == "returns":
            if stripped and not set(stripped) <= {"-"}:
                returns.append(stripped)
        i += 1
    if len(returns) >= 2:
        return params, f"`{clean_doc(returns[0])}` - {clean_doc(' '.join(returns[1:]))}"
    return params, clean_doc(" ".join(returns))


def unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def render_default(node: ast.AST | None) -> str:
    value = unparse(node)
    if len(value) > 60:
        return value[:57] + "..."
    return value


def signature_for(name: str, args: ast.arguments, returns: ast.AST | None = None) -> tuple[str, list[ParameterDoc]]:
    params: list[ParameterDoc] = []
    pieces: list[str] = []
    pos_args = list(args.posonlyargs) + list(args.args)
    defaults: list[ast.AST | None] = [None] * (len(pos_args) - len(args.defaults)) + list(args.defaults)

    def add_arg(arg: ast.arg, default_node: ast.AST | None, prefix: str = "") -> None:
        annotation = unparse(arg.annotation)
        default = render_default(default_node) if default_node is not None else ""
        label = f"{prefix}{arg.arg}"
        if annotation:
            label += f": {annotation}"
        if default_node is not None:
            label += f" = {default}"
        pieces.append(label)
        params.append(
            ParameterDoc(
                name=arg.arg,
                annotation=annotation,
                default=default,
                required=default_node is None,
            )
        )

    for arg, default in zip(pos_args, defaults):
        add_arg(arg, default)
    if args.vararg:
        add_arg(args.vararg, None, "*")
    elif args.kwonlyargs:
        pieces.append("*")
    for arg, default in zip(args.kwonlyargs, args.kw_defaults):
        add_arg(arg, default)
    if args.kwarg:
        add_arg(args.kwarg, None, "**")

    return_annotation = unparse(returns)
    signature = f"{name}({', '.join(pieces)})"
    if return_annotation:
        signature += f" -> {return_annotation}"
    return signature, params


def doc_for_function(node: ast.FunctionDef | ast.AsyncFunctionDef, module: str, qualname: str) -> ApiDoc:
    docstring = ast.get_docstring(node)
    param_docs, returns = parse_docstring_sections(docstring)
    signature, params = signature_for(node.name, node.args, node.returns)
    for param in params:
        param.description = param_docs.get(param.name, "")
    if not returns and node.returns is not None:
        returns = f"`{unparse(node.returns)}`"
    return ApiDoc(
        kind="function",
        name=node.name,
        qualname=qualname,
        module=module,
        import_path=f"{module}.{qualname}",
        signature=signature,
        description=first_paragraph(docstring),
        returns=returns or MISSING_RETURN,
        params=params,
    )


def init_signature(node: ast.ClassDef) -> tuple[str, list[ParameterDoc]]:
    for item in node.body:
        if isinstance(item, ast.FunctionDef) and item.name == "__init__":
            signature, params = signature_for(node.name, item.args, None)
            params = [param for param in params if param.name != "self"]
            return signature, params
    return f"{node.name}()", []


def doc_for_class(node: ast.ClassDef, module: str) -> ApiDoc:
    docstring = ast.get_docstring(node)
    param_docs, returns = parse_docstring_sections(docstring)
    signature, params = init_signature(node)
    for param in params:
        param.description = param_docs.get(param.name, "")
    methods: list[ApiDoc] = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and not item.name.startswith("_"):
            method = doc_for_function(item, module, f"{node.name}.{item.name}")
            method.signature = method.signature.replace(f"{item.name}(", f"{node.name}.{item.name}(", 1)
            method.params = [param for param in method.params if param.name not in {"self", "cls"}]
            methods.append(method)
    return ApiDoc(
        kind="class",
        name=node.name,
        qualname=node.name,
        module=module,
        import_path=f"{module}.{node.name}",
        signature=signature,
        description=first_paragraph(docstring),
        returns=returns or "Class constructor.",
        params=params,
        methods=methods,
    )


def collect_api_docs() -> list[ApiDoc]:
    docs: list[ApiDoc] = []
    for path in sorted(SRC.rglob("*.py")):
        if path.name.startswith("_") and path.name != "__init__.py":
            continue
        mod = module_name(path)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_") or node.name == "main":
                    continue
                docs.append(doc_for_function(node, mod, node.name))
            elif isinstance(node, ast.ClassDef):
                if node.name.startswith("_") or node.name.endswith("Error"):
                    continue
                docs.append(doc_for_class(node, mod))
    return docs


def group_for(api: ApiDoc) -> ReferenceGroup:
    for group in GROUPS:
        if api.module.startswith(group.prefixes):
            return group
    return GROUPS[-1]


def anchor_for(api: ApiDoc) -> str:
    value = api.import_path.lower()
    value = re.sub(r"[^a-z0-9\s-]", "", value)
    value = re.sub(r"\s+", "-", value).strip("-")
    return value or "section"


def render_params(params: list[ParameterDoc]) -> str:
    if not params:
        return "No parameters documented.\n"
    lines = [
        "| Parameter | Required | Type | Default | Description |",
        "| --- | --- | --- | --- | --- |",
    ]
    for param in params:
        lines.append(
            "| "
            + f"`{param.name}` | "
            + ("yes" if param.required else "no")
            + " | "
            + (f"`{param.annotation.replace('|', ' or ')}`" if param.annotation else "")
            + " | "
            + (f"`{param.default.replace('|', ' or ')}`" if param.default else "")
            + " | "
            + (param.description or MISSING_PARAM)
            + " |"
        )
    return "\n".join(lines) + "\n"


def render_api(api: ApiDoc, group: ReferenceGroup, level: int = 2) -> str:
    heading = "#" * level
    lines = [
        f"{heading} `{api.import_path}`",
        "",
        api.description,
        "",
        "**Import path:** `" + api.import_path + "`",
        "",
        "```python",
        api.signature,
        "```",
        "",
        "### Parameters" if level == 2 else "#### Parameters",
        "",
        render_params(api.params),
        "### Returns" if level == 2 else "#### Returns",
        "",
        api.returns,
        "",
        f"**See also:** [{group.title.replace(' Reference', '')} module guide]({group.guide}).",
        "",
    ]
    if api.methods:
        lines.extend(["### Public Methods", ""])
        for method in api.methods:
            lines.extend(render_api(method, group, level=4).splitlines())
            lines.append("")
    return "\n".join(lines)


def write_group_page(group: ReferenceGroup, apis: list[ApiDoc]) -> None:
    lines = [
        f"# {group.title}",
        "",
        group.description,
        "",
        f"For workflow context, see [{group.title.replace(' Reference', '')} module guide]({group.guide}).",
        "",
        "## Functions And Classes",
        "",
    ]
    for api in apis:
        lines.append(f"- [`{api.import_path}`](#{anchor_for(api)})")
        for method in api.methods:
            lines.append(f"- [`{method.import_path}`](#{anchor_for(method)})")
    lines.append("")
    for api in apis:
        lines.append(render_api(api, group))
    (OUT / f"{group.slug}.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def warn_docstring_coverage(apis: list[ApiDoc]) -> None:
    weak = priority_docstring_entries(weak_docstring_entries(apis))
    if weak:
        preview = ", ".join(entry["import_path"] for entry in weak[:10])
        suffix = "" if len(weak) <= 10 else f", ... (+{len(weak) - 10} more)"
        print(f"WARNING: {len(weak)} priority public APIs have incomplete docstring coverage: {preview}{suffix}")


def weak_docstring_entries(apis: list[ApiDoc]) -> list[dict[str, str]]:
    all_docs: list[ApiDoc] = []
    for api in apis:
        all_docs.append(api)
        all_docs.extend(api.methods)
    weak: list[dict[str, str]] = []
    for api in all_docs:
        issues: list[str] = []
        if api.description == MISSING_DESCRIPTION:
            issues.append("missing description")
        if api.returns == MISSING_RETURN:
            issues.append("missing return documentation")
        missing_params = [
            param.name
            for param in api.params
            if param.name not in {"self", "cls"} and not param.description
        ]
        if missing_params:
            issues.append("missing parameter descriptions: " + ", ".join(missing_params))
        if issues:
            weak.append(
                {
                    "module": api.module,
                    "import_path": api.import_path,
                    "issues": "; ".join(issues),
                }
            )
    return weak


def is_priority_docstring_entry(entry: dict[str, str]) -> bool:
    module = entry["module"]
    if module == "fyron":
        return True
    return any(module.startswith(prefix) for prefix in PRIORITY_DOCSTRING_MODULES if prefix != "fyron")


def priority_docstring_entries(entries: list[dict[str, str]]) -> list[dict[str, str]]:
    return [entry for entry in entries if is_priority_docstring_entry(entry)]


def append_coverage_table(lines: list[str], entries: list[dict[str, str]]) -> None:
    by_module: dict[str, list[dict[str, str]]] = {}
    for entry in entries:
        by_module.setdefault(entry["module"], []).append(entry)
    for module in sorted(by_module):
        lines.extend([f"## `{module}`", "", "| API | Issues |", "| --- | --- |"])
        for entry in sorted(by_module[module], key=lambda item: item["import_path"]):
            lines.append(f"| `{entry['import_path']}` | {entry['issues']} |")
        lines.append("")


def write_docstring_coverage(apis: list[ApiDoc]) -> None:
    weak = weak_docstring_entries(apis)
    priority = priority_docstring_entries(weak)
    lines = [
        "# Docstring Coverage Report",
        "",
        "This generated report lists public APIs whose generated reference entries are incomplete. It is a quality-control artifact for maintainers; the module guides remain the main workflow documentation.",
        "",
        f"Priority public-beta APIs with incomplete docstring coverage: **{len(priority)}**.",
        "",
        f"Full generated backlog: **{len(weak)}** incomplete API entries.",
        "",
        "## How To Use This Report",
        "",
        f"- {PRIORITY_DOCSTRING_GUIDANCE}",
        "- Add a short first docstring paragraph, parameter descriptions, and return notes.",
        "- Public APIs are documented package exports and top-level workflow helpers; underscore-prefixed modules and helpers are internal and may change without compatibility guarantees.",
        "- Regenerate the docs with `uv run python scripts/build_docs.py`.",
        "",
        "## Priority Public-Beta Backlog",
        "",
    ]
    append_coverage_table(lines, priority)
    lines.extend(["## Full Generated Backlog", ""])
    append_coverage_table(lines, weak)
    (OUT / "docstring-coverage.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def write_index(grouped: dict[str, list[ApiDoc]]) -> None:
    lines = [
        "# Complete Function Reference",
        "",
        "This generated reference documents Fyron public functions, classes, methods, signatures, parameters, defaults, and return notes directly from the source tree. It complements the curated module pages, which explain workflows, interpretation, and common pitfalls.",
        "",
        "The generator is AST-based, so optional extras are not imported during documentation builds.",
        "",
        "Use this page for exact call signatures. Use the linked module guides for input shapes, required columns, saved artifacts, failure modes, and clinical interpretation.",
        "",
        "## Reference Groups",
        "",
    ]
    for group in GROUPS:
        apis = grouped.get(group.slug, [])
        lines.append(f"- [{group.title}]({group.slug}.md): {len(apis)} top-level public APIs.")
    lines.extend(["", "## Public API Index", ""])
    for group in GROUPS:
        apis = grouped.get(group.slug, [])
        lines.extend([f"### {group.title}", ""])
        for api in apis:
            lines.append(f"- [`{api.import_path}`]({group.slug}.md#{anchor_for(api)})")
            for method in api.methods:
                lines.append(f"- [`{method.import_path}`]({group.slug}.md#{anchor_for(method)})")
        lines.append("")
    (OUT / "index.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    apis = collect_api_docs()
    grouped: dict[str, list[ApiDoc]] = {group.slug: [] for group in GROUPS}
    for api in apis:
        grouped[group_for(api).slug].append(api)
    for group in GROUPS:
        grouped[group.slug].sort(key=lambda item: item.import_path)
        write_group_page(group, grouped[group.slug])
    write_index(grouped)
    write_docstring_coverage(apis)
    warn_docstring_coverage(apis)


if __name__ == "__main__":
    main()
