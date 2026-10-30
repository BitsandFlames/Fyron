"""Deterministic regressions from the final working-tree review."""

import numpy as np
import pandas as pd
import pytest
import SimpleITK as sitk
from PIL import Image

from fyron.preprocessing import fit_imputer, apply_imputer
from fyron.explainability import shap_values_table
from fyron.datasets import prepare_nnunetv2_dataset, prepare_yolo_detection_dataset
from fyron.datasets.preparation import _copy_file
from fyron.validation import find_best_threshold


def test_imputer_rejects_existing_indicator_at_fit_and_apply():
    frame = pd.DataFrame({"age": [1., np.nan], "age_was_missing": [99, 88]})
    original = frame.copy(deep=True)
    with pytest.raises(ValueError, match="indicator"):
        fit_imputer(frame, numeric=["age"], categorical=[], add_missing_indicators=True)
    spec = fit_imputer(frame[["age"]], add_missing_indicators=True)
    with pytest.raises(ValueError, match="indicator"):
        apply_imputer(frame, spec)
    pd.testing.assert_frame_equal(frame, original)


def test_imputer_handles_nullable_integer_and_unseen_category_fill():
    train = pd.DataFrame({"age": pd.Series([1, 2, None], dtype="Int64"),
                          "site": pd.Categorical(["A", "A", None])})
    spec = fit_imputer(train)
    test = pd.DataFrame({"age": pd.Series([None, 4], dtype="Int64"),
                         "site": pd.Categorical([None, "B"])}, index=[0, 1])
    result = apply_imputer(test, spec)
    assert result.age.tolist() == [1.5, 4.]
    assert result.site.tolist() == ["A", "B"]
    assert test.age.isna().sum() == 1


def test_legacy_shap_values_do_not_mix_samples_and_classes():
    X = pd.DataFrame({"a": [10, 20], "b": [30, 40]})
    negative = np.array([[1., 2.], [3., 4.]])
    positive = -negative
    result = shap_values_table(None, X, explainer=lambda X: [negative, positive])
    assert result.shap_value.tolist() == [-1., -2., -3., -4.]


def test_shap_custom_feature_names_keep_original_values():
    X = pd.DataFrame({"a": [10, 20], "b": [30, 40]})
    result = shap_values_table(None, X, feature_names=["Age", "Score"],
                              explainer=lambda X: np.ones((len(X), 2)))
    assert result.feature_value.tolist() == [10, 30, 20, 40]


def test_shap_missing_rows_raise_instead_of_truncating():
    with pytest.raises(ValueError, match="row"):
        shap_values_table(None, np.ones((3, 2)), explainer=lambda X: np.ones((2, 2)))


@pytest.mark.parametrize("copy_mode", ["copy", "move", "symlink"])
def test_dataset_same_file_overwrite_preserves_original(tmp_path, copy_mode):
    source = tmp_path / "original.png"
    source.write_bytes(b"synthetic-original")
    with pytest.raises(ValueError, match="same"):
        _copy_file(source, source, copy_mode=copy_mode, overwrite=True)
    assert source.read_bytes() == b"synthetic-original"


def test_failed_dataset_copy_keeps_existing_target(tmp_path):
    target = tmp_path / "target.png"
    target.write_bytes(b"previous-complete-file")
    with pytest.raises(FileNotFoundError):
        _copy_file(tmp_path / "absent.png", target, copy_mode="copy", overwrite=True)
    assert target.read_bytes() == b"previous-complete-file"


def _detection_manifest(tmp_path):
    paths = [tmp_path / "a.png", tmp_path / "b.png"]
    for path in paths:
        Image.new("L", (20, 20), 100).save(path)
    return pd.DataFrame({"sample": ["one", "one"], "image_path": paths,
                         "split": ["train", "train"], "class": ["lesion", "lesion"],
                         "x_min": [1., 2.], "y_min": [1., 2.],
                         "x_max": [4., 5.], "y_max": [4., 5.]})


@pytest.mark.parametrize("conflict", ["source", "split"])
def test_yolo_rejects_inconsistent_annotation_groups(tmp_path, conflict):
    frame = _detection_manifest(tmp_path)
    if conflict == "split":
        frame.loc[1, "image_path"] = frame.loc[0, "image_path"]
        frame.loc[1, "split"] = "val"
    with pytest.raises(ValueError, match="consistent"):
        prepare_yolo_detection_dataset(frame, tmp_path / "out", sample_id_col="sample")
    assert not (tmp_path / "out").exists()


def test_yolo_rejects_colliding_classes(tmp_path):
    frame = _detection_manifest(tmp_path)
    frame["sample"] = ["one", "two"]
    frame["class"] = ["a b", "a/b"]
    with pytest.raises(ValueError, match="collis"):
        prepare_yolo_detection_dataset(frame, tmp_path / "out", sample_id_col="sample")


