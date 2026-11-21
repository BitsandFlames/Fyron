"""Reconcile five synthetic patients and retry just one failed document offline."""
import io
import json
from unittest.mock import patch

import pandas as pd
import requests
from fyron import FHIRRestClient, FHIRSQLClient, LLMAgent

COHORT = pd.DataFrame({"patient_id": ["001", "002", "003", "004", "005"]})
INDEX = pd.DataFrame([
    ("001", "a"), ("003", "b"), ("004", "c"), ("005", "d"), ("005", "e"),
], columns=["patient_id", "doc_id"])
ROOT = "https://demo.invalid/"
INDEX["url"] = ROOT + INDEX.doc_id
PROMPTS = [{"name": "extract", "prompt": "Extract the follow-up recommendation."},
           {"name": "summary", "prompt": "Summarize the available recommendations."}]


class Fixture(requests.adapters.BaseAdapter):
    recovered = False

    def send(self, request, **kwargs):
        response = requests.Response()
        response.request, response.url, response.status_code = request, request.url, 200
        if "/DocumentReference" in request.url:
            entries = [{"resource": {"resourceType": "DocumentReference", "id": doc,
                        "subject": {"reference": "Patient/" + patient},
                        "content": [{"attachment": {"url": url}}]}}
                       for patient, doc, url in INDEX.itertuples(index=False, name=None)]
            body = json.dumps({"resourceType": "Bundle", "type": "searchset", "entry": entries}).encode()
            response.headers["Content-Type"] = "application/fhir+json"
        else:
            doc = request.url.removeprefix(ROOT)
            if doc == "b" and not self.recovered:
                response.status_code = 404
            body = b" " if doc in {"c", "e"} else b"Follow up in six weeks."
            response.headers["Content-Type"] = "text/plain"
        response.raw = io.BytesIO(body)
        return response

    def close(self):
        pass


def retrieve(route, session):
    if route == "rest":
        with FHIRRestClient(base_url=ROOT, auth=session) as client:
            result = client.search_df("DocumentReference", return_report=True, use_multiprocessing=False,
                fhir_paths=[("owner", "subject.reference"), ("doc_id", "id"), ("url", "content.attachment.url")])
        assert result["report"]["summary"].iloc[0]["retrieval_exhaustive"]
        data = result["data"]
        return data.assign(patient_id=data.owner.str.removeprefix("Patient/")).drop(columns="owner")
    # Mock only the database call. Fyron still builds and binds the cohort keys.
    with patch.object(FHIRSQLClient, "_connect"), FHIRSQLClient() as client:
        with patch.object(client, "query_df", side_effect=lambda sql, params: INDEX[INDEX.patient_id.isin(params.values())]):
            return client.query_df_for_keys(COHORT, "SELECT patient_id, doc_id, url FROM reports WHERE patient_id IN ({cohort_keys})",
                                            key_columns=["patient_id"])


def reconcile(records, answers, summaries):
    counts = records.groupby("patient_id").agg(records_found=("doc_id", "size"), documents_expected=("doc_id", "nunique"))
    read = answers[answers.status.eq("ok")].groupby("patient_id").doc_id.nunique().rename("documents_read")
    table = COHORT.join(counts, on="patient_id").join(read, on="patient_id")
    for key in ("records_found", "documents_expected", "documents_read"):
        table[key] = table[key].fillna(0).astype(int)
    table = table.merge(summaries[["patient_id", "status", "reason"]], how="left", validate="one_to_one")
    table["summary_status"] = table.pop("status").fillna("no_matching_records")
    return table


def walkthrough(route):
    with requests.Session() as session:
        fixture = Fixture()
        session.mount("https://", fixture)
        records = retrieve(route, session)
        agent = LLMAgent(provider="custom", base_url=ROOT, auth_required=False)
        def extract(frame):
            return agent.run_prompts_on_dataframe(frame, url_col="url", document_id_col="doc_id",
                keep_cols=["patient_id", "doc_id"], document_auth=session, document_origin=ROOT,
                prompts=PROMPTS, prompt_names=["extract"])
        def summarize(frame):
            return agent.summarize_dataframe(frame, group_cols=["patient_id"], prompts=PROMPTS,
                                             prompt_names=["summary"], source_prompt_names=["extract"])
        with agent.session, patch.object(agent, "prompt", return_value="Follow up in six weeks."):
            answers = extract(records)
            summaries = summarize(answers)
            before = reconcile(records, answers, summaries)

            retry = answers[answers.reason.eq("download_failed")]
            assert retry.doc_id.tolist() == ["b"]
            fixture.recovered = True
            replacement = extract(records[records.doc_id.isin(retry.doc_id)])
            keys = ["doc_id", "prompt_name"]
            keep = ~answers.set_index(keys).index.isin(replacement.set_index(keys).index)
            answers = pd.concat([answers[keep], replacement], ignore_index=True)
            affected = replacement.patient_id.unique()
            summaries = pd.concat([summaries[~summaries.patient_id.isin(affected)],
                                   summarize(answers[answers.patient_id.isin(affected)])])
            return before, reconcile(records, answers, summaries)


if __name__ == "__main__":
    original, recovered = walkthrough("rest")
    for rest, sql in zip((original, recovered), walkthrough("sql")):
        pd.testing.assert_frame_equal(rest, sql)
    assert original.summary_status.tolist() == ["ok", "no_matching_records", "incomplete", "incomplete", "incomplete"]
    assert recovered.documents_read.tolist() == [1, 0, 1, 0, 1]
    assert recovered.summary_status.tolist() == ["ok", "no_matching_records", "ok", "incomplete", "incomplete"]
    assert recovered.reason.iloc[3:].tolist() == ["empty_text", "empty_text"]
    print(original.to_string(index=False))
    print("\nAfter retrying document b")
    print(recovered.to_string(index=False))
