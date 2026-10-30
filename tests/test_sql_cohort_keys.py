"""Synthetic regression coverage for cohort SQL binding and reports."""
import logging

import pandas as pd
import pytest

from fyron.fhir.sql import FHIRSQLClient, SQLQueryError, _expand_sql_placeholders, _template_tokens


def client_with_query(query):
    client = object.__new__(FHIRSQLClient)
    client.query_df = query
    client.query_to_dataframe = query
    client.log_queries = False
    return client


def test_legacy_occurrence_order_and_repeated_blocks():
    df = pd.DataFrame({'a': ['001', '002'], 'b': ['X', 'Y']})
    sql, params = _expand_sql_placeholders(
        'b IN ({bs}) OR a IN ({{as_}}) OR b IN ({bs})', df,
        {'as_': 'a', 'bs': 'b'})
    assert sql == 'b IN (%s,%s) OR a IN (%s,%s) OR b IN (%s,%s)'
    assert params == ['X', 'Y', '001', '002', 'X', 'Y']
    _, named = _expand_sql_placeholders('a IN ({ids}) OR a IN ({ids})', df, {'ids': 'a'}, 'named')
    assert named == {'ids_0': '001', 'ids_1': '002'}


def test_only_executable_templates_are_expanded():
    sql = """SELECT '{ids}', "{ids}", $$ {ids} $$, $body${ids}$body$,
    E'escaped\\' {ids}' -- {ids}
    /* outer {ids} /* nested */ still {ids} */ WHERE a IN ({ids})"""
    tokens = _template_tokens(sql)
    assert len(tokens) == 1
    expanded, params = _expand_sql_placeholders(sql, pd.DataFrame({'id': [1]}), {'ids': 'id'})
    assert expanded == sql[:tokens[0][0]] + '%s' + sql[tokens[0][1]:]
    assert params == [1]


@pytest.mark.parametrize('sql', ["select 'oops", '/* incomplete', 'select $tag$unfinished'])
def test_unterminated_sql_is_rejected(sql):
    with pytest.raises(ValueError):
        _template_tokens(sql)


def test_legacy_repeated_blocks_respect_parameter_budget():
    calls = []
    client = client_with_query(lambda sql, params=None, **kw: calls.append(params) or pd.DataFrame())
    client.query_df_from(pd.DataFrame({'id': range(5)}), 'a IN ({ids}) OR b IN ({ids})',
                         {'ids': 'id'}, param_limit=5, param_safety_factor=1, chunk_size=100)
    assert [len(p) for p in calls] == [4, 4, 2]


@pytest.mark.parametrize('kwargs', [{'chunk_size': 0}, {'chunk_size': True}, {'param_limit': -1},
                                   {'max_workers': 0}, {'param_safety_factor': float('nan')}, {'merge': 'unknown'}])
def test_legacy_invalid_options_before_queries(kwargs):
    client = client_with_query(lambda *a, **k: pytest.fail('query executed'))
    with pytest.raises(ValueError):
        client.query_df_from(pd.DataFrame({'id': [1]}), 'a IN ({ids})', {'ids': 'id'}, **kwargs)


def test_key_deduplication_bound_values_and_coverage():
    calls = []
    def query(sql, params=None):
        calls.append((sql, params))
        value = params['_fyron_key_0_0']
        return pd.DataFrame({'patient': [value, value] if value == '001' else [], 'value': [3, 4] if value == '001' else []})
    client = client_with_query(query)
    result = client.query_df_for_keys(pd.DataFrame({'id': ['001', '001', "x'); DROP TABLE patient; --"]}),
        'SELECT patient, value FROM observations WHERE patient IN ({cohort_keys}) AND code=%(code)s',
        key_columns=['id'], params={'code': 'synthetic'}, result_key_columns=['patient'],
        chunk_size=1, return_report=True)
    assert len(calls) == 2
    assert all('DROP TABLE' not in sql for sql, _ in calls)
    assert calls[0][1]['_fyron_key_0_0'] == '001'
    assert len(result['data']) == 2
    summary = result['report']['summary'].iloc[0]
    assert summary['distinct_keys'] == 2 and summary['duplicate_keys_removed'] == 1
    assert summary['matched_keys'] == 1 and summary['unmatched_keys'] == 1
    assert result['report']['unmatched_keys']['id'].tolist() == ["x'); DROP TABLE patient; --"]
    assert result['report']['rows']['requested_keys'].tolist() == [1, 1]


