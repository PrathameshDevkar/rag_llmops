from backend.app.rag.graph import build_graph

graph=build_graph()

# state={
#     "user_id":"dummy",
#     "document_id":"aa186a92-36e3-48f5-9639-bc671b6e1714",
#     "user_question":"what is mean by self attention mechanism?",
#     "retrieved_chunks":None,
#     "generated_answer":None
# }

# result = graph.invoke(state)

# print(result['generated_answer'])