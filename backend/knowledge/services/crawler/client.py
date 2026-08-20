from config import settings
import requests
import os
from http.client import HTTPException
from services.crawler.parser import HtmlParser


class KnowledgeApiClient:
    
    @staticmethod
    def fetch_knowledge_content(knowledge_nn:int) -> str:
        """
        Fetch the knowledge API URL from the settings.

        Returns:
            str: The knowledge API URL.
            https://iknow.lenovo.com.cn/knowledgeapi/api/knowledge/knowledgeDetails?knowledgeNo=1
        """
        try:
            knowledge_api_url = "https://iknow.lenovo.com.cn/knowledgeapi/api/knowledge/knowledgeDetails"
            
            params = {
                "knowledgeNo": knowledge_nn
            }
            
            response = requests.get(url = knowledge_api_url, params=params,timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            return response.json().get('data', '')
        except HTTPException as e:
            raise HTTPException(status_code=e.status_code, detail=f"发送知识库请求失败: {e.detail}")
    
    


if __name__ == "__main__":
    knowledge_content = KnowledgeApiClient.fetch_knowledge_content(knowledge_nn=1)
    print(knowledge_content)
    markdown_content = HtmlParser().parse_html_to_markdown(knowledge_no=1, html_data=knowledge_content)
    print(markdown_content)
    file_name = os.path.join(os.path.dirname(__file__), "knowledge_1.md")
    with open(file_name, "w", encoding="utf-8") as f:
        f.write(markdown_content)