"""Custom document naming and cached authentication with synthetic sources."""
import os
from pathlib import Path

import pandas as pd
import pytest

from fyron import Auth, DocumentDownloader
from fyron.cli import main
from fyron.documents import _cli
from fyron.fhir._device_auth import DeviceAuthError
from test_document_download import client, DocumentAdapter, PDF, URL, fake_cli, provider


@pytest.mark.parametrize('flat', [False, True])
@pytest.mark.parametrize('workers', [1, 4])
def test_custom_ids_layout_results_and_restart(tmp_path, flat, workers):
    loader, adapter = client(tmp_path, flat_output=flat, max_workers=workers)
    frame = pd.DataFrame({'document_url': [URL, URL+'?other'], 'id': ['00123', 456]})
    results = loader.download_from_df(frame, id_col='id', results_csv=tmp_path/'results.csv')
    assert results.error.isna().all()
    for row in results.itertuples():
        assert row.download_id == loader.download_id(row.url)
        expected = tmp_path / (row.document_id+'.pdf') if flat else tmp_path/row.document_id/(row.document_id+'.pdf')
        assert Path(row.path) == expected and expected.read_bytes() == PDF
    saved = pd.read_csv(tmp_path/'results.csv', dtype={'document_id': str})
    assert set(saved.document_id) == {'00123', '456'}
    assert loader.download_from_dataframe(frame, id_col='id').skipped.all()
    assert len(adapter.calls) == 2


@pytest.mark.parametrize('value', ['', None, pd.NA, 1.0, True, '../x', 'a/b', 'a\\b', 'a.', ' a', 'ä', 'CON', 'nul.txt', 'COM1', 'LPT9', 'a'*129])
def test_invalid_ids_precede_download(tmp_path, value):
    loader, adapter = client(tmp_path)
    frame = pd.DataFrame({'document_url': [URL, URL+'?next'], 'id': ['good', value]})
    with pytest.raises(ValueError):
        loader.download_from_df(frame, id_col='id')
    assert not adapter.calls and not list(tmp_path.iterdir())


@pytest.mark.parametrize('ids', [['same', 'same'], ['ID', 'id'], [1, '1']])
def test_collisions_precede_authentication(tmp_path, monkeypatch, ids):
    path = tmp_path/'input.csv'
    pd.DataFrame({'document_url': [URL, URL+'?other'], 'id': ids}).to_csv(path, index=False)
    def forbidden(**kwargs):
        pytest.fail('Authentication must not start for invalid IDs')
    monkeypatch.setattr(_cli, 'Auth', forbidden)
    assert main(['document-download', '--csv', str(path), '--id-col', 'id',
                 '--auth-type', 'device_code', '--auth-url', 'https://identity.example.test',
                 '--client-id', 'demo']) == 2


def test_identity_binding_and_overwrite(tmp_path):
    loader, adapter = client(tmp_path, flat_output=True, require_pdf=True)
    first = loader.download_url(URL, document_id='chosen')
    assert first.error is None and first.document_id == 'chosen'
    changed = loader.download_url(URL+'?different', document_id='chosen')
    assert changed.error and not changed.skipped
    adapter.body = b'bad PDF'
    loader.skip_existing = False
    assert loader.download_url(URL, document_id='chosen').error
    assert Path(first.path).read_bytes() == PDF
    adapter.body = b'%PDF-new'
    assert loader.download_url(URL+'?different', document_id='chosen').error is None
    loader.skip_existing = True
    assert loader.download_url(URL, document_id='chosen').error
    assert loader.download_url(URL+'?different', document_id='chosen').skipped


def test_exact_path_no_records_default_and_report_protection(tmp_path):
    loader, _ = client(tmp_path, flat_output=True, write_completion_record=False)
    chosen = tmp_path/'explicit.pdf'
    result = loader.download_url(URL, document_id='001', output_path=chosen)
    assert result.path == str(chosen) and result.document_id == '001'
    assert not list(tmp_path.glob('*.json'))
    frame = pd.DataFrame({'document_url': [URL], 'id': ['002']})
    with pytest.raises(ValueError, match='overwrite a document'):
        loader.download_from_df(frame, id_col='id', results_csv=tmp_path/'002.pdf')
    assert (tmp_path/'002.pdf').read_bytes() == PDF
    assert loader.download_from_df(frame, id_col='id').error.notna().all()
    default = loader.download_url(URL+'?default')
    assert default.document_id == default.download_id == loader.download_id(URL+'?default')


