# Scoring Algorithm Learnings

Insights from processing 4,352 ChatGPT conversations to extract atomic notes.

## Overview

The scoring algorithm uses multi-signal analysis to identify high-value conversations:
- **Tier-weighted domain clusters** aligned to Intelligence Briefing opportunities
- **Structural pattern detection** for framework development
- **Novel framing detection** for original thinking and venture seeds
- **Sustained engagement bonus** for long multi-turn conversations
- **Density normalization** to reward focused conversations over sprawling ones

## Current Scoring Architecture (v3 — Feb 2026)

| Layer | Signal | Points | Cap |
|-------|--------|--------|-----|
| 1 | Domain cluster hits (tier-weighted) | 3-6+ per cluster | — |
| 1b | Cross-cluster breadth bonus | 4/8/12 | 12 |
| 2 | Generic high-value keywords | 1pt each | — |
| 3 | Structural signals (steps, matrices) | 3pt each | 15 |
| 3b | Novel framing signals | 4pt each | 20 |
| 4 | Length (diminishing returns) | 1-2pt per tier | 5 |
| 4b | Sustained engagement (30+/60+ turns) | 5pt each | 10 |
| 5 | Keyword density bonus | 2/5/8 | 8 |
| 6 | Penalties (low-value, length-aimless) | -1 to -5 | — |

### Tier Multipliers (from Intelligence Briefing)

| Tier | Clusters | Multiplier | Rationale |
|------|----------|------------|-----------|
| 1 | Calibrated Truth, Islamic Fintech/Waris | 2.0x | Primary opportunities |
| 2 | Tâm OS, AI-Native Solopreneurship | 1.5x | Core opportunities |
| 3 | Crosscultural Synthesis, Trauma-Informed Design | 1.0x | Supporting depth |
| 4 | Coaching, Social Enterprise | 0.75x | Operational |

## Scoring Performance by Range

### After v3 algorithm (100-conversation mining session, Feb 2026)

| Score Range | Expected Gold Rate | Actual Gold Rate (n=100) | Description |
|-------------|-------------------|--------------------------|-------------|
| 80+ | ~95% | 91% (10/11) | Almost always gold |
| 60-79 | ~70% | 53% (29/55) | Often gold, but many duplicates |
| 50-59 | ~50% | 47% (8/17) | Mixed — needs judgment |
| 40-49 | ~30% | ~30% | Selective |
| <40 | ~10% | Not tested this round | Low priority |

### Key insight: The 60-79 band has HIGH duplicate rate

Many conversations in the 60-79 range scored well on domain relevance but were
skipped because the ideas were **already captured** in existing vault notes.
This is not a scoring failure — it means the algorithm correctly identifies
domain-relevant conversations, but duplicate detection is needed at mining time.

## Gold/Skip Patterns from 100-Conversation Mining

### Top reasons for SKIP (53 skips):

| Reason | Count | Examples |
|--------|-------|---------|
| Already captured in vault | 22 | Tam OS overview → existing Tam-OS.md |
| Pure logistics/operational | 16 | DCA setup, COSEC plan, mock data |
| Too generic/no original insight | 8 | Generational traits, governance advice |
| Duplicate conversation file | 4 | Files with spaces in names |
| Current events commentary | 2 | Trump/Gaza analysis |
| Product specification only | 1 | Legal briefing evaluation |

### Top reasons for GOLD (47 gold):

| Reason | Count | Examples |
|--------|-------|---------|
| Novel framework/model | 18 | Soul-Product-Market-Fit, Soulful FIRE |
| Original problem framing | 10 | Waris as Trust Engine, Faraid Wealth Leakage |
| Cross-domain synthesis | 8 | Tam × Effectuation, Strategy × Ontology |
| Venture seed / opportunity | 6 | Fandom Learning Engine, Revert Pain Map |
| Identity/archetype insight | 5 | Meaning Architect, Missionary→Manager |

