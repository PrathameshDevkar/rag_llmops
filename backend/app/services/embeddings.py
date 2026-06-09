from langchain_huggingface import HuggingFaceEmbeddings
from backend.app.services.model_loader import get_embedding_model
# while running the backend with uvicorn it takes more time now maybe beaceaus of this model loading, check it once

embedding_model= get_embedding_model()
def embed_text(text:str) -> list[float]:
    try:
        embeddings=embedding_model.embed_query(text)
        return embeddings
    except Exception as e:
        print("error during the embeddings generation",e)
        return []
    