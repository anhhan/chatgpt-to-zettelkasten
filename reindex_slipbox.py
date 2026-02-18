#!/usr/bin/env python3
"""
Standalone reindex script for the slip box.
Generates semantic embeddings for all Flowers using sentence-transformers.

Usage:
    python reindex_slipbox.py
"""

import json
import hashlib
import sys
from pathlib import Path

# Import configuration
try:
    from config import FLOWERS_PATH, INDEX_PATH, MODEL_NAME
except ImportError:
    print("Error: config.py not found. Copy config.example.py to config.py and edit paths.")
    sys.exit(1)

# Embedding imports
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    print("Installing sentence-transformers...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "sentence-transformers", "numpy"])
    from sentence_transformers import SentenceTransformer
    import numpy as np


def get_file_hash(path: Path) -> str:
    """Get MD5 hash of file content for change detection."""
    content = path.read_text(encoding='utf-8')
    return hashlib.md5(content.encode()).hexdigest()


def reindex():
    """Index all markdown files in Flowers/ with semantic embeddings."""
    print(f"Loading model: {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)

    if not FLOWERS_PATH.exists():
        print(f"Error: Flowers path not found: {FLOWERS_PATH}")
        return 0

    index = {"files": {}, "embeddings": []}
    file_list = []
    texts = []

    md_files = list(FLOWERS_PATH.glob("*.md"))
    print(f"Found {len(md_files)} markdown files in Flowers/")

    for i, md_file in enumerate(md_files):
        content = md_file.read_text(encoding='utf-8')
        title = md_file.stem.replace("-", " ")
        texts.append(f"{title}\n\n{content}")
        file_list.append(str(md_file))
        index["files"][str(md_file)] = get_file_hash(md_file)

        if (i + 1) % 20 == 0:
            print(f"  Read {i + 1}/{len(md_files)} files...")

    if texts:
        print("Generating embeddings...")
        embeddings = model.encode(texts, show_progress_bar=True)
        index["embeddings"] = [e.tolist() for e in embeddings]

    # Save index
    data = {
        "files": index["files"],
        "embeddings": index["embeddings"],
        "file_list": file_list
    }
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_PATH, 'w') as f:
        json.dump(data, f)

    print(f"Saved index to {INDEX_PATH}")
    return len(file_list)


if __name__ == "__main__":
    count = reindex()
    print(f"\nIndexed {count} notes in Flowers/")
