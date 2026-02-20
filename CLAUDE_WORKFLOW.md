# Claude Code Workflow: ChatGPT to Zettelkasten Processing

## Overview

This workflow processes ChatGPT conversation exports into atomic Seeds and Flowers for Anh's knowledge vault (Zettelkasten/Obsidian).

**Quick Start**: Run `/zettel` in any Claude Code session to invoke the automated processing skill.

**Pipeline Location**: `~/Projects/chatgpt-to-zettelkasten/`
**Vault Location**: `~/Library/Mobile Documents/com~apple~CloudDocs/anh-BOK/`
**Seeds Directory**: `~/Library/Mobile Documents/com~apple~CloudDocs/anh-BOK/Seeds/`
**Flowers Directory**: `~/Library/Mobile Documents/com~apple~CloudDocs/anh-BOK/Flowers/`

## Pipeline Stages

### 1. Ingest (One-Time per Export)
```bash
cd ~/Projects/chatgpt-to-zettelkasten
python3 pipeline.py ingest /path/to/OpenAI-export.zip
```

Extracts conversations from ZIP, converts to markdown, stores in conversations directory.

### 2. Learn + Integrate + Rescore (MANDATORY Before Every Mining Session)

**Do NOT skip to mining without completing this step.**

```bash
python3 process_conversations.py learn     # Analyse past decisions
```

The `learn` output has four sections. Act on each:

**a) Low-Score Gold (false negatives — most actionable):**
For each low-score gold file listed, read the conversation's first 100 lines and identify 2-3 keywords that should have triggered a cluster match. Collect all missing keywords.

**b) High-Score Skips (false positives):**
Look for keywords that keep appearing in skipped conversations — add to LOW_VALUE_KEYWORDS if pattern is consistent.

**c) Cluster Effectiveness:**
Note clusters with gold rate below 35% — their keywords may be too broad.

**d) Update config.py:**
Add the missing keywords from (a) to the appropriate DOMAIN_CLUSTERS. Add skip-pattern keywords from (b) to LOW_VALUE_KEYWORDS. Then rescore:

```bash
python3 process_conversations.py rescore   # Apply updated algorithm
```

Verify the rescore output shows changed scores — this proves the loop worked. If 0 changed but you added keywords, check that config.py saved correctly.

### 3. Mine (Parallel Agents)
```bash
python3 process_conversations.py top 50    # Get candidates
```

Launch 3-5 parallel agents, each processing 10 conversations. Agents:
1. Read and evaluate conversations
2. Check vault for duplicates
3. Create Seeds (readiness 2) or Flowers (readiness 3)
4. Mark as gold/skip in manifest

### 4. Post-Mining Learn Loop (MANDATORY after mining)

**Do NOT just report results. Close the loop first.**

```bash
python3 process_conversations.py stats     # Verify marks
python3 process_conversations.py learn     # Feed decisions back
```

Repeat the same process as Step 2:
1. Read the `learn` output — check low-score gold and high-score skips from THIS batch
2. If low-score gold exists: read those conversations, identify missing keywords
3. Update `config.py` with new keywords
4. `python3 process_conversations.py rescore` — report how many scores changed
5. `python3 reindex_slipbox.py` — rebuild search index
6. Commit changes to git

## Core Policy: No Bulk Skipping

Every conversation MUST be read before marking gold or skip. No exceptions.

- Never mark files as skip based on score alone
- Always read at least 200 lines before deciding
- Note the specific reason for skipping
- Stop processing when diminishing returns are evidence-based (gold rate < 10% for 2 consecutive batches)
- Delete true duplicates from vault rather than skipping them

## Seeds vs Flowers

| Type | Layer | Readiness | When to Use |
|------|-------|-----------|-------------|
| Seed | seed | 2 | Single distinct insight, 1-2 paragraphs, raw but reusable |
| Flower | flower | 3 | Developed framework, 3+ sections, structured argument |

Most gold conversations (62%) yield Seeds, not Flowers. Don't force everything into a Flower.

## Seed Template