def test_yolo_rejects_partial_missing_box(tmp_path):
    frame = _detection_manifest(tmp_path).iloc[:1].copy()
    frame.loc[0, "x_max"] = np.nan
    with pytest.raises(ValueError, match="partial|incomplete"):
        prepare_yolo_detection_dataset(frame, tmp_path / "out")


@pytest.mark.parametrize("geometry", ["spacing", "origin", "direction"])
def test_nnunet_rejects_misaligned_labels_before_moving(tmp_path, geometry):
    image = sitk.GetImageFromArray(np.ones((2, 3, 4), dtype=np.uint8))
    mask = sitk.Image(image)
    if geometry == "spacing": mask.SetSpacing((2., 1., 1.))
    if geometry == "origin": mask.SetOrigin((5., 0., 0.))
    if geometry == "direction": mask.SetDirection((-1., 0., 0., 0., -1., 0., 0., 0., 1.))
    paths = [tmp_path / "image.nii.gz", tmp_path / "mask.nii.gz"]
    for obj, path in zip([image, mask], paths): sitk.WriteImage(obj, str(path))
    frame = pd.DataFrame({"case_id": ["case"], "split": ["train"],
                          "image_path": [paths[0]], "label_path": [paths[1]]})
    with pytest.raises(ValueError, match="geometry|align"):
        prepare_nnunetv2_dataset(frame, tmp_path / "out", 1, "Demo", copy_mode="move")
    assert all(path.exists() for path in paths)


def test_nnunet_rejects_duplicate_cases_even_with_overwrite(tmp_path):
    image = sitk.GetImageFromArray(np.ones((2, 3, 4), dtype=np.uint8))
    source = tmp_path / "image.nii.gz"
    sitk.WriteImage(image, str(source))
    frame = pd.DataFrame({"case_id": ["case", "case"], "split": ["test", "test"],
                          "image_path": [source, source]})
    with pytest.raises(ValueError, match="unique|duplicate"):
        prepare_nnunetv2_dataset(frame, tmp_path / "out", 1, "Demo", overwrite=True)


def test_threshold_search_requires_both_classes():
    with pytest.raises(ValueError, match="both|two"):
        find_best_threshold([0, 0], [.1, .2])


def test_llm_dataframe_preserves_nonidentifier_columns(monkeypatch):
    from fyron.llm import LLMAgent
    agent = LLMAgent(provider="custom", base_url="http://127.0.0.1:1", auth_required=False)
    monkeypatch.setattr(agent, "_request", lambda prompt: prompt)
    result = agent.run_on_dataframe(pd.DataFrame({"clinical text": ["SYNTHETIC"]}),
                                    text_col="clinical text", prompt="Summarize")
    assert result.llm_output.iloc[0] == "Summarize\n\nSYNTHETIC"


def test_llm_recursive_duplicate_names_raise_before_requests(tmp_path, monkeypatch):
    from fyron.llm import LLMAgent
    agent = LLMAgent(provider="custom", base_url="http://127.0.0.1:1", auth_required=False)
    calls = []
    monkeypatch.setattr(agent, "_request", lambda prompt: calls.append(prompt) or "ok")
    for folder in ("one", "two"):
        (tmp_path / folder).mkdir()
        (tmp_path / folder / "same.txt").write_text("SYNTHETIC")
    with pytest.raises(ValueError, match="Duplicate|duplicate"):
        agent.run_on_directory(tmp_path, "Summarize", glob="**/*.txt")
    assert not calls


def test_llm_auto_text_uses_text_route(tmp_path, monkeypatch):
    from fyron.llm import LLMAgent
    agent = LLMAgent(provider="custom", base_url="http://127.0.0.1:1", auth_required=False)
    monkeypatch.setattr(agent, "_request", lambda prompt: "text route")
    monkeypatch.setattr(agent, "_request_multimodal", lambda **kwargs: "wrong route")
    (tmp_path / "sample.txt").write_text("SYNTHETIC")
    assert agent.run_on_directory(tmp_path, "Summarize", mode="auto")["sample.txt"] == "text route"


@pytest.mark.parametrize("method", ["fisher", "chi2", "auto"])
def test_contingency_tables_reject_fractional_counts(method):
    from fyron.statistics import categorical_test
    with pytest.raises(ValueError, match="integer|whole"):
        categorical_test([[1.9, 2.1], [3.2, 4.8]], method=method)


