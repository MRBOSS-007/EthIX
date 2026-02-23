import os

def ensure_asset_folders():
    os.makedirs("assets", exist_ok=True)
    os.makedirs("assets/logs", exist_ok=True)
    os.makedirs("assets/dom", exist_ok=True)
    os.makedirs("assets/css", exist_ok=True)
    os.makedirs("assets/diffs", exist_ok=True)
