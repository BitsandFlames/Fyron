from __future__ import annotations

import ast
import re
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import Mock

import pandas as pd
import pytest

from fyron import FHIRRestClient, audit, clinical_codes, dataframe, ml, plotting, preprocessing
from fyron.fhir import build_partition_params, rest as rest_module
from fyron.fhir.auth import TokenAuth
from fyron.fhir.rest import FHIRRequestError
from fyron.fhir.sql import FHIRSQLClient, build_sql_partitions
from fyron.fhir.types import FHIRObj

ROOT = Path(__file__).resolve().parents[1]


def _read_optional_dependencies() -> dict[str, list[str]]:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    lines = text.splitlines()
    in_section = False
    current_name: str | None = None
    current_value: list[str] = []
    optional: dict[str, list[str]] = {}

    for line in lines:
        stripped = line.strip()
        if stripped == "[project.optional-dependencies]":
            in_section = True
            continue
        if in_section and stripped.startswith("[") and stripped.endswith("]"):
            break
        if not in_section or not stripped or stripped.startswith("#"):
            continue

        if current_name is not None:
            current_value.append(stripped)
            if stripped.endswith("]"):
                optional[current_name] = ast.literal_eval(" ".join(current_value))
                current_name = None
                current_value = []
            continue

        name, value = stripped.split("=", 1)
        name = name.strip()
        value = value.strip()
        if value.startswith("[") and not value.endswith("]"):
            current_name = name
            current_value = [value]
        else:
            optional[name] = ast.literal_eval(value)

    return optional


def test_top_level_example_imports_are_available():
    assert FHIRRestClient is not None
    assert ml is not None
    assert preprocessing is not None
    assert clinical_codes is not None
    assert dataframe is not None
    assert plotting is not None
    assert audit is not None


def test_repository_trust_files_exist_and_are_linked():
    required = [
        "CITATION.cff",
        "SECURITY.md",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/ISSUE_TEMPLATE/feature_request.md",
        ".github/ISSUE_TEMPLATE/documentation.md",
        ".github/ISSUE_TEMPLATE/clinical_workflow.md",
    ]
    for rel_path in required:
        path = ROOT / rel_path
        assert path.exists(), f"Missing repository trust file: {rel_path}"
        assert path.read_text(encoding="utf-8").strip(), f"Empty repository trust file: {rel_path}"

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "CITATION.cff" in readme
    assert 'href="https://fyron.bitsandflames.ai/"' in readme
    assert "https://github.com/BitsandFlames/Fyron/blob/" in readme
    assert "/LICENSE" in readme


def test_api_design_docs_capture_public_conventions():
    api_design = (ROOT / "docs" / "api-design.md").read_text(encoding="utf-8")
    expected_phrases = [
        "DataFrame-first",
        "(fig, ax)",
        "(fig, axes, table)",
        "Optional Dependencies",
        "Stable And Experimental APIs",
        "Deprecation Policy",
        "No hidden upload",
    ]
    for phrase in expected_phrases:
        assert phrase in api_design


def test_priority_module_docs_include_api_contracts():
    module_pages = [
        "modules/fhir/rest.md",
        "modules/dicom/downloader.md",
        "modules/boa-extraction.md",
        "modules/clinical-codes.md",
        "modules/dataframe.md",
        "modules/cohort.md",
        "modules/preprocessing.md",
        "modules/descriptive.md",
        "modules/statistics.md",
        "modules/survival.md",
        "modules/ml.md",
        "modules/validation.md",
        "modules/explainability.md",
        "modules/flow.md",
        "modules/datasets.md",
        "modules/plotting.md",
        "modules/visualization.md",
        "modules/reporting.md",
        "modules/audit.md",
    ]
    required_terms = ["Input shape", "Required", "Return shape", "Saved artifacts", "Failure modes"]
    for rel_path in module_pages:
        text = (ROOT / "docs" / rel_path).read_text(encoding="utf-8")
        assert "## API Contract" in text, f"{rel_path} is missing an API Contract section"
        for term in required_terms:
            assert term in text, f"{rel_path} API Contract is missing {term!r}"


