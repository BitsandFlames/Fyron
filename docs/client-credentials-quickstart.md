# Fyron Client-Credentials Authentication

Available in Fyron 0.3.10. Use `Auth.client_credentials()` instead of
`Auth.token_env()` for service accounts. This uses an application client ID and
secret, not your personal username and password.

## Install

```bash
pip install --upgrade fyron==0.3.10
```

## With OIDC Discovery

```python
import os
from fyron import Auth, FHIRRestClient, load_env

if __name__ == "__main__":
    load_env()

    with Auth.client_credentials(
        auth_url=os.environ["OIDC_ISSUER"],
        client_id=os.environ["OAUTH_CLIENT_ID"],
        client_secret=os.environ["OAUTH_CLIENT_SECRET"],
        scope=os.environ["OAUTH_SCOPE"],
    ) as auth:
        client = FHIRRestClient(
            base_url=os.environ["FHIR_BASE_URL"],
            auth=auth,
            return_fhir_obj=True,
            num_processes=10,
        )

        result_df = client.query_df("Patient")
```

Your local `.env` file:

```dotenv
OIDC_ISSUER=https://identity.example.org/realms/research
OAUTH_CLIENT_ID=your-registered-client
OAUTH_CLIENT_SECRET=your-client-secret
OAUTH_SCOPE=system/Patient.read
FHIR_BASE_URL=https://hospital.example.org/fhir
```

Use the exact issuer URL and scopes approved by your provider. The scope above
is only an example. Keep `.env` out of Git and never share real secrets in logs,
notebooks, or issue reports.

## With a Known Token Endpoint

Supply `token_endpoint` instead of `auth_url` to bypass discovery:

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
            num_processes=10,
        )
        result_df = client.query_df("Patient")
```

Set `OAUTH_TOKEN_URL` to your provider's token endpoint, for example
`https://identity.example.org/oauth/token`. Use `client_secret_post` instead of
`client_secret_basic` only when required by your provider.

## Token Handling and DICOMweb

- Basic or POST client authentication is used only at the token endpoint.
  Resource requests use `Authorization: Bearer <access_token>`.
- Fyron renews tokens after 75% of their declared lifetime. Without lifetime
  metadata, renewal follows a 401 authentication challenge.
- Parallel FHIR and DICOM workers coordinate renewal in the parent process.
- No `refresh_url`, token cache, browser approval, or user password is needed.
- Pass the same `auth` object to `DICOMDownloader(auth=auth, ...)` when its
  service accepts the token's permissions and audience. Complete downloads
  before leaving the authentication context.
- This is OAuth service-account authorization with optional OIDC discovery,
  not interactive user login or ID-token validation. It does not implement
  `private_key_jwt` or every SMART backend-services profile.

See the [FHIR authentication documentation](https://fyron.bitsandflames.ai/modules/fhir/rest/#service-account-authentication)
for provider setup and supported options.
