from backend.app.core.database import SessionLocal
from backend.app.rag.state import RAGState
from backend.app.services.retrieval import chunks_retrieval, memories_retrieval
from backend.app.services.embeddings import embed_text
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Iterator
import os
from colorama import Fore
from backend.app.services.model_loader import get_llm
import json

model = get_llm()

def retrieval_node(state:RAGState) -> RAGState:
    db=SessionLocal()
    
    try:
        query_embedding = embed_text(state['user_question'])
        chunks_results=chunks_retrieval(
            db=db,
            query_embedding=query_embedding,
            document_id=state['document_id']
        )
        query=state['user_question']
        document_id=state['document_id']
        print(Fore.YELLOW + f"\n\n=====user_question in nodes.py is: {query}=========\n\n" + Fore.RESET)
        print(Fore.YELLOW + f"\n\n=====document_id in nodes.py is : {document_id}=========\n\n" + Fore.RESET)

        chunks=[r.content for r in chunks_results]
        print(Fore.YELLOW + f"\n\n=====retrieved chunks in nodes.py are: {chunks}=========\n\n" + Fore.RESET)
        
        memory_results = memories_retrieval(
            db=db,
            query_embedding=query_embedding,
            user_id=state['user_id']
        )
        print(Fore.YELLOW + f"\n\n===== Recalled Long-Term Memory results: {memory_results} =====\n\n" + Fore.RESET)

        recalled_memories = []
        for r in memory_results:
            try:
                recalled_memories.append(json.loads(r.content))
            except:
                recalled_memories.append({"conversation_summary": r.content})
        
        print(Fore.YELLOW + f"\n===== Recalled Long-Term Memories: {recalled_memories} =====" + Fore.RESET)
        
        return {
            **state,
            "retrieved_chunks":chunks,
            "recalled_memories": recalled_memories
        }
    finally:
        db.close()    
        
def generate_node(state:RAGState) -> Iterator[RAGState]:
    
    memory_strings = []
    print(Fore.CYAN + f"\n\n=============recalled memories are:{state['recalled_memories']}===========" + Fore.RESET )

    if state.get("recalled_memories"):
        for memory in state["recalled_memories"]:
            memory_strings.append(
                f"- Historical Turn: {memory.get('conversation_summary')}\n"
                f"  Successful Context: {memory.get('what_worked')}\n"
                f"  pitfall to avoid: {memory.get('what_to_avoid')}\n"
            )
    compiled_memories_context = "\n".join(memory_strings) if memory_strings else "No relevant historical context found"
    
    #enforece sliding context window of the last 5 chat turns
    history_window = state["chat_history"][-5:] if state["chat_history"] else []
    
    prompt=PromptTemplate(
        template="""
        you are a helpful assistant who gives answer to the given question based on the given context. 
        if you dont know the answer just say that you cannot answer the question.
        
        Recet chat history - {chat_history}
        User behavioral profile and historical reflections - {recalled_memories}
        Relevant context from uploaded documents - {context}
        User question - {question}""",
        input_variables=['context','question','chat_history','recalled_memories']
    )
    
    chain = prompt | model | StrOutputParser()
    
    # result=chain.stream({"context":state["retrieved_chunks"],"question":state["user_question"],"chat_history":state["chat_history"]})
    
    # return {**state,
    #         "generated_answer":result}
    partial_answer = ""
    print(Fore.CYAN + f"\n\nchat history is:{state['chat_history']}\n\n" + Fore.RESET)
    
    for chunk in chain.stream({
        "context": "\n".join(state["retrieved_chunks"]),
        "question": state["user_question"],
        "chat_history": "\n".join(history_window),
        
        "recalled_memories": compiled_memories_context
    }):
        partial_answer += chunk
        yield {
            **state,
            "generated_answer": partial_answer
        }
    