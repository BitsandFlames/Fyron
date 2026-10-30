"""Row-level progress for sequential FHIR extraction."""

from unittest.mock import Mock

import pandas as pd
import pytest

from fyron.fhir import rest


@pytest.mark.parametrize("method", ["query_from_dataframe", "query_df_from", "search_df_from"])
@pytest.mark.parametrize("visible", [True, False])
def test_sequential_progress(monkeypatch, method, visible):
    client = object.__new__(rest.FHIRRestClient)
    client.num_processes = 1
    client.log_requests = False
    progress = Mock()
    factory = Mock(return_value=progress)
    monkeypatch.setattr(rest, "tqdm", factory)

    def fetch(**kwargs):
        assert kwargs["show_progress"] is False
        expected = 0 if kwargs["params"]["_id"] == "synthetic-a" else 1
        assert progress.update.call_count == expected
        yield {"resourceType": "Bundle", "entry": []}
        assert progress.update.call_count == expected
        yield {"resourceType": "Bundle", "entry": []}

    client.fetch_bundles = fetch
    client.bundles_to_dataframe = Mock(return_value=pd.DataFrame())
    getattr(client, method)(
        pd.DataFrame({"patient": ["synthetic-a", "synthetic-b"]}),
        "Patient", {"_id": "patient"}, parallel_fetch=True,
        include_column_map_columns=True, show_progress=visible,
    )
    assert factory.call_args.kwargs["total"] == 2
    assert factory.call_args.kwargs["disable"] is (not visible)
    assert progress.update.call_count == 2
    progress.close.assert_called_once()
    assert len(client.bundles_to_dataframe.call_args.kwargs["bundles"]) == 4
    assert len(client.bundles_to_dataframe.call_args.kwargs["per_bundle_metadata"]) == 4


def test_progress_closes_on_failure(monkeypatch):
    client = object.__new__(rest.FHIRRestClient)
    client.num_processes = 1
    client.log_requests = False
    progress = Mock()
    monkeypatch.setattr(rest, "tqdm", Mock(return_value=progress))
    client.fetch_bundles = Mock(side_effect=RuntimeError("synthetic failure"))
    with pytest.raises(RuntimeError, match="synthetic failure"):
        client.query_df_from(pd.DataFrame({"patient": ["a"]}), "Patient", {"_id": "patient"})
    progress.update.assert_not_called()
    progress.close.assert_called_once()


def test_parallel_progress_option():
    client = object.__new__(rest.FHIRRestClient)
    client.num_processes = 2
    client.log_requests = False
    client._fetch_parallel_jobs = Mock(return_value=[(0, [])])
    client.bundles_to_dataframe = Mock(return_value=pd.DataFrame())
    client.query_df_from(pd.DataFrame({"patient": ["a"]}), "Patient", {"_id": "patient"},
                         parallel_fetch=True, show_progress=False)
    assert client._fetch_parallel_jobs.call_args.kwargs["show_progress"] is False
