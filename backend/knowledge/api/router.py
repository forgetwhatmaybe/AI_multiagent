import os

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.concurrency import run_in_threadpool
from services.ingestion.ingestion_processor import IngestionProcessor
import tempfile
import logging
import aiofiles
from schemas.schema import UploadResponse,QueryResponse,QueryRequest
from services.retrieval_serveice import RetrievalService
from services.query_service import QueryService
from config.settings import settings
import shutil

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


router = APIRouter()
ingestion_processor = IngestionProcessor()
retrieval_service = RetrievalService()
query_service = QueryService()


@router.post("/upload", summary="知识库上传", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...), description: str | None = Form(None)
):
    try:
        temp_md_dir = settings.MD_FOLDER_PATH
        file_surffix = os.path.splitext(file.filename)[1]
        temp_md_path = os.path.join(temp_md_dir, file.filename)
        
        
        if not os.path.exists(temp_md_path):
            os.makedirs(temp_md_dir, exist_ok=True)

        async with aiofiles.tempfile.NamedTemporaryFile(
            suffix=file_surffix, delete=False
        ) as temp_file:

            uploaded_file_content = await file.read()
            await temp_file.write(uploaded_file_content)

            temp_file_path = temp_file.name
        shutil.move(temp_file_path, temp_md_path)


        chunks_added = await run_in_threadpool(ingestion_processor.ingest_file, temp_md_path)

        return UploadResponse(
            status="success",
            message=f"文件 {file.filename} 已成功上传并添加到知识库。",
            file_name=file.filename,
            chunks_added=chunks_added,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传知识库失败: {str(e)}")

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.info(f"临时文件 {temp_file_path} 已删除。")

@router.post("/query", summary="查询知识库", response_model=QueryResponse)
async def query(
    request:QueryRequest
):
    try:
        user_question = request.question
        
        if not user_question:
            raise HTTPException(status_code=500,detail="查询问题不存在")
        
        retrieval_context = retrieval_service.retrieval(user_question)
        
        answer = query_service.generate_answer(user_question,retrieval_context)
        
        return QueryResponse(
            question=user_question,
            answer=answer
        )
    except Exception as e:
        logger.error(f"调用查询知识库服务失败:原因:{e}")
        raise HTTPException(status_code=500,detail="服务内部出现异常")
    
    