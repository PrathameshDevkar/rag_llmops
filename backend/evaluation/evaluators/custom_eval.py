import os
import json
import time
from pathlib import Path
from datetime import datetime
from colorama import Fore

import vertexai
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel

from langchain_core.messages import AIMessage
from backend.app.core.logging import GLOBAL_LOGGER as log
from backend.app.rag.graph import build_graph
from backend.app.rag.checkpoint import get_checkpointer


from dotenv import load_dotenv
load_dotenv()
from backend.app.core.config import settings
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY or ""
os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT or "langgraph-rag-backend"


# Explicit Path Setup matching your structure
CURRENT_DIR = Path(__file__).resolve().parents[1]
DATASET_FILE = os.path.join(CURRENT_DIR, "datasets", "rag_dataset.json")
REPORT_DIR = Path(CURRENT_DIR, "reports")
REPORT_FILE = Path(REPORT_DIR, "custom_metrics_report.json")

# Initialize your GCP credentials profile
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\Prathamesh\prathamesh\llmops_rag_langgraph\vertexai-free-credits-api-key.json"
vertexai.init(project="poised-cortex-462609-n4", location="us-central1")

def judge_memory_utilization(judge_model: GenerativeModel, question: str, memory: str, answer: str) -> bool:
    """
    Employs gemini to execute a binary audit verifying if recalled episodic memory constraints were applied
    during generation.
    """
    #Throttling to respect free tier endpoint allocations
    time.sleep(4.0)

    prompt = f"""
    You are an LLMOps system auditor inspecting a lomg term memory engine.
    Analyze the user's question, recalled memory profile and the generated answer.

    User question: {question}
    Recalled memory constraints: {memory}
    Generated Answer: {answer}
    
    Did the geenrated answer adapts its tone, formatting and technical depth to respect the 'what_worked' guidelines or actively avoid the 'pitfall to avoid' 
    listed in the Recalled memory constraints?

    Response exclusively with single JSON block containing a binary statement:
    {{"utilized":true}} OR {{"utilized":false}}
    
    """

    try:
        response = judge_model.generate_content(contents = prompt)
        data = json.loads(response.text.strip().replace("```json","").replace("```",""))
        return bool(data.get("utilized",False))
    
    except Exception as e:
        log.error("Error during the auditing of the recalled memory usage", error = str(e))
        return False


def run_custom_evaluation():
    if not os.path.exists(DATASET_FILE):
        log.error("no evaluation dataset found", error = str(e))
        return
    
    with open(DATASET_FILE, "r", encoding = "utf-8") as f:
        eval_cases = json.load(f)

    run_samples = eval_cases[:3]
    judge_model = GenerativeModel("gemini-2.5-flash")

    detailed_metrics_log = []

    total_queries = len(run_samples)
    queries_with_memory = 0
    total_memories_recalled = 0
    memories_actively_utilized = 0

    with get_checkpointer() as checkpointer:
        checkpointer.setup()
        graph = build_graph(checkpointer)

        for sample in run_samples:
            initial_state={
                "user_id": sample["user_id"],
                "document_id":sample["document_id"],
                "user_question": sample["input_question"],
                "chat_history": [],
                "retrieved_chunks" : None,
                "recalled_memories": None,
                "generated_answer":None
            }

            config = {
                "configurable":{"thread_id":f"custom_eval_{sample['eval_id']}"},
                "metadata":{
                "user_id":sample["user_id"],
                "document_id": sample["document_id"],
                "conversation_id": f"custom_metric_thread_{sample['eval_id']}"
                },
                "tags":["evaluation-harness","custom-metrics-evalrun"]
            }

            final_answer = ""

            #record accurate end-to-end baseline metrics
            e2e_start = time.time()

            try:
                for event, metadata in graph.stream(initial_state, config = config,stream_mode = "messages"):
                    if isinstance(event, AIMessage):
                        final_answer+=event.content

            except Exception as e:
                log.error("llm generation during the test case in custom metrics evaluation failed",eval_id = sample["eval_id"], error = str(e))
                continue

            e2e_latency = (time.time() - e2e_start) * 1000

            #access post-execution state parameteres out of checkpoint boundry
            final_graph_state = graph.get_state(config).values
            print(Fore.YELLOW + f"\n\ninitial state is:{final_graph_state}\n\n" + Fore.RESET)
            recalled_memories = final_graph_state.get("recalled_memories", [])

            #track memory statistics
            if len(recalled_memories) > 0 :
                queries_with_memory+=1
                total_memories_recalled += len(recalled_memories)

            
            # Audit how much memory is used
            memory_utilization_flags= []
            for mem in recalled_memories:
                mem_str= json.dumps(mem)
                mem_used = judge_memory_utilization(judge_model = judge_model, memory = mem_str, question = sample["input_question"],answer = final_answer)
                memory_utilization_flags.append(mem_used)
                if mem_used:
                    memories_actively_utilized +=1

            detailed_metrics_log.append({
                "qusetion": sample["input_question"],
                "e2e_latency_ms": round(e2e_latency),
                "memories_recall_count": len(recalled_memories),
                "memories_utilized_flags":memory_utilization_flags
            })

    #Mathrematical code compilation
    memory_recall_rate = queries_with_memory / total_queries if total_queries > 0 else 0.0
    memory_utilization_rate = memories_actively_utilized / total_memories_recalled if total_memories_recalled > 0 else 0.0

    print(Fore.GREEN + f"""
    \n\n🎯 CUSTOM EPISODIC ENGINE PERFORMANCE METRICS
    \n📊 MEMORY RECALL RATE       : {memory_recall_rate:.2%}
    \n📊 MEMORY UTILIZATION RATE  : {memory_utilization_rate:.2%}
    \n⏱️  AVG END-TO-END LATENCY  : {sum(d['e2e_latency_ms'] for d in detailed_metrics_log)/len(detailed_metrics_log):.2f} ms
    \n\n
    """)
            
    #save the evaluation report to the report file
    report_data = {
        "execution_timestamp": datetime.utcnow().isoformat(),
        "summary":{
            "memory_recall_rate":memory_recall_rate,
            "memory_utilization_rate": memory_utilization_rate,
            "runs":detailed_metrics_log
        }
    }

    with open(REPORT_FILE, "w", encoding = "utf-8") as f:
        json.dump(report_data, f,indent = 2, ensure_ascii = False)


if __name__ == "__main__":
    run_custom_evaluation()
    


