# Cohort Flow Tracking

## Start Here

Keep your normal pandas code. Give each result a name:

```python
import pandas as pd
from fyron import FlowTracker

patients = pd.DataFrame({
    "patient_id": ["demo-1", "demo-2", "demo-3"],
    "age": [45, 16, 72],
})
flow = FlowTracker("Study cohort", id_col="patient_id", progress=True)
flow.add("Starting population", patients)

adults = patients.loc[patients["age"] >= 18].copy()
flow.add("Adults", adults, reason="Younger than 18")

table = flow.cohort_table()
assert table["n"].tolist() == [3, 2]
table.to_csv("cohort_flow.csv", index=False)
print(flow.to_text_flowchart())
# Optional, with plotting dependencies installed:
# fig, ax = flow.plot()
```

`add()` returns its input unchanged. With `id_col`, it counts distinct IDs,
rejects missing IDs, and records both removed and added members. Without
`id_col`, it counts rows and can only infer net changes, not membership changes.
The tracker keeps the previous cohort's ID set in memory; treat it and its
exported artifacts as research data.

## Queries And Live Feedback

Use a context only when you want a running message before an operation finishes:

```python
# client is an authenticated FHIRRestClient.
with flow.step("Retrieve encounters", kind="query") as step:
    result = client.query_df_from(
        df=adults,
        resource_type="Encounter",
        column_map={"subject": "patient_id"},
        fhir_paths=[
            ("patient_id", "subject.reference.replace('Patient/', '')"),
            ("encounter_id", "id"),
        ],
        return_report=True,
    )
    step.result(result)

encounters = result["data"]
selected = adults.loc[adults["patient_id"].isin(encounters["patient_id"])]
flow.add("Patients with encounters", selected)
```

Query activity does not change the cohort baseline. An encounter query can
produce many rows per patient without adding people to your cohort. Selection
remains explicit, as above. Review the query report before treating absent
matches as exclusions, especially when retrieval is page-limited.

Call `step.result(...)` exactly once. Successful context exit records the result
and elapsed seconds. Failure or interruption records its status, propagates the
exception, and never records a successful cohort selection. Failed steps have
an unknown count in the table, not a zero-person cohort.

- `flow.to_dataframe()` contains all recorded activities and their metadata.
- `flow.cohort_table()` contains completed cohort selections only.
- `flow.plot()` and text/console cohort summaries omit queries and failures.
- FHIR report summaries retain execution-complete and retrieval-exhaustive flags.
- `progress=False` (the default) disables live messages, not tracking.

Live messages use Fyron's console, not persistent network diagnostics. Use
nonidentifying labels and reasons. Do not put patient IDs, credentials, URLs, or
query values in labels; console output can itself be captured by notebooks or
schedulers. No remote exception text or result content is printed automatically.

The existing `add_step()` and `track_filter()` remain available and share the
same counting rules. Table columns are additive. Growth now records additions
rather than negative exclusions. The plot uses the existing cohort-count bar
plot, not an automatically generated branching CONSORT diagram.

## More Options

`fyron.flow` records cohort and filter steps as structured, reviewer-facing artifacts. Use it when you need to explain why patients entered or left a study cohort, not when you need a general workflow engine.

The module complements model explainability. `fyron.flow` explains **who entered the analysis**; `fyron.explainability` explains **which features influenced model behavior**.

## When To Use It

- You apply sequential inclusion and exclusion filters.
- You need a CONSORT/STROBE-style count trail.
- You want a console summary during notebooks or scripts.
- You want a Markdown/text flow chart for reports.
- You want a table compatible with `fyron.reporting.cohort_flow_table` and `fyron.plotting.plot_cohort_flow`.

## Imports

```python
from fyron.flow import FlowTracker, track_filter
```

Top-level imports also work:

```python
from fyron import FlowTracker, track_filter
```

## Core Concepts

| Concept | Meaning |
| --- | --- |
| `FlowTracker` | Holds ordered cohort/filter steps for one analysis. |
| step | One recorded DataFrame state after a filter, join, review, or endpoint step. |
| `n` | Number of rows after the step. Usually patients or analysis units. |
| `excluded` | Difference from the previous step. |
| `retained_percent` | Percent retained relative to the first recorded step. |
| `reason` | Human-readable exclusion reason. |
| metadata | Optional key/value details such as query params or reviewer notes. |

## API Contract

| Topic | Contract |
| --- | --- |
| Input shape | DataFrames passed manually to `add_step` or returned by decorated filter functions. |
| Required columns | No fixed columns are required, but the row unit must remain stable and should be documented in metadata. |
| Return shape | `FlowTracker` exports DataFrame, Markdown, and text-flowchart representations. |
| Saved artifacts | Flow table CSV, Markdown/text flow chart, plotted cohort flow, and provenance notes. |
| Failure modes | Decorated functions returning non-DataFrames, unstable row units, duplicate IDs hidden by joins, or missing metadata for key criteria. |

## Research Decisions To Make Explicit

