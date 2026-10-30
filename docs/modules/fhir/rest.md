# FHIR REST

For site-specific access setup, see [FHIR REST authentication](../../authentication/fhir-rest.md). Choose the method and permissions approved by your administrator.

Development update: see [Safe Network Diagnostics](../../diagnostics.md) for logging,
safe error text, batch outcome counts, and sensitive-result handling.

`fyron.fhir.rest` is the API-facing FHIR client for bounded searches, pagination, row-wise cohort lookups, FHIRPath-style extraction, and server write-back. Use it when your data source is a live FHIR endpoint and you want inspectable `pandas.DataFrame` outputs rather than opaque client objects.

## When To Use It

- query resources such as `Patient`, `Observation`, `Condition`, `Procedure`, or `ImagingStudy`,
- page through search results with explicit limits,
- run row-wise queries from a cohort table,
- flatten or project returned resources into analysis columns,
- create/update resources or submit reviewed transaction bundles.

Use [FHIR SQL](sql.md) when the same data is already available in a relational warehouse.

## Row-Wise Query Progress

### Parallel Worker Safety

Fyron 0.3.12 adds `worker_auth_timeout=120` and
`parallel_job_timeout=300` to `FHIRRestClient` (seconds). Both require finite
positive values; only
`parallel_job_timeout=None` explicitly disables the overall job deadline.

```python
client = FHIRRestClient(
    base_url=base_url,
    auth=auth,
    num_processes=4,
    request_timeout=30,
    worker_auth_timeout=120,
    parallel_job_timeout=300,
)
```

The job deadline starts when a worker begins a query, not when it enters the
queue. It covers pagination and result delivery. HTTP timeouts remain separate.
Expired jobs and unexpected worker exits raise `FHIRRequestError`; DataFrame
helpers never return a successful partial table. Streaming consumers may already
have received bundles and must treat them as incomplete if iteration raises.

Coordinated authentication uses parent-created pipes, not listening TCP ports.
Workers retain access-token leases across jobs; credentials and refresh tokens
stay in the parent. Known tokens renew at the existing 75%-lifetime boundary.
Unknown-lifetime tokens have at most a 30-second worker lease; checking with the
parent does not itself force renewal. Generations prevent simultaneous failures
from repeatedly renewing the same token, even if its value is unchanged.
Worker transport accepts access tokens up to 16 KiB.

Slow-job warnings report only local job numbers, elapsed seconds, stage
(`authentication`, `http`, or `delivery`), and unfinished counts. They never
include query values or patient identifiers. Warnings begin after 30 seconds and
are throttled to once per 30-second reporting interval. Token-wait timeouts also
bound browser reapproval during device-authenticated parallel work. User-supplied
approval callbacks must return promptly; they must not block on browser approval.

Pools use spawn. Put script entrypoints under `if __name__ == "__main__":` and
define custom multiprocessing functions at module scope. For notebook-defined
callbacks or interactive environments where spawn cannot import the main module,
use sequential execution. No automatic task resubmission occurs after uncertain
failures. These changes harden workers but do not establish the cause of any
particular server's slow queries.

Starting with 0.3.11, `query_df_from`, `search_df_from`, and
`query_from_dataframe` show a progress bar for sequential fetching too. Existing
calls enable it by default; pass `show_progress=False` to hide it in automated
runs. This option is not available in 0.3.10.

```python
result_df = client.query_df_from(
    df=df,
    resource_type="Patient",
    column_map={"_id": "patient_id"},
    parallel_fetch=False,
    use_multiprocessing=False,
    max_pages=-1,
    show_progress=True,
    fhir_paths=[("patient_id", "id")],
)
```

The bar advances after all pages for an input row have been fetched, including
queries returning no resources. It counts input queries, not patients returned
or pages. It does not show identifiers, URLs, or credentials. One slow query can
still leave the counter unchanged until it finishes; this is progress feedback,
not a fix for parallel-fetch stalls or an overall query deadline.

## Choosing Authentication

| Use case | Fyron interface |
| --- | --- |
| Browser approval with an OIDC provider | `Auth(auth_type="device_code", ...)` |
| Unattended service account with a client ID and secret | `Auth.client_credentials(...)` (Fyron 0.3.10+) |
| Existing username/password-to-token gateway | `Auth.token_env(...)` |
| HTTP Basic authentication | `Auth(auth_type="basic", ...)` |

Device flow and client credentials are different grants. A client registered for
browser approval does not automatically support service-account access. Ask your
provider administrator which grant, client authentication method, scopes, and
audiences are approved. Examples below use fictitious domains only.