def test_composite_keys_keep_tuple_relationships():
    calls = []
    def query(sql, params=None):
        calls.append((sql, params))
        return pd.DataFrame({'p': ['A', 'B'], 'e': [1, 2]})
    result = client_with_query(query).query_df_for_keys(pd.DataFrame({'patient': ['A', 'B'], 'encounter': [1, 2]}),
        'SELECT p,e FROM visits WHERE (p,e) IN ({cohort_keys})', key_columns=['patient', 'encounter'],
        result_key_columns=['p', 'e'], return_report=True)
    assert 'IN ((%(_fyron_key_0_0)s,%(_fyron_key_0_1)s),(%(_fyron_key_1_0)s,%(_fyron_key_1_1)s))' in calls[0][0]
    assert list(calls[0][1].values()) == ['A', 1, 'B', 2]
    assert result['report']['summary'].iloc[0]['matched_keys'] == 2


@pytest.mark.parametrize('kwargs', [dict(key_columns=[]), dict(key_columns='id'), dict(key_columns=['missing']),
    dict(key_columns=['id', 'id']), dict(key_columns=['id'], chunk_size=0),
    dict(key_columns=['id'], params={'_fyron_key_0_0': 5}),
    dict(key_columns=['id'], result_key_columns=['x','y'])])
def test_key_validation_before_execution(kwargs):
    client = client_with_query(lambda *a, **k: pytest.fail('query executed'))
    with pytest.raises(ValueError):
        client.query_df_for_keys(pd.DataFrame({'id': [1]}), 'SELECT id WHERE id IN ({cohort_keys})', **kwargs)


@pytest.mark.parametrize('df', [pd.DataFrame({'id': [None]}), pd.DataFrame([[1, 2]], columns=['id','id']), pd.DataFrame({'id': [[1,2]]})])
def test_invalid_key_data(df):
    with pytest.raises(ValueError):
        client_with_query(lambda *a, **k: pytest.fail('query executed')).query_df_for_keys(
            df, 'SELECT id WHERE id IN ({cohort_keys})', key_columns=['id'])


@pytest.mark.parametrize('sql', ["SELECT '{cohort_keys}'", 'SELECT {cohort_keys}, {cohort_keys}', 'SELECT {{cohort_keys}}'])
def test_requires_exactly_one_executable_block(sql):
    with pytest.raises(ValueError):
        client_with_query(lambda *a, **k: pytest.fail('query executed')).query_df_for_keys(
            pd.DataFrame({'id': [1]}), sql, key_columns=['id'])


def test_empty_input_and_unavailable_coverage():
    client = client_with_query(lambda *a, **k: pytest.fail('query executed'))
    result = client.query_df_for_keys(pd.DataFrame({'id': []}), 'SELECT id WHERE id IN ({cohort_keys})',
                                     key_columns=['id'], return_report=True)
    assert result['data'].empty and result['report']['rows'].empty
    summary = result['report']['summary'].iloc[0]
    assert not summary['coverage_available'] and summary['matched_keys'] is None


def test_budget_includes_scalar_parameters():
    calls = []
    params = {f'p{i}': i for i in range(44998)}
    client = client_with_query(lambda sql, params=None: calls.append(len(params)) or pd.DataFrame())
    client.query_df_for_keys(pd.DataFrame({'id': [1,2,3]}), 'SELECT id WHERE id IN ({cohort_keys})',
                             key_columns=['id'], params=params, chunk_size=1000)
    assert calls == [45000, 44999]


