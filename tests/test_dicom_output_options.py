"""Synthetic naming and JSON opt-out coverage; no clinical services."""
from unittest.mock import Mock

import pandas as pd
import pydicom
import pytest

from fyron.datasets import make_dicom_series
from fyron.dicom import DICOMDownloader
from fyron.dicom.client import _build_tasks, _check_exact_study_directory, _worker_download_task


@pytest.mark.parametrize('layout', ['flat', 'hierarchical'])
@pytest.mark.parametrize('output_format', ['dicom', 'nifti'])
def test_exact_folder_and_no_json(tmp_path, layout, output_format):
    files = make_dicom_series(tmp_path / 'source')
    instances = [pydicom.dcmread(p) for p in files]
    uid = str(instances[0].StudyInstanceUID)
    with DICOMDownloader(dicom_web_url='https://example.org/dicomweb', output_format=output_format,
                         write_completion_record=False) as loader:
        loader.client.iter_study = Mock(return_value=iter(instances))
        result = loader.download_from_df(
            pd.DataFrame({'study_instance_uid': [uid], 'ACC_NR': ['00123']}),
            tmp_path / 'out', download_full_study=True, study_layout=layout,
            study_folder_name_col='ACC_NR', append_study_hash=False,
            save_study_manifest=False,
        )
        assert result.error.isna().all()
        folder = tmp_path / 'out' / '00123'
        assert folder.is_dir()
        assert not list(folder.rglob('*.json'))
        assert list(folder.rglob('*.dcm' if output_format == 'dicom' else '*.nii.gz'))
        assert all(str(folder) in path for path in result.path)
        if output_format == 'dicom':
            loader.client.iter_study = Mock(return_value=iter(instances))
            again = loader.download_study(uid, tmp_path/'out', study_folder_name='00123',
                append_study_hash=False, study_layout=layout, save_study_manifest=False)
            assert any(item.error for item in again)
            assert not any(item.skipped for item in again)
            loader.client.iter_study = Mock(return_value=iter(instances))
            replaced = loader.download_study(uid, tmp_path/'out', study_folder_name='00123',
                append_study_hash=False, study_layout=layout, save_study_manifest=False,
                skip_existing=False)
            assert all(item.error is None for item in replaced)


@pytest.mark.parametrize('labels', [['same','same'], ['Case','case']])
def test_batch_folder_collisions_rejected_before_download(labels):
    with pytest.raises(ValueError, match='collid'):
        _build_tasks(pd.DataFrame({'study':['1.2.3','1.2.4'],'label':labels}),
                     'study','series',True,'label',append_study_hash=False)


@pytest.mark.parametrize('label', [None, '', '../escape', 'folder/name', 'CON', 'trail.', ' space', float('nan')])
def test_unsafe_exact_names_rejected(label):
    with pytest.raises(ValueError):
        DICOMDownloader._study_output_dir_name('1.2.3', label, False)


@pytest.mark.parametrize('uid', [None, float('nan'), 1.2, '', '1.02.3'])
def test_invalid_study_uid_has_controlled_validation(uid):
    with pytest.raises(ValueError, match='StudyInstanceUID'):
        _build_tasks(pd.DataFrame({'study':[uid],'label':['001']}),
                     'study','series',True,'label',append_study_hash=False)


def test_existing_other_study_cannot_share_folder(tmp_path):
    files = make_dicom_series(tmp_path / 'existing')
    with pytest.raises(ValueError, match='different study'):
        _check_exact_study_directory(tmp_path/'existing', '1.2.3')


def test_unidentifiable_existing_folder_is_preserved(tmp_path):
    (tmp_path / 'existing.nii.gz').write_bytes(b'untouched')
    with pytest.raises(ValueError, match='identity'):
        _check_exact_study_directory(tmp_path, '1.2.3')
    assert (tmp_path/'existing.nii.gz').read_bytes() == b'untouched'


def test_worker_propagates_output_options(tmp_path, monkeypatch):
    captured = {}
    class Loader:
        def __init__(self, **kwargs): captured.update(kwargs)
        def _run_task(self, **kwargs): return []
        def close(self): pass
    monkeypatch.setattr('fyron.dicom.client.DICOMDownloader', Loader)
    monkeypatch.setattr('fyron.dicom.client.current_worker_auth', lambda: None)
    args = (('1.2.3',None,True,'001'), 'https://example.org/dicomweb', 'dicom', False,
            True, False, tmp_path, None, None, 'flat', False, False, 'reference.dcm',
            None, False, False)
    assert _worker_download_task(args) == []
    assert captured['append_study_hash'] is False
    assert captured['write_completion_record'] is False


def test_single_series_can_omit_completion_json(tmp_path):
    files = make_dicom_series(tmp_path/'source')
    datasets = [pydicom.dcmread(path) for path in files]
    with DICOMDownloader(dicom_web_url='https://example.org/dicomweb', output_format='dicom',
                         write_completion_record=False) as loader:
        loader.client.iter_series = Mock(return_value=iter(datasets))
        result = loader.download_series(str(datasets[0].StudyInstanceUID),
            str(datasets[0].SeriesInstanceUID), tmp_path/'out')
        assert result.error is None
        assert not list((tmp_path/'out').rglob('*.json'))


def test_cli_flags_and_string_labels_are_forwarded(tmp_path, monkeypatch):
    from fyron.cli import main
    captured = {}
    class Loader:
        def __init__(self, **kwargs): captured.update(kwargs)
        def download_from_dataframe(self, **kwargs):
            captured['df'] = kwargs['df']
            captured['manifest'] = kwargs['save_study_manifest']
            return pd.DataFrame({'error':[None], 'skipped':[False]})
    monkeypatch.setattr('fyron.dicom.DICOMDownloader', Loader)
    csv = tmp_path/'input.csv'
    csv.write_text('study_instance_uid,ACC_NR\n1.2.3,00123\n')
    assert main(['dicom-download','--dicom-web-url','https://example.org/dicomweb',
        '--csv',str(csv),'--full-study','--study-folder-col','ACC_NR',
        '--no-study-hash','--no-completion-record','--no-study-manifest']) == 0
    assert captured['append_study_hash'] is False
    assert captured['write_completion_record'] is False
    assert captured['manifest'] is False
    assert captured['df'].ACC_NR.tolist() == ['00123']


@pytest.mark.parametrize('value', [True, 12.5, ' trimmed '])
def test_batch_exact_labels_are_not_silently_converted(value):
    with pytest.raises(ValueError):
        _build_tasks(pd.DataFrame({'study':['1.2.3'],'label':[value]}),
                     'study','series',True,'label',append_study_hash=False)


def test_arbitrary_column_names_and_duplicate_tasks():
    rows = pd.DataFrame({'Study UID':['1.2.3','1.2.3'],'Acc Nr':['00123','00123']})
    tasks = _build_tasks(rows, 'Study UID', 'Series UID', True, 'Acc Nr', False)
    assert tasks == [('1.2.3', None, True, '00123')]
