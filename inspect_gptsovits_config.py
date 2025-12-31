#!/usr/bin/env python3
"""Inspect GPT-SoVITS checkpoint files to see their config."""
import os
import sys
import torch
import json

GPT_SOVITS_ROOT = "/workspace/GPT-SoVITS"
PRETRAINED_DIR = os.path.join(GPT_SOVITS_ROOT, "GPT_SoVITS", "pretrained_models", "gsv-v2final-pretrained")

def inspect_checkpoint(path, name):
    print(f"\n{'='*60}")
    print(f"Inspecting: {name}")
    print(f"Path: {path}")
    print(f"{'='*60}")
    
    if not os.path.exists(path):
        print(f"  ❌ File not found!")
        return
    
    try:
        data = torch.load(path, map_location="cpu", weights_only=False)
        print(f"  Top-level keys: {list(data.keys())}")
        
        if "config" in data:
            config = data["config"]
            print(f"\n  Config type: {type(config)}")
            if isinstance(config, dict):
                print("  Config contents:")
                print(json.dumps(config, indent=4, default=str))
            else:
                print(f"  Config value: {config}")
        else:
            print("  ❌ No 'config' key found in checkpoint!")
            
        if "weight" in data:
            weights = data["weight"]
            print(f"\n  Weight keys (first 10): {list(weights.keys())[:10]}")
            # Check first layer shape to infer hidden dim
            for key in weights:
                if "embedding" in key.lower() or "proj" in key.lower():
                    print(f"    {key}: shape={weights[key].shape}")
                    break
    except Exception as e:
        print(f"  ❌ Error loading: {e}")

if __name__ == "__main__":
    print(f"Listing {PRETRAINED_DIR}:")
    if os.path.exists(PRETRAINED_DIR):
        files = os.listdir(PRETRAINED_DIR)
        print(files)
        
        for f in files:
            if f.endswith(('.ckpt', '.pth')):
                inspect_checkpoint(os.path.join(PRETRAINED_DIR, f), f)
    else:
        print(f"❌ Directory not found: {PRETRAINED_DIR}")
