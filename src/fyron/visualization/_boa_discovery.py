"""Discover CT and segmentation volumes in BOA output folders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Union

from fyron.imaging._helpers import require_dir, to_path
from fyron.visualization._boa_labels import DEFAULT_SEGMENTATION_FILES, SegmentationKind

StrPath = Union[str, Path]

KNOWN_BOA_MASK_NAMES: frozenset[str] = frozenset(
    {
        "body-regions.nii.gz",
        "body-parts.nii.gz",
        "tissues.nii.gz",
        "total.nii.gz",
        "ctpfav.nii.gz",
    }
)


@dataclass(frozen=True)
class BOAVolumePaths:
    """Resolved CT and segmentation paths for one BOA folder."""

    folder: Path
    ct_path: Path
    segmentation_path: Path


def _list_nifti_files(folder: Path) -> list[Path]:
    return sorted(
        p
        for p in folder.iterdir()
        if p.is_file() and (p.name.endswith(".nii.gz") or p.name.endswith(".nii"))
    )


def discover_ct_path(folder: StrPath, *, ct_filename: str | None = None) -> Path:
    """Resolve the CT NIfTI inside a BOA folder."""
    root = require_dir(folder, what="BOA folder")
    niftis = _list_nifti_files(root)
    if not niftis:
        raise FileNotFoundError(f"No NIfTI files found in BOA folder: {root}")

    if ct_filename is not None:
        ct_path = root / ct_filename
        if not ct_path.is_file():
            raise FileNotFoundError(f"CT file not found: {ct_path} (folder: {root})")
        return ct_path

    candidates = [p for p in niftis if p.name not in KNOWN_BOA_MASK_NAMES]
    if not candidates:
        raise ValueError(f"Could not auto-detect CT in {root}; pass ct_filename explicitly.")
    return max(candidates, key=lambda p: p.stat().st_size)


def discover_mask_path(
    folder: StrPath,
    *,
    kind: SegmentationKind | None = None,
    segmentation_filename: str | None = None,
) -> Path:
    """Resolve a segmentation mask inside a BOA folder."""
    root = require_dir(folder, what="BOA folder")
    if segmentation_filename is None:
        if kind is None:
            raise ValueError("Pass kind or segmentation_filename.")
        segmentation_filename = DEFAULT_SEGMENTATION_FILES[kind]
    seg_path = root / segmentation_filename
    if not seg_path.is_file():
        raise FileNotFoundError(f"Segmentation file not found: {seg_path} (folder: {root})")
    return seg_path


def discover_boa_volumes(
    folder: StrPath,
    *,
    ct_filename: str | None = None,
    segmentation_filename: str = "body-regions.nii.gz",
) -> BOAVolumePaths:
    """Resolve CT and one segmentation path inside a BOA output folder."""
    root = require_dir(folder, what="BOA folder")
    ct_path = discover_ct_path(root, ct_filename=ct_filename)
    seg_path = discover_mask_path(root, segmentation_filename=segmentation_filename)
    return BOAVolumePaths(folder=root, ct_path=ct_path, segmentation_path=seg_path)
