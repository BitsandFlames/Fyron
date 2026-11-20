"""Synthetic regression probes for client recovery, reports and transport boundaries."""
import json
import logging
from pathlib import Path
import threading
from unittest.mock import Mock

import pandas as pd
import pytest
import requests
from urllib3.util.retry import Retry

from fyron import DICOMDownloader, DocumentDownloader, FHIRRestClient, FHIRSQLClient
from fyron._client_io import atomic_csv
from fyron._http import DICOMSession, get_with_retry, private_transport
from fyron.datasets import make_dicom_series
from fyron.dicom.client import DicomDownloadError
from fyron.fhir.sql import SQLConfig, _connect_from_config
from test_document_download import DocumentAdapter, URL, client as document_client


SECRET = 'private-token patient-secret internal.example.org'


def sql_client(query):
    client = FHIRSQLClient.__new__(FHIRSQLClient)
    client.query_df_stream = query
    return client


def export(client, folder, **kwargs):
    return client.export_query_partitioned('SELECT %(filter)s', folder,
        start='2025-01-01', end='2025-01-02', window_days=1,
        params={'filter':'synthetic'}, **kwargs)


def test_sql_verified_resume_and_query_changes(tmp_path):
    calls = []
    def query(*args, **kwargs):
        calls.append(True)
        yield pd.DataFrame({'value':[1]})
    client = sql_client(query)
    first = export(client, tmp_path)
    assert first.status.tolist() == ['ok']
    assert export(client, tmp_path).status.tolist() == ['skipped']
    assert len(calls) == 1
    with pytest.raises(FileExistsError, match='unverified'):
        client.export_query_partitioned('SELECT different', tmp_path,
            start='2025-01-01', end='2025-01-02', window_days=1)
    assert len(calls) == 1
    path = Path(first.iloc[0].output_path)
    path.write_text('corrupted\n')
    with pytest.raises(FileExistsError):
        export(client, tmp_path)
    assert path.read_text() == 'corrupted\n'
    assert export(client, tmp_path, overwrite=True).status.tolist() == ['ok']
    assert path.read_text() == 'value\n1\n'
    for record in tmp_path.rglob('.fyron-complete-*.json'):
        assert 'SELECT' not in record.read_text() and 'synthetic' not in record.read_text()


def test_sql_no_record_and_interruption_preserve_outputs(tmp_path):
    def query(*args, **kwargs):
        yield pd.DataFrame({'value':[1]})
    client = sql_client(query)
    result = export(client, tmp_path, write_completion_record=False)
    path = Path(result.iloc[0].output_path)
    assert not list(tmp_path.rglob('*.json'))
    with pytest.raises(FileExistsError):
        export(client, tmp_path)
    def interrupted(*args, **kwargs):
        yield pd.DataFrame({'value':[9]})
        raise KeyboardInterrupt
    client.query_df_stream = interrupted
    with pytest.raises(KeyboardInterrupt):
        export(client, tmp_path, overwrite=True)
    assert path.read_text() == 'value\n1\n'
    assert not list(tmp_path.rglob('.fyron-sql-*'))


@pytest.mark.parametrize('field', ['statement_timeout','lock_timeout'])
@pytest.mark.parametrize('value', [0,-1,True,float('nan')])
def test_sql_timeouts_validate_before_connect(monkeypatch, field, value):
    connect = Mock()
    monkeypatch.setattr('fyron.fhir.sql.psycopg.connect', connect)
    with pytest.raises(ValueError):
        FHIRSQLClient(dsn='synthetic', **{field:value})
    connect.assert_not_called()


def test_sql_settings_are_bound_on_owned_connections(monkeypatch):
    cursor = Mock()
    connection = Mock()
    connection.cursor.return_value.__enter__ = Mock(return_value=cursor)
    connection.cursor.return_value.__exit__ = Mock(return_value=False)
    monkeypatch.setattr('fyron.fhir.sql.psycopg.connect', Mock(return_value=connection))
    config = SQLConfig('synthetic',None,None,None,None,None,None,2.5,0.5)
    assert _connect_from_config(config,10) is connection
    assert [call.args[1] for call in cursor.execute.call_args_list] == [
        ('statement_timeout','2500'),('lock_timeout','500')]
    connection.commit.assert_called_once()


def test_expected_text_response_and_validation_policy(tmp_path):
    loader, _ = document_client(tmp_path, DocumentAdapter(content_type='text/html', body=b'<html>login</html>'),
                                expected_content_types=['text/plain'])
    result = loader.download_url(URL)
    assert result.error and 'content type' in result.error
    assert not list(tmp_path.rglob('*.html'))
    loader, _ = document_client(tmp_path, DocumentAdapter(content_type='text/plain; charset=utf-8', body=b'hello'),
                                expected_content_types=['text/plain'])
    assert loader.download_url(URL).error is None


