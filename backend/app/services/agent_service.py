from schemas.request import ChatMessageRequest
from collections.abc import AsyncGenerator
import re
from agents.run import Runner,RunConfig
from multi_agent.orchestrator_agent import orchestrator_agent
from utils.response_util import ResponseFactory, ContentKind
from infrastructure.logging.logger import logger
from services.session_servece import session_service
from services.stream_response_service import process_stream_response
class MultiAgentService:
    
    @classmethod
    async def process_task(cls,request:ChatMessageRequest,Flag:bool)->AsyncGenerator:
        """
        处理多智能体任务
        """
        try:
            user_id = request.context.user_id
            session_id = request.context.session_id
            user_query = request.query
            
            chat_history = session_service.prepare_history(user_id, session_id, user_query)
            
            streaming_result = Runner.run_streamed(
                starting_agent=orchestrator_agent,
                input=chat_history,
                max_turns=5,
                run_config=RunConfig(tracing_disabled=True)
            )
            
            async for event in process_stream_response(streaming_result):
                yield event
                
            agent_result = streaming_result.final_output
            
            clean_result = re.sub(r'\n+','\n',agent_result)
            
            chat_history.append({"role":"assistant","content":clean_result})
            
            session_service.save_history(user_id, session_id, chat_history)
        except Exception as e:
            logger.error(f"用户:{user_id}, 会话:{session_id}处理任务失败,原因: {e}")
            text = f"系统错误{str(e)}"
            
            yield "data: " + ResponseFactory.build_text(text, ContentKind.PROCESS).model_dump_json() + "\n\n"
            
            
            if Flag:
                text = f"正在尝试自动重试..."
                yield "data: " + ResponseFactory.build_text(text, ContentKind.PROCESS).model_dump_json() + "\n\n"
                async for event in cls.process_task(request,Flag=False):
                    yield event