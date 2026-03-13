import os
from huggingface_hub import HfApi

# Configuration
REPO_ID = "trioskosmos/LovecaSim"
TOKEN = os.environ.get("HF_TOKEN")

def verify_space():
    if not TOKEN:
        print("ERROR: HF_TOKEN environment variable not set.")
        return

    api = HfApi()
    print(f"Querying Hugging Face API for {REPO_ID}...")
    
    try:
        # 1. Get Repo Info (Latest Commit)
        repo_info = api.repo_info(repo_id=REPO_ID, repo_type="space", token=TOKEN)
        print(f"\n[Latest Commit Information]")
        print(f"Last Modified: {repo_info.lastModified}")
        print(f"Commit ID: {repo_info.sha}")
        
        # Get commit history for the message
        commits = api.list_repo_commits(repo_id=REPO_ID, repo_type="space", token=TOKEN)
        if commits:
            last_commit = commits[0]
            print(f"Commit Message: {last_commit.title}")
            print(f"Author: {last_commit.authors}")
        
        # 2. List Files
        files = api.list_repo_files(repo_id=REPO_ID, repo_type="space", token=TOKEN)
        
        print(f"\n[File Verification]")
        print(f"Total Files: {len(files)}")
        
        # Check for directory structures
        dirs = sorted(list(set([f.split('/')[0] for f in files if '/' in f])))
        print(f"Top-level directories: {dirs}")
        
        print("\n[Sampling Files (first 20)]")
        for f in sorted(files)[:20]:
            print(f"  - {f}")
            
    except Exception as e:
        print(f"Verification failed: {e}")

if __name__ == "__main__":
    verify_space()
