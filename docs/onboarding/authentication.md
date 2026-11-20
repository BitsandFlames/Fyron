# Authentication for the exercises

Complete [Setup](index.md#before-you-start) first. Save the helper below once and reuse it across the HTTP exercises.

Use one configuration per service. FHIR, DICOMweb and documents can require different clients, scopes and token audiences even when they share an issuer. PostgreSQL uses separate database credentials, not the HTTP `Auth` object.

Create a local `.env` using placeholders like these. Replace only the settings needed for your chosen method:

```dotenv
DEMO_FHIR_URL=https://fhir.example.org/r4
DEMO_DICOM_URL=https://dicom.example.org/dicom-web
DEMO_OIDC_ISSUER=https://identity.example.org
DEMO_CLIENT_ID=replace-with-approved-client
DEMO_CLIENT_SECRET=replace-with-approved-secret
DEMO_SCOPE=replace-with-approved-scope
DEMO_ACCESS_TOKEN=replace-with-approved-token
FHIR_USER=replace-with-approved-user
FHIR_PASSWORD=replace-with-approved-password
FHIR_AUTH_URL=https://identity.example.org/example-login
```

`DEMO_*` variables are example-specific and explicitly read below. `FHIR_USER` and `FHIR_PASSWORD` are native environment inputs to the Basic and password-to-token recipes. The example login endpoint is **not** an OAuth token endpoint.

Save this helper as `onboarding_auth.py` beside your scripts. It selects a method explicitly instead of silently inheriting a different service's authentication:

```python
import os
from pathlib import Path
import requests
from dotenv import load_dotenv
from fyron import Auth

load_dotenv(".env", override=False)


def make_auth(method, *, cache_name=None, unattended=False):
    """Return a context manager; choose settings approved for this service."""
    if method == "public":
        # Explicit session avoids Fyron's implicit FHIR-auth environment fallback.
        # Requests can still use environment/proxy/netrc settings; review those.
        return requests.Session()
    if method == "basic":
        return Auth(auth_type="basic", auth_method="env")
    if method == "bearer":
        session = requests.Session()
        session.headers["Authorization"] = "Bearer " + os.environ["DEMO_ACCESS_TOKEN"]
        return session
    if method == "password_token":
        return Auth.token_env(
            auth_url=os.environ["FHIR_AUTH_URL"], token_auth_method="basic"
        )
    if method == "device_code":
        options = {}
        if cache_name is not None:
            options["token_cache"] = str(
                Path.home() / ".cache" / "fyron" / cache_name
            )
        return Auth(
            auth_type="device_code",
            auth_url=os.environ["DEMO_OIDC_ISSUER"],
            client_id=os.environ["DEMO_CLIENT_ID"],
            scope=os.environ["DEMO_SCOPE"],
            allow_reauthentication=not unattended,
            **options,
        )
    if method == "client_credentials":
        return Auth.client_credentials(
            auth_url=os.environ["DEMO_OIDC_ISSUER"],
            client_id=os.environ["DEMO_CLIENT_ID"],
            client_secret=os.environ["DEMO_CLIENT_SECRET"],
            scope=os.environ["DEMO_SCOPE"],
        )
    raise ValueError("Choose a documented authentication method")
```

| Method | When to use it | Renewal |
| --- | --- | --- |
| `public` | Explicitly public or local test HTTP services | No token |
| `basic` | HTTP Basic over HTTPS | Credentials accompany requests |
| `bearer` | An already issued access token | Static token does not renew |
| `password_token` | A service implementing Fyron's endpoint-specific password-to-token protocol | Uses that protocol; not a universal OAuth password grant |
| `device_code` | Browser-approved access for a registered device client | Refresh when supported; may require renewed approval |
| `client_credentials` | Approved service-account access | Obtains new access tokens with the client credentials |

These shared authentication/session patterns can be passed as `auth` to the three HTTP clients below. The password-to-token example expects GET with Basic credentials and a JSON `access_token` or `token`; use `token_auth_method="post"` only for the documented username/password JSON protocol. Never assume an arbitrary identity provider supports it.

Renewal is **demand-driven**, not a background keep-alive. Keep the shared auth object alive throughout the operation. For device flow, the first run requests browser approval. Optional caching stores sensitive plaintext credentials outside the download folder; Fyron requires owner-only POSIX protection and locking, and does not support this cache on non-POSIX systems. After establishing a usable cache, set `unattended=True`: refresh remains allowed, but a job needing new browser approval fails. Client credentials do not use this device cache.

For custom sessions, native DICOM Basic credentials, explicit device/token endpoints, TLS certificates and troubleshooting, see [Choose your authentication](../authentication/index.md), [FHIR REST authentication](../authentication/fhir-rest.md), [DICOMweb authentication](../authentication/dicomweb.md) and [document authentication](../authentication/documents.md). Do not disable TLS verification to resolve certificate failures.

## Select the right settings for each run

The shared helper reads the currently loaded `.env`. Before moving from FHIR to DICOMweb or documents, replace its example-specific values with that service's approved configuration. Distinct cache names avoid mixing cached logins; they do not grant cross-service access.

Start interactively with `make_auth("device_code", cache_name="fhir-demo.json")`. After approval and a successful run, unattended use is explicit:

```python
with make_auth("device_code", cache_name="fhir-demo.json", unattended=True) as auth:
    # Run the same FHIR workflow here. Refresh is allowed; browser prompts are not.
    pass
```

An expired static bearer token must be replaced. A refresh failure is an error to resolve, not a reason to loop indefinitely or silently change authentication methods.

**Next:** [FHIR REST](fhir-rest.md), [DICOMweb](dicomweb.md), or [Documents](documents.md). Database credentials are covered in [PostgreSQL](sql.md).
