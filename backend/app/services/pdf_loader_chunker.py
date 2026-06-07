# from langchain_community.document_loaders import PyPDFLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from langchain_core.documents import Document
from colorama import Fore

def load_and_chunk_pdf(
    file_path:str,
    chunk_size:int=1000,
    chunk_overlap:int=100
):

    
    converter = DocumentConverter()
    docling_docs = converter.convert(file_path).document
    
    chunker = HybridChunker()
    chunks = chunker.chunk(dl_doc = docling_docs)
    
    docs=[]
    i=0
    for chunk in chunks:
        if i==3:
            break
        print(Fore.YELLOW + f"\n\nchunk during uploading is:{chunk}\n\n" + Fore.RESET)
        i+=1
    for chunk in chunks:
        headings = chunk.meta.__dict__.get("headings") or []
        heading = headings[0] or None
        docs.append(Document(page_content=chunk.text, metadata= {"heading":heading}))
        
    return docs
    
    