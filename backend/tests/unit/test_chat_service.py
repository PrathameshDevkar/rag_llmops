import pytest
import uuid
from backend.app.services.chat_service import ChatService
from backend.app.schemas.chat import ChatRequest
from backend.app.models.document import Document
from backend.app.models.conversations import Conversation
from backend.app.models.messages import Messages
from colorama import Fore

@pytest.fixture
def test_document(db_session, test_user):
    doc = Document(user_id=test_user.id, filename="test_doc.pdf", file_path="")
    db_session.add(doc)
    db_session.commit()
    return doc

def test_orchestrate_chat_state_new_conversation(db_session, test_user, test_document, mocker):
    # Mock LLM title generator call
    mocker.patch("backend.app.services.chat_service.generate_conversation_title", return_value="Mocked Summary Title")
    mocker.patch("backend.app.services.chat_service.log")

    service = ChatService(db_session)
    chat_in = ChatRequest(question="What is the main methodology?", document_id=str(test_document.id))

    # Run orchestration for a NEW workspace
    bundle = service.orchestrate_chat_state(chat_in, user_id=str(test_user.id))

    print(Fore.CYAN + f"document_id is: {test_document.id}" + Fore.RESET)
    print(Fore.CYAN + f"dconversation_id is: {bundle}" + Fore.RESET)
    assert bundle is not None
    assert bundle["title"] == "Mocked Summary Title"
    assert bundle["document_id"] == str(test_document.id)
    
    # Ensure user message was captured in database
    msg = db_session.query(Messages).filter(Messages.conversation_id == uuid.UUID(bundle["conversation_id"])).first()
    assert msg.content == "What is the main methodology?"
    assert msg.role == "user"

def test_orchestrate_chat_state_existing_conversation(db_session, test_user, test_document, mocker):
    mocker.patch("backend.app.services.chat_service.log")
    
    print(Fore.CYAN + f"document_id in test_orchestrate_chat_state_existing_conversation is: {test_document.id}" + Fore.RESET)

    # Pre-seed an existing conversation thread
    existing_conv = Conversation(user_id=test_user.id, document_id=test_document.id, title="Existing Chat")
    db_session.add(existing_conv)
    db_session.commit()
    print(Fore.CYAN + f"conversation_id in test_orchestrate_chat_state_existing_conversation is: {existing_conv.id}" + Fore.RESET)


    service = ChatService(db_session)
    chat_in = ChatRequest(question="Follow up query.", conversation_id=str(existing_conv.id))

    bundle = service.orchestrate_chat_state(chat_in, user_id=str(test_user.id))
    
    assert bundle["conversation_id"] == str(existing_conv.id)
    assert bundle["document_id"] == str(test_document.id)
