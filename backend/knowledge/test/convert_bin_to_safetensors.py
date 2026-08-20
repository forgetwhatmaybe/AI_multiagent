"""把 bge-m3 的 pytorch_model.bin 转换为 model.safetensors。

背景:transformers 4.5x+ 因 CVE-2025-32434 禁止 torch<2.6 加载 .bin 权重,
但加载 safetensors 不受限制。本脚本用 torch 原生加载 .bin 再转存 safetensors。
"""
import torch
from safetensors.torch import save_file
import os

MODEL_DIR = r"E:\embedding\bge-m3"
BIN_PATH = os.path.join(MODEL_DIR, "pytorch_model.bin")
SAFE_PATH = os.path.join(MODEL_DIR, "model.safetensors")


def main():
    if os.path.exists(SAFE_PATH):
        print(f"{SAFE_PATH} 已存在,跳过转换。")
        return

    print(f"加载 {BIN_PATH} ...")
    state_dict = torch.load(BIN_PATH, map_location="cpu")
    print(f"共 {len(state_dict)} 个张量,开始保存 safetensors ...")
    save_file(state_dict, SAFE_PATH)
    size = os.path.getsize(SAFE_PATH) / 1024 / 1024
    print(f"转换完成:{SAFE_PATH} ({size:.1f} MB)")


if __name__ == "__main__":
    main()
