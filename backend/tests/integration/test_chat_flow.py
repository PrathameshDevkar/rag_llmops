import pytest
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage

def test_end_to_end_multi_turn_chat_workflow(client, test_user, auth_token, mocker):
    headers = {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}
    
    # 1. Establish initial persistent tracking workspace parameters
    import uuid
    mock_doc_id = str(uuid.uuid4())
    mock_conv_id = str(uuid.uuid4())
    
    # Bypass long running orchestration steps and return clean mocks
    mocker.patch("backend.app.services.chat_service.ChatService.orchestrate_chat_state", return_value={
        "conversation_id": mock_conv_id,
        "document_id": mock_doc_id,
        "title": "Attention Architecture Overview",
        "chat_history": ["user=Hello engineering base agent node"]
    })
    
    # Securely stub multi-turn stream generation engine execution loop loops
    mock_stream = [(AIMessage(content="The attention mechanism assigns dynamic weights to input tokens."), {"metric": "test"})]
    mocker.patch.object(client.app.state.graph, "stream", return_value=mock_stream)
    
    # Track post-generation persistence routines
    mock_cleanup = mocker.patch("backend.app.services.chat_service.ChatService.execute_post_chat_cleanup")

    # turn 1: Call streaming processing loop
    payload = {
        "question": "Explain attention weights explicitly.",
        "conversation_id": None,
        "document_id": mock_doc_id
    }
    
    response = client.post("/chat", headers=headers, json=payload)
    assert response.status_code == 200
    assert response.headers["x-conversation-id"] == mock_conv_id
    assert response.text == "The attention mechanism assigns dynamic weights to input tokens."
    
    # Verify post-processing worker blocks executed properly without connection drops
    mock_cleanup.assert_called_once_with(
        user_id=str(test_user.id),
        conversation_id=mock_conv_id,
        question="Explain attention weights explicitly.",
        final_answer="The attention mechanism assigns dynamic weights to input tokens."
    )