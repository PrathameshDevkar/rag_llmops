
def test_embed_text_success(mocker):
    """mock the langchain embedding model instancequery framwork"""
    mock_model = mocker.patch("backend.app.services.embeddings.embedding_model")
    mock_model.embed_query.return_value = [0.1, -0.2, 0.35, 0.9]
    
    from backend.app.services.embeddings import embed_text

    vector  = embed_text("What is attention mechanism?")
    assert isinstance(vector, list)
    assert len(vector) == 4
    assert vector[0] == 0.1
    mock_model.embed_query.assert_called_once_with("What is attention mechanism?")
    
def test_embed_text_exception_handling(mocker):
    mock_model = mocker.patch("backend.app.services.embeddings.embedding_model")
    mock_model.embed_query.side_effect = Exception("HuggingFace connection error")
        
    from backend.app.services.embeddings import embed_text

    vector = embed_text("Fallback test string")
    assert vector == []