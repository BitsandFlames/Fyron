"""Command-line document downloads using the shared Fyron authentication."""

import logging
import math
import os
from contextlib import ExitStack
from pathlib import Path

import pandas as pd
import requests

from .._diagnostics import error_event, event
from ..console import console_message
from ..fhir.auth import Auth
from ..fhir._device_auth import _url as _oauth_url
from .client import DocumentDownloader, _resolve_document_url, _validate_document_id, _document_ids

logger = logging.getLogger(__name__)


def _add_parser(sub):
    parser = sub.add_parser("document-download", help="Download documents with optional OIDC authentication")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="One document URL")
    source.add_argument("--csv", help="CSV containing document URLs")
    parser.add_argument("--url-col", default="document_url")
    identifiers = parser.add_mutually_exclusive_group()
    identifiers.add_argument("--document-id", help="Exact document ID for --url")
    identifiers.add_argument("--id-col", help="Document ID column for --csv")
    parser.add_argument("--base-url", help="Prefix for relative document paths")
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument("--output", help="Exact file destination; single URL only")
    destination.add_argument("--output-dir", help="Output directory (default: documents_out)")
    parser.add_argument("--flat-output", action="store_true",
                        help="Save directly in the output directory using URL-hash filenames")
    parser.add_argument("--auth-type", choices=("none", "device_code", "client_credentials"), default="none")
    parser.add_argument("--auth-url", help="OIDC issuer")
    parser.add_argument("--client-id")
    parser.add_argument("--scope", help="Approved scopes; defaults to openid for device login, empty for service accounts")
    parser.add_argument("--client-secret-env", help="Name of an environment variable containing the client secret")
    parser.add_argument("--device-authorization-endpoint")
    parser.add_argument("--token-endpoint")
    parser.add_argument("--authorization-endpoint")
    parser.add_argument("--token-cache", help="Opt-in plaintext device-token cache")
    parser.add_argument("--no-reauthentication", action="store_true", help="Disallow interactive device approval")
    parser.add_argument("--pdf", action="store_true", help="Require HTTP 200, PDF content type, and PDF signature")
    parser.add_argument("--timeout", type=float, default=90, help="Download request timeout in seconds (default: 90)")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--overwrite", action="store_true", help="Explicitly replace existing document files")
    parser.add_argument("--no-completion-record", action="store_true",
                        help="Do not write per-document JSON completion records; new downloads cannot be verified for later skips")
    parser.add_argument("--allow-redirects", action="store_true", help="Allow same-origin redirects only")
    parser.add_argument("--results-csv", help="Sensitive URL/path and outcome report")
    parser.set_defaults(func=_run)


def _validate(args):
    """Validate all inputs before creating Auth (which can contact the issuer)."""
    if not math.isfinite(args.timeout) or args.timeout <= 0 or args.workers < 1:
        raise ValueError("--timeout must be positive and finite; --workers must be positive.")
    if (args.csv and args.document_id is not None) or (args.url and args.id_col is not None):
        raise ValueError("--document-id requires --url; --id-col requires --csv.")
    if args.csv and args.output:
        raise ValueError("--output requires --url; use --output-dir for CSV downloads.")
    if args.output and (Path(args.output).is_dir() or not Path(args.output).name):
        raise ValueError("--output must name a file.")
    if args.output_dir and Path(args.output_dir).exists() and not Path(args.output_dir).is_dir():
        raise ValueError("--output-dir must name a directory.")
    if args.results_csv:
        report = Path(args.results_csv).resolve()
        if report.is_dir() or any(report == Path(p).resolve() for p in (args.csv, args.output) if p):
            raise ValueError("--results-csv must be separate from the input CSV and document file.")
    if args.csv:
        frame = pd.read_csv(args.csv, dtype=str, keep_default_na=False)
        if args.url_col not in frame.columns:
            raise ValueError("The input CSV is missing the configured URL column.")
        ids = _document_ids(frame, args.id_col)
        urls = frame[args.url_col].tolist()
        if not urls:
            raise ValueError("The input CSV must contain at least one document URL.")
    else:
        urls = [args.url]
        ids = [None if args.document_id is None else _validate_document_id(args.document_id)]
    urls = [_resolve_document_url(url, args.base_url) for url in urls]

    auth_options = (args.auth_url, args.client_id, args.scope, args.client_secret_env,
                    args.device_authorization_endpoint, args.token_endpoint,
                    args.authorization_endpoint, args.token_cache, args.no_reauthentication)
    if args.auth_type == "none":
        if any(value is not None and value is not False for value in auth_options):
            raise ValueError("Authentication options require an explicit --auth-type.")
        return urls, ids, None
    if not args.client_id or not args.client_id.strip():
        raise ValueError("OIDC authentication requires --client-id.")
    if args.auth_type == "device_code":
        if not args.auth_url:
            raise ValueError("Device authentication requires --auth-url.")
        if bool(args.device_authorization_endpoint) != bool(args.token_endpoint):
            raise ValueError("Supply both device and token endpoints to bypass discovery.")
    else:
        if not args.auth_url and not args.token_endpoint:
            raise ValueError("Service accounts require --auth-url or --token-endpoint.")
        if any((args.device_authorization_endpoint, args.authorization_endpoint,
                args.token_cache, args.no_reauthentication)):
            raise ValueError("Device approval/cache options require --auth-type device_code.")
    for endpoint in (args.auth_url, args.device_authorization_endpoint,
                     args.token_endpoint, args.authorization_endpoint):
        if endpoint is not None:
            _oauth_url(endpoint)
    secret = os.environ.get(args.client_secret_env) if args.client_secret_env else None
    if args.client_secret_env and not secret:
        raise ValueError("The selected client-secret environment variable is empty or unset.")
    if args.auth_type == "client_credentials" and not secret:
        raise ValueError("Service accounts require --client-secret-env.")
    return urls, ids, secret


