# Choose your authentication

Authentication depends on your institution’s server configuration and access policy. Ask your administrator which method, endpoints, client registration, scopes and permissions are required. Fyron supports several methods, but cannot determine which one your site permits.

An API URL, an identity provider’s issuer URL, and a token endpoint are different settings. Scopes and token audiences are service-specific: sharing an issuer does not mean one token grants access to FHIR, DICOMweb and documents. Configure each service separately unless your administrator explicitly approves token reuse.

## Supported paths

| Method | FHIR REST | DICOMweb | Documents | PostgreSQL |
| --- | --- | --- | --- | --- |
| No authentication | Python / CLI | Python / CLI | Python / CLI | Only if database policy allows it |
| HTTP Basic | Python | Python / CLI | Python | Not HTTP authentication |
| Existing Bearer token | Python / CLI | Python session | Python session | No automatic token workflow |
| Password-to-token endpoint | Python / CLI | Python shared Auth | Python shared Auth | Not supported by Auth |
| OAuth device flow | Python | Python | Python / CLI | Not supported by Auth |
| OAuth client credentials | Python | Python | Python / CLI | Not supported by Auth |
| Custom requests.Session | Python | Python; parallel limits apply | Python | Not applicable |
| Database user / password / DSN | Not applicable | Not applicable | Not applicable | Python |

Follow the complete service examples: [FHIR REST](fhir-rest.md), [DICOMweb](dicomweb.md), [Documents](documents.md), or [SQL](sql.md). These guides describe existing interfaces, not additional authentication features.

## Environment files

All endpoints below are fictional. Replace placeholders only with settings approved for your service. Keep `.env` and token caches out of Git and shared output folders. Do not put real tokens into command arguments, notebooks you share, or logs.

Python examples explicitly load a local file with `load_dotenv(".env", override=False)`. Existing process variables take precedence. Client constructors and the unified CLI do not themselves load an arbitrary `.env` file.

For Bash examples, export a **trusted, shell-compatible file you created** before running commands:

```bash
set -a
source .env
set +a
```

Sourcing a file executes shell code. Do not source downloaded or unreviewed environment files. Replace conflicting variables from a previous service configuration rather than mixing examples.

`RESEARCH_*` names in these guides are example-specific: Python reads them explicitly with `os.environ`, or Bash expands them into CLI options. They are not automatic Fyron settings. Native `FHIR_*`, `DICOM_*`, and `FHIR_DB_*` settings are documented on the individual pages.

## HTTP Basic

Use only where the service supports HTTP Basic over HTTPS. This authenticates each request; it does not obtain an OAuth token.

```dotenv
FHIR_USER=replace-me
FHIR_PASSWORD=replace-me
```

```python
from dotenv import load_dotenv
from fyron import Auth

load_dotenv(".env", override=False)
with Auth(auth_type="basic", auth_method="env") as auth:
    # Pass auth to a FHIRRestClient, DICOMDownloader or DocumentDownloader here.
    pass
```

`Auth` reads `FHIR_USER` and `FHIR_PASSWORD` for this mode even when used with DICOMweb or documents. For a password prompt, use `Auth(auth_type="basic", auth_method="password", username="replace-me")` instead.

## Existing Bearer token and custom sessions

A static token does not automatically renew. Obtain it through your site’s approved process and replace it when necessary. For a shared session recipe:

```dotenv
RESEARCH_ACCESS_TOKEN=replace-me
```

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv(".env", override=False)
with requests.Session() as session:
    session.headers["Authorization"] = "Bearer " + os.environ["RESEARCH_ACCESS_TOKEN"]
    # Pass session as auth= to a supported HTTP client inside this block.
    pass
