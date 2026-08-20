from fastapi.routing import APIRouter
from schemas.request import ChatMessageRequest,UserSessionsRequest
from starlette.responses import StreamingResponse
from services.agent_service import MultiAgentService
from infrastructure.logging.logger import logger
from services.session_servece import session_service

router = APIRouter()

@router.post("/api/query",summary="智能体对话端口")
async def query(request_content:ChatMessageRequest)->StreamingResponse:
    user_id = request_content.context.user_id
    session_id = request_content.context.session_id
    user_query = request_content.query
    
    logger.info(f"用户:{user_id}, 会话:{session_id}, 输入:{user_query}")
    
    async_generator_result = MultiAgentService.process_task(request_content, Flag=True)
    
    return StreamingResponse(
        content=async_generator_result,
        media_type='text/event-stream',
        status_code=200,
    )
@router.post("/api/user_sessions")
def get_user_sessions(request: UserSessionsRequest):
    """
    获取用户的所有会话记忆数据。

    Args:
        request: 包含 user_id 的请求体。

    Returns:
        包含用户所有会话信息和记忆的 JSON 响应。
    """
    # 1. 日志记录：记录请求到达
    logger.info("接收到获取用户会话请求")

    # 2. 参数提取：从请求模型中获取目标用户ID
    user_id = request.user_id
    logger.info(f"获取用户 {user_id} 的所有会话记忆数据")

    try:
        # 3. 服务调用 session_service 从底层存储检索所有历史会话
        all_sessions =session_service.get_all_sessions_memory(user_id)
        logger.debug(f"成功获取用户 {user_id} 的 {len(all_sessions)} 个会话")

        # 4. 响应构建：组装并返回标准化的成功 JSON 数据
        return {
            "success": True,
            "user_id": user_id,
            "total_sessions": len(all_sessions),
            "sessions": all_sessions
        }
    except Exception as e:
        # 5. 异常处理：捕获服务层抛出的未知错误，记录日志并返回错误标识
        logger.error(f"获取用户 {user_id} 的会话数据时出错: {str(e)}")
        return {
            "success": False,
            "user_id": user_id,
            "error": str(e)
        }