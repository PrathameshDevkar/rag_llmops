# from langchain_community.document_loaders import PyPDFLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from langchain_core.documents import Document


def load_and_chunk_pdf(
    file_path:str,
    chunk_size:int=1000,
    chunk_overlap:int=100
):
    
    # loader=PyPDFLoader(file_path)
    # docs=loader.load()
    
    # splitter= RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    # chunks=splitter.split_documents(docs)
    
    # return chunks
    
    converter = DocumentConverter()
    docling_docs = converter.convert(file_path).document
    
    chunker = HybridChunker()
    chunks = chunker.chunk(dl_doc = docling_docs)
    
    docs=[]
    for chunk in chunks:
        docs.append(Document(page_content=chunk.text, metadata= {"heading":chunk.meta.__dict__["headings"][0]}))
        
    return docs
    
    