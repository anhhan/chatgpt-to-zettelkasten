#!/usr/bin/env python3
"""
Slip Box MCP Server for semantic search over Flowers.

Provides two tools:
- search_slipbox: Semantic search using natural language queries
- reindex_slipbox: Re-index Flowers after adding new notes

Usage:
    python slipbox_server.py

Add to Claude Code MCP configuration:
    {
      "mcpServers": {
        "slipbox": {
          "command": "python",
          "args": ["/path/to/slipbox_server.py"]
        }
      }
    }
"""

import json
import os
import sys
import hashlib
from pathlib import Path
from typing import Any

# Import configuration
try:
    from config import FLOWERS_PATH, INDEX_PATH, MODEL_NAME
except ImportError:
    print("Error: config.py not found. Copy config.example.py to config.py and edit paths.", file=sys.stderr)
    sys.exit(1)

# MCP protocol imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Installing mcp package...", file=sys.stderr)
    os.system(f"{sys.executable} -m pip install mcp")
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent

# Embedding imports
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    print("Installing sentence-transformers...", file=sys.stderr)
    os.system(f"{sys.executable} -m pip install sentence-transformers numpy")
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
        """Index all markdown files in Flowers/."""
        self.load_model()
        self.load_index()

        if not FLOWERS_PATH.exists():
            return 0

        files_to_index = []
        current_files = {}

        # Check which files need indexing
        for md_file in FLOWERS_PATH.glob("*.md"):
            file_hash = self.get_file_hash(md_file)
            current_files[str(md_file)] = file_hash

            if str(md_file) not in self.index["files"] or \
               self.index["files"][str(md_file)] != file_hash:
                files_to_index.append(md_file)

        if not files_to_index and len(current_files) == len(self.index["files"]):
            return len(self.file_list)  # No changes

        # Re-index everything
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
        return len(self.file_list)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """Semantic search over indexed Flowers."""
        self.load_model()
        self.load_index()

        if not self.index["embeddings"]:
            self.index_flowers()

        if not self.index["embeddings"]:
            return []

        # Encode query
        query_embedding = self.model.encode([query], show_progress_bar=False)[0]

        # Calculate similarities
        similarities = []
        for i, emb in enumerate(self.index["embeddings"]):
            sim = np.dot(query_embedding, emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(emb))
            similarities.append((i, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)

        # Return top results
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


# Initialize slip box
slipbox = SlipBox()

# Create MCP server
server = Server("slipbox")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_slipbox",
            description="Semantic search over the Flowers/ slip box. Returns relevant notes based on meaning, not just keywords.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query - can be a concept, question, or topic"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="reindex_slipbox",
            description="Re-index the Flowers/ directory to pick up new or changed notes.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    if name == "search_slipbox":
        query = arguments.get("query", "")
        top_k = arguments.get("top_k", 5)

        results = slipbox.search(query, top_k)

        if not results:
            return [TextContent(type="text", text="No results found. Try reindexing with reindex_slipbox.")]

        output = f"Found {len(results)} relevant notes:\n\n"
        for i, r in enumerate(results, 1):
            output += f"## {i}. {r['file']} (score: {r['score']:.3f})\n"
            output += f"Path: {r['path']}\n"
            output += f"Preview:\n{r['preview']}\n\n"

        return [TextContent(type="text", text=output)]

    elif name == "reindex_slipbox":
        count = slipbox.index_flowers()
        return [TextContent(type="text", text=f"Indexed {count} notes in Flowers/")]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    # Initial indexing
    print(f"Indexing Flowers/ directory...", file=sys.stderr)
    count = slipbox.index_flowers()
    print(f"Indexed {count} notes.", file=sys.stderr)

    # Run MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
