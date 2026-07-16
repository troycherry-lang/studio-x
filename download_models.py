#!/usr/bin/env python3
"""Download selected SDXL checkpoints into ComfyUI."""
import os
from huggingface_hub import hf_hub_download

CHECKPOINT_DIR = r"C:\Users\troyc\Documents\kimi\workspace\ComfyUI\models\checkpoints"
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

MODELS = [
    ("SG161222/RealVisXL_V5.0", "RealVisXL_V5.0_fp16.safetensors"),
    ("RunDiffusion/Juggernaut-XL-v9", "Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors"),
    ("OnomaAIResearch/Illustrious-xl-early-release-v0", "Illustrious-XL-v0.1.safetensors"),
]

for repo_id, filename in MODELS:
    print(f"[START] {repo_id}/{filename}")
    try:
        path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=CHECKPOINT_DIR,
            local_dir_use_symlinks=False,
            resume_download=True,
        )
        size_gb = os.path.getsize(path) / (1024 ** 3)
        print(f"[DONE] {path} ({size_gb:.2f} GB)")
    except Exception as e:
        print(f"[ERROR] {repo_id}/{filename}: {e}")

print("[ALL DONE]")
