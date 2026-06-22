import os
import sys
import colorama
import json
from sqlalchemy import text
from pathlib import Path
from collections import defaultdict
from backend.app.core.database import engine, SessionLocal, Base
from backend.app.models.base import Document, User, Chunk, Conversation, Memories
from backend.app.core.logging import GLOBAL_LOGGER as log
import uuid

CURRENT_DIR = Path(__file__).resolve().parents[0]
FIXTURES_PATH = Path(CURRENT_DIR,"datasets", "eval_fixtures.json")

def seed_database():
    if not os.path.exists(FIXTURES_PATH):
        log.error("Nor fixture eval dataset found", source =FIXTURES_PATH)
        sys.exit(1)
    with open(FIXTURES_PATH, "r", encoding = "utf-8") as f:
        fixtures = json.load(f)
    
    log.info("Constructing the isolated container database schema layout")

    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    #structural dictionary to track user-to-document relationships dynamically
    user_doc_map = defaultdict(list)
    try:
        #extract the collections
        documents_list = fixtures.get("documents",[])
        memories_list = fixtures.get("memories",[])

        #Phase 1:- Populate structural tenant user and parent Document entities
        log.info("seeding_phase_1_started", doc_count=len(documents_list))

        for doc_data in documents_list:
            user_id = uuid.UUID(doc_data["user_id"])
            doc_id = uuid.UUID(doc_data["document_id"])

            #Retaining a running record map of which documents belongs to which users
            user_doc_map[str(user_id)].append(str(doc_id))
            #Generate user anchor row to satisfy relational constriants
            db_user = User(id=user_id, username = f"tenant_{str(user_id)[:8]}", password_hash="test-password-hash")
            db.merge(db_user)

            #Insert document record entry
            db_doc = Document(id = doc_id, 
            user_id = user_id, 
            filename=f"fixture_{str(doc_id)[:8]}",
            file_path=f"/fixtures/mock_storage/eval_{str(doc_id)[:8]}.pdf"
            )
            db.merge(db_doc)

            for chunk in doc_data["chunks"]:
                db_chunk = Chunk(
                    document_id = doc_id,
                    chunk_index = chunk["chunk_index"],
                    content = chunk["content"],
                    embedding = chunk["embedding"]

                )
                db.add(db_chunk)

            #Batch 1 writes phase 1 data to database in single high performance transaction
            db.commit()
            log.info("\n\nadded the chunks into the chunks table\n\n", document_id = doc_id)

        #Phase 2: adding the fixtures episodic memories in the memories table
        log.info(f"processing the {len(memories_list)} episodic memories...")
        
        seeded_conversation_ids = set()
        for mem_data in memories_list:
            m_user_id = uuid.UUID(mem_data["user_id"])
            m_conv_id = uuid.UUID(mem_data["conversation_id"])
            m_memory_id = uuid.UUID(mem_data["memory_id"])
            #Dynamic Seeding: ensure parents reference exis for memory referance
            db_user = User(id = m_user_id, username = f"tenant_{str(m_user_id)[:8]}", password_hash = "test-password-hash")
            db.merge(db_user)

            if str(m_conv_id) not in seeded_conversation_ids:
                tenant_documents = user_doc_map.get(str(m_user_id))

                if tenant_documents:
                    fallback_doc_id = tenant_documents[0]
                else:
                    fallback_doc_id = documents_list[0]["document_id"] if documents_list else None  

                if fallback_doc_id:
                    db_conv = Conversation(
                        id = m_conv_id,
                        user_id = m_user_id,
                        document_id = fallback_doc_id,
                        title = "CI sedding conversation-memories anchor"
                    )
                    db.merge(db_conv)
                    seeded_conversation_ids.add(str(m_conv_id))
                else:
                    log.warning("Skipped conversation seeding", conversation_id = m_conv_id, reason="No strucutual document available")

            db_memory = Memories(
                id = m_memory_id,
                user_id = m_user_id,
                conversation_id = m_conv_id,
                memory_type = mem_data["memory_type"],
                content = mem_data["content"],
                embedding = mem_data["embedding"]
            )
            db.merge(db_memory)

        #batch write phase 2 tracking records to database disk
        db.commit()
        log.info("seeding pahse 2 completed")

    except Exception as e:
        db.rollback()
        log.error("Error during seeding the github container database", error = str(e))
        sys.exit(1)

    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