def test_generated_reference_uses_professional_missing_docstring_language():
    reference_dir = ROOT / "docs" / "reference"
    reference_files = list(reference_dir.glob("*.md"))
    assert reference_files, "Generated reference files are missing"
    combined = "\n".join(path.read_text(encoding="utf-8") for path in reference_files)
    assert "No description available" not in combined
    coverage = (reference_dir / "docstring-coverage.md").read_text(encoding="utf-8")
    assert "Docstring Coverage Report" in coverage
    assert "Priority public-beta APIs with incomplete docstring coverage" in coverage
    assert "Full generated backlog" in coverage
    match = re.search(r"Priority public-beta APIs with incomplete docstring coverage: \*\*(\d+)\*\*", coverage)
    assert match, "Docstring coverage report is missing the priority public-beta count"
    assert int(match.group(1)) < 150
    assert "Documentation pending for this public API." in combined or "incomplete docstring coverage" in combined


def test_public_beta_ci_smoke_checks_are_documented():
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    optional = (ROOT / ".github" / "workflows" / "optional-extras.yml").read_text(encoding="utf-8")

    assert "scripts/check_wheel.py" in ci
    assert "actions/download-artifact@v4" in ci
    probe = (ROOT / "scripts" / "wheel_probe.py").read_text(encoding="utf-8")
    assert '"curate", "--help"' in probe
    assert "scripts/wheel_matrix.py" in optional
    assert "scripts/check_wheel.py" in optional
    assert "workflow_dispatch" in optional
    assert "schedule:" in optional


def test_dataframe_reference_has_complete_docstrings():
    reference = (ROOT / "docs" / "reference" / "cohort-analysis.md").read_text(encoding="utf-8")
    dataframe_section = reference.split("## `fyron.dataframe.add_code_indicators`", 1)[1]
    dataframe_section = dataframe_section.split("## `fyron.descriptive", 1)[0]

    assert "Not documented yet" not in dataframe_section
    assert "Documentation pending for this public API." not in dataframe_section
    assert "`pandas.DataFrame` - Copy of ``df``" in dataframe_section
    assert "`str or None` - Broad disease group name" in dataframe_section


def test_priority_dicom_and_cohort_reference_sections_are_documented():
    dicom_reference = (ROOT / "docs" / "reference" / "dicom-imaging.md").read_text(
        encoding="utf-8"
    )
    dicom_section = dicom_reference.split("## `fyron.dicom.client.DICOMDownloader`", 1)[1]
    dicom_section = dicom_section.split("## `fyron.dicom.seg", 1)[0]

    cohort_reference = (ROOT / "docs" / "reference" / "cohort-analysis.md").read_text(
        encoding="utf-8"
    )
    cohort_section = cohort_reference.split("## `fyron.cohort.tables.build_survival_columns`", 1)[1]
    cohort_section = cohort_section.split("## `fyron.dataframe", 1)[0]

    assert "Not documented yet" not in dicom_section
    assert "Documentation pending for this public API." not in dicom_section
    assert "Not documented yet" not in cohort_section
    assert "Documentation pending for this public API." not in cohort_section


def test_readme_example_imports_remain_available():
    from fyron import FHIRRestClient as _FHIRRestClient
    from fyron import dataframe as _dataframe
    from fyron import ml as _ml
    from fyron.audit import analysis_run_manifest, write_manifest
    from fyron.cohort import build_time_to_event_endpoint, cohort_profile
    from fyron.explainability import explain_model_summary
    from fyron.fhir import get_fhir_path_preset
    from fyron.flow import FlowTracker, track_filter
    from fyron.statistics import fit_logistic_regression_table, p_value_correction_table
    from fyron.survival import fit_multivariate_cox, plot_kaplan_meier, schoenfeld_test_table
    from fyron.validation import bootstrap_classification_metrics

    assert _FHIRRestClient is not None
    assert _dataframe is not None
    assert get_fhir_path_preset is not None
    assert build_time_to_event_endpoint is not None
    assert cohort_profile is not None
    assert fit_logistic_regression_table is not None
    assert p_value_correction_table is not None
    assert plot_kaplan_meier is not None
    assert fit_multivariate_cox is not None
    assert schoenfeld_test_table is not None
    assert FlowTracker is not None
    assert track_filter is not None
    assert _ml is not None
    assert explain_model_summary is not None
    assert bootstrap_classification_metrics is not None
    assert analysis_run_manifest is not None
    assert write_manifest is not None