## Service-Account Authentication

Use `Auth.client_credentials()` for unattended OAuth 2.0 applications. OIDC
discovery can supply the token endpoint. This is application authorization,
not interactive user login or ID-token validation.

### Using OIDC Discovery

Set `auth_url` to the exact issuer, not a login page, FHIR base URL, or token URL.
Fyron requests `<issuer>/.well-known/openid-configuration`, verifies its issuer,
and uses its advertised token endpoint. No separate token URL is needed when
discovery is available.

```python
import os
from fyron import Auth, FHIRRestClient

if __name__ == "__main__":
    with Auth.client_credentials(
        auth_url="https://identity.example.org/realms/research",  # Exact OIDC issuer.
        client_id=os.environ["OAUTH_CLIENT_ID"],
        client_secret=os.environ["OAUTH_CLIENT_SECRET"],
        scope="system/Patient.read",  # Replace with provider-approved scopes.
    ) as auth:
        client = FHIRRestClient(
            base_url="https://hospital.example.org/fhir",
            auth=auth,
            num_processes=4,
        )
        patients = client.query_df("Patient", max_pages=1)
```

### Using an Explicit Token Endpoint

When discovery is unavailable or your administrator supplies a specific token
endpoint, use `token_endpoint` instead of `auth_url`:

```python
import os
from fyron import Auth, FHIRRestClient, load_env

if __name__ == "__main__":
    load_env()
    with Auth.client_credentials(
        token_endpoint=os.environ["OAUTH_TOKEN_URL"],
        client_id=os.environ["OAUTH_CLIENT_ID"],
        client_secret=os.environ["OAUTH_CLIENT_SECRET"],
        scope=os.environ["OAUTH_SCOPE"],
        client_auth_method="client_secret_basic",
    ) as auth:
        client = FHIRRestClient(
            base_url=os.environ["FHIR_BASE_URL"],
            auth=auth,
            return_fhir_obj=True,
            num_processes=4,
        )
        patients = client.query_df("Patient", max_pages=1)
```

Local `.env` template with placeholder values:

```dotenv
OAUTH_TOKEN_URL=https://identity.example.org/oauth/token
OAUTH_CLIENT_ID=your-service-client
OAUTH_CLIENT_SECRET=replace-locally
OAUTH_SCOPE=your-approved-scopes
FHIR_BASE_URL=https://hospital.example.org/fhir
```

Keep `.env` out of version control. Complete queries and downloads inside the
`with` block so authentication remains open. For discovery, replace
`token_endpoint` with `auth_url` pointing to your issuer.

The equivalent constructor uses
`Auth(auth_type="client_credentials", ...)`. Client authentication prefers
`client_secret_basic`, selecting a supported method from discovery. Set
`client_auth_method="client_secret_post"` when required by your provider.
Basic here authenticates the client at the token endpoint. Resource requests
always use `Authorization: Bearer <access_token>`.

Fyron renews tokens after 75% of their declared lifetime by requesting another
client-credentials token. Without lifetime metadata, renewal follows a 401.
A rejected request is retried once when its body can be replayed safely.
FHIR and DICOM workers coordinate renewal in the parent process. No token cache,
refresh URL, browser approval, or user password is needed. Keep client secrets
out of source control. Token endpoints require HTTPS and redirects are refused.

Register the application, enable client credentials, and approve its scopes and
resource audiences with your provider. Scopes have no universal default. One
token works for FHIR and DICOMweb only when both services accept its audience and
permissions. This supports shared-secret clients, not `private_key_jwt` or every
SMART backend-services profile. `Auth.token_env()` remains the separate legacy
username/password-to-token workflow.

### Troubleshooting OIDC Authentication

- `Auth` has no `client_credentials` attribute: install Fyron 0.3.10 or later in
  the Python environment running your script. Restart notebook kernels after
  upgrading. Check `fyron.__version__` and `fyron.__file__` for an older checkout.
- `OAuth endpoint rejected the request or redirected` during discovery: the
  discovery request returned a non-success HTTP status. Verify the issuer or use
  the administrator-provided `token_endpoint` to bypass discovery. This happens
  before client credentials are submitted and does not prove they are invalid.
- The same error during the token POST: verify the endpoint, registered grant,
  client authentication method, secret, and approved scopes with the provider.
  The redacted error alone does not distinguish these causes. Do not assume
  every rejection is a bad password.
- A resource request still returns 401 or 403: confirm the token audience and
  service permissions. Successful token issuance alone does not grant FHIR or
  DICOMweb access.

