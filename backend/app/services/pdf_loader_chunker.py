# from langchain_community.document_loaders import PyPDFLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
from docling.document_converter import DocumentConverter
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from langchain_core.documents import Document
from colorama import Fore
from backend.app.core.logging import GLOBAL_LOGGER as log
def load_and_chunk_pdf(
    file_path:str,
    chunk_size:int=1000,
    chunk_overlap:int=100
):

    try:
        converter = DocumentConverter()
        docling_docs = converter.convert(file_path).document
        log.info("PDF successfully converted")
        chunker = HybridChunker()
        chunks = chunker.chunk(dl_doc = docling_docs)
        chunks = list(chunker.chunk(dl_doc=docling_docs))
        chunks = list(chunks)

        log.info(
            "Chunking completed",
            total_chunks=len(chunks)
        )
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
    except Exception as e:
        log.exception(
            "Error while creating chunks",
            file_path=file_path,
        )
        raise
    
    