def test_document_reports_and_parallel_input_order(tmp_path):
    loader, _ = document_client(tmp_path, max_workers=3)
    frame = pd.DataFrame({'document_url':[URL+'?n='+str(i) for i in range(8)],
                          'id':[f'{i:03}' for i in range(8)]})
    result = loader.download_from_df(frame,id_col='id',return_report=True)
    assert result['data'].document_id.tolist() == frame.id.tolist()
    assert result['report']['rows'].task.tolist() == list(range(8))
    summary = result['report']['summary'].iloc[0]
    assert summary.requested_tasks == 8 and summary.succeeded_tasks == 8 and summary.successful
    again = loader.download_from_df(frame,id_col='id',return_report=True)
    assert again['report']['summary'].iloc[0].skipped_tasks == 8
    empty = loader.download_urls([],return_report=True)
    assert empty['data'].empty and empty['report']['rows'].empty
    assert empty['report']['summary'].iloc[0].requested_tasks == 0


def test_document_submission_queue_is_bounded(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    import fyron.documents.client as module
    outstanding = 0
    peak = 0
    lock = threading.Lock()
    class Pool(ThreadPoolExecutor):
        def submit(self,*args,**kwargs):
            nonlocal outstanding, peak
            with lock:
                outstanding += 1
                peak = max(peak,outstanding)
            future = super().submit(*args,**kwargs)
            def done(_):
                nonlocal outstanding
                with lock: outstanding -= 1
            future.add_done_callback(done)
            return future
    monkeypatch.setattr(module,'ThreadPoolExecutor',Pool)
    loader, _ = document_client(tmp_path,max_workers=2)
    result = loader.download_urls([URL+'?n='+str(i) for i in range(30)])
    assert len(result) == 30 and result.error.isna().all()
    assert peak <= 4


def test_borrowed_sessions_remain_unchanged(tmp_path):
    with requests.Session() as session:
        adapters = dict(session.adapters)
        hooks = {key:list(value) for key,value in session.hooks.items()}
        headers = dict(session.headers)
        with DocumentDownloader(auth=session, output_dir=tmp_path): pass
        with DICOMDownloader(auth=session, dicom_web_url='https://example.org/dicomweb'): pass
        with FHIRRestClient(auth=session,base_url='https://example.org/fhir',
                            extra_headers={'X-Demo':'synthetic'}): pass
        assert dict(session.adapters) == adapters
        assert session.hooks == hooks and dict(session.headers) == headers


@pytest.mark.parametrize('logger_name', ['dicomweb_client.web', 'urllib3.connectionpool', 'urllib3.connection', 'urllib3.poolmanager'])
def test_upstream_debug_is_suppressed_only_inside_transport(caplog, logger_name):
    upstream = logging.getLogger(logger_name)
    @private_transport
    def operation(): upstream.warning(SECRET)
    with caplog.at_level(logging.DEBUG):
        operation()
        upstream.warning('unrelated application diagnostic')
    assert SECRET not in caplog.text
    assert 'unrelated application diagnostic' in caplog.text


def test_retry_after_and_no_retry_for_permissions(monkeypatch):
    from fyron import _http
    session = requests.Session()
    adapter = DocumentAdapter(status=429)
    session.mount('https://',adapter)
    original = adapter.send
    calls = []
    def send(*args,**kwargs):
        response = original(*args,**kwargs)
        calls.append(True)
        response.status_code = 429 if len(calls)==1 else 200
        response.headers['Retry-After'] = '1'
        return response
    adapter.send = send
    sleeps = []
    monkeypatch.setattr(_http.time,'sleep',sleeps.append)
    assert get_with_retry(session,URL).status_code == 200
    assert len(calls) == 2 and sleeps == [1]
    session.mount('https://',DocumentAdapter(status=403))
    assert get_with_retry(session,URL).status_code == 403
    session.close()


def test_dicom_timeout_facade_forwards_without_mutating_session():
    session = requests.Session()
    session.get = Mock(return_value=Mock(status_code=200,headers={}))
    DICOMSession(session,timeout=7,retries=Retry(total=0)).get('https://example.org/dicomweb')
    assert session.get.call_args.kwargs['timeout'] == 7


def test_invalid_dicom_instance_does_not_publish_partial_study(tmp_path):
    import pydicom
    files = make_dicom_series(tmp_path/'source')
    datasets = [pydicom.dcmread(path) for path in files]
    del datasets[-1].SeriesInstanceUID
    with DICOMDownloader(dicom_web_url='https://example.org/dicomweb',output_format='dicom') as loader:
        loader.client.iter_study = Mock(return_value=iter(datasets))
        with pytest.raises(DicomDownloadError):
            loader.download_study(str(datasets[0].StudyInstanceUID),tmp_path/'out')
    assert not list((tmp_path/'out').rglob('*.dcm'))
    assert not list((tmp_path/'out').rglob('*.json'))


def test_dicom_reports_distinguish_tasks_from_series(tmp_path,monkeypatch):
    from fyron.dicom.client import DicomResult
    with DICOMDownloader(dicom_web_url='https://example.org/dicomweb',output_format='dicom') as loader:
        def run(**kwargs):
            return [DicomResult('1.2.3',f'1.2.3.{n}','hash',str(tmp_path),'dicom') for n in [1,2]]
        monkeypatch.setattr(loader,'_run_task',run)
        result = loader.download_from_dataframe(pd.DataFrame({'study_instance_uid':['1.2.3','1.2.3']}),
            tmp_path,download_full_study=True,return_report=True,show_progress=False)
        summary=result['report']['summary'].iloc[0]
        assert len(result['data'])==2 and summary.input_rows==2 and summary.requested_tasks==1
        assert summary.returned_rows==2


def test_atomic_report_preserves_old_file_on_error(tmp_path,monkeypatch):
    path=tmp_path/'results.csv';path.write_text('old report')
    def fail(*args,**kwargs): raise OSError(SECRET)
    frame=pd.DataFrame({'n':[1]})
    monkeypatch.setattr(frame,'to_csv',fail)
    with pytest.raises(OSError): atomic_csv(frame,path)
    assert path.read_text()=='old report'
    assert not list(tmp_path.glob('.fyron-report-*'))


def test_cancelled_document_batch_cleans_staging_and_writes_partial_report(tmp_path, monkeypatch):
    import fyron.documents.client as module
    loader, _ = document_client(tmp_path/'downloads', max_workers=2)
    def interrupt(*args,**kwargs):
        raise KeyboardInterrupt
    monkeypatch.setattr(module,'wait',interrupt)
    report = tmp_path/'report.csv'
    with pytest.raises(KeyboardInterrupt):
        loader.download_urls([URL+'?n='+str(i) for i in range(40)],results_csv=report)
    assert report.is_file()
    assert not list(tmp_path.rglob('.fyron-stage-*'))
    assert not list(tmp_path.rglob('.fyron-report-*'))
    rows = pd.read_csv(report)
    assert len(rows) <= 4  # Only the bounded initial queue can have executed.


def test_cancelled_retry_does_not_sleep_or_contact_service(monkeypatch):
    from fyron._http import ClientCancelledError
    event = threading.Event(); event.set()
    session = requests.Session()
    session.get = Mock()
    with pytest.raises(ClientCancelledError):
        get_with_retry(session,URL,cancel_event=event)
    session.get.assert_not_called()


def test_empty_and_unrequested_fhir_queries_are_distinct():
    with FHIRRestClient(auth=requests.Session(),base_url='https://example.org/fhir') as loader:
        result=loader.query_df_from(pd.DataFrame({'id':['001']}), 'Patient', {'_id':'id'},
            max_pages=0, use_multiprocessing=False, show_progress=False, return_report=True)
    summary=result['report']['summary'].iloc[0]
    assert summary.executed_queries == 0 and summary.not_requested == 1
    assert not summary.retrieval_exhaustive


@pytest.mark.parametrize('value', ['', '  ', [], [None], ['001', '']])
def test_fhir_empty_cohort_keys_cannot_broaden_queries(value, monkeypatch):
    with FHIRRestClient(auth=requests.Session(),base_url='https://example.org/fhir') as loader:
        query=Mock(side_effect=AssertionError('No network expected'))
        monkeypatch.setattr(loader,'_query_jobs',query)
        with pytest.raises(ValueError):
            loader.query_df_from(pd.DataFrame({'id':[value]}),'Patient',{'_id':'id'},
                                 show_progress=False,use_multiprocessing=False)
        query.assert_not_called()


def test_combined_sql_exports_preserve_identifier_text(tmp_path):
    def query(*args, **kwargs):
        yield pd.DataFrame({'patient_id':['001','NA'], 'value':[1,2]})
    client=sql_client(query)
    result=client.export_query_partitioned('SELECT synthetic',tmp_path,
        start='2025-01-01',end='2025-01-03',window_days=1,combine_by='year')
    combined=tmp_path/'combined_2025.csv'
    data=pd.read_csv(combined,dtype=str,keep_default_na=False)
    assert data.patient_id.tolist()==['001','NA','001','NA']
    assert set(result.status)=={'ok'}
    client.export_query_partitioned('SELECT synthetic',tmp_path,
        start='2025-01-01',end='2025-01-03',window_days=1,combine_by='year')
    combined.write_text('unverified report')
    with pytest.raises(FileExistsError):
        client.export_query_partitioned('SELECT synthetic',tmp_path,
            start='2025-01-01',end='2025-01-03',window_days=1,combine_by='year')
    assert combined.read_text()=='unverified report'


def test_upstream_dicom_warnings_do_not_expose_values(caplog):
    import warnings
    @private_transport
    def operation():
        warnings.warn_explicit(SECRET,UserWarning,'/site-packages/pydicom/valuerep.py',1)
        logging.getLogger('pydicom').warning(SECRET)
    with warnings.catch_warnings(record=True) as caught, caplog.at_level(logging.DEBUG):
        warnings.simplefilter('always')
        operation()
        warnings.warn('unrelated application warning',UserWarning)
    assert SECRET not in caplog.text
    assert [str(item.message) for item in caught] == ['unrelated application warning']
