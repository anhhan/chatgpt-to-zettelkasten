#!/usr/bin/env python3
"""
Command-line semantic search over indexed Flowers.

Usage:
    python search_cli.py "your query here"
    python search_cli.py "coaching frameworks" --top 10

Examples:
    python search_cli.py "truth and calibration"
    python search_cli.py "innovation framework"
    python search_cli.py "how to validate startup ideas"
"""

import sys
import json
import hashlib
from pathlib import Path

# Import configuration
try:
    from config import FLOWERS_PATH, INDEX_PATH, MODEL_NAME
except ImportError:
    print("Error: config.py not found. Copy config.example.py to config.py and edit paths.")
    sys.exit(1)

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    print("Installing dependencies...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "sentence-transformers", "numpy"])
    from sentence_transformers import SentenceTransformer
    import numpy as np


class SlipBox:
    """Semantic search over indexed markdown files."""

    def __init__(self):
        self.model = None
        self.index = {"files": {}, "embeddings": []}
        self.file_list = []

    def load_model(self):
        if self.model is None:
            print("Loading embedding model...", file=sys.stderr)
            self.model = SentenceTransformer(MODEL_NAME)
        return self.model

    def get_file_hash(self, path: Path) -> str:
        content = path.read_text(encoding='utf-8')
        return hashlib.md5(content.encode()).hexdigest()

    def load_index(self):
        if INDEX_PATH.exists():
            with open(INDEX_PATH, 'r') as f:
                data = json.load(f)
                self.index["files"] = data.get("files", {})
                self.index["embeddings"] = [np.array(e) for e in data.get("embeddings", [])]
                self.file_list = data.get("file_list", [])

    def save_index(self):
        data = {
            "files": self.index["files"],
            "embeddings": [e.tolist() for e in self.index["embeddings"]],
            "file_list": self.file_list
        }
        INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(INDEX_PATH, 'w') as f:
            json.dump(data, f)

    def index_flowers(self) -> int:
        """Re-index all Flowers if needed."""
        self.load_model()
        self.load_index()

        if not FLOWERS_PATH.exists():
            return 0

        # Check for changes
        needs_reindex = False
        current_files = set()
        for md_file in FLOWERS_PATH.glob("*.md"):
            current_files.add(str(md_file))
            file_hash = self.get_file_hash(md_file)
            if str(md_file) not in self.index["files"] or \
               self.index["files"][str(md_file)] != file_hash:
                needs_reindex = True

        if not needs_reindex and current_files == set(self.index["files"].keys()):
            return len(self.file_list)

        # Re-index
        print("Indexing Flowers/...", file=sys.stderr)
        self.index = {"files": {}, "embeddings": []}
        self.file_list = []
        texts = []

        for md_file in FLOWERS_PATH.glob("*.md"):
            content = md_file.read_text(encoding='utf-8')
            title = md_file.stem.replace("-", " ")
            texts.append(f"{title}\n\n{content}")
            self.file_list.append(str(md_file))
            self.index["files"][str(md_file)] = self.get_file_hash(md_file)

        if texts:
            embeddings = self.model.encode(texts, show_progress_bar=False)
            self.index["embeddings"] = [np.array(e) for e in embeddings]

        self.save_index()
        print(f"Indexed {len(self.file_list)} notes.", file=sys.stderr)
        return len(self.file_list)

    def search(self, query: str, top_k: int = 5) -> list:
        """
        Semantic search over indexed Flowers.

        Args:
            query: Natural language search query
            top_k: Number of results to return

        Returns:
            List of dicts with file, path, score, preview
        """
        self.load_model()
        self.load_index()

        if not self.index["embeddings"]:
            self.index_flowers()

        if not self.index["embeddings"]:
            return []

        query_embedding = self.model.encode([query], show_progress_bar=False)[0]

        # Calculate cosine similarities
        similarities = []
        for i, emb in enumerate(self.index["embeddings"]):
            sim = np.dot(query_embedding, emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(emb))
            similarities.append((i, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)

        # Build results
        results = []
        for i, sim in similarities[:top_k]:
            file_path = Path(self.file_list[i])
            content = file_path.read_text(encoding='utf-8')
            preview = content[:500].strip()
            if len(content) > 500:
                preview += "..."

            results.append({
                "file": file_path.name,
                "path": str(file_path),
                "score": float(sim),
                "preview": preview
            })

        return results


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    # Parse arguments
    args = sys.argv[1:]
    top_k = 5

    # Check for --top flag
    if "--top" in args:
        idx = args.index("--top")
        if idx + 1 < len(args):
            top_k = int(args[idx + 1])
            args = args[:idx] + args[idx + 2:]

    query = " ".join(args)
    slipbox = SlipBox()

    print(f"Searching: {query}\n", file=sys.stderr)

    results = slipbox.search(query, top_k=top_k)

    if not results:
        print("No results found. Run reindex_slipbox.py first.")
        return

    for i, r in enumerate(results, 1):
        print(f"## {i}. {r['file']} (relevance: {r['score']:.2f})")
        print(f"Path: {r['path']}")
        print(f"\n{r['preview']}\n")
        print("-" * 60)


if __name__ == "__main__":
    main()
