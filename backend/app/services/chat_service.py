import logging
from sqlalchemy.orm import Session
from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.services.conversation_services import create_conversation, generate_conversation_title, add_message
from backend.app.services.memory_service import add_episodic_memory
from backend.app.core.logging import GLOBAL_LOGGER as log
from backend.app.core.custom_exception import DocumentPortalException # Import exception tracking

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, db: Session):
        self.db = db
        self.conversation_repo = ConversationRepository(db)

    def orchestrate_chat_state(self, chat_in, user_id: str):
        """
        Validates conversation state, fetches relevant context parameters,
        and records the incoming user utterance record.
        """
        title = ""
        document_id = ""

        try:
            # Branch 1: Appending to an existing conversation thread
            if chat_in.conversation_id:
                conversation_id = chat_in.conversation_id
                conversation = self.conversation_repo.get_by_id(conversation_id=conversation_id, user_id=user_id)
                
                if not conversation:
                    log.error("conversation_access_denied", conversation_id=conversation_id, user_id=user_id)
                    return None
                    
                document_id = str(conversation.document_id)
                log.info("existing conversation thread conversation loaded", conversation_id=conversation_id, document_id=document_id)
                
            # Branch 2: Constructing a brand new interaction workspace
            else:
                conversation = create_conversation(
                    self.db,
                    user_id=user_id,
                    document_id=chat_in.document_id
                )
                document_id = chat_in.document_id
                conversation_id = str(conversation.id)
                title = generate_conversation_title(chat_in.question)
                
                conversation.title = title
                self.db.commit()
                
                log.info("new conversation thread created", conversation_id=conversation_id, document_id=document_id, title=title)

            # Persist user question statement
            add_message(
                db=self.db,
                conversation_id=conversation_id,
                role="user",
                content=chat_in.question
            )
            
            # Extract ordered transcripts using ORM relationships safely
            chat_history = [f"{m.role}={m.content}" for m in conversation.messages]
            logger.info(f"Successfully compiled context history depth: {len(chat_history)} turns")

            return {
                "conversation_id": conversation_id,
                "document_id": document_id,
                "title": title,
                "chat_history": chat_history
            }

        except Exception as e:
            log.error("failed to assemble chat database transaction boundries", error= str(e))
            raise DocumentPortalException(
                error_message = "failed to assemble chat database transaction boundries",
                error_details = e
            )
    def execute_post_chat_cleanup(self, user_id: str, conversation_id: str, question: str, final_answer: str):
        """ Handles secondary persistence operations outside the streaming runtime loop """
        try:    
            log.info("Post chat cleanup started", conversation_id = conversation_id, user_id = user_id)
            # 1. Commit assistant statement to tracking ledger
            add_message(
                self.db,
                conversation_id,
                role="assistant",
                content=final_answer
            )
            
            # 2. Extract and preserve background episodic profile memory
            chat_turn_text = f"User: {question}\nAssistant: {final_answer}"
            add_episodic_memory(
                db=self.db,
                user_id=user_id,
                conversation_id=conversation_id,
                chat_turn_text=chat_turn_text
            )
            log.info("post_chat_cleanup_success", conversation_id=conversation_id)
        
        except Exception as e:
            log.error("Background episodic memory capture failed", error=str(e))
            raise DocumentPortalException("Background episodic memory capture failed")
