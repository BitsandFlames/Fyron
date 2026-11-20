"""Controlled SQL diagnostics, recovery hints and streaming lifecycle."""
import json
import logging
from unittest.mock import Mock

import pandas as pd
import psycopg
import pytest

from fyron.console import _ColorFormatter, _JsonFormatter
from fyron.fhir.sql import FHIRSQLClient, SQLQueryError, _sql_failure, _worker_query_df

SECRET = 'private-patient secret-password SELECT hidden FROM private_table'


def client():
    obj = FHIRSQLClient.__new__(FHIRSQLClient)
    obj._conn = Mock()
    obj.log_queries = True
    return obj


@pytest.mark.parametrize('error,expected', [
    (psycopg.errors.InvalidPassword, 'authentication'),
    (psycopg.errors.InsufficientPrivilege, 'permission'),
    (psycopg.errors.SyntaxError, 'syntax'),
    (psycopg.errors.UndefinedTable, 'schema'),
    (psycopg.errors.QueryCanceled, 'timeout'),
    (psycopg.errors.InFailedSqlTransaction, 'transaction'),
    (psycopg.errors.DeadlockDetected, 'conflict'),
    (psycopg.errors.InvalidTextRepresentation, 'data'),
    (psycopg.OperationalError, 'connection'),
])
def test_wrapped_postgres_errors_are_actionable_and_redacted(monkeypatch, caplog, error, expected):
    original = error(SECRET)
    wrapped = pd.errors.DatabaseError(SECRET)
    wrapped.__cause__ = original
    monkeypatch.setattr(pd, 'read_sql_query', Mock(side_effect=wrapped))
    with caplog.at_level(logging.INFO), pytest.raises(SQLQueryError) as caught:
        client().query_df(SECRET, params={'id': SECRET})
    assert caught.value._fyron_sql_reason == expected
    assert SECRET not in caplog.text + str(caught.value)
    assert caught.value.__suppress_context__
    assert [r.fyron_event['stage'] for r in caplog.records] == ['started', 'failed']


def test_success_reports_rows_once_and_uses_shared_formatters(monkeypatch, caplog):
    monkeypatch.setattr(pd, 'read_sql_query', Mock(return_value=pd.DataFrame({'id': ['private', 'private']})))
    with caplog.at_level(logging.INFO):
        client().query_df(SECRET)
    assert len(caplog.records) == 2
    record = caplog.records[-1]
    payload = json.loads(_JsonFormatter().format(record))
    assert payload['rows'] == 2 and payload['sql_operation'] == 'dataframe'
    assert payload['elapsed_s'] >= 0
    assert '\x1b[' in _ColorFormatter(color=True).format(record)
    assert '\x1b[' not in _ColorFormatter(color=False).format(record)
    human = _ColorFormatter(color=False).format(record)
    assert 'SQL | DataFrame query finished | 2 rows' in human
    assert record.getMessage().startswith('operation=sql')
    assert SECRET not in caplog.text and 'private' not in caplog.text


def test_stream_interruption_never_logs_success(monkeypatch, caplog):
    def chunks():
        yield pd.DataFrame({'id': [1]})
        raise psycopg.errors.QueryCanceled(SECRET)
    monkeypatch.setattr(pd, 'read_sql_query', Mock(side_effect=lambda *a, **k: chunks()))
    with caplog.at_level(logging.INFO):
        stream = client().query_df_stream(SECRET)
        next(stream)
        with pytest.raises(SQLQueryError, match='time limit'):
            next(stream)
    assert caplog.records[-1].fyron_event['stage'] == 'failed'
    assert caplog.records[-1].fyron_event['rows'] == 1
    assert not any(r.fyron_event['stage'] == 'finished' for r in caplog.records)


def test_closed_stream_is_incomplete_and_closes_iterator(monkeypatch, caplog):
    closed = []
    def chunks():
        try:
            yield pd.DataFrame({'id': [1]})
            yield pd.DataFrame({'id': [2]})
        finally:
            closed.append(True)
    monkeypatch.setattr(pd, 'read_sql_query', Mock(side_effect=lambda *a, **k: chunks()))
    with caplog.at_level(logging.INFO):
        stream = client().query_df_stream(SECRET)
        next(stream)
        stream.close()
    assert closed == [True]
    assert caplog.records[-1].fyron_event['stage'] == 'incomplete'


