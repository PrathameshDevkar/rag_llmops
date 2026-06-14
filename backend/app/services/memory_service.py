import json
from sqlalchemy.orm import Session
from litellm import completion
from backend.app.core.config import settings
from backend.app.models.memories import Memories
from backend.app.repositories.memories_repositories import MemoriesRepository
from backend.app.services.model_loader import get_embedding_model
from colorama import Fore
from langsmith import traceable

reflection_prompt_template="""
You are analyzing conversations about research papers to create memories that will help guide future interactions. Your task is to extract key elements that would be most helpful when encountering similar academic discussions in the future.

Review the conversation and create a memory reflection following these rules:

1. For any field where you don't have enough information or the field isn't relevant, use "N/A"
2. Be extremely concise - each string should be one clear, actionable sentence
3. Focus only on information that would be useful for handling similar future conversations
4. Context_tags should be specific enough to match similar situations but general enough to be reusable

Output valid JSON in exactly this format:
{{
    "context_tags": [              // 2-4 keywords that would help identify similar future conversations
        string,                    // Use field-specific terms like "deep_learning", "methodology_question", "results_interpretation"
        ...
    ],
    "conversation_summary": string, // summary of describing what the conversation accomplished
    "what_worked": string,         // Most effective approach or strategy used in this conversation
    "what_to_avoid": string        // Most important pitfall or ineffective approach to avoid
}}

Examples:
- Good context_tags: ["transformer_architecture", "attention_mechanism", "methodology_comparison"]
- Bad context_tags: ["machine_learning", "paper_discussion", "questions"]

- Good conversation_summary: "Explained how the attention mechanism in the BERT paper differs from traditional transformer architectures"
- Bad conversation_summary: "Discussed a machine learning paper"

- Good what_worked: "Using analogies from matrix multiplication to explain attention score calculations"
- Bad what_worked: "Explained the technical concepts well"

- Good what_to_avoid: "Diving into mathematical formulas before establishing user's familiarity with linear algebra fundamentals"
- Bad what_to_avoid: "Used complicated language"

Additional examples for different research scenarios:

Context tags examples:
- ["experimental_design", "control_groups", "methodology_critique"]
- ["statistical_significance", "p_value_interpretation", "sample_size"]
- ["research_limitations", "future_work", "methodology_gaps"]

Conversation summary examples:
- "Clarified why the paper's cross-validation approach was more robust than traditional hold-out methods"
- "Helped identify potential confounding variables in the study's experimental design"

What worked examples:
- "Breaking down complex statistical concepts using visual analogies and real-world examples"
- "Connecting the paper's methodology to similar approaches in related seminal papers"

What to avoid examples:
- "Assuming familiarity with domain-specific jargon without first checking understanding"
- "Over-focusing on mathematical proofs when the user needed intuitive understanding"

Do not include any text outside the JSON object in your response.
"""
@traceable(name = "Episodic memory synthesis engine", run_type = "chain")
def add_episodic_memory(db:Session, user_id: str, conversation_id:str, chat_turn_text:str):
    """
    Analyzes a cht turn using litellm, extracts structure episodic metadata, 
    embeds it and saves it to production pgvector memories table
    """
    
    embedding_model = get_embedding_model()
    
    messages = [
        {"role":"system", "content":reflection_prompt_template},
        {"role":"user","content":f"Analyze this interaction:\n{chat_turn_text}"}
    ]
    
    try:
        response = completion(
            model = "huggingface/meta-llama/Llama-3.1-8B-Instruct",
            messages=messages,
            api_key=settings.HUGGINGFACE_API_KEY
        )
        
        cleaned_content = response.choices[0].message.content.strip()
        
        #clean up the markdown json blocks given by the model
        if cleaned_content.startswith("```json"):
            cleaned_content = cleaned_content[7:-3].strip()
        elif cleaned_content.startswith("```"):
            cleaned_content = cleaned_content[3:-3].strip()
            
        result = json.loads(cleaned_content)
        
        #embed the summary text for vector similarity matching later
        text_to_embed = result.get("conversation_summary","N/A")
        conv_summary_emb = embedding_model.embed_query(text_to_embed)
        
        #bundle the full structure result into a json string for teh DB text field
        compiled_content = json.dumps({
            "context_tags":result.get("context_tags",[]),
            "conversation_summary":text_to_embed,
            "what_worked":result.get("what_worked","N/A"),
            "what_to_avoid":result.get("what_to_avoid","N/A")
        })
        db_memory = Memories(
            user_id = user_id,
            conversation_id = conversation_id,
            memory_type = "episodic_memory",
            content = compiled_content,
            embedding = conv_summary_emb
        )
        
        memories_repo = MemoriesRepository(db)
        memories_repo.create(db_memory)
        print(Fore.YELLOW + "episodic memory added succesfully" + Fore.RESET)
        
    except Exception as e:
        db.rollback()
        print(Fore.RED + f"error during adding the episodic memory in dataabse:\n{e}" + Fore.RESET)
        
    