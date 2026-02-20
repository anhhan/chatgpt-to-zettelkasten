# ChatGPT to Zettelkasten

A pipeline for extracting atomic notes (Zettelkasten-style) from ChatGPT conversation exports. Includes scoring, processing workflow, semantic search, and MCP server integration.

## Overview

This toolkit helps you:

1. **Ingest** ChatGPT exports (JSON/ZIP) into individual markdown files
2. **Score** conversations for potential value using keyword analysis
3. **Process** conversations systematically, marking them as gold/skip
4. **Extract** valuable insights as atomic notes ("Flowers")
5. **Index** your notes with semantic embeddings
6. **Search** your slip box using natural language queries

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

# Configure paths
cp config.example.py config.py
# Edit config.py with your vault paths

# Run full pipeline on ChatGPT export
python pipeline.py full /path/to/conversations.json

# Or step by step:
python pipeline.py ingest /path/to/conversations.json
python pipeline.py scan
python pipeline.py mine --top 20
```

## Getting Your ChatGPT Export

1. Go to https://chat.openai.com
2. Click your profile → Settings → Data Controls
3. Click "Export data"
4. Wait for email with download link
5. Download and unzip to get `conversations.json`

## Pipeline Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  INGEST                                                              │
│  ┌────────────────────┐      ┌─────────────────────────────────┐    │
│  │ ChatGPT Export     │      │ Individual Conversation Files   │    │
│  │ (JSON or ZIP)      │ ───▶ │ YYYY-MM-DD-title-slug.md        │    │
│  │                    │      │ (ingest_export.py)              │    │
│  └────────────────────┘      └─────────────────────────────────┘    │
│                                           │                          │
├───────────────────────────────────────────┼──────────────────────────┤
│  SCORE                                    ▼                          │
│                         ┌─────────────────────────────────┐          │
│                         │ Score & Rank Conversations      │          │
│                         │ Keywords, length, turn count    │          │
│                         │ (process_conversations.py scan) │          │
│                         └─────────────────────────────────┘          │
│                                           │                          │
├───────────────────────────────────────────┼──────────────────────────┤
│  MINE                                     ▼                          │
│                         ┌─────────────────────────────────┐          │
│                         │ Human/AI Review Top Candidates  │          │
│                         │ Read content, evaluate value    │          │
│                         │ Extract insights → Flowers      │          │
│                         └─────────────────────────────────┘          │
│                                    │              │                  │
│                              ┌─────┘              └─────┐            │
│                              ▼                          ▼            │
│                     ┌──────────────┐          ┌──────────────┐       │
│                     │    GOLD      │          │    SKIP      │       │
│                     │ Create Flower│          │   Archive    │       │
│                     └──────────────┘          └──────────────┘       │
│                              │                                       │
├──────────────────────────────┼───────────────────────────────────────┤
│  INDEX & SEARCH              ▼                                       │
│                     ┌──────────────────────────────────┐             │
│                     │ Flowers/ directory               │             │
│                     │ (Atomic notes with frontmatter)  │             │
│                     └──────────────────────────────────┘             │
│                              │                                       │
│                              ▼                                       │
│                     ┌──────────────────────────────────┐             │
│                     │ Semantic Index                   │             │
│                     │ sentence-transformers embeddings │             │
│                     │ (reindex_slipbox.py)             │             │
│                     └──────────────────────────────────┘             │
│                              │                                       │
│                              ▼                                       │
│                     ┌──────────────────────────────────┐             │
│                     │ Search & Retrieve                │             │
│                     │ (search_cli.py / MCP server)     │             │
│                     └──────────────────────────────────┘             │
└──────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. pipeline.py (Recommended)

Unified command for the entire workflow.

```bash
# Full pipeline: ingest + scan + status
python pipeline.py full /path/to/conversations.json

# Individual commands
python pipeline.py ingest /path/to/conversations.json  # Import export
python pipeline.py scan                                 # Score all
python pipeline.py mine --top 20                        # Show candidates
python pipeline.py status                               # Show stats
python pipeline.py reindex                              # Rebuild index
python pipeline.py search "your query"                  # Search notes
```

### 2. ingest_export.py

Splits ChatGPT export into individual conversation files.

```bash
# From JSON
python ingest_export.py /path/to/conversations.json

# From ZIP (ChatGPT export download)
python ingest_export.py /path/to/chatgpt-export.zip
```

Files are named: `YYYY-MM-DD-conversation-title-slug.md`

### 3. process_conversations.py

Scoring, tracking, and self-learning.

```bash
python process_conversations.py scan              # Score all conversations
python process_conversations.py rescore           # Rescore with current algorithm
python process_conversations.py top 20            # Show top N unprocessed
python process_conversations.py mark "f.md" gold  # Mark as gold
python process_conversations.py mark "f.md" skip  # Mark as skip
python process_conversations.py stats             # Processing statistics
python process_conversations.py learn             # Self-learning feedback loop
python process_conversations.py review-skips      # Reconsider high-score skips
```

### 5. reindex_slipbox.py

Standalone script to reindex your Flowers with semantic embeddings.

```bash
python reindex_slipbox.py
```

### 6. search_cli.py

Command-line semantic search over your indexed notes.

```bash
python search_cli.py "coaching frameworks"
python search_cli.py "how to validate startup ideas"
```

### 7. slipbox_server.py

MCP (Model Context Protocol) server for integration with Claude and other AI tools.

```bash
python slipbox_server.py
```

## Scoring Algorithm (v3)

Multi-signal analysis with tier-weighted domain clusters, structural pattern detection, novel framing detection, and self-learning feedback loop.

| Layer | Signal | Points | Cap |
|-------|--------|--------|-----|
| 1 | Tier-weighted domain cluster hits | 3-6+ per cluster | -- |
| 1b | Cross-cluster breadth bonus | 4/8/12 | 12 |
| 2 | Generic high-value keywords | 1pt each | -- |
| 3 | Structural signals (steps, matrices) | 3pt each | 15 |
| 3b | Novel framing signals (tensions, reframes) | 4pt each | 20 |
| 4 | Length (diminishing returns) | 1-2pt per tier | 5 |
| 4b | Sustained engagement (30+/60+ turns) | 5pt each | 10 |
| 5 | Keyword density bonus | 2/5/8 | 8 |
| 6 | Penalties (low-value, aimless length) | -1 to -5 | -- |

### Self-Learning

The `learn` command analyses gold/skip decisions to find scoring blind spots:
```bash
python process_conversations.py learn
```

This reveals false positives, false negatives, and cluster effectiveness, feeding improvements back into `config.py`.

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

## Processing Statistics

From processing 4,352 ChatGPT conversations (Feb 2026):

| Metric | Value |
|--------|-------|
| Total conversations | 4,352 |
| Processed | 1,750 (40.2%) |
| Gold (valuable) | 232 (13.3%) |
| Skipped | 1,518 (86.7%) |
| Seeds + Flowers extracted | 280+ |

### Gold Rate by Score Band

| Score Range | Gold Rate | Recommendation |
|-------------|-----------|----------------|
| 80+ | ~61% | Always process |
| 60-79 | ~55% | High priority |
| 50-59 | ~54% | Good candidates |
| 40-49 | ~45% | Selective |
| 30-39 | ~28% | Low priority |
| <30 | ~3% | Skip |

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
