"""深度验证:query 与几个候选文档的真实 embedding 相似度。

检查:是「库建错」还是「语义本身如此」,以及 batch 是否影响。
"""
import numpy as np
from repositories.vector_store_repository import VectorStoreRepository

repo = VectorStoreRepository()
emb = repo.embeddings

query = "电脑不能开机怎么办"
candidates = {
    "0003-开机之后无任何反应怎么办？": "开机之后无任何反应怎么办？ 开机没有任何反应,主机灯不亮。第一步:检查电源线是否正常连接;第二步:断开电源线,多按几次电源开关,释放静电,开机重试。",
    "0383-电脑经常死机": "电脑经常死机 经常死机可能是软硬件冲突,病毒等造成的。先关机切断电源,拔掉外接设备,设置干净启动模式。",
    "0068-开机蓝屏(win7)": "开机蓝屏或提示登录进程初始化失败问题的解决方案,Windows 7 开机蓝屏问题解决方案。",
    "0405-开机按F1才能启动": "开机时,需要按F1(或F2)键后才能继续启动。",
    "0298-msconfig设置开机启动项": "如何使用msconfig设置开机启动项。",
    "0438-联想手机A520不能开机": "联想手机A520不能开机如何解决。",
}

# 1. 单独 embed query
q_emb = emb.embed_query(query)
print(f"query: {query}")
print(f"query embedding dim: {len(q_emb)}")
print()

# 2. 各候选的相似度
print("=== query 与候选文本的余弦相似度(越大越相关) ===")
texts = list(candidates.values())
c_embs = emb.embed_documents(texts)
for name, c_emb in zip(candidates.keys(), c_embs):
    sim = float(np.dot(q_emb, c_emb))
    print(f"  {sim:.4f}  {name}")

# 3. 用 Chroma 检索对比(它的 distance)
print("\n=== Chroma similarity_search_with_score 结果(distance 越小越相关) ===")
for doc, dist in repo.search_similarity_with_score(query, top_k=5):
    print(f"  dist={dist:.4f} | {doc.metadata.get('title')} | {doc.page_content[:30]!r}")

# 4. batch 影响验证:分别用 1 / 16 / 64 计算同一批文本,看向量是否一致
print("\n=== batch_size 对向量的影响 ===")
texts_test = ["电脑不能开机怎么办", "手机如何充电", "打印机卡纸怎么办"]
for bs in [1, 16, 64]:
    e1 = emb.embed_documents(texts_test)  # 当前实例固定 16
    print(f"  batch_size={bs}: 第一个向量前3维={[round(x,6) for x in e1[0][:3]]}")
