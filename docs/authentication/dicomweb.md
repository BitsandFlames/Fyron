# DICOMweb authentication

Your imaging service determines whether it accepts Basic credentials, Bearer tokens or an OAuth flow. The DICOMweb base URL is separate from the identity provider. Start with [Choose your authentication](index.md); FHIR access does not automatically grant imaging access.

## Native Basic authentication

Use this complete example only when the DICOMweb service supports HTTP Basic. The UID is synthetic and must be replaced with an authorized study identifier.

```dotenv
DICOM_WEB_URL=https://dicom.example.org/dicom-web
DICOM_USER=replace-me
DICOM_PASSWORD=replace-me
RESEARCH_STUDY_UID=2.25.123456789
```

```python
import os
from dotenv import load_dotenv
from fyron import DICOMDownloader


def main():
    load_dotenv(".env", override=False)
    with DICOMDownloader(output_format="dicom", num_processes=1) as downloader:
        results = downloader.download_study(
            study_uid=os.environ["RESEARCH_STUDY_UID"], output_dir="dicom_out",
        )
        # Inspect each result's status/error before treating the study as complete.


if __name__ == "__main__":
    main()
```

`DICOM_WEB_URL`, `DICOM_USER` and `DICOM_PASSWORD` are native environment fallbacks. `RESEARCH_STUDY_UID` is explicitly read by this example. You can alternatively provide `dicom_web_url`, `dicom_user` and `dicom_password`, or `basic_auth=(user, password)`. Do not combine the Basic tuple with separate credentials.

### CLI equivalent

Export the `.env` using the overview’s Bash instructions:

```bash
fyron dicom-download --study-uid "$RESEARCH_STUDY_UID" \
  --full-study --output-format dicom --output-dir dicom_out --processes 1
```

The CLI reads the native DICOM environment settings. Use environment credentials instead of putting a password in command arguments. It has no shared-Auth/device/client-credentials options; use Python for those methods.

## Shared OAuth authentication

Use a separate environment file for an OAuth-enabled service:

```dotenv
DICOM_WEB_URL=https://dicom.example.org/dicom-web
RESEARCH_OIDC_ISSUER=https://identity.example.org/realms/research
RESEARCH_CLIENT_ID=research-demo
RESEARCH_SCOPE=openid
RESEARCH_STUDY_UID=2.25.123456789
```

```python
import os
from dotenv import load_dotenv
from fyron import Auth, DICOMDownloader


def main():
    load_dotenv(".env", override=False)
    with Auth(
        auth_type="device_code",
        auth_url=os.environ["RESEARCH_OIDC_ISSUER"],
        client_id=os.environ["RESEARCH_CLIENT_ID"],
        scope=os.environ["RESEARCH_SCOPE"],
    ) as auth:
        with DICOMDownloader(
            auth=auth, dicom_web_url=os.environ["DICOM_WEB_URL"],
            output_format="dicom", num_processes=1,
        ) as downloader:
            results = downloader.download_study(
                study_uid=os.environ["RESEARCH_STUDY_UID"], output_dir="dicom_out",
            )


if __name__ == "__main__":
    main()
```

Replace the constructor with [client credentials](index.md#service-accounts) for service accounts or [password-to-token](index.md#password-to-token-endpoints) when required by the service. Shared Basic Auth reads `FHIR_USER`/`FHIR_PASSWORD`, whereas native DICOM Basic uses `DICOM_USER`/`DICOM_PASSWORD`. Device caching uses the [shared cache options](index.md#cache-and-unattended-runs).

## Existing tokens, sessions and precedence

For a static token, build the [Bearer session](index.md#existing-bearer-token-and-custom-sessions) and pass it as `auth=session` to `DICOMDownloader`. The token is not renewed automatically. A custom session must remain open until downloads finish.

Explicit `auth` suppresses environment Basic credentials. Combining `auth` with explicit `basic_auth`, `dicom_user` or `dicom_password` raises instead of choosing one silently. Without explicit authentication, native Basic settings can be inherited. For an unauthenticated public service, pass a fresh `requests.Session()` explicitly without headers or an authentication handler.

For DataFrame batch downloads, native Basic credentials and shared Fyron token/device/client-credentials handlers support parallel workers and coordinated renewal where applicable. Unsupported custom authentication falls back to sequential execution. A manually configured session containing Basic authentication is not the same as the native DICOM Basic-credential path. Use a guarded script entrypoint for multiprocessing.

Continue with [DICOMDownloader](../modules/dicom/downloader.md) for result fields and completion checking, or [troubleshooting](index.md#troubleshooting).
