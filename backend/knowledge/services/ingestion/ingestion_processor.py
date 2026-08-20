from repositories.vector_store_repository import VectorStoreRepository
from config.settings import settings
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.utils import filter_complex_metadata
from pathlib import Path
import sys
import os
from utils.markdown_utils import MarkDownUtils
import logging
import chromadb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# def _resolve_demo_markdown_path() -> Path:
#     if len(sys.argv) > 1:
#         candidate = Path(sys.argv[1]).expanduser()
#         if candidate.exists():
#             return candidate
#         raise FileNotFoundError(f"指定的 Markdown 文件不存在: {candidate}")

#     default_dir = Path(settings.MD_FOLDER_PATH)
#     preferred_file = default_dir / "0429-联想手机K900常见问题汇总.md"
#     if preferred_file.exists():
#         return preferred_file

#     first_markdown = next(default_dir.glob("*.md"), None)
#     if first_markdown is not None:
#         return first_markdown

#     raise FileNotFoundError(f"未在 {default_dir} 找到可导入的 Markdown 文件")


class IngestionProcessor:
    def __init__(self):
        self.vector_store = VectorStoreRepository()
        self.document_spliter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
            separators=["\n##", "\n**", "\n\n", "\n", " "],
        )

    def split_file(self, md_path: str) -> list:
        """加载并切分 Markdown 文件，返回处理后的 Document chunk 列表（不入库）。"""
        try:
            text_loader = TextLoader(md_path, encoding="utf-8")
            documents = text_loader.load()
        except Exception as e:
            logger.error(f"加载文件 {md_path} 时发生错误: {e}")
            raise Exception(f"加载文件 {md_path} 时发生错误: {e}")

        for doc in documents:
            doc.metadata['title'] = MarkDownUtils.extract_title(md_path)

        # 2.切分文档得到文档块列表
        # 2.1 动态机制切分
        # a.如果文档内容不大，直接将这内容作为一个chunk(不用切分)
        # b.如果内容比较大，分析大内容的数据结构，然后为他定制切分策略。采用header rejection:标题注入（保留没一块的业务背景、上下文）

        final_document_chunks = []
        for doc in documents:
            if len(doc.page_content) < 3000:  # 评估一下小文件的内容长度（获取一个平均值）
                # a.不用切分
                final_document_chunks.append(doc)
            else:
                documents_chunks_list = self.document_spliter.split_documents([doc])
                # b:没每个文档块的page_content注入标题（作为块的背景）
                # page_content:来源:联想手机K900常见问题汇总 问题1：如何插拔SIM卡 K900采用Micro-Sim卡
                for document_chunk in documents_chunks_list:
                    # 1.获取每一个文档块的标题
                    chunk_source = document_chunk.metadata['source']
                    title = os.path.basename(chunk_source)
                    # 2.拼接到每一个文档块的page_content上
                    document_chunk.page_content = f"文档来源:{title}\n{document_chunk.page_content}"
                final_document_chunks.extend(documents_chunks_list)

        # 3.切分后文档块的元数据校验(过滤不被向量数据库支持的元数据清除掉)
        clean_documents_chunks = filter_complex_metadata(final_document_chunks)

        # 4. 无效性检查（校验page_content的是否合法（不能为空））
        valid_documents_chunks = [document for document in clean_documents_chunks if document.page_content.strip()]
        return valid_documents_chunks

    def ingest_file(self, md_path: str) -> int:
        """加载、切分并入库单个 Markdown 文件，返回入库的 chunk 数。"""
        valid_documents_chunks = self.split_file(md_path)
        if not valid_documents_chunks:
            logger.error("切分后的文档块没有任何的内容")
            return 0
        # 5.存储文档块到向量数据库
        total_documents_chunks = self.vector_store.add_documents(valid_documents_chunks)
        # 6.返回保存成功的文档块数
        return total_documents_chunks


if __name__ == "__main__":
    # text_loader = TextLoader(file_path="C:\\Users\\Administrator\\Desktop\\0004-开机之后无任何反应怎么办？.md",encoding="utf-8")
    # # b. 加载文件返回文档列表(TextLoader返回的文档列表中有且只有一个文档对象)
    # documents = text_loader.load()
    # for doc  in documents:
    #     print(doc.page_content)

    # from langchain_community.document_loaders import UnstructuredMarkdownLoader

    # loader = UnstructuredMarkdownLoader(
    #     "C:\\Users\\Administrator\\Desktop\\0004-开机之后无任何反应怎么办？.md",
    #     mode="single",
    #     strategy="fast",
    # )
    # docs = loader.load()
    # print(docs[0].metadata)
    # print(docs[0].page_content)

    ingest_processor = IngestionProcessor()
    client = chromadb.PersistentClient(path=settings.VECTOR_STORE_PATH)
    col = client.get_collection(name=settings.CHROMA_COLLECTION_NAME)
    ids = col.get()['ids']
    if ids:
        col.delete(ids=ids)
        logger.info(f"已清空向量存储中的所有文档。")
    else:
        logger.info(f"向量存储中没有任何文档。")
    
    dir_path = Path(settings.MD_FOLDER_PATH)
    all_chunks = []
    for md_path in dir_path.glob("*.md"):
        chunks = ingest_processor.split_file(str(md_path))
        all_chunks.extend(chunks)

    total = ingest_processor.vector_store.add_documents(all_chunks)
    logger.info(f"全量导入完成，共入库 {total} 个文档块。")
    # sample_md_path = _resolve_demo_markdown_path()
    # logger.info(f"开始导入 Markdown 文件: {sample_md_path}")
    # ingest_processor.ingest_file(str(sample_md_path))
