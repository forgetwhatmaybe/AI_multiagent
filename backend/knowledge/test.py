from langchain_openai import ChatOpenAI
from pprint import pprint
llm = ChatOpenAI(model="model2",api_key="123456",base_url="http://127.0.0.1:9876/v1")

pprint(llm.invoke("你是什么模型,是什么型号"))