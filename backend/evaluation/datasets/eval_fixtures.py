import os
import json
from backend.app.core.database import SessionLocal
from backend.app.models.base import Document, User, Chunk, Conversation, Memories
from backend.app.core.logging import GLOBAL_LOGGER as log
from pathlib import Path
from sqlalchemy.orm import joinedload
from colorama import Fore

BASE_DIR = Path(__file__).resolve().parents[0]
DATASET_FILE = Path(BASE_DIR,"rag_dataset.json")
FIXTURE_FILE = Path(BASE_DIR,"eval_fixtures.json")

def serialize_vector(vector_field):
    if vector_field is None:
        return None
    for i in range(1):
        print(Fore.YELLOW + f"\n\nvector field is{vector_field}\n\n")
        print(f"\n\ntype of vector field is{type(vector_field)}\n\n"+Fore.RESET)

    if hasattr(vector_field, "tolist"):
        return vector_field.tolist()
    return list(vector_field)

def export_fixtures():
    if not os.path.exists(DATASET_FILE):
        log.info("No golden dataset found", source_path = DATASET_FILE)
        return

    with open(DATASET_FILE, "r", encoding = "utf-8") as f:
        cases = json.load(f)

    doc_ids = [c["document_id"] for c in cases]
    log.info(f"\n\nscanning local database for {len(doc_ids)} document fixtures...\n\n")

    db = SessionLocal()
    try:
        documents = (
            db.query(Document)
            .filter(Document.id.in_(doc_ids))
            .options(joinedload(Document.chunks))
            .all()
        ) 

        user_ids = [doc.user_id for doc in documents]

        log.info(f"\n\nextracting episodic memories for {len(user_ids)} users")
        memories = (
            db.query(Memories)
            .filter(Memories.user_id.in_(user_ids))
            .all()
        )

        exported_chunks = []
        for doc in documents:
            d_id = str(doc.id)
            sorted_chunks = sorted(doc.chunks, key=lambda c: c.chunk_index)
            chunk_payload=[{
                "chunkPindex": chunk.chunk_index,
                "content": chunk.content,
                "embedding": serialize_vector(chunk.embedding)
                }   
                for chunk in sorted_chunks
            ]  
            exported_chunks.append(
                {
                    "document_id":d_id,
                    "user_id": str(doc.user_id),
                    "chunks":chunk_payload
                }
            )
        
        exported_memories=[
            {
                "memory_id": str(mem.id),
                "user_id": str(mem.user_id),
                "conversation_id": str(mem.conversation_id),
                "memory_type": mem.memory_type,
                "content": mem.content,
                "embedding": serialize_vector(mem.embedding)
            }
            for mem in memories
        ]
             
        fixture_package = {
            "documents":exported_chunks,
            "memories":exported_memories

        }

        with open(FIXTURE_FILE, "w", encoding= "utf-8") as f:
            json.dump(fixture_package, f, indent = 2, ensure_ascii=False)
    
    finally:
        db.close()

if __name__ == "__main__":
    export_fixtures()
        
"""
Let’s pull back the curtain on that SQLAlchemy query. Shifting from raw, SQL-like table queries to an Object-Relational Mapping (ORM) relationship pattern completely changes how your backend talks to the database.

Here is a deep-dive explanation of exactly how that specific `Document` query works, why it's highly efficient for a production RAG pipeline, and how the data is transformed right after.

---

## The Query Breakdown Line-by-Line

```python
documents = (
    db.query(Document)
    .filter(Document.id.in_(doc_ids))
    .options(joinedload(Document.chunks))
    .all()
)

```

### 1. `db.query(Document)`

Instead of querying the `Chunk` table directly, we are telling SQLAlchemy: *"I want to retrieve entries from the `Document` table."* Because your database model defines relationships, every `Document` object returned will act as a parent container that holds references to its owner (`User`) and its children (`Chunks`).

### 2. `.filter(Document.id.in_(doc_ids))`

This translates directly to a SQL `IN` operator clause: `WHERE documents.id IN ('uuid-1', 'uuid-2', ...)`. It efficiently searches through your database and grabs all matching document rows in a single sweep.

### 3. `.options(joinedload(Document.chunks))` *(The Critical Optimization)*

By default, SQLAlchemy uses **Lazy Loading**. If you fetch a document and then try to loop through its text chunks using `doc.chunks`, SQLAlchemy will pause your code and fire a separate, hidden `SELECT * FROM chunks WHERE document_id = ...` query to the database for **every single document** in your list. If you have 100 documents, your app will hit the database 101 times! This is known as the **N+1 Query Problem** and it heavily degrades performance in production.

Using **`joinedload(Document.chunks)`** switches the behavior to **Eager Loading**. It tells SQLAlchemy to instantly issue a SQL `LEFT OUTER JOIN` behind the scenes.

* It pulls the data from the `documents` table and the associated records from the `chunks` table **at the exact same time, in a single database round-trip**.
* When the data arrives back in Python, SQLAlchemy automatically parses that single big table join result and groups the chunks neatly into lists inside their respective parent `Document` objects.

### 4. `.all()`

This executes the fully assembled query against your PostgreSQL instance and returns the results as a standard Python list of `Document` object instances.

---

## The Post-Query Transformation Line-by-Line

Once the database returns the eagerly-loaded `documents` list, the script processes it into the structured fixture format required for evaluation:

```python
for doc in documents:
    d_id = str(doc.id)
    
    # 1. Enforce strict indexing sequence order
    sorted_chunks = sorted(doc.chunks, key=lambda c: c.chunk_index)
    
    # 2. Clean object mapping using your relationship bridges
    fixtures[d_id] = {
        "document_id": d_id,
        "user_id": str(doc.user_id), 
        "chunks": [chunk.content for chunk in sorted_chunks]
    }

```

### 1. Sorting in Memory: `sorted(doc.chunks, key=...`

When database tables are joined using a `LEFT OUTER JOIN`, the database engine doesn't guarantee that the child rows (`chunks`) will arrive in perfect sequential order. To ensure your RAG evaluation doesn't receive a shuffled document, we use Python's built-in `sorted()` function to organize the chunks by their `chunk_index` (0, 1, 2, etc.) in memory before exporting.

### 2. Eliminating Global Maps via Object Attributes

Look at your original implementation compared to the new relationship-driven approach:

* **The Old Way:** You had to manually parse your evaluation file up-front, generate a separate dictionary map (`user_map = {c["document_id"]: c["user_id"]}`), and match them inside your loop.
* **The New Way:** Because a `Document` is structurally linked to its own database row, you can access `doc.user_id` directly from the object itself. The need for manual lookup dictionaries is completely gone.

---

## Why This Configuration Clears the `KeyError: 'User'`

The reason your script originally crashed with `KeyError: 'User'` is due to how SQLAlchemy sets up its internal structural map.

When your script executed `db.query(Chunk)`, SQLAlchemy stepped into your `Chunk` model, saw it linked to `Document`, and then stepped into `Document`. Inside `Document`, it encountered the line `user = relationship("User", ...)` and asked its internal registry: *"Who or what is 'User'?"* Because your standalone script file had never imported the `User` class from `backend/app/models/user.py`, the registry was completely blank for that key, resulting in a crash.

By adding the explicit catch-all model import at the top of the file:

```python
from backend.app.models.base import Document, Chunk, User

```

Python forces every table schema definition to load into memory and register itself with SQLAlchemy simultaneously. When the query executes, the database engine can trace every cross-table relationship flawlessly.

"""