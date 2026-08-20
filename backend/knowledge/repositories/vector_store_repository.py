

from langchain_chroma import Chroma
from config.settings import settings
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
import logging
from typing import List, Dict, Any
import torch


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




class VectorStoreRepository:

    def __init__(self ):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"当前使用设备: {self.device}")
        self.embeddings = HuggingFaceEmbeddings(
            model_name=r"E:\embedding\bge-m3",
            model_kwargs={"trust_remote_code": True, "device": self.device},   # BGE-M3 有自定义模型代码，需要这个
            encode_kwargs={"normalize_embeddings": True, "batch_size": 16},
        )
        self.vector_database = Chroma(
            persist_directory=settings.VECTOR_STORE_PATH,
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedding_function=self.embeddings
            
        )
        
    def add_documents(self, documents: list,batch:int=16)->int:
        """Add documents to the vector store"""
        total_documents_chunks = len(documents)
        
        documents_chunks_added = 0
        try:
            for i in range(0, total_documents_chunks, batch):
                ba = documents[i:i+batch]
                self.vector_database.add_documents(ba)
                documents_chunks_added += len(ba)
                logger.info(f"成功添加 {len(ba)} 个文档到向量存储。当前进度: {documents_chunks_added}/{total_documents_chunks}")
        except Exception as e:
            logger.error(f"添加文档到向量存储时发生错误: {e}")
            raise e
        return documents_chunks_added
        
    def embedd_document(self,text:str)->List[float]:
        """Embed a single document"""
        return self.embeddings.embed_query(text)
        
    def embedd_documents(self,texts:List[str])->List[List[float]]:
        """Embed multiple documents"""
        return self.embeddings.embed_documents(texts)
    
    
    def search_similarity_with_score(self,user_question:str,top_k:int=5)->List[tuple[Document, float]]:
        
        results = self.vector_database.similarity_search_with_score(user_question, k=top_k)
        if not results:
            logger.warning(f"未在向量存储中找到与问题 '{user_question}' 相关的文档。")
            raise ValueError(f"未在向量存储中找到与问题 '{user_question}' 相关的文档。")
        return results