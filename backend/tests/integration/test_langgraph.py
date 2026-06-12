import pytest
from backend.app.rag.nodes import retrieval_node, generate_node
from backend.app.core.custom_exception import DocumentPortalException
from unittest.mock import MagicMock

def test_retrieval_node_execution(db_session, test_user, mocker):
    # Mock embedding framework and raw repository adapters
    mocker.patch("backend.app.rag.nodes.embed_text", return_value=[0.05] * 384)
    mocker.patch("backend.app.rag.nodes.chunks_retrieval", return_value=[
        MagicMock(content="Retrieved Document Chunk text context string", content_metadata={})
    ])
    mocker.patch("backend.app.rag.nodes.memories_retrieval", return_value=[
        MagicMock(content='{"conversation_summary": "Historical profile note clue"}')
    ])

    # Build initial LangGraph workflow state schema dictionary
    initial_state = {
        "user_id": str(test_user.id),
        "document_id": "00000000-0000-0000-0000-000000000000",
        "user_question": "What is the attention mechanism parameter matrix?",
        "chat_history": [],
        "retrieved_chunks": None,
        "recalled_memories": None,
        "generated_answer": None
    }

    # Execute state manipulation logic step execution inside isolated session frame
    mocker.patch("backend.app.rag.nodes.SessionLocal", return_value=db_session)
    updated_state = retrieval_node(initial_state)

    assert len(updated_state["retrieved_chunks"]) == 1
    assert updated_state["retrieved_chunks"][0] == "Retrieved Document Chunk text context string"
    assert updated_state["recalled_memories"][0]["conversation_summary"] == "Historical profile note clue"

def test_retrieval_node_fault_propagation(mocker):
    # Mock an internal operation to force execution into the try/except block
    mocker.patch("backend.app.rag.nodes.embed_text", side_effect=Exception("Embedding pipeline timeout"))
    
    faulty_state = {
        "user_id": "00000000-0000-0000-0000-000000000000",
        "document_id": "00000000-0000-0000-0000-000000000000",
        "user_question": "Error check trigger string",
        "chat_history": [],
        "retrieved_chunks": None,
        "recalled_memories": None,
        "generated_answer": None
    }
    
    with pytest.raises(DocumentPortalException):
        retrieval_node(faulty_state)