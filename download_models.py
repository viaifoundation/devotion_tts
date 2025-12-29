import os
from huggingface_hub import hf_hub_download, snapshot_download

# Paths
# We assume we are running from project root, but let's be absolute or relative to workspace
# The internal structure seems to be /workspace/GPT-SoVITS/GPT_SoVITS/pretrained_models

BASE_DIR = "/workspace/GPT-SoVITS/GPT_SoVITS/pretrained_models"

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def download_gpt_sovits_base():
    print("\n--- Downloading GPT-SoVITS Base Models (lj1995/GPT-SoVITS) ---")
    ensure_dir(BASE_DIR)
    
    files = [
        "s1bert25hz-2kh-longer-epoch=68e-step=50232.ckpt",
        "s2G488k.pth",
        "s2D488k.pth"
    ]
    
    for filename in files:
        print(f"Downloading {filename}...")
        try:
            hf_hub_download(
                repo_id="lj1995/GPT-SoVITS",
                filename=filename,
                local_dir=BASE_DIR,
                local_dir_use_symlinks=False
            )
            print(f"✅ {filename} downloaded.")
        except Exception as e:
            print(f"❌ Failed to download {filename}: {e}")

def download_gpt_sovits_v2():
    """Download the v2 final pretrained models that TTS_Config expects by default."""
    print("\n--- Downloading GPT-SoVITS V2 Final Models ---")
    v2_dir = os.path.join(BASE_DIR, "gsv-v2final-pretrained")
    ensure_dir(v2_dir)
    
    # These are the files TTS_Config falls back to by default
    files = [
        ("lj1995/GPT-SoVITS", "gsv-v2final-pretrained/s1bert25hz-5kh-longer-epoch=12-step=369668.ckpt"),
        ("lj1995/GPT-SoVITS", "gsv-v2final-pretrained/s2G2333k.pth"),
    ]
    
    for repo_id, filename in files:
        basename = os.path.basename(filename)
        print(f"Downloading {basename}...")
        try:
            hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                local_dir=BASE_DIR,
                local_dir_use_symlinks=False
            )
            print(f"✅ {basename} downloaded.")
        except Exception as e:
            print(f"❌ Failed to download {basename}: {e}")

def download_chinese_roberta():
    print("\n--- Downloading Chinese RoBERTa (hfl/chinese-roberta-wwm-ext-large) ---")
    target_dir = os.path.join(BASE_DIR, "chinese-roberta-wwm-ext-large")
    ensure_dir(target_dir)
    
    try:
        snapshot_download(
            repo_id="hfl/chinese-roberta-wwm-ext-large",
            local_dir=target_dir,
            local_dir_use_symlinks=False
        )
        print("✅ Chinese RoBERTa downloaded.")
    except Exception as e:
         print(f"❌ Failed to download RoBERTa: {e}")

def download_chinese_hubert():
    print("\n--- Downloading Chinese HuBERT (TencentGameMate/chinese-hubert-base) ---")
    target_dir = os.path.join(BASE_DIR, "chinese-hubert-base")
    ensure_dir(target_dir)
    
    try:
        snapshot_download(
            repo_id="TencentGameMate/chinese-hubert-base",
            local_dir=target_dir,
            local_dir_use_symlinks=False
        )
        print("✅ Chinese HuBERT downloaded.")
    except Exception as e:
        print(f"❌ Failed to download HuBERT: {e}")

def download_fast_langdetect():
    """Create cache directory for fast_langdetect and download the model."""
    print("\n--- Setting up fast_langdetect cache ---")
    cache_dir = os.path.join(BASE_DIR, "fast_langdetect")
    ensure_dir(cache_dir)
    
    # Download the model file
    model_url = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin"
    model_path = os.path.join(cache_dir, "lid.176.bin")
    
    if os.path.exists(model_path):
        print(f"✅ fast_langdetect model already exists at {model_path}")
        return
    
    print(f"Downloading fasttext language model...")
    try:
        import urllib.request
        urllib.request.urlretrieve(model_url, model_path)
        print(f"✅ Downloaded to {model_path}")
    except Exception as e:
        print(f"❌ Failed to download: {e}")
        print("You may need to manually download from:")
        print(f"  {model_url}")
        print(f"  and place it at: {model_path}")

def download_nltk_data():
    """Download required NLTK data for English text processing."""
    print("\n--- Downloading NLTK Data ---")
    try:
        import nltk
        # These are required for English g2p in GPT-SoVITS
        packages = [
            'averaged_perceptron_tagger_eng',
            'averaged_perceptron_tagger',
            'cmudict',
            'punkt',
            'punkt_tab'
        ]
        for pkg in packages:
            print(f"Downloading {pkg}...")
            try:
                nltk.download(pkg, quiet=True)
                print(f"  ✅ {pkg}")
            except Exception as e:
                print(f"  ⚠️ {pkg}: {e}")
        print("✅ NLTK data download complete.")
    except ImportError:
        print("⚠️ NLTK not installed, skipping data download.")

if __name__ == "__main__":
    print("Starting Custom Model Download...")
    download_gpt_sovits_base()
    download_gpt_sovits_v2()
    download_chinese_roberta()
    download_chinese_hubert()
    download_fast_langdetect()
    download_nltk_data()
    print("\nAll downloads requested.")
