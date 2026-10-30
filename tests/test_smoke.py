import fyron
from fyron import Auth, DICOMDownloader, DocumentDownloader, FHIRRestClient, LLMAgent


def test_package_version():
    assert isinstance(fyron.__version__, str)


def test_auth_init():
    auth = Auth(auth_type=None, auth_method=None)
    assert auth.session is not None


def test_fhir_rest_client_init():
    client = FHIRRestClient(base_url="https://example.org/fhir")
    assert client.base_url


def test_llm_agent_init():
    agent = LLMAgent(provider="custom", base_url="http://localhost:9999", auth_required=False)
    assert agent.config.provider == "custom"


def test_document_downloader_init(tmp_path):
    docs = DocumentDownloader(output_dir=tmp_path)
    assert docs.output_dir.exists()


def test_dicom_downloader_init():
    dicom = DICOMDownloader(dicom_web_url="http://localhost:9999/dicomweb")
    assert dicom.dicom_web_url
