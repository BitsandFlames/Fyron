"""BOA / TotalSegmentator label names and color LUTs.

Colors are taken from UMEssen Body-and-Organ-Analysis:
https://github.com/UMEssen/Body-and-Organ-Analysis/tree/main/body_organ_analysis/_external
"""

from __future__ import annotations

import colorsys
from dataclasses import dataclass
from typing import Literal, Sequence

import numpy as np

SegmentationKind = Literal["body_regions", "tissues", "total"]

# Body regions (body_composition_analysis/body_regions/definition.py + colors.py)
BODY_REGION_NAMES: dict[int, str] = {
    1: "Subcutaneous Tissue",
    2: "Muscle",
    3: "Abdominal Cavity",
    4: "Thoracic Cavity",
    5: "Bone",
    6: "Glands",
    7: "Pericardium",
    8: "Breast Implant",
    9: "Mediastinum",
    10: "Brain",
    11: "Spinal Cord",
}

BODY_REGION_RGB: dict[int, tuple[int, int, int]] = {
    1: (211, 78, 36),
    2: (238, 193, 112),
    3: (6, 158, 45),
    4: (0, 0, 224),
    5: (192, 128, 192),
    6: (0, 224, 0),
    7: (161, 22, 146),
    8: (192, 0, 0),
    9: (142, 184, 229),
    10: (192, 0, 192),
    11: (192, 0, 100),
}

# Tissues (tissue/definition.py + colors.py)
TISSUE_NAMES: dict[int, str] = {
    1: "Muscle",
    2: "Bone",
    3: "SAT",
    4: "VAT",
    5: "IMAT",
    6: "PAT",
    7: "EAT",
}

TISSUE_RGB: dict[int, tuple[int, int, int]] = {
    1: (238, 193, 112),
    2: (192, 128, 192),
    3: (211, 78, 36),
    4: (6, 158, 45),
    5: (0, 109, 119),
    6: (142, 184, 229),
    7: (161, 22, 146),
}

# TotalSegmentator "total" task (map_to_binary.py) — 104 classes
TOTAL_NAMES: dict[int, str] = {
    1: "spleen",
    2: "kidney_right",
    3: "kidney_left",
    4: "gallbladder",
    5: "liver",
    6: "stomach",
    7: "aorta",
    8: "inferior_vena_cava",
    9: "portal_vein_and_splenic_vein",
    10: "pancreas",
    11: "adrenal_gland_right",
    12: "adrenal_gland_left",
    13: "lung_upper_lobe_left",
    14: "lung_lower_lobe_left",
    15: "lung_upper_lobe_right",
    16: "lung_middle_lobe_right",
    17: "lung_lower_lobe_right",
    18: "vertebrae_L5",
    19: "vertebrae_L4",
    20: "vertebrae_L3",
    21: "vertebrae_L2",
    22: "vertebrae_L1",
    23: "vertebrae_T12",
    24: "vertebrae_T11",
    25: "vertebrae_T10",
    26: "vertebrae_T9",
    27: "vertebrae_T8",
    28: "vertebrae_T7",
    29: "vertebrae_T6",
    30: "vertebrae_T5",
    31: "vertebrae_T4",
    32: "vertebrae_T3",
    33: "vertebrae_T2",
    34: "vertebrae_T1",
    35: "vertebrae_C7",
    36: "vertebrae_C6",
    37: "vertebrae_C5",
    38: "vertebrae_C4",
    39: "vertebrae_C3",
    40: "vertebrae_C2",
    41: "vertebrae_C1",
    42: "esophagus",
    43: "trachea",
    44: "heart_myocardium",
    45: "heart_atrium_left",
    46: "heart_ventricle_left",
    47: "heart_atrium_right",
    48: "heart_ventricle_right",
    49: "pulmonary_artery",
    50: "brain",
    51: "iliac_artery_left",
    52: "iliac_artery_right",
    53: "iliac_vena_left",
    54: "iliac_vena_right",
    55: "small_bowel",
    56: "duodenum",
    57: "colon",
    58: "rib_left_1",
    59: "rib_left_2",
    60: "rib_left_3",
    61: "rib_left_4",
    62: "rib_left_5",
    63: "rib_left_6",
    64: "rib_left_7",
    65: "rib_left_8",
    66: "rib_left_9",
    67: "rib_left_10",
    68: "rib_left_11",
    69: "rib_left_12",
    70: "rib_right_1",
    71: "rib_right_2",
    72: "rib_right_3",
    73: "rib_right_4",
    74: "rib_right_5",
    75: "rib_right_6",
    76: "rib_right_7",
    77: "rib_right_8",
    78: "rib_right_9",
    79: "rib_right_10",
    80: "rib_right_11",
    81: "rib_right_12",
    82: "humerus_left",
    83: "humerus_right",
    84: "scapula_left",
    85: "scapula_right",
    86: "clavicula_left",
    87: "clavicula_right",
    88: "femur_left",
    89: "femur_right",
    90: "hip_left",
    91: "hip_right",
    92: "sacrum",
    93: "face",
    94: "gluteus_maximus_left",
    95: "gluteus_maximus_right",
    96: "gluteus_medius_left",
    97: "gluteus_medius_right",
    98: "gluteus_minimus_left",
    99: "gluteus_minimus_right",
    100: "autochthon_left",
    101: "autochthon_right",
    102: "iliopsoas_left",
    103: "iliopsoas_right",
    104: "urinary_bladder",
}

