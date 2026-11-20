#!/usr/bin/env python3
"""Build source-checked parameter guides for the four data-access clients."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENTS = [
    ('rest', 'FHIRRestClient', 'src/fyron/fhir/rest.py', 'docs/modules/fhir/rest', 'FHIR REST'),
    ('sql', 'FHIRSQLClient', 'src/fyron/fhir/sql.py', 'docs/modules/fhir/sql', 'FHIR SQL'),
    ('dicom', 'DICOMDownloader', 'src/fyron/dicom/client.py', 'docs/modules/dicom/downloader', 'DICOM downloader'),
    ('documents', 'DocumentDownloader', 'src/fyron/documents/client.py', 'docs/modules/documents/downloader', 'Document downloader'),
]

COMMON = {
    'auth': 'An existing Fyron `Auth` or `requests.Session`. Borrowed sessions stay open and retain their configuration. Use a service-approved authentication method.',
    'base_url': 'Service base URL. `None` falls back to `FHIR_BASE_URL`. Documents use it only to resolve relative URLs; absolute URLs work without it.',
    'auth_url': 'Login/token endpoint for Fyron’s existing environment username/password mechanism. Use shared Auth for OIDC issuer discovery, device flow or service accounts; this argument is not a universal OAuth selector.',
    'num_processes': 'Worker process count. Use `1` while learning. FHIR uses it for parallel fetch/conversion; DICOM uses it for DataFrame downloads with supported worker authentication. Guard spawned script entrypoints.',
    'request_timeout': 'Positive seconds for each network connect/read wait. This is not a whole-extraction deadline. DICOM also accepts `None` to retain unbounded request waits.',
    'worker_auth_timeout': 'Positive finite seconds a worker may wait for parent-coordinated authentication.',
    'parallel_job_timeout': 'Positive finite worker execution deadline in seconds, excluding queue wait; `None` disables it. FHIR and DICOM have different constructor defaults, shown in the table.',
    'retries': 'An optional `urllib3.util.retry.Retry` GET policy. `None` selects Fyron’s bounded default, including 429/502/503/504 and Retry-After. Existing retry-capable caller adapters retain their own policy. No automatic SQL or write retries.',
    'log_requests': 'Enable controlled request timing/status events with the shared Fyron logger. Never prints query values, tokens, URLs or response bodies.',
    'log_downloads': 'Enable controlled download timing, outcomes and counts. Configure console colors or JSON logging once in the application.',
    'log_request_urls': 'Compatibility option for controlled activity events. Actual URLs are never printed.',
    'log_queries': 'Enable timed SQL connection/query events and row/chunk counts at INFO; SQL text and parameters are never logged.',
    'df': 'Input pandas DataFrame. Column labels must be unique; mapped identifiers must meet the method’s missing-value rules. Preserve identifier strings and leading zeros.',
    'show_progress': 'Display a progress bar. Units depend on the operation: pages, partitions, input queries or download tasks. Disable for noninteractive jobs; CLI quiet/no-progress/JSON settings disable bars.',
    'return_report': 'False keeps the normal data return. True returns `{"data": ..., "report": ...}`. Read the return-format section below for the client-specific report tables.',
    'start': 'Inclusive first boundary, supplied as a date/date-time string or pandas Timestamp. Use consistent timezone semantics.',
    'end': 'Exclusive final boundary. Must be later than start; do not describe this as an inclusive end date.',
    'frequency': 'Pandas date frequency such as `"MS"` (monthly) or `"YS"` (yearly). Ignored when `window_days` is supplied.',
    'window_days': 'Optional positive fixed window width in days; overrides the calendar frequency.',
    'include_partition_columns': 'Attach explicit window/grid metadata to returned rows. Metadata names must not collide with result columns.',
    'deduplicate_by': 'A result-column name or ordered list of names used for explicit duplicate removal. None retains repeated rows. Choose resource IDs deliberately; do not deduplicate clinical observations by patient alone.',
    'rename': 'Optional mapping of existing result column names to desired names; does not change the query or its predicates.',
    'output_dir': 'Destination directory. DICOM creates study/series folders beneath it; documents use flat or per-document layout according to `flat_output`.',
    'results_csv': 'Optional sensitive CSV of outcome rows and actual paths. Written atomically; keep it separate from downloaded files and client metadata.',
    'skip_existing': 'True skips only outputs verified by matching completion records. False explicitly permits replacement. Disabling JSON does not make existing files automatically trusted.',
    'write_completion_record': 'Write new hidden JSON completion records for verified restarts. False omits new records; it neither deletes existing JSON nor disables token caching.',
    'overwrite': 'Explicitly replace existing output after review. For SQL exports, `skip_existing=False` also permits replacement for compatibility.',
    'chunksize': 'Positive number of rows per DataFrame/CSV chunk. It does not guarantee server-side cursor streaming or limit the query’s total result size.',
    'chunk_size': 'Maximum input rows/keys per bound SQL batch. Positive integer when supplied; the actual size may be reduced by the parameter budget.',
    'max_workers': 'Optional positive SQL process count. None uses the pool default except `query_df_for_keys`, which defaults to four parallel workers.',
    'parallel': 'Execute SQL batches in separate owned connections. False is easier to inspect. Worker connections do not share a transaction snapshot.',
    'sql': 'Reviewed SQL text with bound placeholders. Ordinary queries use `%s` or `%(name)s`; key-cohort queries require one executable `{cohort_keys}` block. Never interpolate identifiers or values with f-strings.',
    'resource_type': 'FHIR resource type such as `"Patient"`, `"Observation"` or `"ImagingStudy"`. Supported resource/search combinations depend on the server.',
    'resource': 'A validated FHIR R4 resource dictionary. It must agree with an explicitly supplied resource type.',
    'resource_id': 'Logical FHIR resource ID for update. None uses the ID in the resource; an update requires an ID.',
    'bundle': 'Validated FHIR transaction Bundle to submit to the server base URL. Collection bundles are not accepted for submission.',
    'study_uid': 'Nonmissing DICOM StudyInstanceUID string. Use the numeric-dot UID, not a FHIR ImagingStudy resource ID or accession number.',
    'series_uid': 'DICOM SeriesInstanceUID string for a known series. It is optional only on the hash helper; whole-study methods discover series themselves.',
    'study_uid_col': 'Input column containing StudyInstanceUID strings. Read CSV with `dtype="string"` to preserve identifier text.',
    'series_uid_col': 'Input column containing SeriesInstanceUID strings. Required for series-level batch downloads; unused in full-study mode.',
    'download_full_study': 'True retrieves every returned series in each requested study. False downloads the selected study/series pairs.',
    'study_layout': '`"hierarchical"` creates a directory per series inside the study directory. `"flat"` stores instances or per-series NIfTI files directly in the study directory; it does not remove the study folder.',
    'study_folder_name': 'Optional explicit label for one full-study folder. By default it prefixes a study hash; with hash appending disabled it must be an exact safe unique label.',
    'study_folder_name_col': 'Optional input column supplying full-study labels, such as `"ACC_NR"`. Different studies must not collide when hashes are disabled.',
    'append_study_hash': 'True keeps `<label>__<study_hash>`. False requires an exact safe label and rejects collisions. A method-level None inherits the constructor setting. Applies only to full-study folders.',
    'write_manifest': 'Whether to write the full-study `study_manifest.json` summary. Independent of per-series completion JSON; unused for individual series.',
    'save_study_manifest': 'None inherits `write_manifest`; True/False explicitly enables/disables the study summary. Does not control hidden per-series completion records.',
    'save_reference_dicom': 'Keep one original DICOM instance beside each converted NIfTI series. Unnecessary for DICOM output. Method-level None inherits the constructor setting.',
    'reference_dicom_name': 'File name for the optional reference DICOM, not a path; `.dcm` is appended when missing. Method-level None inherits the constructor setting. Prefer hierarchical layout to avoid cross-series conflicts.',
    'keep_reference_dicom': 'Deprecated compatibility alias for `save_reference_dicom`; conflicting simultaneous values raise. Prefer the supported name in new code.',
    'dicom_web_url': 'Approved DICOMweb base endpoint. None reads `DICOM_WEB_URL`; an endpoint is required.',
    'dicom_user': 'HTTP Basic username; None can read `DICOM_USER` when explicit auth is absent. Do not combine explicit authentication methods.',
    'dicom_password': 'HTTP Basic password; None can read `DICOM_PASSWORD` when explicit auth is absent. Keep credentials out of shared code and logs.',
    'basic_auth': 'Optional `(username, password)` tuple. Do not combine with shared `auth` or conflicting explicit credentials.',
    'output_format': 'Canonical choices: `"dicom"` preserves DICOM instances; `"nifti"` converts each series to a NIfTI volume. Format normalization also accepts `dcm`, `.dcm`, `nii`, `.nii`, `nii.gz` and `.nii.gz`.',
    'use_compression': 'Pass compression through to the NIfTI writer. Saved NIfTI names use the implementation’s `.nii.gz` naming; this does not change DICOM preservation.',
    'url': 'Approved HTTP(S) document URL, or a relative URL with a configured base URL. Embedded credentials and whitespace are rejected.',
    'urls': 'Iterable of approved document URLs. Use a DataFrame method when you also need per-document custom IDs.',
    'url_col': 'Input column containing document URLs.',
    'id_col': 'Optional column of unique filename-safe document IDs. Strings preserve leading zeros; integers are accepted, but floats, booleans, missing values and case-insensitive duplicates are rejected.',
    'document_id': 'Optional custom string/integer ID for one document. Replaces the default hash in automatic names; explicit `output_path` still takes precedence.',
    'output_path': 'Optional exact destination file for one document. Overrides automatic directory/name choices. Existing-file protection still applies.',
    'timeout': 'Positive finite network connect/read timeout in seconds. Python defaults to 30; document CLI defaults to 90. Not a whole-batch deadline.',
    'save_mode': 'Naming choices: `"auto"` uses response MIME extension when available; `"txt"` or `"pdf"` appends that extension. Other values retain the URL-derived name. This changes naming, not conversion or validation.',
    'force_extension': 'Optional extension, with or without a leading dot, appended to the automatic base name. Takes precedence over save_mode. It does not convert the content.',
    'require_pdf': 'Require HTTP 200, PDF media type and a streamed `%PDF-` prefix. Does not validate full PDF syntax or clinical correctness.',
    'allow_redirects': 'True follows guarded same-origin redirects; False rejects redirects. Never authorizes sending tokens to arbitrary attachment hosts.',
    'flat_output': 'True writes custom-ID/hash-named files directly in output_dir with absolute result paths. False uses a document subfolder. Explicit output_path overrides both.',
    'expected_content_types': 'Optional nonempty sequence of exact MIME types, e.g. `["text/plain", "application/pdf"]`. Comparison ignores response charset/case. No wildcards. A PDF requirement must remain compatible.',
    'statement_timeout': 'Optional positive seconds per SQL statement on parent and worker connections. None retains server settings. No automatic retry or rollback follows cancellation.',
    'lock_timeout': 'Optional positive seconds waiting for SQL locks. None retains server settings.',
    'dsn': 'Optional PostgreSQL DSN; None can read `FHIR_DB_DSN`. A supplied/effective DSN takes precedence over separate host/user/password settings; they are not merged.',
    'host': 'Database host; None reads `FHIR_DB_HOST` when no DSN is used.',
    'port': 'Database port; None can read `FHIR_DB_PORT`, otherwise connection defaults to 5432 without a DSN.',
    'dbname': 'Database name; None reads `FHIR_DB_NAME` when no DSN is used.',
    'user': 'Database role; None reads `FHIR_DB_USER` when no DSN is used.',
    'password': 'Database password/token; None reads `FHIR_DB_PASSWORD` when no DSN is used. HTTP Auth does not renew database credentials.',
    'sslmode': 'PostgreSQL/libpq modes: `disable`, `allow`, `prefer`, `require`, `verify-ca`, `verify-full`. None reads `FHIR_DB_SSLMODE` or retains connection defaults. Use the site-approved TLS policy, normally `verify-full` plus its CA; do not downgrade verification to bypass errors.',
    'connect_timeout': 'Database connection timeout in seconds. Separate from statement_timeout and lock_timeout; forwarded to psycopg/libpq.',
    'key_columns': 'Nonempty ordered input key-column list. One column filters IDs; multiple columns bind complete tuples. Complete keys are globally deduplicated before batching.',
    'result_key_columns': 'Optional ordered output key columns corresponding to key_columns. Enables matched/unmatched distinct-key coverage; missing or unexpected result keys raise.',
    'param_limit': 'Positive SQL bind-parameter budget; constrained by PostgreSQL’s 65,535 maximum and the safety factor. Repeated positional placeholders count more than once.',
    'param_safety_factor': 'Finite fraction in `(0, 1]` of param_limit used for sizing SQL batches.',
    'param_style': '`"positional"` expands legacy blocks to `%s`; `"named"` uses named bound placeholders. Both bind values rather than interpolate them.',
    'merge': '`"concat"` retains every returned observation; `"drop_duplicates"` explicitly removes duplicates using unique_on or all columns.',
    'unique_on': 'Optional result-column list used only with merge="drop_duplicates". Avoid patient-only deduplication when repeated observations matter.',
    'jobs': 'Sequence of `(sql, params)` pairs for parallel SQL execution. Each worker owns its connection; a failed job raises.',
    'param_grid': 'Optional mapping of parameter names to nonempty value sequences. Expands a Cartesian grid across time windows; start_ts/end_ts are reserved.',
    'derived_params': 'Optional mapping of parameter names to callables receiving the partition parameter dictionary. Used to derive approved query values; start_ts/end_ts remain reserved.',
    'continue_on_error': 'False raises on failed partitions. True allows successful partitions to remain available while failures are recorded. Inspect the manifest/error rows before calling the extract complete.',
    'errors': '`"raise"` or `"record"`. Record mode appends explicit error rows and partition metadata; earlier chunks from a failed partition are discarded.',
    'output_columns': 'Optional ordered columns to retain in exported CSVs. Missing result columns raise.',
    'part_filename': 'Relative CSV filename template inside `_parts`, e.g. `"{year}/{date}.csv"`. Templates must not escape the output directory or resolve to colliding partitions.',
    'combine_by': 'Optional partition metadata group such as `"year"` or a grid parameter. None leaves parts separate. Combined output can be partial when errors were allowed.',
    'combined_filename': 'Relative combined-output filename template, e.g. `"combined_{value}.csv"`. Verified files are protected and identifier text is preserved when combining CSVs.',
    'request_params': 'Default FHIR query-parameter dictionary merged into every request; per-query values override matching defaults.',
    'bearer_token': 'Optional static access token; otherwise FHIR_TOKEN may apply. A static token does not renew. Shared Auth/session authentication takes precedence when already configured.',
    'extra_headers': 'Additional HTTP headers applied per request, leaving a borrowed session unchanged. Do not log or publish credential-bearing values.',
    'return_fhir_obj': 'Wrap fetched resources/bundles as FHIRObj rather than plain dictionaries. Normal DataFrame processing still uses the conversion helpers.',
    'token_auth_method': 'For Fyron’s existing username/password token mechanism: `"basic"` or `"post"`. This is not a universal OAuth password grant.',
    'cache_ttl_seconds': 'In-memory GET response lifetime in seconds. Zero disables caching; a cached response is not proof the source has remained unchanged.',
    'cache_max_entries': 'Maximum entries in the in-memory response cache; zero disables it. No response cache is written to disk.',
    'max_pages': 'Maximum pages per query: positive integer, `-1` for all available pages, `0` for no request. A page cap is not an empty match.',
    'max_pages_per_partition': 'Page limit within each window: positive integer, `-1` for all available pages, `0` for no request. Not a limit across all windows.',
    'partition_param': 'Actual server-supported FHIR date search parameter, e.g. `"recorded-date"`, `"date"` or `"_lastUpdated"`. It describes the chosen resource date, not necessarily clinical onset.',
    'param_list': 'Sequence of separate FHIR query dictionaries; each becomes an independent fetch job.',
    'parallel_params': 'Optional sequence of query dictionaries for independent parallel FHIR searches. None performs one search with params. Inspect job-level completeness.',
    'parallel_fetch': 'Fetch input queries/partitions concurrently when workers are available. Separate from use_multiprocessing, which controls conversion.',
    'use_multiprocessing': 'Convert bundles in worker processes when the configured process count exceeds one. Custom processors must be importable/pickleable; use a guarded entrypoint.',
    'param_prefix': 'Optional mapping from FHIR search parameter to a prefix, e.g. `{"subject": "Patient/"}`. Original input values are retained when metadata is requested.',
    'include_column_map_columns': 'Copy original mapped input columns into each returned row. Works with parallel fetch/custom processing; collisions with output columns raise.',
    'auto_sort': 'Add the selected sort unless an explicit `_sort` is already supplied in params. Requires server support; sorting does not prove completeness.',
    'sort': 'FHIR `_sort` expression used by auto_sort, normally `"_id"`; select a server-supported stable sort.',
    'fhir_paths': 'Sequence of FHIRPath strings or `(output_name, expression)` pairs. Expressions are resource-relative. Providing paths selects the path extractor and overrides a custom process_function.',
    'process_function': 'Custom bundle processor for mode="custom". Accepts a bundle and returns a dictionary of output-table names to lists of row dictionaries.',
    'mode': '`"flatten"` uses standard flattening; `"custom"` requires a processor unless fhir_paths supplies the extractor. Other values raise.',
    'bundles': 'Iterable of already retrieved Bundle dictionaries/FHIRObj objects to convert. Conversion materializes the iterable; it does not fetch more pages.',
    'per_bundle_metadata': 'Advanced: list of dictionaries aligned one-to-one with bundles. Values are attached to every output row; conflicting output names raise.',
}


def description(kind, method, name):
    if name == 'params':
        if kind == 'rest':
            return 'FHIR search-parameter dictionary, e.g. `{"_count": 100, "code": "demo"}`. Available clinical parameters/codes are defined by the server. DataFrame row mappings override matching base filters.'
        return 'Bound SQL values: dictionary for `%(name)s` or sequence for `%s`. query_df_for_keys accepts named scalar filters; its `_fyron_key_` parameter namespace is reserved.'
    if name == 'column_map':
        return ('FHIR search parameter → input DataFrame column, e.g. `{"subject": "patient_id"}`. Each input row creates a query; null, blank or empty-list keys are rejected.' if kind == 'rest' else
                'Legacy SQL template block → input column, e.g. `{"ids": "patient_id"}` for `{ids}`. Separate lists are independent and do not preserve patient/encounter pairs; use query_df_for_keys for tuples.')
    if name == 'max_workers' and kind == 'documents':
        return 'Thread count for list/DataFrame downloads. The scheduler submits at most twice the worker count at a time; results remain in input order.'
    if name == 'chunk_size' and method == 'query_df_for_keys':
        return 'Positive maximum distinct keys per batch. The method reduces it to fit its conservative 45,000-bound-value budget, counting scalar filters and all composite-key values.'
    if name not in COMMON:
        raise ValueError(f'Missing documentation for {kind}.{method}.{name}')
    return COMMON[name]


def cell(text):
    return str(text).replace('|', r'\|').replace('\n', ' ')


def parameters(node):
    positional = list(node.args.posonlyargs) + list(node.args.args)
    defaults = [None] * (len(positional) - len(node.args.defaults)) + list(node.args.defaults)
    items = [(arg, default, False) for arg, default in zip(positional, defaults) if arg.arg not in {'self','cls'}]
    items += [(arg, default, True) for arg, default in zip(node.args.kwonlyargs, node.args.kw_defaults)]
    return items


def render(kind, name, source, base, title):
    tree = ast.parse((ROOT/source).read_text())
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == name)
    methods = [node for node in cls.body if isinstance(node, ast.FunctionDef)
               and (not node.name.startswith('_') or node.name == '__init__')]
    lines = [f'# {title}: complete parameter reference', '',
        f'[Back to the workflow guide](../{Path(base).name}.md)', '',
        'Use this page when you know the operation and need every argument, its actual Python default and its interactions. Signatures and parameter coverage are generated from the current source; descriptions explain operational choices.', '',
        '**Version scope:** Fyron 0.3.20b5 (Beta 5). The reporting, deadline, naming and validation options below require Beta 5 or newer; they are not available in previously published Beta 4 packages.', '',
        '## Reading the tables', '',
        '- **Required** means the Python signature has no default. A default of `None` can still require environment configuration or a value from the resource.',
        '- **Keyword only** arguments must be passed by name. Boolean options accept Python `True` / `False`; `None` is a separate inherit/unset choice where documented.',
        '- Use the workflow guide for setup, authentication, return schemas and safe restarts. FHIR `params` and SQL schemas are site-specific; this page lists Fyron arguments, not every parameter a remote service might support.',
        '- These clients support `with ... as client:` and `close()`; they close owned resources and keep borrowed HTTP sessions open.', '',
        '## Function index', '']
    for method in methods:
        label = name if method.name == '__init__' else method.name
        anchor = 'constructor' if method.name == '__init__' else method.name.replace('_','-')
        lines.append(f'- [{label}](#{anchor})')
    for method in methods:
        label = name if method.name == '__init__' else method.name
        heading = 'Constructor' if method.name == '__init__' else method.name.replace('_',' ')
        items = parameters(method)
        lines += ['',f'## {heading}', '', f'`{label}`', '', 'Signature reference (use the workflow guide for runnable calls):', '', '```python', f'def {label}(']
        saw_keyword = False
        for arg, default, keyword in items:
            if keyword and not saw_keyword:
                lines.append('    *,')
                saw_keyword=True
            default_text = '' if default is None else '=' + ast.unparse(default)
            lines.append(f'    {arg.arg}{default_text},')
        lines += ['):', '    ...', '```', '']
        if not items:
            lines.append('No arguments. Closes owned resources; call once work has finished.')
            continue
        lines += ['| Parameter | Type | Python default | Purpose and accepted options |', '| --- | --- | --- | --- |']
        for arg, default, keyword in items:
            annotation = ast.unparse(arg.annotation) if arg.annotation else 'See purpose'
            value = '**Required**' if default is None else '`'+ast.unparse(default)+'`'
            label = '`'+arg.arg+'`'+(' (keyword only)' if keyword else '')
            lines.append('| '+ ' | '.join([label,cell('`'+annotation+'`'),cell(value),cell(description(kind,method.name,arg.arg))])+' |')
    lines += ['', '## Return formats and limits', '']
    returns = {
        'rest': 'Fetch methods yield bundles. DataFrame methods return a DataFrame or a dictionary of tables according to conversion output; `return_report=True` wraps data with `report.rows` and `report.summary`. A failure raises. Write methods return FHIRWriteResult metadata. An exhausted page sequence is not proof against hidden server caps.',
        'sql': '`query` returns a list of row dictionaries; `query_df`/`query_to_dataframe` and batch queries return DataFrames; `query_df_stream` yields chunks; exports return a partition manifest. Only `query_df_for_keys` supports `return_report=True`, including `rows`, `summary` and `unmatched_keys`. Coverage requires explicit result_key_columns; unmatched means this query returned no row.',
        'dicom': '`download_series` returns DicomResult; `download_study` returns a list of series results. Batch methods return a DataFrame, or data with `report.rows` / `report.summary` when requested. A study can yield multiple series rows. Completion records verify local files, not the server inventory.',
        'documents': '`download_url` returns DocumentResult; batch methods return a DataFrame, or data with `report.rows` / `report.summary` when requested. Batch results retain input order. The internal download_id remains the source URL hash even with custom filenames. PDF/MIME checks do not establish clinical validity.',
    }
    lines += [returns[kind], '', '**Sensitive outputs:** result paths, identifiers, URLs and detailed reports belong in approved research storage. Progress logs use controlled labels and counts.', '', f'Return to the [workflow guide](../{Path(base).name}.md) for worked examples.', '']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Fail when the generated guides differ from source; do not write')
    args=parser.parse_args()
    stale=[]
    for spec in CLIENTS:
        path=ROOT/(spec[3]+'/parameters.md')
        text=render(*spec)
        if args.check:
            if not path.exists() or path.read_text()!=text:stale.append(str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(text)
    if stale:
        raise SystemExit('Client parameter guides need regeneration: '+', '.join(stale))
    print('Client parameter guides match all four source signatures.' if args.check else 'Generated four complete client parameter guides.')


if __name__=='__main__':
    main()
