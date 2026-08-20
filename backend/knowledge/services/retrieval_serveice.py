from typing import List
from langchain_core.documents import Document
from utils.markdown_utils import MarkDownUtils
from typing import Dict, Any
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from config.settings import settings
import jieba
from sklearn.metrics.pairwise import cosine_similarity
from services.ingestion.ingestion_processor import  IngestionProcessor

from repositories.vector_store_repository import VectorStoreRepository
import re




class RetrievalService:

    # RRF(Reciprocal Rank Fusion) 融合参数:k 越大,排名带来的权重差异越小
    RRF_K = 60
    # 最终返回给 LLM 的文档数
    TOP_RETRIEVAL = 5

    def __init__(self):
        self.chroma_vector = VectorStoreRepository()
        self.spliter = IngestionProcessor()

    def retrieval(self, user_question: str) -> List[Document]:
        # 两路各自取更多候选,保留各自的排名(列表顺序即排名)
        based_vector_candidates = self._search_based_vector(user_question)
        based_title_candidates = self._search_based_title(user_question)

        # 用 RRF 融合两路结果,按融合分降序返回
        return self._rrf_fusion(based_vector_candidates, based_title_candidates, top_n=self.TOP_RETRIEVAL)

    def _search_based_vector(self, user_question: str) -> List[Document]:
        documents_with_score = self.chroma_vector.search_similarity_with_score(user_question, top_k=10)
        return [doc for doc, score in documents_with_score]
    
    def _search_based_title(self,user_question:str)->List[Document]:
        mds_metadata = MarkDownUtils.collect_md_metadata(settings.MD_FOLDER_PATH)
        rough_mds_title = self.rough_ranking(user_question,mds_metadata)
        finally_mds_metadata = self.final_ranking(user_question,rough_mds_title)
        based_title_candidates = []
        for final_md in finally_mds_metadata:
            try:
                with open(final_md["path"], "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    
                if len(content)< 3000:
                    doc = Document(page_content=content,metadata={
                        'path': final_md["path"],
                        'title': final_md['title']
                    })
                    based_title_candidates.append(doc)
                else:
                    doc_chunks = self._deal_long_title_content(content,final_md,user_question)
                    based_title_candidates.extend(doc_chunks)
            except Exception as e:
                logger.error(f"读取文件 {final_md['path']} 时发生错误: {e}")
                return []
        return based_title_candidates
    
    @staticmethod
    def _candidate_key(document: Document) -> tuple:
        """生成候选文档的去重 key:去掉「文档来源:」前缀后,取 title + 内容前100字符。"""
        clean_content = re.sub(r'^文档来源:.*?(?=(\n|#))', '', document.page_content, flags=re.DOTALL).strip()
        return (document.metadata.get('title', ''), clean_content[:100])

    def _rrf_fusion(
        self,
        vector_candidates: List[Document],
        title_candidates: List[Document],
        top_n: int = 5,
    ) -> List[Document]:
        """RRF 融合:对每条候选,按「它在每一路中的排名」累加 1/(k+rank)。

        同一份内容出现在两路时,key 相同 → 分数累加 → 排更靠前。
        """
        scores: Dict[tuple, List] = {}  # key -> [rrf_score, doc]

        def accumulate(candidates: List[Document]) -> None:
            for rank, doc in enumerate(candidates):
                key = self._candidate_key(doc)
                add_score = 1.0 / (self.RRF_K + rank + 1)  # rank 从 0 开始
                if key in scores:
                    scores[key][0] += add_score
                else:
                    scores[key] = [add_score, doc]

        accumulate(vector_candidates)
        accumulate(title_candidates)

        ranked = sorted(scores.values(), key=lambda x: x[0], reverse=True)
        return [doc for _, doc in ranked[:top_n]]

    def _deal_long_title_content(self,content:str,final_md:Dict[str,Any],user_question:str):
        doc_chunks = self.spliter.document_spliter.split_text(content)
        
        doc_chunks_title = final_md['title']
        
        doc_chunks_inject_title = [f'文档来源:{doc_chunks_title}'+doc_chunk for doc_chunk in doc_chunks]
        
        query_embedding = self.chroma_vector.embedd_document(user_question)
        
        
        doc_chunk_embeddings = self.chroma_vector.embedd_documents(doc_chunks_inject_title)
        
        
        doc_chunk_similarity = cosine_similarity([query_embedding],doc_chunk_embeddings).flatten()
        
        
        top_doc_chunks_indices = doc_chunk_similarity.argsort()[-3:][::-1]
        
        
        docs = []
        for index,idx in enumerate(top_doc_chunks_indices):
            doc = Document(
                page_content=doc_chunks_inject_title[idx],
                metadata={
                    'path':final_md["path"],
                    'title':final_md['title'],
                    'chunk_index':int(idx),
                    'similarity':float(doc_chunk_similarity[idx])
                }
            )
            docs.append(doc)
        return docs
        
        
        
        
    
    
    
    def final_ranking(self,user_question:str,rough_mds_title:List[Dict[str,Any]])->List[Dict[str,Any]]:
        if not user_question or not rough_mds_title:
            return []
        query_embedding = self.chroma_vector.embedd_document(user_question)
        candidate_embeddings = [md["title"] for md in rough_mds_title]
        rough_title_embeddings = self.chroma_vector.embedd_documents(candidate_embeddings)
        similarities = cosine_similarity([query_embedding], rough_title_embeddings).flatten()
        ROUGH_WEIGHT=0.3
        SIM_WEIGHT=0.7
        for index,md_metadata in enumerate(rough_mds_title):
            sim = similarities[index]
            if sim<0:
                sim = 0
            roughing_score = md_metadata.get("roughing_score", 0)
            final_score = ROUGH_WEIGHT * roughing_score + SIM_WEIGHT * sim
            md_metadata["sim_score"] = sim
            md_metadata["final_score"] = final_score
        # 标题路也取更多候选,供 RRF 融合
        return sorted(rough_mds_title, key=lambda x: x.get("final_score", 0), reverse=True)[:10]
        
        
    
    def rough_ranking(self,user_question,mds_metadata:List[Dict[str,Any]])->List[Dict[str,Any]]:
        if not user_question or not mds_metadata:
            return []
        rough_word_weight = 0.7
        
        for md_metadata in mds_metadata:
            md_title = md_metadata.get("title", "")
            if not md_title or not md_title.strip():
                continue
            user_query_char = set(user_question)
            md_metadata_title_char = set(md_title)
            
            unique_char = len(user_query_char | md_metadata_title_char)
            char_score = len(user_query_char & md_metadata_title_char) / unique_char if unique_char > 0 else 0
            
            user_query_words = set(jieba.cut(user_question))
            md_metadata_title_words = set(jieba.cut(md_title))
            
            unique_words = len(user_query_words | md_metadata_title_words)
            word_score = len(user_query_words & md_metadata_title_words) / unique_words if unique_words > 0 else 0
            
            rough_score = (1 - rough_word_weight) * char_score + rough_word_weight * word_score
            md_metadata["roughing_score"] = rough_score
            
        return sorted(mds_metadata, key=lambda x: x.get("roughing_score", 0), reverse=True)[:50]
            
                
if __name__ == "__main__":
    retrival_service = RetrievalService()
    # rough_ranking_result = retrival_service.rough_ranking("电脑如何开机",MarkDownUtils.collect_md_metadata(settings.MD_FOLDER_PATH))  
    
    # for roughing_result in rough_ranking_result[:5]:
    #     print(roughing_result)
    
    # retrieval_result = retrival_service.final_ranking("电脑如何开机",rough_ranking_result[:10])
    # for final_result in retrieval_result[:5]:
    #     print(final_result)
    result = retrival_service.retrieval("联想手机K900常见问题")
    for a in result:
        print(a)