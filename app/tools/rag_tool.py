from crewai.tools import BaseTool
import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
CHROMA_PATH=os.getenv('CHROMA_PATH','./data/chroma')
def get_db(): return Chroma(persist_directory=CHROMA_PATH, embedding_function=OpenAIEmbeddings())
def ingest_document(path: str) -> int:
    loader=PyPDFLoader(path) if path.endswith('.pdf') else TextLoader(path)
    docs=loader.load(); chunks=RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(docs); get_db().add_documents(chunks); return len(chunks)
class RAGSearchTool(BaseTool):
    name: str='rag_search'; description: str='Search internal vector DB. Input: question.'
    def _run(self, query: str) -> str:
        try:
            docs=get_db().similarity_search(query,k=5)
            if not docs: return 'RAG EMPTY: No data. Answer No data and do not invent.'
            return '\n\n---\n\n'.join([f"SOURCE: {d.metadata.get('source')} | {d.page_content[:800]}" for d in docs])
        except Exception as e: return f'RAG ERROR: {e}'