def test_optional_extra_install_message_policy_is_documented():
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    api_design = (ROOT / "docs" / "api-design.md").read_text(encoding="utf-8")
    assert 'uv add "fyron[' in contributing
    assert 'uv add "fyron[' in api_design


def test_all_extra_includes_every_declared_feature_dependency():
    optional = _read_optional_dependencies()
    all_deps = set(optional["all"])
    excluded_aliases = {"all", "reporting", "audit"}

    for extra_name, dependencies in optional.items():
        if extra_name in excluded_aliases:
            continue
        missing = set(dependencies) - all_deps
        assert not missing, f"fyron[all] is missing dependencies from fyron[{extra_name}]: {sorted(missing)}"

    heavy_extras = {
        "survival-ml",
        "dicom-seg",
        "radiomics",
        "visualization",
        "explainability",
        "boruta",
    }
    for extra_name in heavy_extras:
        assert set(optional[extra_name]).issubset(all_deps), f"fyron[all] omits heavy extra: {extra_name}"


def test_fhir_rest_friendly_aliases_are_available():
    assert hasattr(FHIRRestClient, "search_df")
    assert hasattr(FHIRRestClient, "search_df_from")
    assert hasattr(FHIRRestClient, "search_df_partitioned")
    assert hasattr(FHIRRestClient, "query_df")
    assert hasattr(FHIRRestClient, "query_df_from")
    assert hasattr(FHIRRestClient, "query_df_partitioned")


def test_fhir_sql_partitioned_helpers_are_available():
    assert callable(build_sql_partitions)
    assert hasattr(FHIRSQLClient, "query_df_partitioned")
    assert hasattr(FHIRSQLClient, "export_query_partitioned")


def test_search_df_delegates_to_query_to_dataframe():
    client = FHIRRestClient("https://example.org/fhir")
    client.query_to_dataframe = Mock(return_value=pd.DataFrame({"id": ["p1"]}))  # type: ignore[method-assign]

    result = client.search_df(
        "Patient",
        params={"_count": 1},
        max_pages=1,
        use_multiprocessing=False,
    )

    assert list(result["id"]) == ["p1"]
    client.query_to_dataframe.assert_called_once_with(
        resource_type="Patient",
        params={"_count": 1},
        max_pages=1,
        process_function=None,
        fhir_paths=None,
        mode="flatten",
        use_multiprocessing=False,
        parallel_params=None,
        return_report=False,
    )


def test_search_df_from_delegates_to_query_from_dataframe():
    client = FHIRRestClient("https://example.org/fhir")
    cohort = pd.DataFrame({"patient_id": ["Patient/p1"]})
    client.query_from_dataframe = Mock(return_value=pd.DataFrame({"id": ["obs1"]}))  # type: ignore[method-assign]

    result = client.search_df_from(
        cohort,
        resource_type="Observation",
        column_map={"subject": "patient_id"},
        params={"code": "http://loinc.org|718-7"},
        max_pages=1,
        include_column_map_columns=True,
    )

    assert list(result["id"]) == ["obs1"]
    client.query_from_dataframe.assert_called_once_with(
        df=cohort,
        resource_type="Observation",
        column_map={"subject": "patient_id"},
        params={"code": "http://loinc.org|718-7"},
        max_pages=1,
        process_function=None,
        fhir_paths=None,
        mode="flatten",
        use_multiprocessing=True,
        parallel_fetch=False,
        param_prefix=None,
        include_column_map_columns=True,
        show_progress=True,
        return_report=False,
    )