DEFAULT_SEGMENTATION_FILES: dict[SegmentationKind, str] = {
    "body_regions": "body-regions.nii.gz",
    "tissues": "tissues.nii.gz",
    "total": "total.nii.gz",
}

LAYER_TITLES: dict[SegmentationKind, str] = {
    "body_regions": "Body Regions",
    "tissues": "Tissues",
    "total": "Organs",
}


def _hsv_colors(num_colors: int) -> list[tuple[int, int, int]]:
    return [
        tuple(int(c * 255) for c in colorsys.hsv_to_rgb((x * 1.0) / num_colors, 1.0, 1.0))
        for x in range(num_colors)
    ]


def _lut_from_rgb_map(rgb_map: dict[int, tuple[int, int, int]], *, max_label: int = 255) -> np.ndarray:
    lut = np.zeros((max_label + 1, 3), dtype=np.uint8)
    for label_id, rgb in rgb_map.items():
        if 0 <= label_id <= max_label:
            lut[label_id] = rgb
    return lut


def _total_lut() -> np.ndarray:
    lut = np.zeros((256, 3), dtype=np.uint8)
    for label_id, rgb in zip(range(1, 105), _hsv_colors(104), strict=True):
        lut[label_id] = rgb
    return lut


_BODY_REGION_LUT = _lut_from_rgb_map(BODY_REGION_RGB)
_TISSUE_LUT = _lut_from_rgb_map(TISSUE_RGB)
_TOTAL_LUT = _total_lut()


def color_lut_for_kind(kind: SegmentationKind) -> np.ndarray:
    if kind == "body_regions":
        return _BODY_REGION_LUT
    if kind == "tissues":
        return _TISSUE_LUT
    if kind == "total":
        return _TOTAL_LUT
    raise ValueError(f"Unknown segmentation kind: {kind!r}")


def label_name(kind: SegmentationKind, label_id: int) -> str:
    if kind == "body_regions":
        return BODY_REGION_NAMES.get(label_id, f"label_{label_id}")
    if kind == "tissues":
        return TISSUE_NAMES.get(label_id, f"label_{label_id}")
    if kind == "total":
        return TOTAL_NAMES.get(label_id, f"label_{label_id}")
    raise ValueError(f"Unknown segmentation kind: {kind!r}")


@dataclass(frozen=True)
class SegmentationLayer:
    """One segmentation column in the collage."""

    kind: SegmentationKind
    display_mode: Literal["ct", "ct_overlay", "segmentation"] = "segmentation"
    filename: str | None = None
    opacity: float | None = None

    @property
    def mask_filename(self) -> str:
        if self.filename is not None:
            return self.filename
        return DEFAULT_SEGMENTATION_FILES[self.kind]

    @property
    def title(self) -> str:
        return LAYER_TITLES[self.kind]


def parse_segmentation_layers(
    layers: Sequence[SegmentationLayer | SegmentationKind | str] | None,
) -> list[SegmentationLayer]:
    if layers is None:
        return [
            SegmentationLayer("body_regions", display_mode="ct_overlay"),
            SegmentationLayer("tissues", display_mode="ct_overlay"),
            SegmentationLayer("total", display_mode="ct_overlay"),
        ]
    parsed: list[SegmentationLayer] = []
    for item in layers:
        if isinstance(item, SegmentationLayer):
            parsed.append(item)
        elif item in {"body_regions", "tissues", "total"}:
            kind = item  # type: ignore[assignment]
            parsed.append(SegmentationLayer(kind, display_mode="ct_overlay"))
        else:
            raise ValueError(
                f"Invalid segmentation layer {item!r}. "
                "Use 'body_regions', 'tissues', 'total', or SegmentationLayer(...)."
            )
    return parsed