Fyron deliberately refuses token-endpoint redirects. Use the final approved
HTTPS endpoint rather than disabling this protection. Never include client
secrets, access tokens, patient data, or private endpoint URLs in public issues.

## Device Authentication

Fyron supports browser-approved institutional sign-in through its existing `Auth`
interface. No user password is passed to the script. Basic authentication and
password-to-token authentication remain separate, supported options.

```python
from fyron import Auth, FHIRRestClient

with Auth(
    auth_type="device_code",
    auth_url="https://keycloak.example.org/realms/research",
    client_id="fyron-cli",
    scope="openid",
    token_cache="~/.cache/fyron/tokens.json",  # Optional; contains credentials.
) as auth:
    client = FHIRRestClient(
        base_url="https://hospital.example.org/fhir",
        auth=auth,
        num_processes=4,
    )
    patients = client.search_df("Patient", params={"_count": 10}, max_pages=1)
```

The issuer must enable the OAuth device authorization grant for the registered
client. Prefer a public CLI client, without a client secret. The provider must
issue access tokens with the audience and scopes accepted by your FHIR server or
DICOMweb gateway. Device flow does not bypass institutional MFA or permissions.
Fyron follows [RFC 8628](https://www.rfc-editor.org/rfc/rfc8628.html).

Fyron displays a verification URL and user code. Open the URL in any browser and
approve the sign-in. It does not open a browser automatically. A
`device_code_callback` receives a dictionary with `verification_uri`,
`user_code`, `expires_in`, and optional `verification_uri_complete` for a notebook
or application. Callbacks during parallel operations run on a coordinator thread
in the parent process, not in workers; marshal UI work to your application's UI
thread if needed. Avoid including codes or complete verification URLs in shared
logs.

`auth_url` is the exact OIDC issuer for this authentication type, not the token
endpoint. Discovery validates the issuer. For providers without discovery, pass
both `device_authorization_endpoint` and `token_endpoint`; optionally supply
`authorization_endpoint` to recognize login redirects. Endpoints require HTTPS,
except literal loopback addresses for local tests. Confidential clients may pass
`client_secret`; discovery supports `client_secret_basic` (preferred) and
`client_secret_post`. Explicit endpoints default to Basic client authentication.

Tokens refresh at 75% of their declared lifetime. Opaque tokens are supported;
without lifetime metadata, renewal relies on an authentication challenge.
Recognized 401/login-redirect challenges receive at most one safe replay. Fyron
never restores a token stripped on a cross-host redirect, and cannot replay a
consumed non-seekable body. Network failures do not start another sign-in flow.

For long jobs, request `scope="openid offline_access"` if your provider permits
offline refresh tokens. This does not guarantee indefinite access. Set
`allow_reauthentication=False` for unattended jobs: a usable cache is required
at startup, and rejected refresh credentials fail rather than waiting for a
browser. Both FHIR parallel queries and DICOM downloads coordinate token renewal
in the parent process, including rotating refresh tokens. Use the usual
`if __name__ == "__main__":` guard for multiprocessing scripts.

Caching is opt-in. Cache files contain **unencrypted access and refresh tokens**,
not client secrets. Keep them out of Git, shared folders, logs, and distributed
job artifacts. Fyron binds each record to the issuer, client, endpoints, and
scopes, writes atomically with owner-only POSIX permissions, and coordinates
refresh using file locks. Use a private local filesystem with reliable locking.
On platforms without supported owner-only file protection, omit `token_cache`;
caching fails explicitly. Do not share a cache path between different accounts.
Independent copies of an auth object are not a replacement for Fyron's worker
coordination. No live institutional-provider compatibility is implied by the
local integration tests.

## Core Concepts

| Concept | Meaning in Fyron |
| --- | --- |
| `resource_type` | The FHIR resource name, such as `Patient`, `Observation`, `Condition`, or `ImagingStudy`. |
| `params` | Ordinary FHIR search parameters sent to the server, for example `_count`, `code`, `subject`, or `date`. |
| `max_pages` | Safety limit for Bundle pagination. Use a small value during exploration and `-1` only for deliberate full extracts. |
| `fhir_paths` | Explicit field projection from nested FHIR JSON into DataFrame columns. |
| FHIRPath preset | Reusable list of `(column_name, fhir_path)` pairs for common resources. |
| `process_function` | Custom Python function for resource-to-row transformation when simple paths are not enough. |
| `column_map` | Mapping from FHIR search parameter names to columns in an input cohort table. |
| `deduplicate_by` | Column or columns used to remove repeated resources after partitioned extraction. |

Most read functions return `pandas.DataFrame` outputs. Write functions return `FHIRWriteResult` objects with request status and server response information.

## API Contract

| Topic | Contract |
| --- | --- |
| Input shape | FHIR resource type plus explicit search parameters; row-wise helpers also accept a cohort DataFrame. |
| Required columns | `search_df_from` and related helpers require the columns referenced by `column_map`. |
| Return shape | Read helpers return `pandas.DataFrame`; lower-level fetch helpers return FHIR bundles/resources; write helpers return `FHIRWriteResult`. |
| Saved artifacts | Optional CSV/JSON outputs are caller-managed; CLI workflows can write result tables and logs. |
| Failure modes | Missing mapped columns, authentication errors, server errors, invalid FHIRPath extraction, pagination limits, or write-back rejection. |

## Research Decision: Extraction Safety

| Decision | Practical guidance |
| --- | --- |
| Pagination | Keep `max_pages` low during exploration; remove or expand only for planned extracts. |
| Partitioning | Use `search_df_partitioned` for broad date ranges or servers with result caps. |
| Deduplication | Set `deduplicate_by` when overlapping date windows can return the same resource. |
| FHIRPath | Use `fhir_paths` for explicit columns instead of ad hoc nested JSON parsing. |
| Write-back | Treat create/update/transaction calls as reviewed outputs, not exploration steps. |

## Required Inputs

| Input | Needed for | Notes |
| --- | --- | --- |
| `base_url` | all REST queries | May come from `FHIR_BASE_URL`. |
| `resource_type` | searches | FHIR resource name, e.g. `Observation`. |
| query parameters | filtered searches | Use ordinary FHIR search params. |

## Optional Inputs

| Input | Use |
| --- | --- |
| `auth`, `basic_auth`, `bearer_token` | authenticated servers |
| `max_pages` | safe development limits |
| `fhir_paths` | explicit field projection |
| `get_fhir_path_preset(...)` | reusable default projections for common resources |
| `process_function` | custom resource-to-row logic |
| `cache_ttl_seconds` | repeat query caching |

## Minimal Example

```python
from fyron import FHIRRestClient

client = FHIRRestClient("https://hapi.fhir.org/baseR4")
patients = client.search_df(
    "Patient",
    params={"_count": 25, "_sort": "_id"},
    max_pages=1,
)
```

`search_df` is the right starting point when one FHIR query should become one DataFrame. Keep `_count` and `max_pages` explicit so the extract is reproducible.

## Auth And Long-Running Extracts

Fyron supports refreshable token authentication through `fyron.fhir.Auth` / `TokenAuth`. Sequential FHIR REST requests attach a response hook that refreshes or re-authenticates when the token is near expiry or when the server returns `401 Unauthorized`. Some clinical gateways report expired sessions as `400 Bad Request` or `403 Forbidden`; Fyron retries those once when the response body or `WWW-Authenticate` header looks token/session related.

For long-running parallel extracts, configure worker-refreshable auth instead of passing only a static bearer token:

```python
from fyron import Auth, FHIRRestClient

auth = Auth.token_env(
    auth_url="https://fhir.example.org/auth/token",
    refresh_url="https://fhir.example.org/auth/refresh",  # optional
)

client = FHIRRestClient(
    "https://fhir.example.org/r4",
    auth=auth,
    auth_url="https://fhir.example.org/auth/token",
    num_processes=4,
)
```

Set `FHIR_USER` and `FHIR_PASSWORD` in the worker environment. With those values plus `auth_url`, Fyron lets each parallel worker create its own `TokenAuth`, so expired tokens can be refreshed or re-issued during a long query. If only `bearer_token` is provided, workers can use that token but cannot refresh it after expiry.

For real FHIR `400` responses, Fyron includes the server's `OperationOutcome.issue.diagnostics` in the raised `FHIRRequestError` so bad search parameters can be distinguished from authentication problems.

## Clinical Example

```python
observations = client.search_df_from(
    cohort,
    resource_type="Observation",
    column_map={"subject": "patient_id"},
    params={"code": "http://loinc.org|718-7"},
    fhir_paths=[
        ("observation_id", "id"),
        ("patient_ref", "subject.reference"),
        ("value", "valueQuantity.value"),
        ("unit", "valueQuantity.unit"),
    ],
    max_pages=1,
)
```

`search_df_from` is for row-wise cohort lookups. In this example, each cohort row contributes a `subject` search parameter from its `patient_id` column. This is useful when you already have a reviewed cohort and want to retrieve related resources.

If extracted `Condition` or `Procedure` resources contain ICD-10, OPS, medication, or local code strings, use [DataFrame Operations](modules/dataframe.md) to derive broad code indicators or date intervals before cohort modeling.

## FHIRPath Extraction

FHIRPath extraction is the most readable way to turn nested FHIR JSON into a stable analysis table when the desired values are direct resource fields. In Fyron, `fhir_paths` accepts either plain path strings or named tuples:

```python
fhir_paths=[
    ("condition_id", "id"),
    ("patient_reference", "subject.reference"),
    ("diagnosis_date", "recordedDate"),
    ("icd_code", "code.coding.code"),
]
```

Named tuples are preferred because the first value becomes the DataFrame column name. This keeps downstream cohort joins, Table 1 creation, and model feature tables readable.

FHIRPath results follow a simple table contract:

| FHIRPath result | DataFrame value |
| --- | --- |
| no value | missing value |
| one value | scalar |
| multiple values | list |

Use FHIRPath for direct projections. Use `process_function` when you need logic such as choosing one coding system from many, exploding components into separate rows, unit conversion, extension parsing, or local phenotype rules.

### FHIRPath Extraction Presets

Fyron includes copyable defaults for common FHIR R4 resources. They are intended as starting points, not as hidden clinical assumptions. Review the resulting columns against your server profile and remove or add paths before freezing an analysis.

```python
from fyron import FHIRRestClient, get_fhir_path_preset

client = FHIRRestClient("https://fhir.example.org/r4")

paths = get_fhir_path_preset("Observation")
paths.append(("local_lab_flag", "extension.where(url = 'https://example.org/fhir/lab-flag').valueCode"))

labs = client.search_df(
    "Observation",
    params={"code": "http://loinc.org|718-7", "_count": 500},
    max_pages=2,
    fhir_paths=paths,
)
```

Available presets:

| Resource | Typical use | Important columns |
| --- | --- | --- |
| `Patient` | demographics and patient identifiers | `patient_id`, `identifier_value`, `gender`, `birth_date`, death fields |
| `Encounter` | visit timelines and encounter context | `encounter_id`, `patient_reference`, `class_code`, `period_start`, `period_end` |
| `Condition` | diagnoses and clinical phenotypes | `condition_id`, `patient_reference`, `code`, `recorded_date`, `onset_datetime` |
| `Observation` | labs, vitals, scores, components | `observation_id`, `patient_reference`, `code`, `effective_datetime`, `value`, `unit` |
| `Procedure` | operations and interventions | `procedure_id`, `patient_reference`, `code`, performed date/period |
| `DiagnosticReport` | reports and linked observations | `report_id`, `patient_reference`, `code`, `issued`, `result_reference`, `conclusion` |
| `ImagingStudy` | imaging cohorts and DICOM joins | `study_instance_uid`, `series_instance_uid`, `series_modality`, `series_description` |
| `MedicationStatement` | medication exposure tables | medication code/display, effective period, assertion date |
| `ServiceRequest` | orders and requested procedures | request id, patient, code, authored date, requester |
| `Specimen` | biospecimen timelines | specimen id, patient, collection date/period, body site |
| `DocumentReference` | clinical notes and document artifacts | document id, patient, type, date, content URL/title |

The raw preset dictionary is also available when you want to inspect or document it:

```python
from fyron.fhir import FHIR_PATH_PRESETS

FHIR_PATH_PRESETS["ImagingStudy"]
```

### Preset Examples By Resource

Use `Patient` for the first cohort identity table:

```python
patients = client.search_df(
    "Patient",
    params={"_count": 500, "_sort": "_id"},
    max_pages=1,
    fhir_paths=get_fhir_path_preset("Patient"),
)
```

Use `Condition` to build diagnosis cohorts:

```python
conditions = client.search_df_partitioned(
    "Condition",
    partition_param="recorded-date",
    start="2020-01-01",
    end="2026-01-01",
    params={"code": "http://hl7.org/fhir/sid/icd-10|C34", "_count": 500},
    fhir_paths=get_fhir_path_preset("Condition"),
    deduplicate_by="condition_id",
)
```

Use `ImagingStudy` when you need `StudyInstanceUID` and `SeriesInstanceUID` for DICOM download or BOA merges:

```python
imaging = client.search_df_from(
    cohort.rename(columns={"patient_id": "input_patient_id"}),
    resource_type="ImagingStudy",
    column_map={"subject": "input_patient_id"},
    param_prefix={"subject": "Patient/"},
    fhir_paths=get_fhir_path_preset("ImagingStudy"),
    include_column_map_columns=True,
    max_pages=1,
)
```

For high-stakes analyses, save the exact paths beside the extracted CSV as provenance. This makes it possible to reproduce why a column exists and which FHIR field populated it.

## Function Guide

| Function | Use it when | Output |
| --- | --- | --- |
| `search_df` | One FHIR search should become one DataFrame. | DataFrame or dict of DataFrames when a processing function splits outputs. |
| `search_df_from` | A cohort table should drive one query per row. | Combined result DataFrame with optional source-row metadata. |
| `search_df_partitioned` | A broad search may hit server result caps. | Merged DataFrame with partition trace columns. |
| `get_fhir_path_preset` | You want a reviewed starting projection for a common resource. | list of `(column_name, fhir_path)` pairs. |
| `query_df` / `query_df_from` | You need compatibility aliases for older code. | Same as search aliases. |
| `build_partition_params` | You want to preview date windows before running. | list of parameter dictionaries. |
| `create_resource` / `update_resource` | You need single-resource write-back. | `FHIRWriteResult`. |
| `submit_bundle` | You need transaction-bundle write-back. | `FHIRWriteResult`. |

## Parameter Notes

| Parameter | Practical guidance |
| --- | --- |
| `params` | Values are passed as FHIR search params. Use server-supported names from the CapabilityStatement. |
| `_count` | Controls server page size, not total rows. Combine with `max_pages` during development. |
| `max_pages` | Use `1` for smoke tests; use `-1` only when you intentionally want all pages. |
| `fhir_paths` | Prefer named tuples like `("diagnosis_date", "recordedDate")` so output columns are readable. |
| `process_function` | Use when values require custom logic, multiple rows per resource, or more robust coding extraction. |
| `include_source_columns` | Use row-wise queries to preserve cohort identifiers beside extracted FHIR data. |

## Sequenced Search For Large Result Sets

Some FHIR servers enforce hard result caps, commonly around 10,000 resources. When a query reaches that cap, ordinary Bundle `next` links may stop even though more matching resources exist. This is a server-side search behavior; the remedy is to split the search into smaller, non-overlapping windows and run those windows one after another.

Fyron calls this **partitioned search** in the API. Conceptually, it is a sequenced FHIR REST extraction: build date windows, query each window, merge the rows, and optionally de-duplicate by the resource ID.

Use `search_df_partitioned` when a resource supports a date-like search parameter such as `recorded-date`, `date`, `authored`, `issued`, `started`, or `_lastUpdated`.

### Minimal Sequenced Example

```python
from fyron import FHIRRestClient

client = FHIRRestClient("https://fhir.example.org/r4")

conditions = client.search_df_partitioned(
    "Condition",
    partition_param="recorded-date",
    start="2020-01-01",
    end="2024-01-01",
    frequency="YS",
    params={"_count": 500, "code": "C34,C34.9"},
    max_pages_per_partition=-1,
)
```

This creates yearly windows:

```text
recorded-date=ge2020-01-01&recorded-date=lt2021-01-01
recorded-date=ge2021-01-01&recorded-date=lt2022-01-01
recorded-date=ge2022-01-01&recorded-date=lt2023-01-01
recorded-date=ge2023-01-01&recorded-date=lt2024-01-01
```

### Clinical Condition Extraction

```python
conditions = client.search_df_partitioned(
    "Condition",
    partition_param="recorded-date",
    start="2018-01-01",
    end="2026-01-01",
    frequency="YS",
    params={
        "_count": 500,
        "identifier": "https://example.org/system|",
        "code": "C34,C34.0,C34.1,C34.2,C34.3,C34.4,C34.5,C34.8,C34.9",
    },
    fhir_paths=[
        ("condition_id", "id"),
        ("patient_reference", "subject.reference"),
        ("encounter_reference", "encounter.reference"),
        ("diagnosis_date", "recordedDate"),
        ("icd_code", "code.coding[0].code"),
    ],
    deduplicate_by="condition_id",
    show_progress=True,
)
```

Partitioned search adds `_sort=_id` by default when no sort is provided, uses valid repeated FHIR date bounds like `recorded-date=ge2020-01-01&recorded-date=lt2021-01-01`, and adds `_fyron_partition_start` / `_fyron_partition_end` columns for traceability.

### Monthly Or Fixed-Day Windows

Use monthly windows when yearly windows still hit the server cap:

```python
monthly_observations = client.search_df_partitioned(
    "Observation",
    partition_param="date",
    start="2023-01-01",
    end="2024-01-01",
    frequency="MS",
    params={"_count": 500, "code": "http://loinc.org|718-7"},
    deduplicate_by="id",
)
```

Use fixed-day windows when you want predictable partition size:

```python
weekly_reports = client.search_df_partitioned(
    "DiagnosticReport",
    partition_param="issued",
    start="2023-01-01",
    end="2024-01-01",
    window_days=7,
    params={"_count": 200},
)
```

### De-Duplication

Use `deduplicate_by` when partitions may overlap or when a server returns the same resource in adjacent windows because of date precision:

```python
conditions = client.search_df_partitioned(
    "Condition",
    partition_param="recorded-date",
    start="2018-01-01",
    end="2026-01-01",
    frequency="YS",
    params={"code": "C34,C34.9"},
    fhir_paths=[
        ("condition_id", "id"),
        ("patient_reference", "subject.reference"),
        ("diagnosis_date", "recordedDate"),
    ],
    deduplicate_by="condition_id",
)
```

### Parameter Reference

| Parameter | Required | Meaning |
| --- | --- | --- |
| `resource_type` | yes | FHIR resource type, e.g. `Condition`, `Observation`, `DiagnosticReport`. |
| `partition_param` | yes | Date-like FHIR search parameter used to split the query. |
| `start`, `end` | yes | Inclusive lower bound and exclusive upper bound for the overall search. |
| `params` | no | Ordinary FHIR search parameters reused for every partition. |
| `frequency` | no | Pandas-style frequency such as `YS` for yearly or `MS` for monthly windows. |
| `window_days` | no | Fixed-size windows in days; overrides `frequency` when set. |
| `max_pages_per_partition` | no | Page limit for each partition. Use `-1` for all pages within every window. |
| `deduplicate_by` | no | Column name or columns used to drop duplicate rows after merging. |
| `include_partition_columns` | no | Adds `_fyron_partition_start` and `_fyron_partition_end`; default is `True`. |
| `parallel_fetch` | no | Fetch partition windows in parallel when the client has multiple processes and suitable auth. |
| `auto_sort` | no | Adds `_sort=_id` by default for stable pagination. |

### Preview Windows Before Running

Preview the query windows before running a large extraction:

```python
from fyron.fhir import build_partition_params

windows = build_partition_params(
    {"_count": 500, "code": "C34,C34.9"},
    partition_param="recorded-date",
    start="2018-01-01",
    end="2026-01-01",
    frequency="YS",
)
```

The output is a list of ordinary parameter dictionaries. The partition bounds are represented internally as repeated FHIR parameters so Fyron sends a valid query string instead of a comma-joined date expression.

### Choosing The Right Partition Parameter

| Resource | Typical parameter | Notes |
| --- | --- | --- |
| `Condition` | `recorded-date` | Good for diagnosis/cohort extraction when supported by the server. |
| `Observation` | `date` | Often maps to effective time. |
| `DiagnosticReport` | `issued` or `date` | Server support varies; inspect the CapabilityStatement. |
| `Procedure` | `date` | Useful for operation/procedure cohorts. |
| `ImagingStudy` | `started` | Useful for imaging cohort discovery. |
| Any resource | `_lastUpdated` | Good for incremental synchronization, not always equivalent to clinical event time. |

### When Not To Use It

Do not use partitioning as a substitute for correct clinical filters. It is a transport strategy for large result sets. If every monthly or weekly partition still reaches the server cap, narrow the clinical query, use a smaller `window_days`, or ask the FHIR server administrator whether the endpoint supports asynchronous bulk export.

## CLI Workflow

```bash
fyron fhir-rest \
  --base-url "$FHIR_BASE_URL" \
  --resource Observation \
  --input cohort.csv \
  --column-map subject=patient_id \
  --param 'code=http://loinc.org|718-7' \
  --max-pages 1 \
  --output observations.csv
```

## Function Table

| Function | Required | Optional | Returns |
| --- | --- | --- | --- |
| `FHIRRestClient(...)` | `base_url` or `FHIR_BASE_URL` | auth, timeout, cache, logging | client |
| `search_df(resource_type, ...)` | resource type | params, max pages | DataFrame |
| `search_df_partitioned(...)` | resource type, partition param, start, end | frequency, window days, de-duplication | DataFrame |
| `search_df_from(df, ...)` | input table, resource type, column map | params, paths, metadata | DataFrame |
| `query_df(...)` / `query_df_from(...)` | same as search aliases | compatibility names for existing code |
| `build_partition_params(...)` | params, partition param, start, end | frequency, window days | list of parameter dicts |
| `create_resource(resource, ...)` | FHIR resource dict | resource type override | `FHIRWriteResult` |
| `update_resource(resource, ...)` | FHIR resource dict | id/type override | `FHIRWriteResult` |
| `submit_bundle(bundle)` | transaction bundle | none | `FHIRWriteResult` |

## Return Values

| Output | Meaning |
| --- | --- |
| DataFrame rows | Usually one row per returned resource, unless a custom processor emits multiple rows. |
| FHIR path columns | Values projected from nested FHIR JSON; missing paths become missing table values. |
| `_fyron_partition_start`, `_fyron_partition_end` | Trace columns added by partitioned search when enabled. |
| `FHIRWriteResult` | Write-back status, response payload, and request context for review/logging. |

## Common Pitfalls

- Keep `max_pages` during development so exploratory queries do not pull a whole server.
- If a server caps broad searches, partition by date instead of relying on endless pagination.
- FHIR references often need `Patient/<id>` rather than a bare ID; inspect your server behavior.
- `collection` bundles are for local review; submit `transaction` bundles to servers.
- Fyron validates structure lightly. Production write-back should still use server/profile validation.

## Related Modules

- [FHIR](../../fhir/index.html) for the overview.
- [FHIR Mapping](mapping.md) for CSV/DataFrame-to-FHIR bundles.
- [Core I/O](../../core/index.html) for `.env`, table, Teable, and S3 helpers.

## Pagination and Transport Safety

Sequential and parallel searches validate `max_pages`: use `-1` for all pages,
`0` for no requests, or a positive integer for an explicit limit. A page limit
does not mean that every matching resource has been retrieved.

Next links are resolved against the response URL. Pagination must stay on the
same origin (scheme, host, and port); cross-origin links are rejected before
Fyron sends another authenticated request. Repeated page URLs raise
`FHIRRequestError` instead of looping or returning duplicate pages. Streaming
consumers must treat previously yielded bundles as incomplete if iteration fails.

Top-level `OperationOutcome` responses and JSON without a resource type are not
treated as successful resource results. Errors use safe diagnostic descriptions.

Workers receive the configured retry policy and session headers. Explicit Basic
credentials are preserved rather than replaced with environment credentials.
Static Bearer tokens also apply to sequential requests. HTTP request timeouts
must be finite positive values; they remain distinct from parallel job deadlines.

## Query Reports And Input Association

DataFrame query methods and their `query_df`/`search_df` aliases accept the
keyword-only option `return_report=True`. This also works for row-wise and
partitioned queries. The default return type is unchanged.

```python
result = client.search_df_from(
    cohort.rename(columns={"patient_id": "input_patient_id"}),
    resource_type="Patient",
    column_map={"_id": "input_patient_id"},
    parallel_fetch=True,
    use_multiprocessing=False,
    include_column_map_columns=True,
    return_report=True,
)
patients = result["data"]
query_rows = result["report"]["rows"]
summary = result["report"]["summary"]
```

Copied input columns now work during parallel fetching. They contain original
input values, not prefixes added to search parameters. Input ordinals associate
results even with duplicate queries or non-default DataFrame indices. Row-query
outputs follow input order and then page order. Rename input metadata columns if
they conflict with extracted resource columns; collisions raise rather than
silently overwriting data.

Reports contain job ordinals, `status`, `pages`, `resource_entries`, `exhausted`,
and `page_limited`. The summary distinguishes `execution_complete` from
`retrieval_exhaustive`, with counts for queries, no-match queries, page-limited
queries, pages, and entries. Entry counts precede custom processing or
deduplication and can include included resources. They are not unique-patient counts.

| Status | Interpretation |
| --- | --- |
| `success` | Finished with entries and no advertised next page. |
| `no_match` | Finished with no entries and no advertised next page. |
| `page_limit` | An advertised next page was not fetched because of the requested limit. |
| `not_requested` | `max_pages=0`; no HTTP requests and no claim of exhaustive retrieval. |

Exhaustion means following the server's advertised pagination, not independently
verifying its search implementation or access permissions. Failed DataFrame
queries still raise without returning a successful-looking partial report.

| Setting | What it controls |
| --- | --- |
| `parallel_fetch=True` | HTTP queries across worker processes when `num_processes > 1`. |
| `use_multiprocessing=True` | Bundle-to-table processing, separately from HTTP fetching. |
| `num_processes=1` | Sequential execution; useful for debugging and small runs. |

HTTP sessions are reused within each worker for a pool run, retaining connection
pools, configured retries, and authentication. Sessions are not shared between
workers or separate runs. Normal completion closes workers gracefully; failures
and cancellation terminate the pool. This does not add task resubmission or
change the distinction between HTTP timeouts and execution deadlines.
