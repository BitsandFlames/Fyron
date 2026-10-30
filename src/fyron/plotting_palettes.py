"""Scientific color palettes and Matplotlib styles for Fyron plots."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Sequence
import warnings

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, to_hex, to_rgb

PaletteKind = Literal["qualitative", "sequential", "diverging"]


@dataclass(frozen=True)
class PaletteSpec:
    """Metadata for one named scientific color palette."""

    name: str
    kind: PaletteKind
    colors: tuple[str, ...]
    max_recommended: int | None
    colorblind_safe: bool
    source_note: str


PALETTES: dict[str, PaletteSpec] = {
    "okabe_ito": PaletteSpec(
        name="okabe_ito",
        kind="qualitative",
        colors=("#000000", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"),
        max_recommended=8,
        colorblind_safe=True,
        source_note="Okabe-Ito colorblind-safe qualitative palette.",
    ),
    "wong": PaletteSpec(
        name="wong",
        kind="qualitative",
        colors=("#000000", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00"),
        max_recommended=7,
        colorblind_safe=True,
        source_note="Wong/Okabe-Ito style colorblind-safe qualitative palette.",
    ),
    "muted_scientific": PaletteSpec(
        name="muted_scientific",
        kind="qualitative",
        colors=("#4E79A7", "#F28E2B", "#59A14F", "#E15759", "#B07AA1", "#76B7B2"),
        max_recommended=6,
        colorblind_safe=False,
        source_note="Muted journal-style categorical palette for up to six groups.",
    ),
    "nature_cool": PaletteSpec(
        name="nature_cool",
        kind="qualitative",
        colors=("#386CB0", "#7FC97F", "#BEAED4"),
        max_recommended=3,
        colorblind_safe=False,
        source_note="Cool Nature-style two-to-three group comparison palette.",
    ),
    "bf": PaletteSpec(
        name="bf",
        kind="qualitative",
        colors=("#4D9ED8", "#E56B6F", "#8E7CC3", "#F2A65A", "#5F6872", "#5B8E7D"),
        max_recommended=6,
        colorblind_safe=False,
        source_note="Bits & Flames / BOARISK brand-compatible palette.",
    ),
    "bf_core": PaletteSpec(
        name="bf_core",
        kind="qualitative",
        colors=("#243B53", "#4D9ED8", "#F2A65A", "#E56B6F", "#5B8E7D", "#8E7CC3"),
        max_recommended=6,
        colorblind_safe=False,
        source_note="Balanced Bits & Flames palette for branded clinical dashboards and slide figures.",
    ),
    "bf_flames": PaletteSpec(
        name="bf_flames",
        kind="qualitative",
        colors=("#7F1D1D", "#C2410C", "#F97316", "#F2A65A", "#FACC15", "#475569"),
        max_recommended=6,
        colorblind_safe=False,
        source_note="Warm Bits & Flames palette for emphasis, highlights, and branded presentation figures.",
    ),
    "bf_embers": PaletteSpec(
        name="bf_embers",
        kind="qualitative",
        colors=("#111827", "#374151", "#64748B", "#4D9ED8", "#5B8E7D", "#E56B6F"),
        max_recommended=6,
        colorblind_safe=False,
        source_note="Cool ember-inspired Bits & Flames palette for quiet clinical analytics figures.",
    ),
    "bf_vibrant": PaletteSpec(
        name="bf_vibrant",
        kind="qualitative",
        colors=("#D72660", "#4E2284", "#FFC845", "#009DE0", "#1C163D"),
        max_recommended=5,
        colorblind_safe=False,
        source_note="High-contrast Bits & Flames palette for vibrant branded figures and presentation highlights.",
    ),
    "bf_vibrant_muted": PaletteSpec(
        name="bf_vibrant_muted",
        kind="qualitative",
        colors=("#B84A6D", "#66508D", "#E6B65A", "#3F9FCB", "#332E55"),
        max_recommended=5,
        colorblind_safe=False,
        source_note="Muted Bits & Flames vibrant palette for branded figures that need less saturation.",
    ),
    "fyron_sequential_blue": PaletteSpec(
        name="fyron_sequential_blue",
        kind="sequential",
        colors=("#F7FBFF", "#9ECAE1", "#4292C6", "#08519C"),
        max_recommended=None,
        colorblind_safe=True,
        source_note="Single-hue blue sequential palette for increasing magnitude.",
    ),
    "fyron_sequential_teal": PaletteSpec(
        name="fyron_sequential_teal",
        kind="sequential",
        colors=("#F7FCFD", "#B2E2E2", "#66C2A4", "#238B45"),
        max_recommended=None,
        colorblind_safe=True,
        source_note="Single-hue teal sequential palette for ordered magnitude.",
    ),
    "fyron_diverging_blue_red": PaletteSpec(
        name="fyron_diverging_blue_red",
        kind="diverging",
        colors=("#B2182B", "#F4A582", "#F7F7F7", "#92C5DE", "#2166AC"),
        max_recommended=None,
        colorblind_safe=False,
        source_note="Blue-red diverging palette for values centered on a meaningful midpoint.",
    ),
    "fyron_diverging_teal_orange": PaletteSpec(
        name="fyron_diverging_teal_orange",
        kind="diverging",
        colors=("#C75D2C", "#F3C39B", "#F7F7F7", "#9BD3C7", "#00796B"),
        max_recommended=None,
        colorblind_safe=False,
        source_note="Teal-orange diverging palette for centered differences.",
    ),
}


def get_palette(name: str = "okabe_ito", n: int | None = None, *, reverse: bool = False) -> list[str]:
    """Return a named scientific palette as hex colors."""

    spec = _palette_spec(name)
    colors = list(reversed(spec.colors) if reverse else spec.colors)
    if n is None:
        return colors
    if n < 0:
        raise ValueError("n must be non-negative.")
    if spec.max_recommended is not None and n > spec.max_recommended:
        warnings.warn(
            f"Palette {name!r} is recommended for at most {spec.max_recommended} categories; "
            "consider hatches, markers, faceting, or small multiples.",
            UserWarning,
            stacklevel=2,
        )
    if n <= len(colors):
        return colors[:n]
    return [colors[i % len(colors)] for i in range(n)]


def list_palettes(kind: str | None = None) -> pd.DataFrame:
    """List available Fyron scientific palettes."""

    rows = []
    for spec in PALETTES.values():
        if kind is not None and spec.kind != kind:
            continue
        rows.append(
            {
                "name": spec.name,
                "kind": spec.kind,
                "n_colors": len(spec.colors),
                "max_recommended": spec.max_recommended,
                "colorblind_safe": spec.colorblind_safe,
                "source_note": spec.source_note,
                "colors": list(spec.colors),
            }
        )
    if kind is not None and not rows:
        raise ValueError("kind must be one of qualitative, sequential, or diverging.")
    return pd.DataFrame(rows)


def get_colormap(name: str = "fyron_sequential_blue", *, reverse: bool = False) -> LinearSegmentedColormap:
    """Return a Matplotlib colormap from a named sequential/diverging palette."""

    spec = _palette_spec(name)
    if spec.kind not in {"sequential", "diverging"}:
        raise ValueError(f"Palette {name!r} is {spec.kind}; use a sequential or diverging palette as a colormap.")
    colors = get_palette(name, reverse=reverse)
    return LinearSegmentedColormap.from_list(f"{name}{'_r' if reverse else ''}", colors)


def resolve_palette(palette: str | Sequence[str] | None, n: int, *, default: str = "okabe_ito") -> list[str]:
    """Resolve a named or explicit palette to ``n`` colors."""

    if palette is None:
        return get_palette(default, n=n)
    if isinstance(palette, str):
        return get_palette(palette, n=n)
    colors = list(palette)
    if not colors:
        return get_palette(default, n=n)
    return [to_hex(color) for color in (colors[i % len(colors)] for i in range(n))]


def resolve_colormap(cmap: str | Any) -> Any:
    """Resolve a Fyron colormap name or pass through any Matplotlib colormap."""

    if isinstance(cmap, str) and cmap in PALETTES and PALETTES[cmap].kind in {"sequential", "diverging"}:
        return get_colormap(cmap)
    return cmap


def set_plot_style(style: str = "paper", palette: str = "okabe_ito") -> None:
    """Set Fyron Matplotlib defaults for publication figures."""

    if style not in {"paper", "poster", "minimal"}:
        raise ValueError("style must be 'paper', 'poster', or 'minimal'.")
    colors = get_palette(palette)
    base = {
        "axes.prop_cycle": plt.cycler(color=colors),
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    }
    if style == "paper":
        base.update({"figure.dpi": 120, "savefig.dpi": 300, "font.size": 11, "axes.grid": True, "grid.color": "#E8EBF0", "grid.alpha": 0.9})
    elif style == "poster":
        base.update({"figure.dpi": 120, "savefig.dpi": 300, "font.size": 14, "axes.grid": True, "grid.color": "#E1E5EB", "grid.alpha": 0.9, "lines.linewidth": 2.4})
    else:
        base.update({"figure.dpi": 120, "savefig.dpi": 300, "font.size": 11, "axes.grid": False})
    plt.rcParams.update(base)


def palette_luminance_table(name_or_colors: str | Sequence[str]) -> pd.DataFrame:
    """Return luminance and text-color guidance for a palette."""

    colors = get_palette(name_or_colors) if isinstance(name_or_colors, str) else [to_hex(c) for c in name_or_colors]
    rows = []
    for index, color in enumerate(colors):
        r, g, b = to_rgb(color)
        luminance = _relative_luminance(r, g, b)
        rows.append(
            {
                "index": index,
                "hex": to_hex(color).upper(),
                "r": r,
                "g": g,
                "b": b,
                "relative_luminance": luminance,
                "recommended_text_color": "#000000" if luminance > 0.45 else "#FFFFFF",
            }
        )
    return pd.DataFrame(rows)


def palette_grayscale_contrast(name_or_colors: str | Sequence[str]) -> pd.DataFrame:
    """Return adjacent luminance differences for grayscale readability checks."""

    lum = palette_luminance_table(name_or_colors)
    rows = []
    for i in range(len(lum) - 1):
        rows.append(
            {
                "left_index": int(lum.loc[i, "index"]),
                "right_index": int(lum.loc[i + 1, "index"]),
                "left_hex": lum.loc[i, "hex"],
                "right_hex": lum.loc[i + 1, "hex"],
                "luminance_delta": abs(float(lum.loc[i, "relative_luminance"]) - float(lum.loc[i + 1, "relative_luminance"])),
            }
        )
    return pd.DataFrame(rows)


def preview_palette(name: str, n: int | None = None, *, save_path: str | Path | None = None) -> tuple[Any, Any]:
    """Preview a named palette as labeled swatches."""

    colors = get_palette(name, n=n)
    fig, ax = plt.subplots(figsize=(max(4.0, 0.7 * len(colors)), 1.4))
    for index, color in enumerate(colors):
        ax.add_patch(plt.Rectangle((index, 0), 1, 1, facecolor=color, edgecolor="black", linewidth=0.7))
        ax.text(index + 0.5, -0.18, color.upper(), ha="center", va="top", fontsize=8, rotation=45)
    ax.set_xlim(0, len(colors))
    ax.set_ylim(-0.55, 1)
    ax.set_axis_off()
    ax.set_title(name)
    fig.tight_layout()
    if save_path is not None:
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, bbox_inches="tight")
    return fig, ax


def _palette_spec(name: str) -> PaletteSpec:
    key = name.lower().replace("-", "_")
    if key not in PALETTES:
        available = ", ".join(sorted(PALETTES))
        raise ValueError(f"Unknown palette {name!r}. Available palettes: {available}.")
    return PALETTES[key]


def _relative_luminance(r: float, g: float, b: float) -> float:
    def channel(value: float) -> float:
        return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4

    rr, gg, bb = channel(r), channel(g), channel(b)
    return 0.2126 * rr + 0.7152 * gg + 0.0722 * bb


__all__ = [
    "PALETTES",
    "PaletteSpec",
    "get_colormap",
    "get_palette",
    "list_palettes",
    "palette_grayscale_contrast",
    "palette_luminance_table",
    "preview_palette",
    "resolve_colormap",
    "resolve_palette",
    "set_plot_style",
]
