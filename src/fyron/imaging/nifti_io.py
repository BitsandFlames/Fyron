"""NIfTI read/write via SimpleITK."""

from __future__ import annotations

from pathlib import Path
from typing import Union

import numpy as np
import SimpleITK as sitk

from fyron.imaging._helpers import copy_geometry_from_reference, is_sitk_image, require_file, to_path

StrPath = Union[str, Path]


def _validate_nifti_path(path: Path) -> Path:
    name = path.name.lower()
    if not (name.endswith(".nii.gz") or name.endswith(".nii")):
        raise ValueError(f"NIfTI path must end with .nii or .nii.gz, got: {path}")
    return path


def read_nifti(
    nifti_path: StrPath,
    *,
    return_array: bool = False,
) -> Union[sitk.Image, tuple[sitk.Image, np.ndarray]]:
    """Read a NIfTI volume with SimpleITK.

    Parameters
    ----------
    nifti_path
        Path ending in ``.nii`` or ``.nii.gz``.
    return_array
        If True, also return a NumPy array in **Z, Y, X** order (``GetArrayFromImage``).

    Returns
    -------
    SimpleITK.Image or tuple
        Image, or ``(image, array)`` when ``return_array`` is True.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.

    Examples
    --------
    >>> from fyron.imaging import read_nifti
    >>> # img = read_nifti(\"vol.nii.gz\")
    >>> # img, arr = read_nifti(\"vol.nii.gz\", return_array=True)
    """
    path = _validate_nifti_path(to_path(nifti_path))
    path = require_file(path, what="NIfTI file")
    image = sitk.ReadImage(str(path))
    if return_array:
        return image, sitk.GetArrayFromImage(image)
    return image


def write_nifti(
    image: sitk.Image | np.ndarray,
    output_path: StrPath,
    *,
    reference_image: sitk.Image | None = None,
    compress: bool = True,
) -> Path:
    """Write a ``SimpleITK.Image`` or NumPy array to NIfTI.

    Parameters
    ----------
    image
        ``SimpleITK.Image`` or array in **Z, Y, X** order (as produced by
        ``GetArrayFromImage``).
    output_path
        Destination ``.nii`` or ``.nii.gz`` (parent directories are created).
    reference_image
        When ``image`` is a NumPy array, copy spacing, origin, and direction from this
        image. When ``image`` is already a ``SimpleITK.Image`` and ``reference_image`` is
        set, geometry is overwritten from the reference before writing.
    compress
        If True, request compression (always on for ``.nii.gz``; for plain ``.nii`` uses
        SimpleITK's writer compression flag when supported).

    Returns
    -------
    pathlib.Path
        Resolved output path.

    Examples
    --------
    >>> from fyron.imaging import write_nifti
    >>> # write_nifti(arr, \"out/ct.nii.gz\", reference_image=ref)
    """
    out = to_path(output_path)
    out = _validate_nifti_path(out)
    out.parent.mkdir(parents=True, exist_ok=True)

    if is_sitk_image(image):
        sitk_img = sitk.Image(image)
        if reference_image is not None:
            copy_geometry_from_reference(sitk_img, reference_image)
        _write_sitk_image(sitk_img, out, compress=compress)
        return out.resolve()

    if not isinstance(image, np.ndarray):
        raise TypeError(f"image must be SimpleITK.Image or numpy.ndarray, got {type(image)!r}")

    arr = np.asarray(image)
    sitk_img = sitk.GetImageFromArray(arr.astype(np.float32, copy=False))
    if reference_image is not None:
        copy_geometry_from_reference(sitk_img, reference_image)
    else:
        dim = sitk_img.GetDimension()
        sitk_img.SetSpacing((1.0,) * dim)
        sitk_img.SetOrigin((0.0,) * dim)
        sitk_img.SetDirection(np.eye(dim).flatten().tolist())

    _write_sitk_image(sitk_img, out, compress=compress)
    return out.resolve()


def _write_sitk_image(image: sitk.Image, path: Path, *, compress: bool) -> None:
    use_compression = compress or str(path).lower().endswith(".nii.gz")
    writer = sitk.ImageFileWriter()
    writer.SetFileName(str(path))
    writer.SetUseCompression(bool(use_compression))
    writer.Execute(image)
