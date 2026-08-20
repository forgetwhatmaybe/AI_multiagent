import torch
from repositories.vector_store_repository import VectorStoreRepository

print("torch:", torch.__version__)
print("cuda build:", torch.version.cuda)
print("cuda available:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("device name:", torch.cuda.get_device_name(0))

# 加载模型并跑一次 embedding,验证 GPU 链路
repo = VectorStoreRepository()
print("device:", repo.device)
emb = repo.embedd_document("测试 GPU 向量化")
print("embedding dim:", len(emb))
print("OK: GPU embedding works")
