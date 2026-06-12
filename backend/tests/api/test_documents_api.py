import pytest
from io import BytesIO
from unittest.mock import MagicMock

def test_upload_document_success(client, auth_token, mocker):
    #mock docling loader and embedding transformations
    mock_lc_doc = MagicMock()
    mock_lc_doc.page_content = "this is production rag testing chunk sample content"
    mock_lc_doc.metadata = {"heading":"Introduction"}
    mocker.patch("backend.app.api.documents.load_and_chunk_pdf", return_value = [mock_lc_doc])
    mocker.patch("backend.app.api.documents.embed_text", return_value = [0.1]*384)
    mocker.patch("os.makedirs")
    mocker.patch("builtins.open", mocker.mock_open())
    mocker.patch("shutil.copyfileobj")

    headers = {"Authorization": f"Bearer {auth_token}"}
    pdf_file = {"file": ("sample.pdf", BytesIO(b"%PDF-1.4 mock content"), "application/pdf")}
    
    response = client.post("/documents/upload", headers=headers, files=pdf_file)
    assert response.status_code == 200
    
    data = response.json()
    assert "document_id" in data
    assert data["filename"] == "sample.pdf"
    
def test_upload_document_invalid_type(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    txt_file = {"file": ("malicious.txt", BytesIO(b"not a pdf"), "text/plain")}
    
    response = client.post("/documents/upload", headers=headers, files=txt_file)
    assert response.status_code == 400
    assert "only PDF files are allowed" in response.json()["detail"]