def test_statistical_vectors_must_not_flatten_multiple_dimensions():
    from fyron.statistics import compare_two_groups, correlation_test
    with pytest.raises(ValueError, match="one-dimensional"):
        compare_two_groups([[1, 2], [3, 4]], [5, 6, 7, 8])
    with pytest.raises(ValueError, match="one-dimensional"):
        correlation_test([[1, 2], [3, 4]], [[4, 3], [2, 1]])


def test_binary_bootstrap_does_not_mix_in_macro_f1():
    from fyron.validation import bootstrap_classification_metrics
    table = bootstrap_classification_metrics([0, 1], [0, 0], n_rounds=40, random_state=0)
    f1 = table.set_index("metric").loc["f1"]
    assert f1.bootstrap_mean == 0.
    assert 0 < f1.n_successful_rounds < 40


def test_segmentation_rejects_nonfinite_masks():
    from fyron.imaging.segmentation import dice_score
    with pytest.raises(ValueError, match="finite"):
        dice_score(np.array([[np.nan]]), np.array([[1.]]))


def test_ct_normalization_rejects_nonfinite_window():
    from fyron.imaging import normalize_ct
    with pytest.raises(ValueError, match="finite"):
        normalize_ct(np.array([1., 2.]), hu_min=0, hu_max=np.inf)


@pytest.mark.parametrize("copy_mode", ["copy", "move", "symlink"])
def test_dataset_atomic_copy_success(tmp_path, copy_mode):
    source, target = tmp_path / "input", tmp_path / "output"
    source.write_bytes(b"complete"); target.write_bytes(b"old")
    _copy_file(source, target, copy_mode=copy_mode, overwrite=True)
    assert target.read_bytes() == b"complete"
    assert source.exists() == (copy_mode != "move")
    assert target.is_symlink() == (copy_mode == "symlink")


def test_dataset_copy_io_failure_preserves_previous_output(tmp_path, monkeypatch):
    import shutil
    source, target = tmp_path / "input", tmp_path / "output"
    source.write_bytes(b"complete"); target.write_bytes(b"old")
    def fail_copy(src, dest):
        dest.write_bytes(b"partial")
        raise OSError("synthetic disk failure")
    monkeypatch.setattr(shutil, "copy2", fail_copy)
    with pytest.raises(OSError):
        _copy_file(source, target, copy_mode="move", overwrite=True)
    assert target.read_bytes() == b"old"
    assert source.read_bytes() == b"complete"


@pytest.mark.parametrize("measurements", [{}, {"original_firstorder_Mean": float("nan")},
                                         {"original_firstorder_Mean": 2., "original_shape_Volume": float("inf")}])
def test_radiomics_reports_missing_measurements_as_partial(tmp_path, monkeypatch, measurements):
    from fyron.boa_radiomics import extract_boa_radiomics_features
    import fyron.boa_radiomics.features as module
    case = tmp_path / "synthetic"
    case.mkdir()
    image = sitk.GetImageFromArray(np.ones((3, 3, 3), dtype=np.uint8))
    for name in ("ct.nii.gz", "total.nii.gz"):
        sitk.WriteImage(image, str(case / name))
    class Extractor:
        def execute(self, *args, **kwargs): return measurements
    monkeypatch.setattr(module, "_make_extractor", lambda settings=None: Extractor())
    result = extract_boa_radiomics_features([case], labels={"organ": 1},
                num_workers=1, show_progress=False, return_report=True)
    assert set(result["report"]["rows"].status) == {"partial"}


@pytest.mark.parametrize("copy_mode", ["copy", "move"])
def test_nnunet_compresses_uncompressed_nifti(tmp_path, copy_mode):
    image = sitk.GetImageFromArray(np.ones((2, 3, 4), dtype=np.uint8))
    source = tmp_path / "source.nii"
    sitk.WriteImage(image, str(source))
    frame = pd.DataFrame({"case_id": ["case"], "split": ["test"], "image_path": [source]})
    result = prepare_nnunetv2_dataset(frame, tmp_path / "out", 1, "Demo", copy_mode=copy_mode)
    from pathlib import Path
    assert Path(result.image_path.iloc[0]).read_bytes()[:2] == b"\x1f\x8b"
    assert source.exists() == (copy_mode != "move")


def test_nnunet_rejects_unwritten_channels(tmp_path):
    image = sitk.GetImageFromArray(np.ones((2, 3, 4), dtype=np.uint8))
    source = tmp_path / "source.nii.gz"
    sitk.WriteImage(image, str(source))
    frame = pd.DataFrame({"case_id": ["case"], "split": ["test"], "image_path": [source]})
    with pytest.raises(ValueError, match="channel"):
        prepare_nnunetv2_dataset(frame, tmp_path / "out", 1, "Demo", channel_names={0: "CT", 1: "MR"})
