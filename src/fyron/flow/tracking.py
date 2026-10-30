"""Track cohort filter steps as reviewer-facing flow artifacts."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from functools import wraps
from time import monotonic
from typing import Any, TextIO, TypeVar

import pandas as pd

from fyron.console import info, supports_color

F = TypeVar("F", bound=Callable[..., pd.DataFrame])


@dataclass(frozen=True)
class FlowStep:
    """One recorded cohort/filter-flow step."""

    order: int
    label: str
    n: int
    excluded: int | None = None
    retained_percent: float | None = None
    excluded_percent: float | None = None
    reason: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


class FlowTracker:
    """Record ordered cohort filter steps and render flow summaries.

    Parameters
    ----------
    title:
        Human-readable name for the cohort or workflow.
    id_col:
        Optional analysis-unit column. Count distinct nonmissing IDs instead of
        rows and track membership changes between cohort steps.
    progress:
        Display nonidentifying step labels and counts on the interactive console.

    Examples
    --------
    >>> import pandas as pd
    >>> from fyron.flow import FlowTracker
    >>> flow = FlowTracker("Demo cohort")
    >>> raw = pd.DataFrame({"id": [1, 2, 3], "age": [70, 15, 60]})
    >>> flow.add_step("Source cohort", raw)
    >>> flow.add_step("Adults", raw[raw["age"] >= 18], reason="age < 18")
    >>> flow.to_dataframe()["n"].tolist()
    [3, 2]
    """

    def __init__(
        self, title: str = "Cohort flow", *, id_col: str | None = None,
        progress: bool = False,
    ) -> None:
        self.title = title
        self.steps: list[FlowStep] = []
        self.id_col = id_col
        self.progress = progress
        self._members: set | None = None
        self._cohort_n: int | None = None
        self._source_n: int | None = None

    def add(
        self, label: str, result: Any, *, reason: str | None = None,
        kind: str = "cohort",
    ) -> Any:
        """Record a result unchanged, counting unique IDs when configured.

        ``kind="query"`` records activity without changing the cohort baseline.
        Accept a DataFrame or Fyron's ``{"data": DataFrame, "report": ...}``
        result. Missing IDs are rejected. Labels/reasons are explicit research
        output: use nonidentifying labels when enabling console progress.

        Parameters
        ----------
        label:
            Nonidentifying step name.
        result:
            DataFrame or Fyron DataFrame/report dictionary.
        reason:
            Optional selection reason.
        kind:
            ``cohort`` for a selection, ``query`` for retrieval activity.

        Returns
        -------
        object
            The original result, unchanged.
        """
        if kind not in {"cohort", "query"}:
            raise ValueError("kind must be 'cohort' or 'query'.")
        df = result["data"] if isinstance(result, dict) else result
        self._validate_dataframe(df, context="result")
        members = None
        if self.id_col is not None:
            if self.id_col not in df or df[self.id_col].isna().any():
                raise ValueError("The configured ID column must exist and contain no missing IDs.")
            members = set(df[self.id_col])
        n = len(df) if members is None else len(members)
        excluded = added = None
        if kind == "cohort":
            if self._cohort_n is not None:
                if members is not None and self._members is not None:
                    excluded = len(self._members - members)
                    added = len(members - self._members)
                else:
                    excluded = max(0, self._cohort_n - n)
                    added = max(0, n - self._cohort_n)
            if self._source_n is None:
                self._source_n = n
        metadata = {"kind": kind, "status": "complete", "rows": len(df), "added": added}
        if isinstance(result, dict) and "report" in result:
            summary = result["report"]["summary"]
            for key in ("execution_complete", "retrieval_exhaustive"):
                if key in summary and len(summary) == 1:
                    metadata[key] = bool(summary[key].iloc[0])
        self.steps.append(FlowStep(
            order=len(self.steps) + 1, label=str(label), n=n,
            excluded=excluded, reason=reason, metadata=metadata,
            retained_percent=(
                (100 * n / self._source_n if self._source_n else 0.0)
                if kind == "cohort" else None
            ),
            excluded_percent=(
                100 * excluded / self._cohort_n
                if excluded is not None and self._cohort_n else None
            ),
        ))
        if kind == "cohort":
            self._members, self._cohort_n = members, n
        if self.progress:
            detail = f"{n:,} units / {len(df):,} rows"
            if excluded is not None:
                detail += f"; excluded {excluded:,}; added {added:,}"
            if metadata.get("retrieval_exhaustive") is False:
                detail += "; retrieval not exhaustive"
            info(f"{label}: {detail}")
        return result

    def step(self, label: str, *, kind: str = "cohort", reason: str | None = None):
        """Announce an operation and record its result on successful context exit.

        Call ``step.result(data)`` once inside the context. Exceptions propagate
        and record a failed activity without storing exception text or changing
        the cohort baseline.

        Parameters
        ----------
        label:
            Nonidentifying operation name.
        kind:
            ``cohort`` or ``query``.
        reason:
            Optional selection reason.

        Returns
        -------
        context manager
            A step with a ``result(value)`` method.
        """
        if kind not in {"cohort", "query"}:
            raise ValueError("kind must be 'cohort' or 'query'.")
        return _StepContext(self, label, kind, reason)

    def cohort_table(self) -> pd.DataFrame:
        """Return only completed cohort selections, excluding query activities."""
        table = self.to_dataframe()
        if table.empty:
            return table
        kinds = table.get("metadata.kind", pd.Series("cohort", index=table.index)).fillna("cohort")
        statuses = table.get("metadata.status", pd.Series("complete", index=table.index)).fillna("complete")
        return table.loc[(kinds == "cohort") & (statuses == "complete")].copy()

    def plot(self, **kwargs: Any):
        """Plot completed cohort selections using Fyron's plotting facade.

        Requires the plotting dependencies. Returns the plotting function's
        figure/axes result; query activities and failures are omitted.

        Parameters
        ----------
        kwargs:
            Options forwarded to ``fyron.plotting.plot_cohort_flow``.

        Returns
        -------
        tuple
            Figure and axes from the existing plotting function.
        """
        from fyron.plotting import plot_cohort_flow

        table = self.cohort_table()
        if table.empty:
            raise ValueError("No completed cohort steps to plot.")
        kwargs.setdefault("title", self.title)
        return plot_cohort_flow(table, **kwargs)

    def add_step(
        self,
        label: str,
        df: pd.DataFrame,
        *,
        reason: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> pd.DataFrame:
        """Record a DataFrame step and return ``df`` unchanged.

        Parameters
        ----------
        label:
            Short reviewer-facing step label.
        df:
            DataFrame after the filter or workflow step.
        reason:
            Optional exclusion reason, usually describing why rows were removed
            from the previous step.
        metadata:
            Optional JSON-like metadata such as filter parameters or notes.

        Returns
        -------
        pandas.DataFrame
            The same DataFrame object passed to ``df`` for pipeline-friendly use.
        """
        self._validate_dataframe(df, context=label)
        self.add(label, df, reason=reason)
        reserved = self.steps[-1].metadata
        self.steps[-1].metadata.update({
            key: value for key, value in (metadata or {}).items() if key not in reserved
        })
        return df

    def to_dataframe(self) -> pd.DataFrame:
        """Return the recorded flow as a structured DataFrame.

        The output includes ``step`` and ``n`` columns so it can be passed
        directly to ``fyron.reporting.cohort_flow_table`` or
        ``fyron.plotting.plot_cohort_flow``.
        """
        rows = []
        for step in self.steps:
            row = {
                "order": step.order,
                "step": step.label,
                "n": step.n if step.metadata.get("status", "complete") == "complete" else None,
                "excluded": step.excluded,
                "retained_percent": step.retained_percent,
                "excluded_percent": step.excluded_percent,
                "reason": step.reason,
            }
            row.update({f"metadata.{key}": value for key, value in step.metadata.items()})
            rows.append(row)
        return pd.DataFrame(rows)

    def to_markdown(self, *, digits: int = 1) -> str:
        """Render the flow as a Markdown table."""
        table = self.to_dataframe().copy()
        if table.empty:
            return "| order | step | n | excluded | retained_percent | reason |\n| --- | --- | --- | --- | --- | --- |"
        for col in ("retained_percent", "excluded_percent"):
            if col in table.columns:
                table[col] = table[col].map(lambda value: "" if pd.isna(value) else f"{float(value):.{digits}f}%")
        return _dataframe_to_markdown(table)

    def to_text_flowchart(self, *, digits: int = 1) -> str:
        """Render an arrow-style text flow chart."""
        steps = self._cohort_steps()
        if not steps:
            return f"{self.title}\n(no steps recorded)"
        lines = [self.title]
        for index, step in enumerate(steps):
            label = f"{step.label} (n={step.n:,}"
            if step.excluded is not None:
                label += f"; excluded {step.excluded:,}"
            if step.retained_percent is not None:
                label += f"; retained {step.retained_percent:.{digits}f}%"
            label += ")"
            if step.reason:
                label += f" [{step.reason}]"
            prefix = "" if index == 0 else "  -> "
            lines.append(f"{prefix}{label}")
        final = steps[-1]
        source = steps[0].n
        retained = 100.0 * final.n / source if source else 0.0
        lines.append(f"  => Final cohort (n={final.n:,}; retained {retained:.{digits}f}%)")
        return "\n".join(lines)

    def print(
        self,
        *,
        stream: TextIO | None = None,
        color: bool = True,
        quiet: bool = False,
    ) -> str:
        """Print and return a Bits & Flames-style console flow summary."""
        text = self._console_text(color=color and supports_color(stream))
        if not quiet:
            print(text, file=stream)
        return text

    def _console_text(self, *, color: bool) -> str:
        title = f"fyron cohort flow: {self.title}"
        if color:
            title = f"\033[38;2;255;106;26m{title}\033[0m"
        steps = self._cohort_steps()
        if not steps:
            return f"{title}\n\n(no steps recorded)"
        width = max(len(step.label) for step in steps)
        lines = [title, ""]
        for step in steps:
            excluded = "" if step.excluded is None else f"   excluded={step.excluded:,}"
            reason = "" if not step.reason else f"   reason={step.reason}"
            lines.append(f"[{step.order}] {step.label:<{width}}   n={step.n:,}{excluded}{reason}")
        source = steps[0].n
        final = steps[-1].n
        retained = 100.0 * final / source if source else 0.0
        lines.append("")
        lines.append(f"Final cohort: {final:,} / {source:,} retained ({retained:.1f}%)")
        return "\n".join(lines)

    def _cohort_steps(self):
        return [
            step for step in self.steps
            if step.metadata.get("kind", "cohort") == "cohort"
            and step.metadata.get("status", "complete") == "complete"
        ]

    @staticmethod
    def _validate_dataframe(value: Any, *, context: str) -> None:
        if not isinstance(value, pd.DataFrame):
            raise TypeError(f"Flow step {context!r} must be a pandas DataFrame, got {type(value).__name__}.")


def track_filter(
    tracker: FlowTracker,
    *,
    label: str,
    reason: str | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> Callable[[F], F]:
    """Decorate a DataFrame filter function and record its output.

    Parameters
    ----------
    tracker:
        FlowTracker instance that receives the recorded step.
    label:
        Reviewer-facing label for the filter.
    reason:
        Optional exclusion reason.
    metadata:
        Optional JSON-like metadata saved with the step.

    Returns
    -------
    callable
        Wrapped function that returns the original DataFrame result after
        recording it in ``tracker``.
    """

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
            result = func(*args, **kwargs)
            FlowTracker._validate_dataframe(result, context=label)
            tracker.add_step(label, result, reason=reason, metadata=metadata)
            return result

        return wrapper  # type: ignore[return-value]

    return decorator


class _StepContext:
    def __init__(self, tracker, label, kind, reason):
        self.tracker, self.label, self.kind, self.reason = tracker, label, kind, reason
        self._has_result = False

    def __enter__(self):
        self.started = monotonic()
        if self.tracker.progress:
            info(f"{self.label}: running")
        return self

    def result(self, value):
        if self._has_result:
            raise ValueError("Record exactly one result per step.")
        self.value, self._has_result = value, True
        return value

    def _failed(self, status):
        self.tracker.steps.append(FlowStep(
            order=len(self.tracker.steps) + 1, label=str(self.label), n=0,
            metadata={"kind": self.kind, "status": status,
                      "elapsed_seconds": monotonic() - self.started},
        ))
        if self.tracker.progress:
            info(f"{self.label}: {status}")

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self._failed("interrupted" if issubclass(exc_type, (KeyboardInterrupt, SystemExit)) else "failed")
            return False
        try:
            if not self._has_result:
                raise ValueError("Call step.result(data) before leaving the step.")
            self.tracker.add(self.label, self.value, reason=self.reason, kind=self.kind)
        except BaseException:
            self._failed("failed")
            raise
        self.tracker.steps[-1].metadata["elapsed_seconds"] = monotonic() - self.started
        return False


def _dataframe_to_markdown(df: pd.DataFrame) -> str:
    headers = [str(col) for col in df.columns]
    rows = [["" if pd.isna(value) else str(value) for value in row] for row in df.to_numpy()]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)
