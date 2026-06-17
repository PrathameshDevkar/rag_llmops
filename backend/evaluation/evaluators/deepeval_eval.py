from accelerate import big_modeling
from accelerate import big_modeling
from deepeval.evaluate import AsyncConfig
import os
from pathlib import Path
import time
import json
import asyncio
import pandas as pd
from datetime import datetime

# from google import genai
from google.cloud import aiplatform
import vertexai
from vertexai.generative_models import GenerativeModel



from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.models.base_model import DeepEvalBaseLLM
from deepeval.metrics import (
    AnswerRelevancyMetric,
    FaithfulnessMetric,
    HallucinationMetric,
    ContextualPrecisionMetric,
    ContextualRecallMetric
)
from deepeval.models import GeminiModel

from backend.app.core.logging import GLOBAL_LOGGER as log
from backend.app.rag.checkpoint import get_checkpointer
from backend.app.rag.graph import build_graph
from backend.app.services.model_loader import get_llm
from backend.app.core.config import settings
from langchain_core.messages import AIMessage

from colorama import Fore

#Define relative paths
CURRENT_DIR= Path(__file__).resolve().parents[1]
DATASET_FILE = os .path.join(CURRENT_DIR, "datasets", "rag_dataset.json")
REPORT_DIR = Path(CURRENT_DIR,"reports")
REPORT_FILE = Path(REPORT_DIR, "deepeval_report.json")

# client = genai.Client(api_key = settings.GEMINI_API_KEY)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\Prathamesh\prathamesh\llmops_rag_langgraph\vertexai-free-credits-api-key.json"
vertexai.init(project = "poised-cortex-462609-n4", location = "us-central1")


class DeepEvalCustomLlama(DeepEvalBaseLLM):
    """
    Custom deepeval model wrapper that intercepts framework evaluation prompts
    and pipes them down to your local llama instance
    """
    def __init__(self, model):
        self.model = GenerativeModel(model)

    def load_model(self):
        return self.model

    def generate(self, prompt: str) -> str:
        #add a tiny throttling window to prevent free tier 429 bursts
        time.sleep(4.0)

        #using the geminin client
        # response = client.models._generate_content(
        #             model = self.model,
        #             contents = prompt
        # )
        # return response.text

        #using vertexai
        response = self.model.generate_content(contents = prompt)
        return response.text


    async def a_generate(self,prompt:str) -> str:
        #handel asynchronous execution tasks inside the deepeval metrics
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.generate, prompt)

    def get_model_name(self):
        # return "Llama-3.1-8B-Instruct"
        return "gemini-2.5-flash"

def run_deepeval_harness():
    """
    loads the synthetic golden dataset, executes the langraph state machine
    and runs Deepeval's metric pipeline using our custom local model handler.
    """

    if not os.path.exists(DATASET_FILE):
        log.error(f"No golden dataset found at path:{DATASET_FILE}")

    log.info("loading the golden dataset", source = DATASET_FILE)

    with open(DATASET_FILE, "r", encoding = "utf-8") as f:
        eval_cases = json.load(f)

    run_samples = eval_cases[:3]

    test_cases_pool = []
    hallucination_test_cases_pool = []
    with get_checkpointer() as checkpointer:
        checkpointer.setup()
        graph = build_graph(checkpointer)

        for sample in run_samples:
            initial_state = {
                "user_id": sample["user_id"],
                "document_id": sample["document_id"],
                "user_question": sample["input_question"],
                "chat_history":[],
                "retrieved_chunks":None,
                "recalled_memories":None,
                "generated_answer": None
            }

            config ={
                "configurable":{"thread_id":f"deepeval_thread_{sample['eval_id']}"},
                "metadata":{
                    "user_id":sample["user_id"],
                    "document_id": sample["document_id"],
                    "conversation_id": f"deepeval_thread_{sample['eval_id']}"
                },
                "tags":["evaluation-harness", "deepeval-test-run"]
            }

            final_answer=""
            try:
                for event, metadata in graph.stream(initial_state, config = config, stream_mode = "messages"):
                    if isinstance(event, AIMessage):
                        final_answer+=event.content

                final_graph_state = graph.get_state(config).values
                retrieved_chunks = final_graph_state.get("retrieved_chunks",[])
            
            except Exception as e:
                log.error("llm generation during the test case in custom metrics evaluation failed",eval_id = sample["eval_id"], error = str(e))
                continue
            
            if not retrieved_chunks:
                retrieved_chunks = ["no chunks retrieved by the database retriever"]

            #buils deepeval test cases
            test_case = LLMTestCase(
                input = sample["input_question"],
                actual_output = final_answer if final_answer else "final answer context is empty",
                expected_output = sample["ground_truth_answer"],
                retrieval_context = retrieved_chunks
            )

            hallucination_test_case = LLMTestCase(
                input = sample["input_question"],
                actual_output = final_answer if final_answer else "final answer context is empty",
                context = retrieved_chunks
            )

            test_cases_pool.append(test_case)
            hallucination_test_cases_pool.append(hallucination_test_case)

    if not test_cases_pool:
        log.error("deepeval aborted as there are no deepeval test cases")
        return

    # eval_llm = GeminiModel(
    #         model = "gemini-2.0-flash",
    #         api_key = settings.GEMINI_API_KEY,
    #         temperature=0
    # )
    local_judge = DeepEvalCustomLlama("gemini-2.5-flash")

    #configure target evaluation metrics with our custom judge model
    answer_relevancy =  AnswerRelevancyMetric(threshold = 0.5, model = local_judge, include_reason = True)
    faithfulness = FaithfulnessMetric(threshold = 0.5, model = local_judge, include_reason = True)
    hallucination = HallucinationMetric(threshold=0.5, model = local_judge, include_reason = True, verbose_mode = True)
    context_recall = ContextualRecallMetric(threshold = 0.5, model = local_judge, include_reason = True)
    context_precision = ContextualPrecisionMetric(threshold = 0.5, model = local_judge, include_reason= True)

    # metrics = [answert_relevancy,faithfulness,context_precision, context_recall]
    metrics = [answer_relevancy]

    scores = evaluate(
        test_cases = test_cases_pool,
        metrics = metrics,
        async_config=AsyncConfig(run_async=False) # removes the concurrency in the code, so that the api request will be in sequence. avoids sending multiple api requests so that resources wont get exhausted
    )
    print(Fore.GREEN + f"\n\nthe scores are:{scores}\n\n" + Fore.RESET)

    hallucination_score = evaluate(
        test_cases = hallucination_test_cases_pool,
        metrics = [hallucination],
        async_config=AsyncConfig(run_async=False)
    )
    print(Fore.GREEN + f"\n\nthe hallucination evaluation result is:{hallucination_score}\n\n" + Fore.RESET)

    detailed_test_runs = []
    for tc in test_cases_pool:
        detailed_test_runs.append({
            "question": tc.input,
            "actual_answer": tc.actual_output,
            "ground_truth": tc.expected_output,
            "context": tc.retrieval_context
        })

    report_output = {
        "execution_timestamp": datetime.utcnow().isoformat(),
        "score":str(scores),
        "hallucination_score": str(hallucination_score),
        "detailed_test_runs":detailed_test_runs
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report_output, f, indent=2, ensure_ascii = False)
    
    log.info("✅ DeepEval validation successfully finished", report_file = REPORT_FILE)


if __name__ == "__main__":
    run_deepeval_harness()

    