```yaml
---
title: Idea as Title
layer: seed
status: draft
published: false
field: [relevant-field]
tags: [relevant-tags]
related: ["[[Related-Note]]"]
created: YYYY-MM-DD
updated: YYYY-MM-DD
pipelineTier: 3-moderate-work
readiness: 2
fruitType: framework|essay|mental-model|strategy-brief
sourceMaterial: "[[chatgpt-conversations/filename.md]]"
---

# Idea Title

[1-2 paragraphs]

## Key Insight
> One sentence distillation
```

## Flower Template

```yaml
---
title: Framework Name
layer: flower
status: draft
published: false
field: [relevant-field]
tags: [relevant-tags]
related: ["[[Related-Note]]"]
created: YYYY-MM-DD
updated: YYYY-MM-DD
pipelineTier: 2-light-polish
readiness: 3
fruitType: framework|essay|methodology-guide|case-study
sourceMaterial: "[[chatgpt-conversations/filename.md]]"
---

# Framework Name

[Opening]

## Core Concept
## Key Components
## Application
## Key Insight
> Distillation

---
**Links**: [[Related-Framework]]
**Source**: ChatGPT conversation YYYY-MM-DD (Title)
```

## Scoring Algorithm (v3.1)

### Architecture
| Layer | Signal | Points | Cap |
|-------|--------|--------|-----|
| 1 | Tier-weighted domain cluster hits | 3-6+ per cluster | -- |
| 1b | Cross-cluster breadth bonus | 4/8/12 | 12 |
| 2 | Generic high-value keywords | 1pt each | -- |
| 3 | Structural signals | 3pt each | 15 |
| 3b | Novel framing signals | 4pt each | 20 |
| 4 | Length (diminishing returns) | 1-2pt | 5 |
| 4b | Sustained engagement (30+/60+ turns) | 5pt each | 10 |
| 5 | Keyword density bonus | 2/5/8 | 8 |
| 6 | Penalties | -1 to -5 | -- |

### Tier Multipliers (Intelligence Briefing)
- Tier 1 (2.0x): Calibrated Truth Delivery, Islamic Fintech/Waris
- Tier 2 (1.5x): Tam OS, AI-Native Solopreneurship
- Tier 3 (1.0x): Crosscultural Synthesis, Trauma-Informed Design
- Tier 4 (0.75x): Coaching, Social Enterprise

### Gold Rate by Score Band
| Band | Gold Rate | Recommendation |
|------|-----------|---------------|
| 80+ | ~61% | Always process |
| 60-79 | ~55% | High priority (check for duplicates) |
| 50-59 | ~54% | Good candidates |
| 40-49 | ~45% | Selective |
| 30-39 | ~28% | Only if backlog small |
| <30 | ~3% | Skip |

## Self-Learning Workflow

The learn → integrate → rescore loop runs twice per session:
1. **Before mining** (Step 2): integrates learnings from ALL previous sessions
2. **After mining** (Step 4): integrates learnings from THIS session's decisions

Each loop:
1. `python3 process_conversations.py learn` — identify patterns
2. Read low-score gold conversations — find missing keywords
3. Update `config.py` — add keywords to clusters
4. `python3 process_conversations.py rescore` — apply changes
5. Verify scores shifted — proves the loop worked
6. Commit to git

## Commands Quick Reference

```bash
python3 process_conversations.py stats          # Pipeline statistics
python3 process_conversations.py top 20         # Top 20 unprocessed
python3 process_conversations.py learn          # Self-learning analysis
python3 process_conversations.py rescore        # Rescore with current algorithm
python3 process_conversations.py mark "f" gold  # Mark as gold
python3 process_conversations.py mark "f" skip  # Mark as skip
python3 process_conversations.py review-skips   # Reconsider high-score skips
python3 reindex_slipbox.py                      # Rebuild semantic search
python3 pipeline.py ingest /path/to/export.zip  # Ingest new export
```

## Quality Rules

### GOLD: Create note when
- Distinct, reusable idea (not a conversation summary)
- Not duplicated in existing vault
- Aligns with Intelligence Briefing domains
- Novel problem framing or tension-spotting = venture seeds

### SKIP: Pass when
- Already captured in vault (most common reason)
- Pure logistics/debugging/financial admin
- Generic advice, no original angle
- Meta conversations (tool config, project instructions)

---

**Last Updated**: 2026-02-22
**Maintained By**: Claude Code sessions with Anh
