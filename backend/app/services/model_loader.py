from functools import lru_cache
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace, HuggingFaceEmbeddings
from backend.app.core.config import settings
from google import genai

@lru_cache
def get_llm():

    llm = HuggingFaceEndpoint(
        model="meta-llama/Llama-3.1-8B-Instruct",
        huggingfacehub_api_token=settings.HUGGINGFACE_API_KEY
    )

    return ChatHuggingFace(llm=llm)
    # client = genai.Client(api_key = settings.GEMINI_API_KEY)


@lru_cache
def get_embedding_model():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