def test_fetch_bundles_paginates_when_returning_fhir_objects(monkeypatch):
    calls = []
    pages = [
        {
            "resourceType": "Bundle",
            "type": "searchset",
            "entry": [{"resource": {"resourceType": "Patient", "id": "p1"}}],
            "link": [{"relation": "next", "url": "Patient?_page=2"}],
        },
        {
            "resourceType": "Bundle",
            "type": "searchset",
            "entry": [{"resource": {"resourceType": "Patient", "id": "p2"}}],
        },
    ]

    def fake_request_json(**kwargs):
        calls.append(kwargs["url"])
        page = pages[len(calls) - 1]
        return page, f"https://example.org/fhir/{kwargs['url']}", 200, 1.0

    monkeypatch.setattr(rest_module, "_request_json", fake_request_json)
    client = FHIRRestClient("https://example.org/fhir", return_fhir_obj=True)

    bundles = list(client.fetch_bundles("Patient", max_pages=2, show_progress=False))

    assert len(bundles) == 2
    assert all(isinstance(bundle, FHIRObj) for bundle in bundles)
    assert bundles[0].entry[0].resource.id == "p1"
    assert bundles[1].entry[0].resource.id == "p2"


def test_fetch_bundles_rejects_non_object_response(monkeypatch):
    def fake_request_json(**kwargs):
        return None, "https://example.org/fhir/Patient", 200, 1.0

    monkeypatch.setattr(rest_module, "_request_json", fake_request_json)
    client = FHIRRestClient("https://example.org/fhir")

    with pytest.raises(FHIRRequestError, match="must be a JSON object"):
        list(client.fetch_bundles("Patient", max_pages=1, show_progress=False))


def test_parallel_token_auth_prefers_worker_refresh_when_env_credentials_exist(monkeypatch):
    captured_jobs = []

    class FakePool:
        def __init__(self, processes):
            self.processes = processes

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, exc_tb):
            return None

        def imap_unordered(self, func, jobs):
            captured_jobs.extend(jobs)
            return [(0, [{"resourceType": "Bundle", "type": "searchset", "entry": []}])]

    session = rest_module.requests.Session()
    session.auth = TokenAuth(
        username="",
        password="",
        auth_url="",
        token="parent-token",
        session=session,
    )
    monkeypatch.setenv("FHIR_USER", "worker-user")
    monkeypatch.setenv("FHIR_PASSWORD", "worker-password")
    monkeypatch.setattr(rest_module, "managed_pool", lambda *args: nullcontext((FakePool(2), None)))
    monkeypatch.setattr(rest_module, "monitored_results", lambda pool, events, func, jobs, timeout: pool.imap_unordered(func, jobs))

    client = FHIRRestClient(
        "https://example.org/fhir",
        auth_url="https://example.org/token",
        auth=session,
        num_processes=2,
    )

    bundles = list(client.fetch_bundles_parallel("Patient", [{"_count": 1}], show_progress=False))

    assert len(bundles) == 1
    job_args = captured_jobs[0]
    headers = job_args[2]
    auth_mode = job_args[7]
    auth_url = job_args[8]
    assert auth_mode == "token_env"
    assert auth_url == "https://example.org/token"
    assert "Authorization" not in headers