def test_cli_custom_ids_and_leading_zeros(tmp_path, monkeypatch):
    fake_cli(monkeypatch, DocumentAdapter())
    source = tmp_path/'input.csv'
    source.write_text('document_url,document_id\n'+URL+',00123\n')
    output = tmp_path/'docs'; report = tmp_path/'results.csv'
    assert main(['document-download', '--csv', str(source), '--id-col', 'document_id',
                 '--flat-output', '--no-completion-record', '--output-dir', str(output),
                 '--results-csv', str(report)]) == 0
    assert (output/'00123.pdf').read_bytes() == PDF
    assert pd.read_csv(report, dtype=str).document_id.tolist() == ['00123']
    assert main(['document-download', '--url', URL, '--document-id', 'single',
                 '--flat-output', '--output-dir', str(output)]) == 0
    assert (output/'single.pdf').read_bytes() == PDF
    assert main(['document-download', '--url', URL, '--id-col', 'id']) == 2
    assert main(['document-download', '--csv', str(source), '--document-id', 'id']) == 2


@pytest.mark.skipif(os.name != 'posix', reason='Protected cache requires POSIX')
def test_document_cache_reuse_and_parallel_refresh(provider, tmp_path):
    cache = tmp_path/'cache/tokens.json'; callbacks = []
    kwargs = dict(auth_type='device_code', auth_url=provider['url'], client_id='demo',
                  token_cache=str(cache), device_code_callback=callbacks.append)
    with Auth(**kwargs) as auth:
        with DocumentDownloader(auth=auth, output_dir=tmp_path/'first', require_pdf=True) as loader:
            assert loader.download_url(provider['url']+'/documents/first').error is None
    assert len(callbacks) == 1
    provider['revoked'] = True
    provider['download_delay'] = 0.03
    with Auth(**kwargs, allow_reauthentication=False) as auth:
        with DocumentDownloader(auth=auth, output_dir=tmp_path/'second', require_pdf=True,
                                flat_output=True, write_completion_record=False) as loader:
            frame = pd.DataFrame({'document_url': [provider['url']+f'/documents/{i}' for i in range(8)],
                                  'id': [f'doc-{i}' for i in range(8)]})
            results = loader.download_from_df(frame, id_col='id')
            assert results.error.isna().all()
    assert len(callbacks) == 1 and provider['logins'] == 1 and provider['refreshes'] == 1
    assert provider['peak_downloads'] > 1
    assert cache.stat().st_mode & 0o777 == 0o600
    assert not list((tmp_path/'second').glob('*.json'))
    with pytest.raises(DeviceAuthError):
        Auth(**{**kwargs, 'token_cache': str(tmp_path/'missing.json')}, allow_reauthentication=False)


@pytest.mark.skipif(os.name != 'posix', reason='Protected cache requires POSIX')
def test_cli_cached_document_session(provider, tmp_path, capsys):
    args = ['--no-color', 'document-download', '--url', provider['url']+'/documents/one',
            '--auth-type', 'device_code', '--auth-url', provider['url'], '--client-id', 'demo',
            '--token-cache', str(tmp_path/'cache.json'), '--output', str(tmp_path/'one.pdf')]
    assert main(args) == 0
    assert 'Sign in' in capsys.readouterr().out
    args[args.index('--output')+1] = str(tmp_path/'two.pdf')
    assert main(args+['--no-reauthentication']) == 0
    assert 'Sign in' not in capsys.readouterr().out
    provider['refresh_error'] = 'invalid_grant'; provider['revoked'] = True
    args[args.index('--output')+1] = str(tmp_path/'three.pdf')
    assert main(args+['--no-reauthentication']) == 1
    assert not (tmp_path/'three.pdf').exists()
    assert provider['logins'] == 1


@pytest.mark.parametrize('workers', [1, 4])
def test_distinct_ids_cannot_overwrite_each_other_after_extension_resolution(tmp_path, workers):
    loader, _ = client(tmp_path, flat_output=True, max_workers=workers, skip_existing=False)
    frame = pd.DataFrame({'document_url': [URL, URL+'?different'], 'id': ['report', 'report.pdf']})
    results = loader.download_from_df(frame, id_col='id')
    assert results.error.isna().sum() == 1
    assert results.error.notna().sum() == 1
    assert (tmp_path/'report.pdf').read_bytes() == PDF