```

A custom session can carry approved headers, cookies, certificate settings or a Requests authentication handler. Fyron does not provide automatic OAuth renewal for arbitrary handlers. FHIR multiprocessing does not reproduce arbitrary session behavior; use one process unless the documented worker path supports your configuration. DICOM batch downloads fall back to one process for unsupported custom authentication. Document threads share the session: custom stateful handlers must be safe for concurrent use; otherwise use one worker.

The caller owns a supplied `Auth` or session. Close the client first, then the supplied authentication/session using nested context managers as shown in the service guides.

## Password-to-token endpoints

This is Fyron’s existing endpoint-specific protocol, **not a universal OAuth password grant**. Ask whether your endpoint accepts GET with HTTP Basic (`token_auth_method="basic"`) or POST with JSON `username` and `password` (`"post"`). It must return JSON with `access_token` or `token`. Do not assume an OAuth provider’s token endpoint implements this protocol.

```dotenv
FHIR_AUTH_URL=https://identity.example.org/research/login
FHIR_USER=replace-me
FHIR_PASSWORD=replace-me
```

```python
import os
from dotenv import load_dotenv
from fyron import Auth

load_dotenv(".env", override=False)
with Auth.token_env(
    auth_url=os.environ["FHIR_AUTH_URL"],
    token_auth_method="basic",
) as auth:
    # Pass auth to the required HTTP client here.
    pass
```

Only configure `refresh_url` / `FHIR_REFRESH_URL` when the service implements Fyron’s existing refresh protocol. This legacy token helper is separate from OAuth device-flow refresh tokens. Do not treat token parsing as signature or ID-token validation.

## Browser-approved device flow

Choose this when the identity provider supports device authorization for your registered client. Fyron displays approval instructions, polls the provider, and renews credentials when supported. You approve access in the browser; you do not supply your institutional password to the script.

```dotenv
RESEARCH_OIDC_ISSUER=https://identity.example.org/realms/research
RESEARCH_CLIENT_ID=research-demo
RESEARCH_SCOPE=openid
```

```python
import os
from dotenv import load_dotenv
from fyron import Auth

load_dotenv(".env", override=False)
with Auth(
    auth_type="device_code",
    auth_url=os.environ["RESEARCH_OIDC_ISSUER"],
    client_id=os.environ["RESEARCH_CLIENT_ID"],
    scope=os.environ["RESEARCH_SCOPE"],
) as auth:
    # Keep the client operations inside this block.
    pass
```

`openid` is an illustrative scope, not a promise of API access or a refresh token. Request only the scopes your administrator specifies. A confidential device client may also require `client_secret`. To bypass discovery, supply **both** `device_authorization_endpoint` and `token_endpoint`; supplying only one is not an equivalent configuration. An optional `authorization_endpoint` identifies login redirects.

### Cache and unattended runs

Caching is opt-in for device authentication. Add a path outside the document/image output directory:

```python
from pathlib import Path

cache_path = Path.home() / ".cache" / "fyron" / "research-device-token.json"
# Add token_cache=str(cache_path) to the device Auth constructor above.
# After an approved first run, also add allow_reauthentication=False for unattended jobs.
```

The cache contains sensitive, unencrypted credentials. The implementation requires POSIX owner-only protection and file locking. Device-token caching is not supported on non-POSIX platforms. Cached credentials must match the configured identity, client and scopes. An expired access token may be refreshed if usable renewal credentials remain. With `allow_reauthentication=False`, missing or unusable credentials fail instead of requesting browser approval. This option applies to device flow, not as a general disable-authentication switch.

Document completion JSON and authentication caches are unrelated. Disabling completion records does not disable token caching. Do not copy caches into results, source control or publication archives.

## Service accounts

Use client credentials only when your site registers a service account and grants it the needed access. This renews access tokens using the client credentials; it is not user login and does not use the device-token cache.

```dotenv
RESEARCH_OIDC_ISSUER=https://identity.example.org/realms/research
RESEARCH_CLIENT_ID=research-service-demo
RESEARCH_CLIENT_SECRET=replace-me
RESEARCH_SCOPE=research.read
```

```python
import os
from dotenv import load_dotenv
from fyron import Auth