def test_parallel_token_auth_uses_static_bearer_without_worker_credentials(monkeypatch):
    captured_jobs = []

    class FakePool:
        def __init__(self, processes):
            self.processes = processes

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, exc_tb):
            return None

        def imap_unordered(self, func, jobs):
            captured_jobs.extend(jobs)
            return [(0, [{"resourceType": "Bundle", "type": "searchset", "entry": []}])]

    session = rest_module.requests.Session()
    session.auth = TokenAuth(
        username="",
        password="",
        auth_url="",
        token="parent-token",
        session=session,
    )
    monkeypatch.delenv("FHIR_USER", raising=False)
    monkeypatch.delenv("FHIR_PASSWORD", raising=False)
    monkeypatch.setattr(rest_module, "managed_pool", lambda *args: nullcontext((FakePool(2), None)))
    monkeypatch.setattr(rest_module, "monitored_results", lambda pool, events, func, jobs, timeout: pool.imap_unordered(func, jobs))

    client = FHIRRestClient(
        "https://example.org/fhir",
        auth_url="https://example.org/token",
        auth=session,
    )

    list(client.fetch_bundles_parallel("Patient", [{"_count": 1}], show_progress=False))

    job_args = captured_jobs[0]
    headers = job_args[2]
    auth_mode = job_args[7]
    assert auth_mode == "bearer"
    assert headers["Authorization"] == "Bearer parent-token"


def test_token_auth_retries_auth_like_bad_request(monkeypatch):
    session = rest_module.requests.Session()
    auth = TokenAuth(
        username="",
        password="",
        auth_url="",
        token="expired-token",
        session=session,
    )
    auth._set_token = Mock(side_effect=lambda token: setattr(auth, "_token", token))  # type: ignore[method-assign]
    monkeypatch.setattr(auth, "_refresh", Mock(side_effect=lambda: auth._set_token("fresh-token")))

    request = rest_module.requests.Request("GET", "https://example.org/fhir/Patient").prepare()
    response = rest_module.requests.Response()
    response.status_code = 400
    response._content = b'{"error":"expired access token"}'
    response.request = request

    resent = rest_module.requests.Response()
    resent.status_code = 200
    resent._content = b'{"resourceType":"Bundle"}'
    monkeypatch.setattr(session, "send", Mock(return_value=resent))

    result = auth._refresh_hook(response)

    assert result is resent
    assert auth._refresh.call_count == 1
    assert session.send.call_count == 1
    sent_request = session.send.call_args.args[0]
    assert sent_request.headers["Authorization"] == "Bearer fresh-token"


def test_token_auth_does_not_retry_plain_bad_request(monkeypatch):
    session = rest_module.requests.Session()
    auth = TokenAuth(
        username="",
        password="",
        auth_url="",
        token="valid-token",
        session=session,
    )
    monkeypatch.setattr(auth, "_refresh", Mock())
    monkeypatch.setattr(session, "send", Mock())

    request = rest_module.requests.Request("GET", "https://example.org/fhir/Procedure").prepare()
    response = rest_module.requests.Response()
    response.status_code = 400
    response._content = b'{"resourceType":"OperationOutcome","issue":[{"diagnostics":"Unknown search parameter"}]}'
    response.request = request

    result = auth._refresh_hook(response)

    assert result is response
    assert auth._refresh.call_count == 0
    assert session.send.call_count == 0


def test_request_json_omits_operation_outcome_diagnostics():
    class FailingSession:
        auth = None
        headers = {}

        def get(self, url, timeout):
            response = rest_module.requests.Response()
            response.status_code = 400
            response.url = url
            response._content = (
                b'{"resourceType":"OperationOutcome",'
                b'"issue":[{"diagnostics":"Reference value must include resource type"}]}'
            )
            error = rest_module.requests.HTTPError("400 Client Error", response=response)
            raise error

    with pytest.raises(FHIRRequestError, match="HTTP 400") as caught:
        rest_module._request_json(
            session=FailingSession(),
            url="https://example.org/fhir/Procedure",
            params={"encounter": "abc"},
            timeout=30,
            log=None,
        )
    assert "Reference value" not in str(caught.value)
    assert "example.org" not in str(caught.value)
    assert caught.value.__suppress_context__


