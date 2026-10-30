"""Medical imaging visualization utilities.

Install optional dependencies with::

    uv add "fyron[visualization]"

"""

from __future__ import annotations

try:
    import cv2  # noqa: F401
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "The fyron.visualization module requires opencv-python-headless. "
        'Install it with: uv add "fyron[visualization]"'
    ) from exc

from fyron.visualization._boa_labels import SegmentationLayer
from fyron.visualization.boa import create_boa_segmentation_collage
from fyron.visualization.curate_previews import prepare_curate_image_previews
from fyron.visualization.segmentation_collage import (
    create_segmentation_collage,
    create_segmentation_collages_from_cases,
)
from fyron.visualization.volume_difference import plot_volume_difference_heatmap

__all__ = [
    "SegmentationLayer",
    "create_boa_segmentation_collage",
    "create_segmentation_collage",
    "create_segmentation_collages_from_cases",
    "prepare_curate_image_previews",
    "plot_volume_difference_heatmap",
]
