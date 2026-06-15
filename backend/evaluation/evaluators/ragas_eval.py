import os
import json
import pandas as pd
from datasets import Dataset
from backend.app.core.logging import GLOBAL_LOGGER as log
import time
from datetime import datetime
import nest_asyncio

from ragas import evaluate
from ragas.metrics.collections import (
    ContextPrecision,
    ContextRecall,
    Faithfulness,
    AnswerRelevancy
)


from backend.app.rag.graph import build_graph
from backend.app.rag.checkpoint import get_checkpointer
from backend.app.services.model_loader import get_llm, get_embedding_model

from langchain_core.messages import AIMessage

from colorama import Fore

#==============================================================================================================================
"""
we set this env variables initially because - LangChain and LangGraph look directly inside the operating system's environment (os.environ) the exact microsecond they are imported.
When you run ragas_eval.py as a standalone script, your Pydantic settings load your .env variables into a Python object (settings.LANGSMITH_PROJECT),
 but it does not automatically push them into Windows' os.environ. Because LangChain initializes before those variables are explicitly mapped to the OS, the tracing engine stays completely asleep.
"""
from dotenv import load_dotenv
load_dotenv()
from backend.app.core.config import settings
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY or ""
os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT or "langgraph-rag-backend"
#==============================================================================================================================

#patch event loop conflicts for local synchronous script runs
nest_asyncio.apply()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_FILE = os.path.join(BASE_DIR, "datasets","rag_dataset.json")
REPORT_DIR = os.path.join(BASE_DIR,"reports")
REPORT_FILE = os.path.join(REPORT_DIR, "ragas_report.json")


def execute_evaluation_run():
    """
    Injects synthetic cases, spins up langgraph checkpointer,
    runs end-to-end processing loops, calculates ragas metrics.
    """
    if not os.path.exists(DATASET_FILE):
        log.error(Fore.RED + "No golden dataset is available" + Fore.RESET)
        return
    
    log.info("loading the golden dataset", source = DATASET_FILE)
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        eval_cases = json.load(f)
    
    run_samples = eval_cases[:3]
    
    compiled_evaluation_data = []
    
    with get_checkpointer() as checkpointer:
        checkpointer.setup()
        graph = build_graph(checkpointer)
        log.info(Fore.GREEN + "successfully build the graph with checkpointer" + Fore.RESET)
        
        for idx,item in enumerate(run_samples):
            initial_state ={
                "user_id": item["user_id"],
                "document_id": item["document_id"],
                "user_question":item["input_question"],
                "chat_history":[],
                "retrieved_chunks":None,
                "recalled_memories":None,
                "generated_answer":None
            }
            
            # Build production metadata structure matching your chat.py updates
            config = {
                "configurable": {"thread_id": f"eval_run_{item['eval_id']}"},
                "metadata": {
                    "user_id": item["user_id"],
                    "document_id": item["document_id"],
                    "conversation_id": f"eval_conv_{item['eval_id']}"
                },
                "tags": ["evaluation-harness", "ragas-test-run"]
            }
            
            final_answer = ""
            start_time = time.time()
            
            try:
                #Iterate over the messags, stream exactly like chat.py to process generator nodes smoothly
                for event, metadata in graph.stream(
                    initial_state,
                    config = config,
                    stream_mode = "messages"
                ):
                    if isinstance(event, AIMessage):
                        final_answer += event.content
                        
                final_graph_state = graph.get_state(config).values
                retrieved_chunks = final_graph_state.get("retrieved_chunks",[])
                
            except Exception as e:
                log.error("graph_execution failure", eval_id = item["eval_id"], error= str(e))
                continue
            
            duration = time.time() - start_time
            
            if not retrieved_chunks:
                retrieved_chunks = ["no context retrieved by the retirve node"]
                
            compiled_evaluation_data.append({
                "question":item["input_question"],
                "answer": final_answer if final_answer else "system failure, empty answer content",
                "contexts": retrieved_chunks,
                "ground_truth":item["ground_truth_answer"],
                "latency_sec": round(duration,3)
            })
        
    if not compiled_evaluation_data:
        log.error(Fore.RED + "No system output compiled Successfully, aboritng the evaluation" + Fore.RESET)
        return
    
    # Transform the evaluationmatrix in to huggingface dataset format
    df = pd.DataFrame(compiled_evaluation_data)
    ragas_dataset = Dataset.from_pandas(df)
    
    local_llm = get_llm()
    local_embedding_model = get_embedding_model()
    
    metrics = [ContextPrecision(),
    ContextRecall(),
    Faithfulness(),
    AnswerRelevancy()]
    
    scores = evaluate(
        dataset = ragas_dataset,
        metrics = metrics,
        llm= local_llm,
        embeddings = local_embedding_model,
        allow_nest_asyncio = True
    )
    
    if scores:
        log.info(Fore.GREEN + "evaluation is successfull" + Fore.RESET)
        print(f"\nscore is:{scores}\n")
        print(f"\ncontext_precision is:{scores['context_precision']}\n")
        print(f"\ncontext_recall is:{scores['context_recall']}\n")
        print(f"\nfaithfulness is:{scores['faithfulness']}\n")
        print(f"\nanswer_relevancy is:{scores['answer_relevancy']}\n")

    # 7. Write structured json analytics out to file disk
    os.makedirs(REPORT_DIR, exist_ok=True)
    report_output = {
        "execution_timestamp": datetime.utcnow().isoformat(),
        "summary_scores": str(scores),
        "detailed_test_runs": compiled_evaluation_data
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as out_f:
        json.dump(report_output, out_f, indent=2, ensure_ascii=False)
    
    log.info("evaluation_report_exported", target_file=REPORT_FILE)
    print(f"✅ Full report safely written to disk path at: {REPORT_FILE}")


if __name__ == "__main__":
    execute_evaluation_run()
            