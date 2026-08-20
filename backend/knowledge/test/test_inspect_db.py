import chromadb
from collections import Counter

client = chromadb.PersistentClient(path=r"d:\pythonProject\AI_multiAgent_0728\backend\knowledge\chroma_kb")
col = client.get_collection("knowledge_base")
print("count:", col.count())

got = col.get(limit=2000)
ids = got["ids"]
docs = got["documents"]
metas = got["metadatas"]
print("fetched:", len(ids))

titles = Counter(m.get("title", "") for m in metas if m)
print("\n=== 按 title 统计 chunk 数(前30) ===")
for t, c in titles.most_common(30):
    print(f"  {c:3d}  {t}")

print("\n=== 样本 chunk 前3条 ===")
for i in range(min(3, len(docs))):
    print(f"--- id={ids[i]} title={metas[i].get('title')}")
    print(repr(docs[i][:150]))
    print()
