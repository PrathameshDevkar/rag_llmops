from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_and_chunk_pdf(
    file_path:str,
    chunk_size:int=1000,
    chunk_overlap:int=100
):
    
    loader=PyPDFLoader(file_path)
    docs=loader.load()
    
    splitter= RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks=splitter.split_documents(docs)
    
    return chunks