@pytest.mark.parametrize('frame', [pd.DataFrame({'wrong':[1]}), pd.DataFrame({'id':[999]}), pd.DataFrame({'id':[None]})])
def test_invalid_result_coverage_is_not_success(frame):
    with pytest.raises(SQLQueryError):
        client_with_query(lambda *a, **k: frame).query_df_for_keys(pd.DataFrame({'id':[1]}),
            'SELECT id WHERE id IN ({cohort_keys})', key_columns=['id'], result_key_columns=['id'])


def test_late_failure_has_no_partial_return_or_sensitive_logs(caplog):
    calls = []
    def query(sql, params=None):
        calls.append(params)
        if len(calls) == 2:
            raise RuntimeError('secret-token patient-private remote body')
        return pd.DataFrame({'id':[1]})
    caplog.set_level(logging.DEBUG)
    with pytest.raises(SQLQueryError, match='no partial result') as exc:
        client_with_query(query).query_df_for_keys(pd.DataFrame({'id':[1,2,3]}),
            'SELECT id WHERE id IN ({cohort_keys})', key_columns=['id'], chunk_size=1)
    assert len(calls) == 2
    assert 'secret-token' not in str(exc.value) + caplog.text
    assert 'patient-private' not in caplog.text


@pytest.fixture
def synthetic_postgres():
    """Opt in only to the disposable loopback fixture, never a clinical DSN."""
    import os
    port = os.environ.get('FYRON_SYNTHETIC_POSTGRES_PORT')
    if not port:
        pytest.skip('Set FYRON_SYNTHETIC_POSTGRES_PORT for isolated PostgreSQL verification')
    with FHIRSQLClient(dsn=f'postgresql://postgres:synthetic-only@127.0.0.1:{int(port)}/fyron_synthetic') as client:
        yield client


def test_postgres_composite_and_parallel_equivalence(synthetic_postgres):
    query = '''WITH visits(p,e,value) AS (VALUES ('001',1,10),('001',2,20),('002',1,30),('002',2,40))
    SELECT * FROM visits WHERE (p,e) IN ({cohort_keys}) AND value > %(minimum)s'''
    df = pd.DataFrame({'patient':['001','002','001','003'], 'encounter':[1,2,1,9]})
    kwargs = dict(key_columns=['patient','encounter'], result_key_columns=['p','e'],
                  params={'minimum':0}, chunk_size=1, return_report=True)
    sequential = synthetic_postgres.query_df_for_keys(df, query, **kwargs)
    parallel = synthetic_postgres.query_df_for_keys(df, query, parallel=True, max_workers=2, **kwargs)
    pd.testing.assert_frame_equal(sequential['data'], parallel['data'])
    assert sequential['data']['value'].tolist() == [10,40]
    assert sequential['report']['summary'].iloc[0]['unmatched_keys'] == 1
    assert sequential['report']['unmatched_keys'].to_dict('records') == [{'patient':'003','encounter':9}]


@pytest.mark.parametrize('parallel', [False, True])
def test_postgres_later_batch_error(synthetic_postgres, parallel):
    with pytest.raises(SQLQueryError, match='no partial result'):
        synthetic_postgres.query_df_for_keys(pd.DataFrame({'id':[1,0,2]}),
            'SELECT id, 10/id AS value FROM (VALUES (1),(0),(2)) AS t(id) WHERE id IN ({cohort_keys})',
            key_columns=['id'], chunk_size=1, parallel=parallel, max_workers=2)


@pytest.mark.parametrize('style',['positional','named'])
def test_postgres_legacy_order_repetition_and_quoted_blocks(synthetic_postgres, style):
    result = synthetic_postgres.query_df_from(pd.DataFrame({'a':['001'], 'b':['002']}),
        "SELECT id, '{a}' AS literal FROM (VALUES ('001'),('002'),('003')) AS t(id) WHERE id IN ({b}) OR id IN ({a}) OR id IN ({b}) ORDER BY id",
        {'a':'a','b':'b'}, param_style=style)
    assert result['id'].tolist() == ['001','002']
    assert result['literal'].tolist() == ['{a}','{a}']