Flow explainability is only useful when the unit of counting is clear. Decide before tracking whether one row means one patient, one study, one lesion, one series, or one prediction. Keep that row unit stable across the flow or add a manual step that explains why the unit changed.

| Decision | Document in |
| --- | --- |
| Source population and extraction date | first step metadata |
| Inclusion criteria | step labels and metadata |
| Exclusion reasons | `reason` |
| Row unit | first step metadata and manuscript methods |
| Duplicate handling | manual step after deduplication |
| Join behavior | manual step after merging tables |
| Endpoint construction | manual step with event/censoring assumptions |

## Manual Tracking

Manual tracking is best for joins, merges, review exports, external tools, or any step that is not a simple function call.

```python
from fyron.flow import FlowTracker

flow = FlowTracker("NSCLC CT cohort")

flow.add_step("Source FHIR cohort", raw)
flow.add_step(
    "Age >= 18",
    raw[raw["age"] >= 18],
    reason="age < 18",
    metadata={"criterion": "age_at_index >= 18"},
)
flow.add_step(
    "Has baseline CT",
    with_ct,
    reason="missing CT",
    metadata={"window": "index date -90 to +30 days"},
)
flow.add_step(
    "Has outcome follow-up",
    final,
    reason="missing follow-up",
    metadata={"minimum_followup_days": 90},
)

flow.print(color=False)
```

## Decorated Filters

Use `track_filter` for DataFrame-in/DataFrame-out filters that should be recorded automatically.

```python
from fyron.flow import FlowTracker, track_filter

flow = FlowTracker("NSCLC CT cohort")
flow.add_step("Source cohort", raw)

@track_filter(flow, label="Age >= 18", reason="age < 18")
def filter_adults(df):
    return df[df["age"] >= 18]

@track_filter(flow, label="Has baseline CT", reason="missing CT")
def filter_baseline_ct(df):
    return df[df["baseline_ct"].notna()]

cohort = filter_baseline_ct(filter_adults(raw))
```

Decorators deliberately require a `pandas.DataFrame` return value. Use manual `add_step` when a step returns several tables or needs local logic before recording.

## Joins, Duplicates, And Unit Changes

Use manual steps for operations where counts can change for reasons other than a simple filter. This makes the flow auditable instead of pretending a join is an exclusion criterion.

```python
flow.add_step("Source patients", patients, metadata={"row_unit": "patient"})

deduplicated = patients.drop_duplicates("patient_id")
flow.add_step(
    "Deduplicated patients",
    deduplicated,
    reason="duplicate patient_id",
    metadata={"id_col": "patient_id", "rule": "keep first reviewed row"},
)

with_imaging = deduplicated.merge(imaging, on="patient_id", how="inner")
flow.add_step(
    "Joined baseline imaging",
    with_imaging,
    reason="no matching baseline imaging row",
    metadata={"join": "inner", "on": "patient_id"},
)
```

If the row unit changes, say so in metadata. For example, going from one row per patient to one row per lesion should be a named manual step, not a hidden side effect.

## Outputs

```python
flow_table = flow.to_dataframe()
markdown = flow.to_markdown()
text_chart = flow.to_text_flowchart()
```

`flow.to_dataframe()` returns columns including `step`, `n`, `excluded`, `retained_percent`, `excluded_percent`, and `reason`. The `step` and `n` columns make it compatible with existing reporting and plotting helpers:

```python
from fyron import plotting as fp
from fyron import reporting as fr

table = flow.to_dataframe()
flow_markdown = fr.dataframe_to_markdown(table)
fig, ax = fp.plot_cohort_flow(table)
```

## What To Save

For manuscripts and reviewer responses, save all three forms when possible:

| Artifact | Use |
| --- | --- |
| `flow.to_dataframe()` | structured audit table and plotting input |
| `flow.to_markdown()` | methods supplement or protocol notes |
| `flow.to_text_flowchart()` | readable console/log output |

Add those files to your provenance manifest together with source cohort hashes, filter parameters, and output paths.

## Console Output

```text
fyron cohort flow: NSCLC CT cohort

[1] Source cohort       n=1,240
[2] Age >= 18           n=1,210   excluded=30   reason=age < 18
[3] Has baseline CT     n=830     excluded=380  reason=missing CT

Final cohort: 830 / 1,240 retained (66.9%)
```

## Common Pitfalls

- Record the source cohort first so retention percentages have a meaningful denominator.
- Use one row per patient or one row per analysis unit consistently.
- Keep reasons short and reviewer-facing.
- Do not hide clinical assumptions inside filter names; include key criteria in labels or metadata.
- Use manual steps for joins and endpoint construction where the row count may change for reasons other than filtering.

## Related Modules

- [Reporting](reporting.md) for flow tables and Markdown exports.
- [Clinical Plotting](plotting.md) for `plot_cohort_flow`.
- [Explainability](explainability.md) for model-level explanation tables.
- [Audit & Provenance](audit.md) for persisted run manifests.