def test_disabled_activity_stays_quiet_and_invalid_chunk_size_does_not_execute(monkeypatch, caplog):
    query = Mock(return_value=pd.DataFrame())
    monkeypatch.setattr(pd, 'read_sql_query', query)
    obj = client()
    obj.log_queries = False
    with caplog.at_level(logging.DEBUG):
        obj.query_df(SECRET)
        with pytest.raises(ValueError):
            list(obj.query_df_stream(SECRET, chunksize=0))
    assert not caplog.records
    assert query.call_count == 1


def test_worker_connect_failure_is_redacted(monkeypatch):
    monkeypatch.setattr('fyron.fhir.sql._connect_from_config', Mock(side_effect=psycopg.OperationalError(SECRET)))
    with pytest.raises(SQLQueryError, match='connection') as caught:
        _worker_query_df((None, 10, SECRET, None, None))
    assert SECRET not in str(caught.value)
    assert _sql_failure(caught.value, 'Batch')._fyron_sql_reason == 'connection'


def test_connection_auth_error_has_safe_category(monkeypatch, caplog):
    monkeypatch.setattr(psycopg, 'connect', Mock(side_effect=psycopg.errors.InvalidPassword(SECRET)))
    with caplog.at_level(logging.INFO), pytest.raises(SQLQueryError, match='authentication'):
        FHIRSQLClient(dsn='postgresql://synthetic:synthetic@localhost/synthetic', log_queries=True)
    assert caplog.records[-1].fyron_event['sql_operation'] == 'connection'
    assert caplog.records[-1].fyron_event['sql_error'] == 'authentication'
    assert SECRET not in caplog.text


def test_dict_query_and_exhausted_stream_count_results(monkeypatch, caplog):
    from types import SimpleNamespace
    obj = client()
    cursor = Mock()
    cursor.description = [SimpleNamespace(name='id')]
    cursor.fetchall.return_value = [(1,), (2,)]
    obj._conn.cursor.return_value.__enter__ = Mock(return_value=cursor)
    obj._conn.cursor.return_value.__exit__ = Mock(return_value=False)
    with caplog.at_level(logging.INFO):
        assert obj.query(SECRET) == [{'id': 1}, {'id': 2}]
    assert caplog.records[-1].fyron_event['rows'] == 2
    monkeypatch.setattr(pd, 'read_sql_query', Mock(return_value=iter([
        pd.DataFrame({'id': [1, 2]}), pd.DataFrame({'id': [3]}),
    ])))
    with caplog.at_level(logging.INFO):
        assert len(list(obj.query_df_stream(SECRET))) == 2
    assert caplog.records[-1].fyron_event['rows'] == 3
    assert caplog.records[-1].fyron_event['chunks'] == 2
    assert caplog.records[-1].fyron_event['stage'] == 'finished'


def test_failures_are_logged_with_activity_disabled(monkeypatch, caplog):
    obj = client()
    obj.log_queries = False
    monkeypatch.setattr(pd, 'read_sql_query', Mock(side_effect=psycopg.errors.SyntaxError(SECRET)))
    with caplog.at_level(logging.INFO), pytest.raises(SQLQueryError, match='syntax'):
        obj.query_df(SECRET)
    assert len(caplog.records) == 1
    assert caplog.records[0].levelno == logging.ERROR
    assert caplog.records[0].fyron_event['sql_error'] == 'syntax'


def test_missing_configuration_reports_a_controlled_error(monkeypatch, caplog):
    for key in ['DSN', 'HOST', 'PORT', 'NAME', 'USER', 'PASSWORD', 'SSLMODE']:
        monkeypatch.delenv('FHIR_DB_' + key, raising=False)
    with caplog.at_level(logging.INFO), pytest.raises(SQLQueryError, match='connection settings'):
        FHIRSQLClient()
    assert caplog.records[-1].fyron_event['sql_error'] == 'configuration'