def _run(args):
    try:
        urls, ids, secret = _validate(args)
    except Exception as exc:
        # Do not echo parser, filesystem, or malformed-URL exception text.
        error_event(logger, "documents", exc)
        console_message("Invalid document-download inputs; check arguments and input files.",
                        level="error", color=args.color, quiet=args.quiet or args.json_log)
        return 2

    def instructions(value):
        # Required interactive instructions are displayed, never logged or put
        # into result reports. --quiet suppresses only nonessential messages.
        console_message(f"Sign in at {value['verification_uri']} with code {value['user_code']}",
                        level="info", color=args.color)

    try:
        with ExitStack() as stack:
            if args.auth_type == "device_code":
                auth = stack.enter_context(Auth(
                    auth_type="device_code", auth_url=args.auth_url, client_id=args.client_id,
                    client_secret=secret, scope=args.scope,
                    device_authorization_endpoint=args.device_authorization_endpoint,
                    token_endpoint=args.token_endpoint, authorization_endpoint=args.authorization_endpoint,
                    token_cache=args.token_cache, allow_reauthentication=not args.no_reauthentication,
                    device_code_callback=instructions,
                ))
            elif args.auth_type == "client_credentials":
                auth = stack.enter_context(Auth.client_credentials(
                    auth_url=args.auth_url, token_endpoint=args.token_endpoint,
                    client_id=args.client_id, client_secret=secret,
                    scope=args.scope if args.scope is not None else "",
                ))
            else:
                # Explicit anonymous mode must not inherit FHIR environment auth.
                auth = stack.enter_context(requests.Session())
            downloader = stack.enter_context(DocumentDownloader(
                auth=auth, output_dir=args.output_dir or (str(Path(args.output).parent) if args.output else "documents_out"),
                timeout=args.timeout, max_workers=args.workers, skip_existing=not args.overwrite,
                require_pdf=args.pdf, allow_redirects=args.allow_redirects,
                write_completion_record=not args.no_completion_record,
                flat_output=args.flat_output,
            ))
            if args.url:
                result = downloader.download_url(urls[0], output_path=args.output, document_id=ids[0])
                results = pd.DataFrame([result.__dict__])
            else:
                frame = pd.DataFrame({"document_url": urls, "document_id": ids})
                results = downloader.download_from_df(
                    frame, id_col="document_id" if args.id_col is not None else None,
                )
            if args.results_csv:
                report = Path(args.results_csv)
                # Resolved filenames can depend on response content types.
                if any(report.resolve() == Path(p).resolve() for p in results["path"]):
                    raise ValueError("Result report would overwrite a document.")
                report.parent.mkdir(parents=True, exist_ok=True)
                results.to_csv(report, index=False)
        failed = int(results["error"].notna().sum())
        skipped = int((results["error"].isna() & results["skipped"]).sum())
        succeeded = len(results) - failed - skipped
        if args.json_log:
            event(logger, "documents", "incomplete" if failed else "finished",
                  level=logging.ERROR if failed else logging.INFO,
                  total=len(results), succeeded=succeeded, skipped=skipped, failed=failed)
        else:
            console_message(f"Documents: {succeeded} succeeded, {skipped} skipped, {failed} failed.",
                            level="error" if failed else "success", color=args.color, quiet=args.quiet)
        return 1 if failed else 0
    except KeyboardInterrupt:
        event(logger, "documents", "incomplete", level=logging.ERROR)
        return 130
    except Exception as exc:
        error_event(logger, "documents", exc)
        return 1
