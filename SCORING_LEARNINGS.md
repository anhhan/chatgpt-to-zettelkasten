# Scoring Algorithm Learnings

Insights from processing 1,548 ChatGPT conversations to extract atomic notes.

## Overview

The scoring algorithm attempts to identify high-value conversations that are likely to contain extractable frameworks, insights, or reusable knowledge.

## Scoring Summary by Range

| Score Range | Expected Gold Rate | Description |
|-------------|-------------------|-------------|
| 50+ | ~90% | Almost always valuable |
| 40-49 | ~60% | Usually valuable |
| 30-39 | ~30% | Sometimes valuable |
| 20-29 | ~10% | Occasionally valuable |
| <20 | ~2% | Rarely valuable |

## Gold Found in Lower Scores (False Negatives)

These patterns were valuable but scored lower than expected:

### Score 49: Soulful Role Alignment
- Rich coaching niche positioning
- Career identity exploration
- **Missing keywords**: "role", "niche", "positioning", "alignment"

### Score 48: AI for Personal Integration
- Deep personal integration with AI assistance
- Reflection and soul work patterns
- **Missing patterns**: AI-assisted reflection, introspective work

### Score 39: Blind Spots Inventory
- Detailed founder blind spots analysis
- Actionable insights with frameworks
- **Missing keywords**: "blind spots", "watch-out", "growth edges"

### Score 39: 10X Performers
- Delegation and empowerment framework
- Performance assessment methodology
- **Missing keywords**: "10X", "delegation", "empowerment"

## Recommended Scoring Improvements

### Additional High-Value Keywords

```python
# Personal/Professional Development
"role", "niche", "positioning", "alignment",
"blind spots", "watch-out", "growth",
"10x", "delegation", "empowerment",

# Templates & Artifacts
"artifact", "template", "canvas",
"assumption", "hypothesis", "validation",

# Inner Work / Reflection
"soul fragment", "unreconciled", "integration",
"ritual", "ceremony", "practice",
"archetype", "lineage", "genealogy"
```

### Pattern Detection Ideas

1. **Deep Personal Reflection**
   - Questions like "given everything you know about me..."
   - Explorations of "what's missing" or "where I'm stuck"

2. **Framework/Template Generation**
   - PRFAQ, BMC, artifact templates
   - Structured outputs that can be reused

3. **Coaching/Mentoring Conversations**
   - Discovery of gifts, blind spots, growth edges
   - Role alignment and career exploration

4. **Action-Plan-Rich Content**
   - Numbered steps
   - Tables with specific recommendations

### Adjust Word Count Scoring

Very short conversations (< 1000 words) with high insight density should score higher. The "Blind Spots" conversation was high-value despite medium length because it was dense with actionable frameworks.

## Processing Statistics (Full Run)

| Metric | Value |
|--------|-------|
| Total files | 1,548 |
| Processed | 1,548 (100%) |
| Gold | 124 (8%) |
| Skipped | 1,424 (92%) |
| Flowers extracted | 135 |

## Score Distribution

| Range | Count | % of Total |
|-------|-------|------------|
| 50+ | 37 | 2.4% |
| 40-49 | 78 | 5.0% |
| 30-39 | 137 | 8.9% |
| 20-29 | 211 | 13.6% |
| 10-19 | 313 | 20.2% |
| 0-9 | 772 | 49.9% |

## Lessons Learned

1. **High scores are reliable** - 50+ scores were almost always gold
2. **Low scores have hidden gems** - Random sampling found occasional valuable content
3. **Keywords matter less than structure** - Dense, organized conversations often scored lower
4. **Domain-specific keywords help** - Adding project names and domain terms improved accuracy
5. **AI-assisted review is essential** - Human/AI pairing found patterns the algorithm missed
