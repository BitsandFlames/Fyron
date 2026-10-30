"""CT / MR intensity normalization."""

from __future__ import annotations

import numpy as np
import SimpleITK as sitk

from fyron.imaging._helpers import float32_sitk_from_array, get_array_from_image, is_sitk_image


def normalize_ct(
    image: sitk.Image | np.ndarray,
    hu_min: float = -1000.0,
    hu_max: float = 3000.0,
) -> sitk.Image | np.ndarray:
    """Clip CT Hounsfield units and scale linearly to ``[0, 1]`` as float32.

    Parameters
    ----------
    image
        ``SimpleITK.Image`` (HU) or NumPy array in **Z, Y, X** order.
    hu_min, hu_max
        HU window; ``hu_max`` must be greater than ``hu_min``.

    Returns
    -------
    SimpleITK.Image or numpy.ndarray
        Same container type as input; float32 intensities in ``[0, 1]``.
        For ``SimpleITK`` input, spacing, origin, and direction are preserved.

    Examples
    --------
    >>> import numpy as np
    >>> from fyron.imaging import normalize_ct
    >>> arr = np.array([[-1000.0, 0.0, 4000.0]], dtype=np.float32)
    >>> out = normalize_ct(arr, hu_min=-1000, hu_max=3000)
    >>> float(out.min()), float(out.max())
    (0.0, 1.0)
    """
    if not np.isfinite(hu_min) or not np.isfinite(hu_max):
        raise ValueError("CT window bounds must be finite.")
    if hu_max <= hu_min:
        raise ValueError(f"hu_max must be greater than hu_min; got hu_min={hu_min}, hu_max={hu_max}")
    if is_sitk_image(image):
        ref: sitk.Image = image  # type: ignore[assignment]
        arr = get_array_from_image(ref)
        scaled = _scale_ct_array(arr, hu_min, hu_max)
        return float32_sitk_from_array(scaled, ref)
    if not isinstance(image, np.ndarray):
        raise TypeError(f"image must be SimpleITK.Image or numpy.ndarray, got {type(image)!r}")
    return _scale_ct_array(np.asarray(image, dtype=np.float32), hu_min, hu_max)


def _scale_ct_array(arr: np.ndarray, hu_min: float, hu_max: float) -> np.ndarray:
    clipped = np.clip(arr, hu_min, hu_max)
    return ((clipped - hu_min) / (hu_max - hu_min)).astype(np.float32)


def normalize_mr(
    image: sitk.Image | np.ndarray,
    *,
    mode: str = "percentile",
    percentile: float = 99.0,
    value: float | None = None,
    ignore_zeros: bool = True,
    clip: bool = True,
) -> sitk.Image | np.ndarray:
    """Normalize MR intensities to a ``[0, 1]`` float scale (default: high percentile).

    Parameters
    ----------
    image
        ``SimpleITK.Image`` or NumPy array in **Z, Y, X** order.
    mode
        ``\"percentile\"`` (divide by given percentile), ``\"max\"`` (divide by max),
        or ``\"value\"`` (divide by fixed ``value``).
    percentile
        Used when ``mode=\"percentile\"`` (e.g. 95 or 99).
    value
        Required positive divisor when ``mode=\"value\"``.
    ignore_zeros
        If True, zeros are excluded when computing percentile or max statistics.
    clip
        If True, clip output to ``[0, 1]``.

    Returns
    -------
    SimpleITK.Image or numpy.ndarray
        Same container type as input; float32. Geometry preserved for ``SimpleITK``.

    Raises
    ------
    ValueError
        For unknown ``mode``, invalid percentile, missing ``value`` in value-mode,
        or zero / invalid normalization denominator.

    Examples
    --------
    >>> import numpy as np
    >>> from fyron.imaging import normalize_mr
    >>> x = np.array([[0.0, 10.0, 100.0]], dtype=np.float32)
    >>> y = normalize_mr(x, mode="percentile", percentile=90, ignore_zeros=True)
    """
    mode_l = mode.lower().strip()
    if mode_l not in {"percentile", "max", "value"}:
        raise ValueError(f"mode must be 'percentile', 'max', or 'value'; got {mode!r}")

    if is_sitk_image(image):
        ref: sitk.Image = image  # type: ignore[assignment]
        arr = get_array_from_image(ref)
        scaled = _normalize_mr_array(
            arr,
            mode=mode_l,
            percentile=percentile,
            value=value,
            ignore_zeros=ignore_zeros,
            clip=clip,
        )
        return float32_sitk_from_array(scaled, ref)
    if not isinstance(image, np.ndarray):
        raise TypeError(f"image must be SimpleITK.Image or numpy.ndarray, got {type(image)!r}")
    return _normalize_mr_array(
        np.asarray(image, dtype=np.float32),
        mode=mode_l,
        percentile=percentile,
        value=value,
        ignore_zeros=ignore_zeros,
        clip=clip,
    )


def _normalize_mr_array(
    arr: np.ndarray,
    *,
    mode: str,
    percentile: float,
    value: float | None,
    ignore_zeros: bool,
    clip: bool,
) -> np.ndarray:
    flat = arr.ravel()
    if ignore_zeros:
        mask = flat != 0
        stat_vals = flat[mask] if mask.any() else flat
    else:
        stat_vals = flat

    if stat_vals.size == 0:
        raise ValueError("Cannot normalize an empty array.")

    if mode == "percentile":
        if not 0 < percentile <= 100:
            raise ValueError(f"percentile must be in (0, 100]; got {percentile}")
        denom = float(np.percentile(stat_vals, percentile))
    elif mode == "max":
        denom = float(np.max(stat_vals))
    else:
        if value is None or value <= 0:
            raise ValueError("mode='value' requires a positive `value` argument.")
        denom = float(value)

    if denom == 0.0 or not np.isfinite(denom):
        raise ValueError(f"Invalid normalization denominator for mode={mode!r}: {denom!r}")

    scaled = (arr / denom).astype(np.float32)
    if clip:
        scaled = np.clip(scaled, 0.0, 1.0)
    return scaled
