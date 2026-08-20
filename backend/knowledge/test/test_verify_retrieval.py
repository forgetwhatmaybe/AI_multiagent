"""决定性验证:Chroma 检索 vs 手动算库内全部向量相似度,是否一致。

如果一致 → 检索正常,只是语义上"死机/蓝屏"确实更接近;问题在数据内容。
如果不一致 → 检索链路有 bug。
"""
import numpy as np
import chromadb
from repositories.vector_store_repository import VectorStoreRepository

repo = VectorStoreRepository()
query = "电脑不能开机怎么办"

# 拉库内全部文档+向量
client = chromadb.PersistentClient(path=r"d:\pythonProject\AI_multiAgent_0728\backend\knowledge\chroma_kb")
col = client.get_collection("knowledge_base")
got = col.get(limit=2000, include=["documents", "metadatas", "embeddings"])
docs = got["documents"]
metas = got["metadatas"]
emb_matrix = np.array(got["embeddings"])
print("库内向量:", emb_matrix.shape, "维度确认:", emb_matrix.shape[1])

# query 向量
q_emb = np.array(repo.embedd_document(query))
q_emb = q_emb / np.linalg.norm(q_emb)

# 手动余弦相似度(库内向量已是归一化,保险起见再归一)
normed = emb_matrix / np.linalg.norm(emb_matrix, axis=1, keepdims=True)
sims = normed @ q_emb
order = np.argsort(sims)[::-1]

print("\n=== 手动余弦相似度 top8(库内真实 chunk) ===")
for idx in order[:8]:
    print(f"  sim={sims[idx]:.4f} | {metas[idx].get('title')} | {docs[idx][:40]!r}")

print("\n=== Chroma 检索 top8 ===")
for doc, dist in repo.search_similarity_with_score(query, top_k=8):
    print(f"  dist={dist:.4f} | {doc.metadata.get('title')} | {doc.page_content[:40]!r}")

# 重点看几个对题文档在库里的相似度排名
target_titles = ["开机之后无任何反应怎么办？", "联想手机A520不能开机如何解决", "联想手机S680不能开机如何解决", "联想手机A3000无法开机的解决办法", "电脑经常死机"]
print("\n=== 对题文档的相似度排名 ===")
for i, idx in enumerate(order):
    t = metas[idx].get("title", "")
    if t in target_titles:
        print(f"  排名#{i+1} sim={sims[idx]:.4f} | {t} | {docs[idx][:50]!r}")
