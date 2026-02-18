# ChatGPT to Zettelkasten

A pipeline for extracting atomic notes (Zettelkasten-style) from ChatGPT conversation exports. Includes scoring, processing workflow, semantic search, and MCP server integration.

## Overview

This toolkit helps you:

1. **Score** conversations for potential value using keyword analysis
2. **Process** conversations systematically, marking them as gold/skip
3. **Extract** valuable insights as atomic notes ("Flowers")
4. **Index** your notes with semantic embeddings
5. **Search** your slip box using natural language queries

## Quick Start

```bash
# Clone and setup
git clone https://github.com/yourusername/chatgpt-to-zettelkasten.git
cd chatgpt-to-zettelkasten

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure paths (edit config.py)
cp config.example.py config.py
# Edit config.py with your paths

# Scan and score conversations
python process_conversations.py scan

# View top candidates
python process_conversations.py top 20

# Process and create Flowers manually (or with AI assistance)
python process_conversations.py mark "filename.md" gold "Flower-Name"
```

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ChatGPT Export (JSON)                         │
│                            │                                     │
│                            ▼                                     │
│              ┌─────────────────────────┐                        │
│              │   Split into .md files   │                        │
│              └─────────────────────────┘                        │
│                            │                                     │
│                            ▼                                     │
│              ┌─────────────────────────┐                        │
│              │   Score conversations    │  ◄── Keywords, length  │
│              │   (process_conversations)│      turn count        │
│              └─────────────────────────┘                        │
│                            │                                     │
│                            ▼                                     │
│              ┌─────────────────────────┐                        │
│              │   Human/AI Review        │  ◄── Read, evaluate    │
│              │   Mark gold/skip         │      extract insights  │
│              └─────────────────────────┘                        │
│                            │                                     │
│              ┌─────────┴─────────┐                              │
│              ▼                   ▼                              │
│     ┌──────────────┐    ┌──────────────┐                        │
│     │   Gold       │    │   Skip       │                        │
│     │   Create     │    │   Archive    │                        │
│     │   Flower     │    │              │                        │
│     └──────────────┘    └──────────────┘                        │
│              │                                                   │
│              ▼                                                   │
│     ┌──────────────────────────────────┐                        │
│     │   Flowers/ directory             │                        │
│     │   (Atomic notes with frontmatter)│                        │
│     └──────────────────────────────────┘                        │
│              │                                                   │
│              ▼                                                   │
│     ┌──────────────────────────────────┐                        │
│     │   Semantic Index                  │  ◄── sentence-transformers
│     │   (reindex_slipbox.py)            │      all-MiniLM-L6-v2 │
│     └──────────────────────────────────┘                        │
│              │                                                   │
│              ▼                                                   │
│     ┌──────────────────────────────────┐                        │
│     │   Search & Retrieve               │                        │
│     │   (search_cli.py / MCP server)    │                        │
│     └──────────────────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. process_conversations.py

Main processing script for scoring and tracking conversation processing.

```bash
# Scan all conversations and calculate scores
python process_conversations.py scan

# Show top N unprocessed by score
python process_conversations.py top 20

# Mark a file as processed
python process_conversations.py mark "filename.md" gold "Created-Flower-Name"
python process_conversations.py mark "filename.md" skip

# Show processing statistics
python process_conversations.py stats
```

### 2. reindex_slipbox.py

Standalone script to reindex your Flowers with semantic embeddings.

```bash
python reindex_slipbox.py
```

### 3. search_cli.py

Command-line semantic search over your indexed notes.

```bash
python search_cli.py "coaching frameworks"
python search_cli.py "how to validate startup ideas"
```

### 4. slipbox_server.py

MCP (Model Context Protocol) server for integration with Claude and other AI tools.

```bash
python slipbox_server.py
```

## Scoring Algorithm

Conversations are scored based on:

| Factor | Points |
|--------|--------|
| Word count > 2000 | +3 |
| Word count > 1000 | +2 |
| Word count > 500 | +1 |
| Turn count > 20 | +3 |
| Turn count > 10 | +2 |
| Turn count > 5 | +1 |
| Each high-value keyword | +2 |
| Each low-value keyword | -1 |

### High-Value Keywords

Frameworks, philosophy, methodology, innovation, coaching, strategy, business model, product, architecture, transformation, purpose, etc.

### Low-Value Keywords

Code, error, bug, debug, translate, recipe, weather, etc.

## Flower Template

Flowers are atomic notes following this structure:

```markdown
---
title: Note Title
aliases: [Alias1, Alias2]
tags: [topic1, topic2, topic3]
source: chatgpt-distillation
created: YYYY-MM-DD
---

# Note Title

Brief description of the concept.

## Section 1

Content with frameworks, tables, insights.

## Section 2

More structured content.

## Key Insight

> **The main takeaway in a memorable blockquote.**

---

**Links**: [[Related-Note-1]], [[Related-Note-2]]
**Source**: ChatGPT conversation YYYY-MM-DD
```

## Configuration

Copy `config.example.py` to `config.py` and edit:

```python
from pathlib import Path

# Your Obsidian vault or notes directory
VAULT_PATH = Path.home() / "Projects" / "your-vault"

# Where your ChatGPT conversation markdown files are
CONVERSATIONS_PATH = VAULT_PATH / "Private" / "Conversations"

# Where to store processed Flowers
FLOWERS_PATH = VAULT_PATH / "Flowers"

# Processing manifest (tracks what's been processed)
MANIFEST_PATH = CONVERSATIONS_PATH / "processing_manifest.json"

# Semantic search index
INDEX_PATH = VAULT_PATH / ".slipbox" / "index.json"
```

## Processing Statistics (Example)

From processing 1,548 ChatGPT conversations:

| Metric | Value |
|--------|-------|
| Total conversations | 1,548 |
| Gold (valuable) | 124 (8%) |
| Skipped | 1,424 (92%) |
| Flowers extracted | 135 |

### Score Distribution

| Score Range | Count | Gold Rate |
|-------------|-------|-----------|
| 50+ | 37 | ~90% |
| 40-49 | 78 | ~60% |
| 30-39 | 137 | ~30% |
| 20-29 | 211 | ~10% |
| <20 | 1,085 | ~2% |

## Best Practices

### What Makes a Good Flower

1. **Atomic** - One concept per note
2. **Titled clearly** - The title IS the idea
3. **Linked** - References related notes
4. **Reusable** - Frameworks, templates, insights that apply broadly
5. **Structured** - Tables, headers, clear organization

### When to Extract Multiple Flowers

Some conversations yield 2-5 Flowers:
- Coaching frameworks conversation → Multiple technique notes
- Philosophy discussion → Core concept + application notes
- Business planning → Strategy note + tactics notes

### When to Skip

- Pure code debugging
- Translation requests
- One-off questions without frameworks
- Corrupted/incomplete exports

## Semantic Search

The slip box uses `sentence-transformers` with the `all-MiniLM-L6-v2` model for semantic search. This enables:

- Natural language queries ("how do I validate a startup idea")
- Concept matching (finds notes about validation even if they use different words)
- Relevance scoring based on cosine similarity

## MCP Integration

The `slipbox_server.py` provides an MCP server with two tools:

1. **search_slipbox** - Semantic search over your notes
2. **reindex_slipbox** - Refresh the index after adding notes

Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "slipbox": {
      "command": "python",
      "args": ["/path/to/slipbox_server.py"]
    }
  }
}
```

## Learnings

See [SCORING_LEARNINGS.md](SCORING_LEARNINGS.md) for insights from processing conversations, including:

- Keywords that predict high-value content
- Patterns that indicate extractable frameworks
- Score distribution analysis

## License

MIT License - See [LICENSE](LICENSE)

## Contributing

Contributions welcome! Areas of interest:

- Improved scoring algorithms
- Additional export format support (Claude, etc.)
- Better deduplication detection
- Visualization of the slip box graph
