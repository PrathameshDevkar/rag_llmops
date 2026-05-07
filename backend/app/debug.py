from backend.app.rag.checkpoint import get_checkpointer

THREAD_ID = "1ca8eeb0-0012-481e-b8ca-9d6ee66da264"

with get_checkpointer() as cp:
    tup = cp.get_tuple({"configurable": {"thread_id": THREAD_ID}})

    print("\n--- FULL CHANNEL VALUES ---")
    print(tup)

