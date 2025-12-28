import os
import sys

GPT_SOVITS_ROOT = "/workspace/GPT-SoVITS"

print(f"--- Inspecting {GPT_SOVITS_ROOT} ---")
if os.path.exists(GPT_SOVITS_ROOT):
    print("Listing root directory:")
    print(os.listdir(GPT_SOVITS_ROOT))
    
    gpt_pkg = os.path.join(GPT_SOVITS_ROOT, "GPT_SoVITS")
    if os.path.exists(gpt_pkg):
        print(f"\nListing {gpt_pkg}:")
        print(os.listdir(gpt_pkg))
    else:
        print(f"WARNING: {gpt_pkg} does not exist.")
        
    pretrained = os.path.join(GPT_SOVITS_ROOT, "GPT_SoVITS", "pretrained_models")
    if os.path.exists(pretrained):
        print(f"\nListing {pretrained}:")
        print(os.listdir(pretrained))
    else:
        # Maybe it's at root/pretrained_models?
        pretrained_root = os.path.join(GPT_SOVITS_ROOT, "pretrained_models")
        if os.path.exists(pretrained_root):
             print(f"\nListing {pretrained_root}:")
             print(os.listdir(pretrained_root))
        else:
             print("\nWARNING: No pretrained_models found.")

    # Try importing
    sys.path.append(GPT_SOVITS_ROOT)
    try:
        import GPT_SoVITS
        print("\nSUCCESS: 'import GPT_SoVITS' worked.")
    except ImportError as e:
        print(f"\nFAILURE: 'import GPT_SoVITS' failed: {e}")
        
else:
    print(f"ERROR: {GPT_SOVITS_ROOT} does not exist.")
