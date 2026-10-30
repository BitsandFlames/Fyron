# FHIR REST authentication

Choose the method your FHIR administrator supports. See [Choose your authentication](index.md) for the support matrix, shared recipes and `.env` loading. An identity provider issuer is not the FHIR base URL.

## Device login example

This complete example performs a bounded Patient search after browser approval. The endpoint and client are fictional; access to Patient resources requires appropriate permission.

```dotenv
FHIR_BASE_URL=https://fhir.example.org/r4
RESEARCH_OIDC_ISSUER=https://identity.example.org/realms/research
RESEARCH_CLIENT_ID=research-demo
RESEARCH_SCOPE=openid
```

```python
import os
from dotenv import load_dotenv
from fyron import Auth, FHIRRestClient


def main():
    load_dotenv(".env", override=False)
    with Auth(
        auth_type="device_code",
        auth_url=os.environ["RESEARCH_OIDC_ISSUER"],
        client_id=os.environ["RESEARCH_CLIENT_ID"],
        scope=os.environ["RESEARCH_SCOPE"],
    ) as auth:
        with FHIRRestClient(
            base_url=os.environ["FHIR_BASE_URL"], auth=auth, num_processes=1,
        ) as client:
            rows = client.query_df("Patient", params={"_count": 10}, max_pages=1)
            rows.to_csv("patients.csv", index=False)


if __name__ == "__main__":
    main()
```

For Basic, password-to-token or service accounts, replace the `Auth` constructor with the corresponding [shared recipe](index.md). Keep the client inside the authentication context. For cached device login, follow [Cache and unattended runs](index.md#cache-and-unattended-runs).

## Static Bearer token

Use a separate environment file without `FHIR_AUTH_URL`, `FHIR_REFRESH_URL`, or legacy credentials. Fyron reads `FHIR_TOKEN` automatically; this is a static header, not a renewal mechanism.

```dotenv
FHIR_BASE_URL=https://fhir.example.org/r4
FHIR_TOKEN=replace-me
```

```python
import os
import requests
from dotenv import load_dotenv
from fyron import FHIRRestClient

load_dotenv(".env", override=False)
with requests.Session() as session:
    with FHIRRestClient(
        base_url=os.environ["FHIR_BASE_URL"],
        auth=session,
        bearer_token=os.environ["FHIR_TOKEN"],
        num_processes=1,
    ) as client:
        rows = client.query_df("Patient", params={"_count": 10}, max_pages=1)
        rows.to_csv("patients.csv", index=False)
```

A supplied session avoids automatic password-to-token setup. A nonempty `bearer_token` takes precedence over `FHIR_TOKEN`, but is attached only when `session.auth` is absent. Do not mix a session authentication handler with a second Bearer configuration.

## Environment defaults and public endpoints

| Setting | Existing behavior |
| --- | --- |
| `FHIR_BASE_URL` | Used when `base_url` is omitted. |
| `FHIR_AUTH_URL` | Without a supplied Auth/session, enables password-to-token authentication. |
| `FHIR_REFRESH_URL` | Optional legacy refresh endpoint for automatic authentication. |
| `FHIR_USER`, `FHIR_PASSWORD` | Credentials for legacy token or shared Basic authentication. |
| `FHIR_TOKEN` | Static Bearer fallback when no session authentication handler is set. |

Explicit `Auth` or a session takes priority over automatic authentication. A supplied unauthenticated session can still receive `FHIR_TOKEN`. For a deliberately unauthenticated public endpoint, use a clean environment with no `FHIR_TOKEN` or authentication variables; merely passing `auth=None` does not disable inherited settings.

```python
import os
import requests
from fyron import FHIRRestClient

# This example deliberately makes an unauthenticated request.
os.environ.pop("FHIR_TOKEN", None)
with requests.Session() as session:
    with FHIRRestClient(base_url="https://fhir.example.org/public/r4", auth=session) as client:
        rows = client.query_df("Patient", params={"_count": 1}, max_pages=1)
```

## CLI

Export the static-token `.env` above using the overview’s Bash instructions, then run:

```bash
fyron fhir-rest --resource Patient --param _count=10 --max-pages 1 --output patients.csv
```

The CLI reads `FHIR_BASE_URL`, `FHIR_TOKEN` and legacy `FHIR_AUTH_URL` settings. Its legacy token path uses the default HTTP Basic login protocol. It does not expose device-flow, client-credentials, resource Basic-auth, or arbitrary-session configuration flags; use Python for those workflows. Never pass a real token directly as a command argument.

## Parallel execution

Shared device, client-credentials and supported password-token authentication coordinate renewal across FHIR workers. Use a guarded `if __name__ == "__main__":` entrypoint for multiprocessing. Custom session handlers are not generally portable across workers; keep them sequential unless supported. Static tokens remain static. Authentication failure must not be interpreted as a complete extract, even if some streamed bundles arrived earlier.

Continue with [FHIR REST queries](../modules/fhir/rest.md) and [troubleshooting](index.md#troubleshooting).
