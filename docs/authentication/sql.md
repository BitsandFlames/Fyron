# SQL authentication and connections

`FHIRSQLClient` connects to PostgreSQL using Psycopg. It does **not** accept the HTTP `Auth` object or automatically perform OIDC login or token renewal. Your database administrator determines the host, database, role, credential method, TLS settings and network access required. FHIR REST permissions do not imply access to the database behind it.

## User and password through environment settings

Use a read-only database role where appropriate. These values are fictional placeholders. Python explicitly loads the file; the SQL constructor reads the native `FHIR_DB_*` variables from the process environment.

```dotenv
FHIR_DB_HOST=database.example.org
FHIR_DB_PORT=5432
FHIR_DB_NAME=research_demo
FHIR_DB_USER=research_reader
FHIR_DB_PASSWORD=replace-me
FHIR_DB_SSLMODE=verify-full
PGSSLROOTCERT=/path/to/approved-ca.pem
```

```python
from dotenv import load_dotenv
from fyron import FHIRSQLClient

load_dotenv(".env", override=False)
with FHIRSQLClient(connect_timeout=10) as client:
    result = client.query_df("SELECT 1 AS connection_ok")
    assert result.iloc[0]["connection_ok"] == 1
```

`PGSSLROOTCERT` is a PostgreSQL/libpq setting, not a Fyron variable. Replace the path with your approved CA certificate. `verify-full` verifies certificate trust and hostname; the server must support TLS and its certificate must match the configured host. Do not fix certificate failures by disabling verification.

## DSN alternative and precedence

Use either a DSN or individual connection settings. A DSN can be a PostgreSQL connection URI or a libpq connection string:

```dotenv
FHIR_DB_DSN="host=database.example.org port=5432 dbname=research_demo user=research_reader sslmode=verify-full"
PGPASSWORD=replace-me
PGSSLROOTCERT=/path/to/approved-ca.pem
```

Use the DSN explicitly in a complete connection check:

```python
import os
from dotenv import load_dotenv
from fyron import FHIRSQLClient

load_dotenv(".env", override=False)
with FHIRSQLClient(dsn=os.environ["FHIR_DB_DSN"], connect_timeout=10) as client:
    result = client.query_df("SELECT 1 AS connection_ok")
    assert result.iloc[0]["connection_ok"] == 1
```

`PGPASSWORD` is a libpq fallback for this example, not `FHIR_DB_PASSWORD`. Prefer your administrator’s approved credential mechanism; environment credentials remain sensitive. Libpq also supports password files, whose access permissions must follow PostgreSQL requirements.

- A nonempty explicit `dsn` takes priority over `FHIR_DB_DSN`.
- When either DSN is present, Fyron connects using it and `connect_timeout`; separate `host`, `user`, `password` and `sslmode` arguments/settings are not merged into it.
- Without a DSN, nonempty explicit arguments take priority over corresponding `FHIR_DB_*` settings. The default port is 5432.
- Remove an old `FHIR_DB_DSN` from the process environment before switching to individual settings. An empty argument does not reliably override environment fallbacks.

Avoid passwords inside connection URIs when possible. If your site requires them, URI-encode special characters and never log or publish the DSN. Site-specific certificate, service-file or externally obtained token configurations must follow the administrator’s PostgreSQL setup. Passing a short-lived database token as a password does not add automatic refresh to Fyron.

## Installation and running from a shell

Fyron declares Psycopg, but its default installation needs a working `libpq` library. Install your platform’s approved PostgreSQL client libraries. Alternatively, where permitted, install the Psycopg binary extra compatible with your environment:

```bash
uv add 'psycopg[binary]'
```

This is a deployment choice, not a change to Fyron’s dependencies. A missing libpq/import error occurs before database authentication; changing credentials will not resolve it.

There is no dedicated SQL authentication CLI. Save the complete Python example as `sql_connection.py`, then run:

```bash
uv run python sql_connection.py
```

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Missing database connection information | Set host, database and user, or provide a complete DSN. |
| Connection refused / timeout | Approved hostname, port, VPN/network route and server availability. |
| Password authentication failed | Correct database role and credential source; verify that an old DSN is not overriding individual settings. |
| Certificate or hostname error | Approved CA path, server certificate and `verify-full` hostname. |
| Permission denied for a relation | Database grants for the role; successful connection does not grant every query. |
| Psycopg / libpq import failure | PostgreSQL client library or approved binary installation. |

Continue with [SQL cohort extraction](../modules/fhir/sql.md). Keep identifiers and query results in explicit protected outputs, not diagnostic logs.
