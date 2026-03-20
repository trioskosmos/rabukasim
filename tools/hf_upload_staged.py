import os

from huggingface_hub import HfApi

# Configuration
REPO_ID = "trioskosmos/rabukasim"
TOKEN = os.environ.get("HF_TOKEN")


def upload_to_hf():
    api = HfApi()

    print(f"Starting upload to {REPO_ID}...")

    # Upload the entire directory
    # We rely on .gitignore and ignore_patterns to keep it lean
    try:
        api.upload_folder(
            folder_path=".",
            repo_id=REPO_ID,
            repo_type="space",
            token=TOKEN,
            ignore_patterns=[
                ".git/*",
                ".venv/*",
                "__pycache__/*",
                "*.pyc",
                "launcher/target/*",
                "dist/*",
                "web_dist/*",
                ".mypy_cache/*",
                ".ruff_cache/*",
                "node_modules/*",
                "*.lock",
                "logs/*",
                "hf_space/*",
                ".uv-cache/*",
                ".uv-cache-work/*",
                ".uv_cache/*",
                "tmp/*",
                ".kilocode/*",
                ".python/*",
                "engine_rust_src/target/*",
            ],
        )
        print("Upload complete!")
    except Exception as e:
        print(f"Upload failed: {e}")


if __name__ == "__main__":
    upload_to_hf()
