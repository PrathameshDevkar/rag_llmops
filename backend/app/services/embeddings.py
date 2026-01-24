from langchain_huggingface import HuggingFaceEmbeddings

# while running the backend with uvicorn it takes more time now maybe beaceaus of this model loading, check it once

embedding_model= HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-l6-v2")
def embed_text(text:str) -> list[float]:
    try:
        embeddings=embedding_model.embed_query(text)
        return embeddings
    except Exception as e:
        print("error during the embeddings generation",e)
        return []
    