
from typing import List
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from config.settings import settings

class QueryService:
    
    def __init__(self):
        self.llm = ChatOpenAI(
                model=settings.MODEL,
                api_key=settings.API_KEY,
                base_url=settings.BASE_URL,
                temperature=0.2,
            
        )
    
    
    def generate_answer(self,user_question,retrival_context:List[Document])->str:
        if not retrival_context:
            return "未检索到任何相关文档,无法回复"

        # 把 Document 列表格式化成干净的编号文本,避免把对象 repr 塞进 prompt
        context_text = "\n\n".join(
            f"【资料{i+1}】\n{doc.page_content.strip()}" for i, doc in enumerate(retrival_context)
        )

        prompt = f"""
        你是一位经验丰富的高级技术支持专家。请基于下方的【参考资料】回答【用户问题】。

        【参考资料】：
        ```
        {context_text}
        ```

        【用户问题】：
        ```
        {user_question}
        ```

        【回答要求】：
        1.  **基于事实**：严格基于【参考资料】的内容回答，严禁编造资料中未提及的信息。如果资料无法回答问题，请直接回答：“当前的知识库中暂时没有找到该问题的解决方案。”
        2.  **去特定化处理**：(重要)
            - 除非用户问题中明确指明了特定型号/品牌，否则在回答中请**移除**具体的设备型号、品牌名称（如“联想”、“K900”等）。
            - 例如：将“联想手机设置”泛化为“手机设置”；将“打开联想电脑管家”泛化为“打开系统管理软件”或“相关设置工具”。
        3.  **结构清晰**：
            - 如果是操作步骤，请使用有序列表（1. 2. 3.）。
            - 语言风格应简洁、专业、直接，避免寒暄和废话。
        4. 引用来源：在回答的最后，请列出你参考的【资料x】的编号(仅列出编号即可) 

        【开始回答】：
        """
        
        
        llm_response = self.llm.invoke(prompt)
        print(f"prompt: {prompt}")
        print(f"llm_response: {llm_response.content}")
        return llm_response.content
    
    
if __name__ == "__main__":
    user_question = " 电脑不能开机怎么办"
    from services.retrieval_serveice import RetrievalService
    retrieval_service = RetrievalService()
    
    retrieval_context = retrieval_service.retrieval(user_question)
    query_service = QueryService()
    answer = query_service.generate_answer(user_question,retrieval_context)
    print(answer)