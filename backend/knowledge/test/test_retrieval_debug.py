from services.retrieval_serveice import RetrievalService

svc = RetrievalService()
q = "电脑不能开机怎么办"

print("=== 路① 向量路 top5 ===")
for doc, score in svc.chroma_vector.search_similarity_with_score(q, top_k=5):
    print(f"  {score:.4f} | {doc.metadata.get('title')} | {doc.page_content[:40]!r}")

print("\n=== 路② 标题路 ===")
mds = __import__("utils.markdown_utils", fromlist=["MarkDownUtils"]).MarkDownUtils.collect_md_metadata(
    __import__("config.settings", fromlist=["settings"]).settings.MD_FOLDER_PATH
)
rough = svc.rough_ranking(q, mds)
print("粗排 top10 标题:")
for m in rough[:10]:
    print(f"  rough={m['roughing_score']:.3f} | {m['title']}")
final = svc.final_ranking(q, rough)
print("精排 top5 标题:")
for m in final:
    print(f"  final={m['final_score']:.3f} | sim={m['sim_score']:.3f} | {m['title']}")

print("\n=== retrieval() 最终结果 ===")
for doc in svc.retrieval(q):
    print(f"  {doc.metadata.get('title')} | {doc.page_content[:50]!r}")
