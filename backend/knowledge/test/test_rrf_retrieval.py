from services.retrieval_serveice import RetrievalService

svc = RetrievalService()
for q in ["电脑不能开机怎么办", "联想手机K900常见问题", "如何插拔SIM卡"]:
    print(f"\n===== 问题: {q} =====")
    print("路① 向量路 top5:")
    for doc, s in svc.chroma_vector.search_similarity_with_score(q, top_k=5):
        print(f"  {s:.4f} | {doc.metadata.get('title')}")
    print("RRF 融合后结果:")
    for doc in svc.retrieval(q):
        print(f"  title={doc.metadata.get('title')} | {doc.page_content[:35]!r}")