load_dotenv(".env", override=False)
with Auth.client_credentials(
    auth_url=os.environ["RESEARCH_OIDC_ISSUER"],
    client_id=os.environ["RESEARCH_CLIENT_ID"],
    client_secret=os.environ["RESEARCH_CLIENT_SECRET"],
    scope=os.environ["RESEARCH_SCOPE"],
) as auth:
    # Pass auth to the approved HTTP service here.
    pass
```

Alternatively, supply `token_endpoint` instead of the issuer. `client_auth_method` supports `client_secret_basic` and `client_secret_post`; use the method required by the provider. The example scope is fictional and must be replaced. `Auth.client_credentials(...)` does not implicitly read these example environment names.

## Token renewal during long runs

Renewal happens when Fyron requests credentials for an operation. It is not a background service that keeps an idle token alive. Access can still expire or be revoked during a job; renewal cannot restore permissions removed by the server.

| Authentication | Renewal behavior | When intervention is needed |
| --- | --- | --- |
| Static Bearer token | No automatic renewal. | Obtain and configure a replacement through your approved process. |
| Device flow | Reuses the access token, then uses a refresh token when available. When the provider supplies a lifetime, renewal becomes due after 75% of that lifetime, on the next credential request. | Without usable refresh credentials, another browser approval may be required. |
| Client credentials | Obtains a new access token using the registered client credentials when renewal is due or the token is rejected. Known lifetimes use the same 75% renewal threshold. | Expired or revoked client secrets, denied scopes and provider failures require administrator attention. |
| Password-to-token helper | Uses the configured endpoint-specific login/refresh protocol. | The endpoint must implement that protocol; do not assume standard OAuth refresh support. |
| Custom session | Depends on the supplied handler; a static Authorization header stays static. | Your handler or application must manage renewal. |
| PostgreSQL | No HTTP token renewal through `FHIRSQLClient`. | Arrange database credentials and any short-lived credential replacement separately. |

For unattended device-flow jobs, establish a cache with an approved interactive run first, then use `allow_reauthentication=False` (document CLI: `--no-reauthentication`). This still permits refresh; it prevents a new browser login. Missing credentials or an invalid refresh grant that requires approval will fail instead of prompting. Other refresh errors also fail rather than guaranteeing a fresh login. A cache is not a guarantee of indefinite access.

FHIR REST and DICOMweb coordinate supported shared authentication across their workers. Document download threads reuse the supplied shared `Auth`. Keep that object alive for the entire operation rather than copying its current token into a static header. See the service guides for supported parallel configurations. After an authentication failure, inspect the operation's explicit results and completion records before retrying; do not treat partial output as a complete extract.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Device approval denied or expired | Client registration, supported grant, requested scopes and approval deadline; start a new approved flow if appropriate. |
| Repeated 401 or expired token | Token audience, issuer, expiry and renewal configuration; a static token cannot renew itself. |
| 403 / access denied | Service permissions and scopes; signing in successfully does not authorize every dataset. Do not repeatedly reauthenticate to work around access restrictions. |
| HTML login page or redirect | Use the approved API endpoint, not a browser login URL. Document redirects are guarded; cross-origin redirects are blocked. |
| Discovery or token endpoint failure | Distinguish issuer, API base URL and explicit endpoints; confirm network access with your administrator. |
| Certificate verification failure | Use the approved CA bundle and correct hostname. For HTTP, Requests supports `REQUESTS_CA_BUNDLE`; for SQL, use PostgreSQL TLS settings. Do not disable verification. |
| Cache permission or unattended failure | Check supported OS, ownership, cache location and whether an approved first run established reusable credentials. |

Share controlled error types and status codes when asking for help, not tokens, response bodies or identifying URLs. See [Safe Network Diagnostics](../diagnostics.md).
