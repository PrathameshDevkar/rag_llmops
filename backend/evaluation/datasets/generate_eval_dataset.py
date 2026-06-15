import os
import json
import uuid
from backend.app.core.logging import GLOBAL_LOGGER as log
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.user import User
from backend.app.models.conversations import Conversation
from backend.app.models.document import Document
from backend.app.models.chunk import Chunk
from backend.app.models.messages import Messages
from backend.app.models.memories import Memories
from backend.app.services.model_loader import get_llm
from backend.app.core.database import SessionLocal


from langchain_core.messages import HumanMessage, SystemMessage

from colorama import Fore

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "rag_dataset_1.json")

#pydantic schema to validate LLM output structure
class SyntheticEvaluationItem(BaseModel):
    input_question: str = Field(..., description = "A clear question derived from the given context.")
    ground_truth_answer: str = Field(..., description = "An explicit comprehensive answer supported only by the context")
    context_tag: str = Field(..., description = "A 2-3 word snake-category tag for long term memory tracking")
    
class SyntheticBatch(BaseModel):
    items: List[SyntheticEvaluationItem]
    

def clean_llm_json(raw_text: str) -> str:
    """strip markdown clde blocks and whitespace from the LLM output"""
    cleaned = raw_text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    elif cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()

def generate_synthetic_data(db:Session, chunks_per_doc: int = 3) -> List[Dict[str,Any]]:
    """
    Queries the database chunks, processes them with the chat llm,
    and returns list matching the enterprise evaluation schema
    """
    i=1

    #Fetch chunk, joined with Document table to capture the tenant info
    chunks = (
        db.query(Chunk)
        .join(Document, Chunk.document_id == Document.id)
        .order_by(Chunk.chunk_index)
        .all()
    )
    
    if not chunks:
        log.warning("No document or chunks found, please upload a document first")
        return []
    
    # Group by document to ensure distribution
    doc_chunks_map: Dict[str, List[Chunk]] = {}
    for chunk in chunks:
        doc_chunks_map.setdefault(str(chunk.document_id), []).append(chunk)
        
    eval_dataset: List[Dict[str, Any]] = []
    chat_model = get_llm()
    
    system_prompt = """
        You are an expert QA and LLMOPS engineer specialized in evaluating RAG architecture.
        Your job is to read the provided combined text chunks and generate high-quality, chellenging question-answer pairs.
        
        You must return response EXCLUSIVELY as a valid json object matching this schema:
        {
            "items": [
                {
                    "input_question":"...", 
                    "ground_truth_answer":"...", 
                    "context_tag":"..."
                }
            ]   
        }
        
        Guidelines:
        1.The question must be naswerable only using the exact text chunk details.
        2.The ground_truth_answer should be complete and factual to the context.
        3.Create a short context_tag using the snake_case (e.g. 'attention complexity')
        
        Do not output markdown text outside the JSON block. Do not include any conversation filler             
        
    """
    sample_chunks=[]
    for doc_id, doc_chunks in doc_chunks_map.items():
        sample_chunks.extend(doc_chunks[:9])
        print(Fore.YELLOW + f"===============\n\nsample chunks are:{sample_chunks}\n\n=========", Fore.RESET)
        for i in range(0,len(sample_chunks),3):
            combined_chunks = sample_chunks[i:i+3]
            
            if len(combined_chunks)<3:
                log.info(Fore.CYAN+"\n\nskipping the remainder batch of chunks\n\n" + Fore.RESET)
                continue
            
            combined_context = "\n".join(chunk.content for chunk in combined_chunks)
            chunk_indices = [c.chunk_index for c in combined_chunks]
            
            log.info("processing chunk", chunk_index = chunk_indices, document_id = doc_id)
            
            human_prompt = f"TEXT CHUNK\n{combined_context}\n"
            
            try:
                messages = [
                    SystemMessage(content = system_prompt),
                    HumanMessage(content = human_prompt)
                ]
                
                response = chat_model.invoke(messages)
                print(Fore.CYAN + f"\n\nresponse is:{response}\n\n" + Fore.RESET)
                raw_content = response.content
                
                #sanitize the raw content
                cleaned_content = clean_llm_json(raw_content)
                parsed_data= json.loads(cleaned_content)
                
                #validate schema structure
                batch = SyntheticBatch(**parsed_data)

                primary_chunk = combined_chunks[0]
                #map LLLM output into the Multi-tenant enterprise schema
                for item in batch.items:
                    eval_record = {
                        "eval_id":f"eval_{uuid.uuid4().hex[:8]}",
                        "user_id":str(primary_chunk.document.user_id) if hasattr(primary_chunk.document, "user_id") else "system_test_tenant",
                        "document_id": str(primary_chunk.document_id),
                        "input_question": item.input_question,
                        "ground_truth_answer": item.ground_truth_answer,
                        "expected_context_snippets": [chunk.content for chunk in combined_chunks],
                        "expected_memory_profile":{
                            "has_relevant_past_interaction": True,
                            "context_tags":item.context_tag
                        }
                    }
                    if i==1:
                        print(Fore.YELLOW + f"eval record is: {eval_record}" + Fore.RESET)
                    eval_dataset.append(eval_record)
                    
            except Exception as e:
                chunk_ids = [chunk.id for chunk in combined_chunks]
                log.error("Failed to generate evaluation item", Chunk_ID=chunk_ids, error= str(e))
                continue   
        break     
    return eval_dataset      

def main():
    log.info("initiating database session")            
    db = SessionLocal()
    
    try:
        os.makedirs(OUTPUT_DIR, exist_ok = True)
        
        log.info("Starting synthetic dataset generation pipeline via Llama-3.1-8B...")
        dataset = generate_synthetic_data(db)
        
        if dataset:
            with open(OUTPUT_FILE, "w", encoding = "utf-8") as f:
                json.dump(dataset, f, indent = 2, ensure_ascii = False)
            log.info("Successfully generated {len(dataset)} evaluation pairs at: {OUTPUT_FILE}")
        else:
            log.error("Dataset generation halted: No records compiled.")
    
    finally:
        db.close()
        log.info("database session closed")
    
if __name__ == "__main__":
    main()
        

            
        
        
    