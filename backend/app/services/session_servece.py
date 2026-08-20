from repositories.session_repository import session_repository
from typing import List, Dict, Any
from json import JSONDecodeError
from infrastructure.logging.logger import logger

class SessionService:
    
    DEFAULT_SESSION_ID = "default_session"
    
    def __init__(self):
        self._repo = session_repository
        
        
    def prepare_history(self,user_id:str,session_id:str,user_input:str,max_turn:int=3)->List[Dict[str,Any]]:
        """
        准备用户历史会话数据，供模型使用。
        
        Args:
            user_id (str): 用户ID
            session_id (str): 会话ID
            max_turn (int): 最大对话轮数，默认3
        
        Returns:
            List[Dict[str, Any]]: 历史会话数据列表，每条数据包含角色和内容。
        """
        chat_history = self.load_history(user_id, session_id)
        
        chat_history.append({"role": "user", "content": user_input})
        
        truncate_history = self._truncate_history(chat_history, max_turn)
        
        return truncate_history
        
    def load_history(self, user_id:str, session_id:str)->List[Dict[str,Any]]:
        """
        加载用户历史会话数据。
        
        Args:
            user_id (str): 用户ID
            session_id (str): 会话ID
        
        Returns:
            List[Dict[str, Any]]: 历史会话数据列表，每条数据包含角色和内容。
        """
        target_session_id = session_id if session_id else self.DEFAULT_SESSION_ID
        try:
            session_history = self._repo.load_session(user_id, target_session_id)
            if session_history is None:
                return self._init_system_msg_instruct(target_session_id)
            return session_history
        except JSONDecodeError as e:
            logger.error(f"用户:{user_id}, 会话:{target_session_id}读取失败,原因: {e}")
            return [{"role": "system", "content": "用户对话文件读取失败."}]
        
    def save_history(self, user_id:str, session_id:str, history:List[Dict[str,Any]])->None:
        """
        保存用户历史会话数据。
        
        Args:
            user_id (str): 用户ID
            session_id (str): 会话ID
            history (List[Dict[str, Any]]): 历史会话数据列表，每条数据包含角色和内容。
        """
        if not history:
            return  # 如果历史为空，则不保存
        target_session_id = session_id if session_id else self.DEFAULT_SESSION_ID
        try:
            self._repo.save_session(user_id, target_session_id, history)
        except Exception as e:
            logger.error(f"用户:{user_id}, 会话:{target_session_id}保存失败,原因: {e}")
        
    def _init_system_msg_instruct(self, session_id:str)->List[Dict[str,Any]]:
        """
        初始化会话历史数据，添加系统指令。
        
        Args:
            session_id (str): 会话ID
        
        Returns:
            List[Dict[str, Any]]: 初始化后的会话历史数据列表。
        """
        system_instruction = {
            "role": "system",
            "content": f"你是一个有记忆的智能体助手,请基于上下文历史对话内容进行回答,当前会话ID为: {session_id}"
        }
        return [system_instruction]
    
    def _truncate_history(self, history:List[Dict[str,Any]], max_turn:int)->List[Dict[str,Any]]:
        """
        截断历史会话数据，保留最近的max_turn轮对话。
        
        Args:
            history (List[Dict[str, Any]]): 历史会话数据列表
            max_turn (int): 最大对话轮数
        
        Returns:
            List[Dict[str, Any]]: 截断后的历史会话数据列表。
        """
        system_msg = [msg for msg in history if msg["role"] == "system"]
        
        user_assistant_msgs = [msg for msg in history if msg["role"] != "system"]
        
        msg_limit = max_turn * 2  # 每轮对话包含用户和助手两条消息
        
        
        truncate_msg = user_assistant_msgs[-msg_limit:] if len(user_assistant_msgs) > msg_limit else user_assistant_msgs
        
        return system_msg + truncate_msg
    
    def get_all_sessions_memory(self, user_id: str) -> List[Dict[str, Any]]:
        """获取并格式化用户的所有会话列表（用于前端侧边栏展示）。

        Args:
            user_id: 用户唯一标识。

        Returns:
            List[Dict]: 按创建时间倒序排列的会话列表。
            格式示例:
            [
                {
                    "session_id": "...",
                    "create_time": "...",
                    "memory": [...],
                    "total_messages": 5
                }, ...
            ]
        """
        # 1. 从 Repo 获取原始元数据
        # 类型提示: List[Tuple[session_id, create_time, data_or_error]]
        raw_sessions = self._repo.get_all_sessions_metadata(user_id)

        formatted_sessions = []

        for session_id, create_time, data_or_error in raw_sessions:
            session_item = {
                "session_id": session_id,
                "create_time": create_time,
            }

            # 2. 处理可能的读取错误 (隔离异常，防止一个文件损坏导致整个列表挂掉)
            if isinstance(data_or_error, Exception):
                logger.error(
                    "读取会话 %s 失败: %s", session_id, str(data_or_error)
                )
                session_item.update({
                    "memory": [],
                    "total_messages": 0,
                    "error": "无法读取会话数据",
                })
            else:
                # 3. 正常数据处理：过滤 System 消息，只展示用户可见内容
                memory = data_or_error
                user_visible_memory = [
                    msg for msg in memory if msg.get("role") != "system"
                ]
                session_item.update({
                    "memory": user_visible_memory,
                    "total_messages": len(user_visible_memory),
                })

            formatted_sessions.append(session_item)



        # 4. 排序：按时间倒序（最新的在最前）
        formatted_sessions.sort(
            key=lambda x: x.get("create_time") or "",
            reverse=True
        )

        return formatted_sessions


session_service = SessionService()

if __name__ == "__main__":
    result1 = session_service.prepare_history(user_id="user1", session_id="session1", max_turn=3)
    session_service.save_history(user_id="user1", session_id="session1", history=result1)