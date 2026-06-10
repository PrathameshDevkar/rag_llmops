from backend.app.core.custom_exception import DocumentPortalException
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
import time

from backend.app.core.logging import GLOBAL_LOGGER as log


model = get_llm()

def retrieval_node(state:RAGState) -> RAGState:
    db=SessionLocal()
    start_time = time.time()
    
    log.info("vector_retrieval_started", user_id=state['user_id'], document_id=state['document_id'])
    try:
        query_embedding = embed_text(state['user_question'])
        chunks_results=chunks_retrieval(
            db=db,
            query_embedding=query_embedding,
            document_id=state['document_id']
        )
        query=state['user_question']
        document_id=state['document_id']
      
        chunks=[r.content for r in chunks_results]
        
        memory_results = memories_retrieval(
            db=db,
            query_embedding=query_embedding,
            user_id=state['user_id']
        )

        recalled_memories = []
        for r in memory_results:
            try:
                recalled_memories.append(json.loads(r.content))
            except:
                recalled_memories.append({"conversation_summary": r.content})
            
        elapsed_ms = (time.time() - start_time) * 1000
        log.info("vector_retrieval_completed", 
                 elapsed_ms=round(elapsed_ms, 2),
                 chunks_found=len(chunks), 
                 memories_found=len(recalled_memories))
        
        return {
            **state,
            "retrieved_chunks":chunks,
            "recalled_memories": recalled_memories
        }
    except Exception as e:
        # Wrap and propagate the error with full traceback tracking up the stack line
        log.error("error in the retrieval node",error = str(e) )
        raise DocumentPortalException(
            "Critical retrieval execution fault inside LangGraph context node structure"
        )
    finally:
        db.close()    
        
def generate_node(state:RAGState) -> Iterator[RAGState]:
    
    memory_strings = []

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
    