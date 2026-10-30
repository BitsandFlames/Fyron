# Document authentication

Document endpoints may use different access rules from FHIR or DICOMweb, even at the same site. Use the method your administrator specifies. See [Choose your authentication](index.md) for shared methods and cache behavior.

## Browser approval with an optional cache

The examples below use a fictional PDF endpoint. `RESEARCH_*` variables are example-specific and are passed explicitly; the downloader does not discover them automatically.

```dotenv
RESEARCH_DOCUMENT_URL=https://documents.example.org/reports/demo.pdf
RESEARCH_OIDC_ISSUER=https://identity.example.org/realms/research
RESEARCH_CLIENT_ID=research-demo
RESEARCH_SCOPE=openid
```

```python
import os
from pathlib import Path
from dotenv import load_dotenv
from fyron import Auth, DocumentDownloader


def main():
    load_dotenv(".env", override=False)
    cache = Path.home() / ".cache" / "fyron" / "documents-device-token.json"
    with Auth(
        auth_type="device_code",
        auth_url=os.environ["RESEARCH_OIDC_ISSUER"],
        client_id=os.environ["RESEARCH_CLIENT_ID"],
        scope=os.environ["RESEARCH_SCOPE"],
        token_cache=str(cache),
    ) as auth:
        with DocumentDownloader(
            auth=auth, output_dir="documents_out", timeout=90,
            require_pdf=True, allow_redirects=False,
        ) as downloader:
            result = downloader.download_url(os.environ["RESEARCH_DOCUMENT_URL"])
            # Inspect result['status'] and result['error']; counts alone are not success.


if __name__ == "__main__":
    main()
```

The first run requests browser approval. Later runs may reuse the cache and refresh when supported. Remove `token_cache` to avoid persistent caching. After an approved first run, add `allow_reauthentication=False` for an unattended job that must fail instead of requesting approval. The cache contains plaintext credentials and requires the [documented POSIX protections](index.md#cache-and-unattended-runs).

`require_pdf=True` checks media type and a PDF signature, not complete PDF validity. For general documents, including `text/plain`, omit it. The Python timeout default remains 30 seconds; this example explicitly uses 90.

### CLI equivalent

Export the environment file as described in the overview:

```bash
fyron document-download --url "$RESEARCH_DOCUMENT_URL" \
  --output-dir documents_out --pdf --timeout 90 \
  --auth-type device_code --auth-url "$RESEARCH_OIDC_ISSUER" \
  --client-id "$RESEARCH_CLIENT_ID" --scope "$RESEARCH_SCOPE" \
  --token-cache "$HOME/.cache/fyron/documents-device-token.json"
```

Add `--no-reauthentication` for unattended runs with an established cache. Explicit discovery alternatives are `--device-authorization-endpoint` together with `--token-endpoint`. The CLI rejects redirects by default; `--allow-redirects` enables only permitted same-origin redirects, not arbitrary cross-origin forwarding.

## Service-account CLI

For this alternative, add these example-specific variables to the file and export it again:

```dotenv
RESEARCH_CLIENT_ID=research-service-demo
RESEARCH_CLIENT_SECRET=replace-me
RESEARCH_SCOPE=research.read
```

```bash
fyron document-download --url "$RESEARCH_DOCUMENT_URL" \
  --output-dir documents_out --pdf \
  --auth-type client_credentials --auth-url "$RESEARCH_OIDC_ISSUER" \
  --client-id "$RESEARCH_CLIENT_ID" --scope "$RESEARCH_SCOPE" \
  --client-secret-env RESEARCH_CLIENT_SECRET
```

The secret option accepts an **environment variable name**, not its value. Python uses `Auth.client_credentials(...)` from the [shared recipe](index.md#service-accounts), passed into the same downloader. Service-account token renewal does not use the device cache.

## Basic, static tokens and legacy token endpoints

HTTP Basic is available through `basic_auth=(user, password)` or shared Basic `Auth`. For example:

```dotenv
RESEARCH_DOCUMENT_URL=https://documents.example.org/reports/demo.txt
RESEARCH_USER=replace-me
RESEARCH_PASSWORD=replace-me
```

```python
import os
from dotenv import load_dotenv
from fyron import DocumentDownloader

load_dotenv(".env", override=False)
with DocumentDownloader(
    basic_auth=(os.environ["RESEARCH_USER"], os.environ["RESEARCH_PASSWORD"]),
    output_dir="documents_out", allow_redirects=False, timeout=90,
) as downloader:
    result = downloader.download_url(os.environ["RESEARCH_DOCUMENT_URL"])
```

For a static token or custom handler, pass the [configured session](index.md#existing-bearer-token-and-custom-sessions) as `auth=session`. For the legacy endpoint protocol, pass `Auth.token_env(...)`. Do not combine `auth` and Basic credentials: a supplied Auth/session is selected before `basic_auth`. These methods have no direct document CLI flags; use Python.

## Defaults and deliberately unauthenticated downloads

The **Python API** may create legacy token authentication when no Auth/session or Basic tuple is supplied and `FHIR_AUTH_URL` or `FHIR_REFRESH_URL` is set. That path uses the shared FHIR credential variables. `auth=None` therefore does not force an unauthenticated request. Supplying a new session avoids inherited authentication:

```python
import requests
from fyron import DocumentDownloader

with requests.Session() as session:
    with DocumentDownloader(auth=session, output_dir="documents_out", allow_redirects=False) as downloader:
        result = downloader.download_url("https://documents.example.org/public/demo.txt")
```

The **CLI** defaults to `--auth-type none` and deliberately supplies an unauthenticated session, so it does not inherit those FHIR authentication variables:

```bash
fyron document-download --url 'https://documents.example.org/public/demo.txt' \
  --auth-type none --output-dir documents_out
```

Document threads share the Auth/session and renewal coordination. Custom stateful authentication handlers must support concurrent use; otherwise use one worker. For batch result paths, custom IDs and completion records, see [DocumentDownloader](../modules/documents/downloader.md). Completion JSON does not contain the device-token cache; disabling it does not disable caching.