def test_build_partition_params_uses_repeated_fhir_date_bounds():
    partitions = build_partition_params(
        {"_count": 500, "code": ["C34", "C34.9"]},
        partition_param="recorded-date",
        start="2020-01-01",
        end="2022-01-01",
        frequency="YS",
    )

    assert len(partitions) == 2
    query_sequence = rest_module._params_to_query_sequence(partitions[0])
    assert ("code", "C34,C34.9") in query_sequence
    assert ("recorded-date", "ge2020-01-01") in query_sequence
    assert ("recorded-date", "lt2021-01-01") in query_sequence


def test_search_df_partitioned_adds_sort_and_partition_metadata(monkeypatch):
    client = FHIRRestClient("https://example.org/fhir")
    captured_params = []

    def fake_fetch_bundles(**kwargs):
        params = kwargs["params"]
        captured_params.append(params)
        index = len(captured_params)
        yield {
            "resourceType": "Bundle",
            "type": "searchset",
            "entry": [
                {
                    "resource": {
                        "resourceType": "Condition",
                        "id": f"c{index}",
                        "recordedDate": f"202{index}-01-15",
                    }
                }
            ],
        }

    monkeypatch.setattr(client, "fetch_bundles", fake_fetch_bundles)

    result = client.search_df_partitioned(
        "Condition",
        partition_param="recorded-date",
        start="2020-01-01",
        end="2022-01-01",
        params={"_count": 500},
        frequency="YS",
        use_multiprocessing=False,
        show_progress=False,
    )

    assert list(result["id"]) == ["c1", "c2"]
    assert captured_params[0]["_sort"] == "_id"
    first_bounds = rest_module._params_to_query_sequence(captured_params[0])
    assert ("recorded-date", "ge2020-01-01") in first_bounds
    assert ("recorded-date", "lt2021-01-01") in first_bounds
    assert list(result["_fyron_partition_start"]) == ["2020-01-01", "2021-01-01"]
    assert list(result["_fyron_partition_end"]) == ["2021-01-01", "2022-01-01"]


def test_documentation_release_pages_support_beta_versions():
    import runpy

    sort_key = runpy.run_path(str(ROOT / "scripts" / "build_docs.py"))["release_sort_key"]
    versions = ["v0.3.20", "v0.3.20b10", "v0.3.19", "v0.3.20rc1", "v0.3.20b2", "v0.3.20a1"]
    assert sorted(versions, key=lambda version: sort_key(Path(version + ".md"))) == [
        "v0.3.19", "v0.3.20a1", "v0.3.20b2", "v0.3.20b10", "v0.3.20rc1", "v0.3.20",
    ]


def test_imaging_navigation_is_separate_from_body_and_organ_analysis():
    import runpy

    docs = runpy.run_path(str(ROOT / "scripts" / "build_docs.py"))
    pages = {page.output: page for page in docs["PAGES"]}
    imaging = pages["modules/imaging/index.html"]
    assert imaging.group == "Imaging"
    assert pages["modules/boa/index.html"].group == "Body and Organ Analysis"
    anchors = dict(docs["SECTION_NAV"][imaging.output])
    assert anchors["CT normalization · normalize_ct"] == "normalizect"
    assert anchors["MRI normalization · normalize_mr"] == "normalizemr"
    for anchor in ["readdicomheader", "getdicomseriesids", "readdicomseries", "readnifti", "writenifti"]:
        assert anchor in anchors.values()


def test_curate_guides_navigation_and_nested_asset_links():
    import runpy

    docs = runpy.run_path(str(ROOT / "scripts" / "build_docs.py"))
    pages = docs["PAGES"]
    groups = list(dict.fromkeys(page.group for page in pages))
    assert groups[groups.index("Audit & Provenance") + 1] == "Curate"
    assert "Applications" not in groups
    curate = [page for page in pages if page.group == "Curate"]
    assert [page.title for page in curate] == [
        "Overview", "Start the app", "Prepare your data", "Review & export",
    ]
    review = next(page for page in curate if "review-export" in page.source)
    assert docs["rewrite_href"]("../../assets/curate-synthetic-zen.png", review) == (
        "../../../assets/curate-synthetic-zen.png"
    )
