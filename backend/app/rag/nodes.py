from backend.app.core.database import SessionLocal
from backend.app.rag.state import RAGState
from backend.app.services.retrieval import similarity_search
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Iterator
import os
from colorama import Fore
from backend.app.services.model_loader import get_llm

model = get_llm()

def retrieval_node(state:RAGState) -> RAGState:
    db=SessionLocal()
    
    try:
        results=similarity_search(
            db=db,
            query=state['user_question'],
            document_id=state['document_id']
        )
        query=state['user_question']
        document_id=state['document_id']
        print(Fore.YELLOW + f"\n\n=====user_question in nodes.py is: {query}=========\n\n" + Fore.RESET)
        print(Fore.YELLOW + f"\n\n=====document_id in nodes.py is : {document_id}=========\n\n" + Fore.RESET)

        chunks=[r.content for r in results]
        print(Fore.YELLOW + f"\n\n=====retrieved chunks in nodes.py are: {chunks}=========\n\n" + Fore.RESET)
        
        return {
            **state,
            "retrieved_chunks":chunks
        }
    finally:
        db.close()    
        
def generate_node(state:RAGState) -> Iterator[RAGState]:
    
    prompt=PromptTemplate(
        template="""
        you are a helpful assistant who gives answer to the given question based on the given context. 
        if you dont know the answer just say that you cannot answer the question.
        
        conversation so far - {chat_history}
        here is the context - {context}
        here is the question - {question}""",
        input_variables=['context','question','chat_history']
    )
    
    chain = prompt | model | StrOutputParser()
    
    # result=chain.stream({"context":state["retrieved_chunks"],"question":state["user_question"],"chat_history":state["chat_history"]})
    
    # return {**state,
    #         "generated_answer":result}
    partial_answer = ""
    print(Fore.YELLOW + f"\n\nchat history is:{state['chat_history']}\n\n" + Fore.RESET)
    
    for chunk in chain.stream({
        "context": "\n".join(state["retrieved_chunks"]),
        "question": state["user_question"],
        "chat_history": "\n".join(state["chat_history"]),
    }):
        partial_answer += chunk
        yield {
            **state,
            "generated_answer": partial_answer
        }
    