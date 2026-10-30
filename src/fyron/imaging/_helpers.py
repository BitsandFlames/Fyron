"""Internal helpers for fyron.imaging."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Union

import numpy as np
import SimpleITK as sitk
from pydicom.datadict import tag_for_keyword
from pydicom.tag import Tag

StrPath = Union[str, Path]


def to_path(path: StrPath) -> Path:
    """Return a resolved ``Path`` (does not require existence)."""
    return Path(path).expanduser().resolve()


def require_file(path: StrPath, *, what: str = "file") -> Path:
    p = to_path(path)
    if not p.exists():
        raise FileNotFoundError(f"{what.capitalize()} does not exist: {p}")
    if not p.is_file():
        raise ValueError(f"Expected a {what}, but path is not a regular file: {p}")
    return p


def require_dir(path: StrPath, *, what: str = "directory") -> Path:
    p = to_path(path)
    if not p.exists():
        raise FileNotFoundError(f"{what.capitalize()} does not exist: {p}")
    if not p.is_dir():
        raise ValueError(f"Expected a {what}, but path is not a directory: {p}")
    return p


def is_sitk_image(obj: Any) -> bool:
    return isinstance(obj, sitk.Image)


def get_array_from_image(image: sitk.Image) -> np.ndarray:
    """Return a NumPy copy in SimpleITK order (Z, Y, X)."""
    return sitk.GetArrayFromImage(image).astype(np.float32, copy=False)


def float32_sitk_from_array(arr: np.ndarray, reference: sitk.Image) -> sitk.Image:
    """Build a float32 ``SimpleITK.Image`` from ``arr`` (Z, Y, X) and copy geometry from ``reference``."""
    out = sitk.GetImageFromArray(np.asarray(arr, dtype=np.float32))
    out.CopyInformation(reference)
    return out


def copy_geometry_from_reference(target: sitk.Image, reference: sitk.Image) -> None:
    """Copy spacing, origin, and direction from ``reference`` onto ``target``."""
    target.SetSpacing(reference.GetSpacing())
    target.SetOrigin(reference.GetOrigin())
    target.SetDirection(reference.GetDirection())


def parse_dicom_tag_spec(spec: str) -> Tag:
    """Map a keyword ``'PatientID'`` or ``'0010,0020'`` / ``'00100020'`` to a ``pydicom.tag.Tag``."""
    spec = spec.strip()
    hex_match = re.fullmatch(r"([0-9a-fA-F]{4}),?([0-9a-fA-F]{4})", spec)
    if hex_match:
        g, e = hex_match.groups()
        return Tag(int(g, 16), int(e, 16))
    tid = tag_for_keyword(spec)
    if tid is None:
        raise KeyError(f"Unknown DICOM keyword or invalid tag string: {spec!r}")
    return Tag(tid)


def dataset_to_plain_dict(ds: Any, *, skip_pixel_data: bool = True) -> dict[str, Any]:
    """Flatten a pydicom ``Dataset`` to primitive-friendly values (best effort)."""
    out: dict[str, Any] = {}
    for elem in ds:
        if skip_pixel_data and elem.tag == Tag(0x7FE0, 0x0010):
            continue
        key = elem.keyword if elem.keyword else str(elem.tag)
        try:
            out[key] = elem.value
        except Exception:  # noqa: BLE001
            out[key] = str(elem.value)
    return out