### Output distribution:

| Output Type | Count | % of Gold |
|-------------|-------|-----------|
| Seeds (readiness 2) | 31 | 62% |
| Flowers (readiness 3) | 19 | 38% |

**Key insight**: Most gold conversations yield Seeds, not Flowers. The previous
skill only created Flowers, missing the opportunity to capture raw-but-distinct
insights at the Seed level.

## False Negative Patterns (Gold that scored lower than expected)

### Pattern 1: Dense short conversations
- Conversations under 2000 words with a single breakthrough insight
- Example: "Cynicism as Frozen Hope" (model-origin-explanation, score 63)
- **Fix applied**: Density bonus rewards high hits-per-1000-words

### Pattern 2: Vietnamese/Malay language conversations
- Faraid discussions in Malay score lower because keywords are in English
- Example: "pembahagian-harta-pusaka" — rich faraid scenario but Malay content
- **Potential fix**: Add key Malay/Vietnamese terms to clusters

### Pattern 3: Reframing conversations
- Conversations that pivot from mundane to profound mid-stream
- Example: gold-collateral-loan → Nya Labs manifesto + Tam Fieldwork Sequence
- **Fix applied**: Novel framing patterns detect pivots

### Pattern 4: Gestalt/coaching insight buried in long sessions
- 537-turn coaching session (coachgpt) scored high but was skipped — too much noise
- **Fix applied**: Sustained engagement bonus requires cluster hit, not just length

## Recommended Scoring Improvements (Next Iteration)

### 1. Add Malay/Vietnamese domain terms
```python
# Islamic Fintech — Malay terms
"harta pusaka", "pembahagian harta", "harta sepencarian",
"surat kuasa mentadbir", "sijil faraid",

# Crosscultural — Vietnamese terms
"tâm linh", "tình thương", "đạo đức",
```

### 2. Duplicate detection signal
Add a scoring penalty or flag when a conversation's top cluster + title
closely matches an existing vault note. This would reduce false positives
in the 60-79 band where many conversations are "about Tam OS" but don't
add new insight beyond existing notes.

### 3. Mid-conversation pivot detection
Detect when the tone/topic shifts dramatically mid-conversation.
Conversations that start as logistics and pivot to philosophy are
often the richest finds.

### 4. Feedback loop from mining decisions
Track gold/skip decisions per score range and adjust thresholds
automatically. If a score band consistently produces skips, adjust
the recommendation threshold.

## Processing Statistics

### Current (Feb 2026, post v3)

| Metric | Value |
|--------|-------|
| Total files | 4,352 |
| Processed | 1,750 (40.2%) |
| Gold | 232 (13.3%) |
| Skip | 1,518 (86.7%) |
| Pending | 2,602 |

### Score Distribution (Unprocessed)

| Range | Count | % of Unprocessed |
|-------|-------|-----------------|
| 50+ | 88 | 3.4% |
| 40-49 | 105 | 4.0% |
| 30-39 | 149 | 5.7% |
| 20-29 | 237 | 9.1% |
| 10-19 | 660 | 25.4% |
| 0-9 | 1,363 | 52.4% |

## Algorithm Evolution History

### v1 (Initial)
- Simple keyword matching + word count
- 6 abstract territory clusters
- Gold rate: ~8%

### v2 (Tightened)
- Removed ambiguous standalone keywords ("tâm", "duyên", "zen", "gestalt")
- Replaced with multi-word specific phrases
- Distribution: 50+ went from 891 → 263

### v3 (Intelligence Briefing aligned)
- 8 tiered clusters aligned to 4 world-class opportunities
- Novel framing detection (40 regex patterns)
- Sustained engagement bonus
- Density normalization
- Distribution: 50+ settled at 88
- Gold rate in top 100: 47%

---

**Last Updated**: 2026-02-21
**Maintained By**: Claude Code sessions with Anh
