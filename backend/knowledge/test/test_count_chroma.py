import chromadb

DB_PATH = r"d:\pythonProject\AI_multiAgent_0728\backend\knowledge\chroma_kb"


def get_kb_count() -> int:
    """查询 knowledge_base 集合当前的向量记录数。"""
    client = chromadb.PersistentClient(path=DB_PATH)
    return client.get_collection("knowledge_base").count()


if __name__ == "__main__":
    print("knowledge_base count:", get_kb_count())
