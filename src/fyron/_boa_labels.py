"""Canonical BOA labels from Body-and-Organ-Analysis's BCA definitions.

Reference: UMEssen/Body-and-Organ-Analysis, commit
5ae52b5a813f697e89b00d74ba04b2e2b35d71de, body_composition_analysis/{tissue,body_regions}/definition.py.
Tissue masks and anatomical body-region masks have different semantics.
"""

BODY_REGION_LABELS = {
    "subcutaneous_tissue": 1,
    "muscle": 2,
    "abdominal_cavity": 3,
    "thoracic_cavity": 4,
    "bone": 5,
    "glands": 6,
    "pericardium": 7,
    "breast_implant": 8,
    "mediastinum": 9,
    "brain": 10,
    "nervous_system": 11,
}

TISSUE_LABELS = {"muscle": 1, "bone": 2, "sat": 3, "vat": 4, "imat": 5, "pat": 6, "eat": 7}
