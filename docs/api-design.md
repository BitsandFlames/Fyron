# API Design

Fyron APIs are designed for clinical research workflows where another person should be able to inspect the inputs, assumptions, outputs, and artifacts without reading a hidden framework.

This page documents the public design conventions that new modules and functions should follow.

## Core Principles

| Principle | Meaning |
| --- | --- |
| Explicit assumptions | Clinical and statistical assumptions belong in parameter names, docstrings, tables, or manifests. |
| DataFrame-first | Cohorts, feature tables, metrics, and summaries should usually be `pandas.DataFrame` objects. |
| Ordinary Python inputs | Prefer DataFrames, arrays, dictionaries, paths, and fitted sklearn/lifelines-style objects. |
| Inspectable outputs | Return DataFrames, dictionaries, dataclasses, Matplotlib handles, file paths, or fitted estimators. |
| Optional extras | Heavy dependencies stay optional and raise clear install messages. |
| No hidden upload | Functions should not contact external systems unless the user explicitly configures a client or command. |

## Naming Conventions

Use parameter names that describe the clinical role:

| Pattern | Use |
| --- | --- |
| `id_col` | patient, study, series, lesion, or row identifier column |
| `duration_col`, `event_col` | survival endpoints |
| `group_col`, `hue` | stratification for tables and plots |
| `feature_cols`, `label_col`, `outcome_col` | ML or statistics inputs |
| `save_path`, `output_path` | explicit artifact destinations |
| `random_state` | reproducible stochastic behavior |

Avoid short generic names when a clinical name is clearer. A call with `duration_col="time"` and `event_col="death"` is easier to review than one that relies on hidden defaults.

## Return Shapes

| Function family | Preferred return |
| --- | --- |
| table builders and QC helpers | `pandas.DataFrame` |
| model fitting helpers | dict/dataclass with fitted object, metrics, and tables |
| plotting helpers | `(fig, ax)`, `(fig, axes)`, or `(fig, axes, table)` |
| file writers | resolved `Path` or manifest table |
| FHIR builders | plain JSON-serializable dictionaries |
| audit helpers | JSON-serializable dictionaries |

When a computed table is useful for reviewers, return it instead of hiding it inside a figure object.

## Optional Dependencies

Optional modules must fail clearly. Use messages like:

```text
Install with: uv add "fyron[visualization]"
```

Do not import optional packages at top level unless the module is itself optional and already raises a clear install message.

## Stable And Experimental APIs

Most public names that do not start with `_` are treated as stable once documented on module pages or in the generated reference.

Experimental APIs must say so in their docstring and docs page. They should explain what needs validation before study use, for example segmentation label assumptions, FHIR profile assumptions, or model-comparison limitations.

During public beta releases, new workflows can be marked beta when their behavior is useful but still expected to evolve. The beta label should appear in the docs page, CLI help or README section, and release notes. Curate is treated this way because it combines a Python package entrypoint with a local Docker Compose application.

## Deprecation Policy

Avoid breaking notebooks. When an API must change:

1. Add the replacement first.
2. Keep the old name as an alias when feasible.
3. Document the migration path.
4. Warn before removal.
5. Mention the change in the changelog.

## Design Checklist

Before adding a public function, confirm:

- the module is the right home,
- required columns or shapes are validated early,
- output shape is documented,
- clinical assumptions are explicit,
- optional dependencies are guarded,
- the example uses synthetic or de-identified data,
- tests cover both expected use and common failure modes.

## Related Pages

- [Using Fyron In Research](repository-trust.md)
- [Fyron Curate](applications/curate.md)
- [Modules Overview](modules/index.md)
- [Function Reference](function-reference.md)
- [Complete Function Reference](reference/index.md)
