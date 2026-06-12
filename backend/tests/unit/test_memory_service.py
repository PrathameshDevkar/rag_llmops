import pytest
import json
import uuid
from unittest.mock import MagicMock, patch
from backend.app.services.memory_service import add_episodic_memory
from backend.app.models.document import Document
from backend.app.models.conversations import Conversation
from backend.app.models.memories import Memories

def test_add_episodic_memory_success(db_session, test_user, mocker):
    # 1. Seed database parents to preserve foreign key constraints
    document = Document(user_id=test_user.id, filename="paper.pdf", file_path="")
    db_session.add(document)
    db_session.commit()

    conversation = Conversation(user_id=test_user.id, document_id=document.id, title="RAG Talk")
    db_session.add(conversation)
    db_session.commit()

    # 2. Mock LiteLLM response payload with raw markdown blocks
    mock_llm_output = """```json
    {
        "context_tags": ["deep_learning", "transformers"],
        "conversation_summary": "User asked about self-attention math mechanics.",
        "what_worked": "Using step-by-step matrix breakdown.",
        "what_to_avoid": "Skipping basic linear algebra checks."
    }
    ```"""
    
    mock_choice = MagicMock()
    mock_choice.message.content = mock_llm_output
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    
    mocker.patch("backend.app.services.memory_service.completion", return_value=mock_response)

    # 3. Mock the embedding model vector output
    mock_embed = mocker.patch("backend.app.services.memory_service.get_embedding_model")
    mock_embed.return_value.embed_query.return_value = [0.1] * 384

    # 4. Execute target business function
    add_episodic_memory(
        db=db_session,
        user_id=str(test_user.id),
        conversation_id=str(conversation.id),
        chat_turn_text="User: How does attention work? Assistant: It uses queries, keys, and values."
    )

    # 5. Assert the record was saved in Postgres safely
    saved_memory = db_session.query(Memories).filter(Memories.conversation_id == conversation.id).first()
    assert saved_memory is not None
    assert saved_memory.user_id == test_user.id
    assert saved_memory.memory_type == "episodic_memory"
    
    parsed_content = json.loads(saved_memory.content)
    assert parsed_content["conversation_summary"] == "User asked about self-attention math mechanics."
