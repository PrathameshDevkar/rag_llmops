from backend.app.rag.checkpoint import get_checkpointer

THREAD_ID = "16b5ffc4-f3e7-4f32-ac7b-afbc3676605e"

with get_checkpointer() as cp:
    tup = cp.get_tuple({"configurable": {"thread_id": THREAD_ID}})

    print("\n--- FULL CHANNEL VALUES ---")
    print(tup)

