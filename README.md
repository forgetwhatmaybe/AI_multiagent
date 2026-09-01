# AI_multiagent

基于 FastAPI 的多智能体（Multi-Agent）智能服务系统，由两个独立 Python 服务组成：**多智能体对话后端**（`backend/app`）与 **RAG 知识库服务**（`backend/knowledge`）。

## 整体架构

```
用户 ──▶ 多智能体后端 (backend/app)
            │  Orchestrator ──▶ Service Agent / Technical Agent（openai-agents 编排）
            │  工具：本地工具（知识库检索/服务网点）+ MCP（百炼托管、百度地图）
            │  会话持久化：MySQL
            └──▶ 知识库服务 (backend/knowledge, :8001)
                    爬虫采集 / 文件上传 ──▶ 向量化 ──▶ Chroma 向量库
                    混合检索（向量 + BM25/关键词，RRF 融合）
```

## backend/app —— 多智能体对话服务

FastAPI 应用（ITS API），启动时自动建立 MCP 连接，支持流式响应。

- **多智能体编排**（`app/multi_agent/`）：基于 `openai-agents` SDK，由 Orchestrator（编排/调度）分发给 Service Agent（综合服务）与 Technical Agent（技术支持），Agent 均由 Markdown prompt 文件定义（`app/prompts/`）
- **LLM 接入**（`app/infrastructure/ai/`）：OpenAI 兼容接口（硅基流动/百炼等，主/子模型可分开配置），prompt 从文件加载
- **工具体系**（`app/infrastructure/tools/`）：
  - 本地工具：知识库检索（对接 knowledge 服务）、服务网点查询
  - MCP 工具：阿里百炼托管 MCP（Streamable HTTP）+ 百度地图官方 MCP
- **会话管理**（`app/repositories/` + `app/services/`）：MySQL 持久化会话历史，支持流式输出（SSE）

### 启动

```bash
cd backend/app
pip install -r requirements.txt
cp .env_example .env        # 填写 LLM / MySQL / MCP / 知识库配置
uvicorn api.main:create_app --host 127.0.0.1 --port 8000 --reload
```

## backend/knowledge —— RAG 知识库服务

独立的 FastAPI 服务（`:8001`），负责知识的采集、入库与检索。

- **采集**（`cli/` + `services/crawler/`）：
  - `crawl_cli.py`：爬取目标站点，HTML 清洗转 Markdown（markdownify / BeautifulSoup）
  - `upload_cli.py`：上传本地文档（PDF/Word/Markdown，unstructured 解析）
- **向量化入库**（`services/ingestion/`）：LangChain + HuggingFace/sentence-transformers Embedding，存入 Chroma（`langchain-chroma`），中文分词用 jieba
- **检索**（`services/`）：向量语义检索 + BM25/关键词检索，RRF（Reciprocal Rank Fusion）融合排序；含 Embedding 相似度调试工具（`test/`）

### 启动

```bash
cd backend/knowledge
pip install -r requirements.txt
cp .env_example .env        # 填写 LLM/Embedding 模型与 Chroma 配置
python main.py              # FastAPI :8001（api.main:create_app）
```

## 配置说明

两个服务的配置均通过 `.env` 注入（模板见各自目录的 `.env_example`）：

| 服务 | 关键配置 |
|---|---|
| backend/app | `SF_API_KEY`/`SF_BASE_URL`/`MAIN_MODEL_NAME`（主模型）、`AL_BAILIAN_*`（百炼子模型）、`MYSQL_*`（会话库）、`DASHSCOPE_*`/`BAIDUMAP_*`（MCP）、`KNOWLEDGE_BASE_URL`（知识库地址，默认 `http://127.0.0.1:8001`） |
| backend/knowledge | `API_KEY`/`BASE_URL`/`MODEL`（LLM）、`EMBEDDING_MODEL`、`KNOWLEDGE_BASE_URL`（采集源）、`CHROMA_COLLECTION_NAME` |

## 技术栈

FastAPI · Uvicorn · openai-agents · LangChain（core/community/openai/chroma） · Chroma · sentence-transformers · MySQL(PyMySQL + DBUtils) · MCP · jieba · scikit-learn · unstructured
