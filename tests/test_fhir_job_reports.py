"""Local socket acceptance for ordered parallel queries and pooled sessions."""

import json
import multiprocessing as mp
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlparse

import pandas as pd

from fyron import Auth, FHIRRestClient
from fyron.fhir._client_credentials import _ClientCredentialsAuth


def test_spawned_query_reports_sessions_and_metadata():
    ports = set()

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):
            pass

        def do_GET(self):
            ports.add(self.client_address[1])
            query = parse_qs(urlparse(self.path).query)
            identity = query["_id"][0]
            page = query.get("page", ["1"])[0]
            payload = {"resourceType": "Bundle", "entry": [{
                "resource": {"resourceType": "Patient", "id": identity + "-" + page}}]}
            if page == "1":
                payload["link"] = [{"relation": "next", "url": "?" + urlencode({"_id": identity, "page": 2})}]
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    children = {p.pid for p in mp.active_children()}
    try:
        payload = {"access_token": "synthetic", "token_type": "Bearer", "expires_in": 3600}
        with patch.object(_ClientCredentialsAuth, "_request", return_value=payload):
            with Auth.client_credentials(client_id="synthetic", client_secret="synthetic",
                    token_endpoint="https://identity.example.test/token") as auth:
                client = FHIRRestClient(base_url=f"http://127.0.0.1:{server.server_port}/fhir",
                    auth=auth, num_processes=2)
                inputs = pd.DataFrame({"source_key": ["a", "a", "b", "c"]}, index=[7, 2, 7, 9])
                kwargs = dict(df=inputs, resource_type="Patient", column_map={"_id": "source_key"},
                    include_column_map_columns=True, param_prefix={"_id": "Patient/"},
                    use_multiprocessing=False, show_progress=False, return_report=True)
                sequential = client.query_df_from(**kwargs)
                ports.clear()
                parallel = client.query_df_from(**kwargs, parallel_fetch=True)
                pd.testing.assert_frame_equal(sequential["data"], parallel["data"])
                pd.testing.assert_frame_equal(sequential["report"]["rows"], parallel["report"]["rows"])
                assert parallel["report"]["rows"].pages.tolist() == [2] * 4
                assert parallel["report"]["summary"].loc[0, "retrieval_exhaustive"]
                assert parallel["data"].source_key.tolist() == ["a", "a", "a", "a", "b", "b", "c", "c"]
                assert 1 <= len(ports) <= 2
                first_ports = set(ports)
                ports.clear()
                client.query_df_from(**kwargs, parallel_fetch=True)
                assert not ports.intersection(first_ports)
                assert not ({p.pid for p in mp.active_children()} - children)
        assert not any(t.name.startswith("fyron-token-") for t in threading.enumerate())
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
