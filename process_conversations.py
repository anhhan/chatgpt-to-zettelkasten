#!/usr/bin/env python3
"""
Systematic processor for ChatGPT conversations.
Scores conversations for value and tracks processing state.

Usage:
    python process_conversations.py scan     - Scan and score all conversations
    python process_conversations.py rescore  - Rescore all unprocessed conversations
    python process_conversations.py top [N]  - Show top N candidates by score
    python process_conversations.py stats    - Show processing statistics
    python process_conversations.py mark <file> <status> [flower] - Mark as gold/skip
    python process_conversations.py review-skips [N] - Review high-score skips for reconsideration
    python process_conversations.py learn    - Analyse gold/skip decisions to improve scoring
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

# Import configuration
try:
    from config import (
        CONVERSATIONS_PATH, MANIFEST_PATH,
        HIGH_VALUE_KEYWORDS, LOW_VALUE_KEYWORDS,
        DOMAIN_CLUSTERS, LOW_VALUE_STRONG, STRUCTURAL_PATTERNS,
        NOVEL_FRAMING_PATTERNS, CLUSTER_TIER,
    )
except ImportError:
    print("Error: config.py not found. Copy config.example.py to config.py and edit paths.")
    sys.exit(1)


def load_manifest():
    """Load the processing manifest from disk."""
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, 'r') as f:
            return json.load(f)
    return {"version": 1, "stats": {}, "files": {}}


def save_manifest(manifest):
    """Save the processing manifest to disk."""
    manifest["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)


def score_conversation(file_path: Path) -> dict:
    """
    Score a conversation for potential value using multi-signal analysis.

    Scoring layers:
    1. Domain cluster hits (weighted by density and co-occurrence)
    2. Structural signals (numbered steps, frameworks, matrices)
    3. Length/depth (with diminishing returns and density normalization)
    4. Low-value penalties (aggressive for strong signals)

    Design principles:
    - A 2,000-word conversation developing a novel framework should outscore
      an 80,000-word personality reflection
    - Co-occurrence of keywords within a domain cluster signals depth
    - Co-occurrence across clusters signals breadth (cross-pollination potential)
    - Structural patterns (steps, matrices, archetypes) indicate framework development
    - Keyword density matters more than raw keyword count
    """
    content = file_path.read_text(encoding='utf-8', errors='ignore')
    content_lower = content.lower()

    # Basic metrics
    word_count = len(content.split())
    turn_count = content.count("## User") + content.count("## Assistant")

    # Check for corrupted content
    if "[object Object]" in content:
        return {
            "score": 0, "reason": "corrupted",
            "word_count": word_count, "turn_count": turn_count,
            "clusters_hit": [], "structural_hits": 0, "density": 0.0,
        }

    # Strong low-value check (early exit)
    strong_low_hits = sum(1 for kw in LOW_VALUE_STRONG if kw in content_lower)
    if strong_low_hits >= 2:
        return {
            "score": 0, "reason": "strong_low_value",
            "word_count": word_count, "turn_count": turn_count,
            "clusters_hit": [], "structural_hits": 0, "density": 0.0,
        }

    score = 0.0
    clusters_hit = []

    # ── Layer 1: Tier-weighted domain cluster scoring ─────────────────
    # Tier 1 clusters (Calibration, Waris) score highest per hit.
    # Tier 2 (Tâm OS, Solopreneurship) score well.
    # Tier 3-4 (supporting) score lower — they add signal but don't drive.
    #
    # Tier multipliers: T1 = 2.0x, T2 = 1.5x, T3 = 1.0x, T4 = 0.75x
    TIER_MULTIPLIER = {1: 2.0, 2: 1.5, 3: 1.0, 4: 0.75}

    total_domain_hits = 0
    for cluster_name, keywords in DOMAIN_CLUSTERS.items():
        hits = sum(1 for kw in keywords if kw in content_lower)
        if hits > 0:
            clusters_hit.append(cluster_name)
            total_domain_hits += hits
            tier = CLUSTER_TIER.get(cluster_name, 3)
            multiplier = TIER_MULTIPLIER.get(tier, 1.0)
            # Depth within cluster: first hit = 3pts, each additional = 2pts
            cluster_score = (3 + (hits - 1) * 2) * multiplier
            score += cluster_score

    # Cross-cluster breadth bonus: hitting 3+ clusters = strong signal
    num_clusters = len(clusters_hit)
    if num_clusters >= 4:
        score += 12
    elif num_clusters >= 3:
        score += 8
    elif num_clusters >= 2:
        score += 4

    # ── Layer 2: Generic high-value keywords (lower weight) ──────────
    generic_hits = sum(1 for kw in HIGH_VALUE_KEYWORDS if kw in content_lower)
    score += generic_hits * 1  # 1pt each (down from 2)

    # ── Layer 3: Structural signals ──────────────────────────────────
    # Conversations that develop frameworks have structural markers
    structural_hits = 0
    for pattern in STRUCTURAL_PATTERNS:
        if re.search(pattern, content_lower):
            structural_hits += 1
    # Each structural signal = 3pts, capped at 15
    score += min(structural_hits * 3, 15)

    # ── Layer 3b: Novel framing signals ────────────────────────────────
    # Detect original problem reframing, tension spotting, opportunity
    # identification. These are seeds of possible ventures — weighted
    # higher than structural patterns because rarer and more valuable.
    novel_framing_hits = 0
    for pattern in NOVEL_FRAMING_PATTERNS:
        if re.search(pattern, content_lower):
            novel_framing_hits += 1
    # Each novel framing signal = 4pts, capped at 20
    score += min(novel_framing_hits * 4, 20)

    # ── Layer 4: Length with diminishing returns ─────────────────────
    # Reward substance but don't let length dominate
    if word_count >= 1000:
        score += 2
    if word_count >= 3000:
        score += 2
    if word_count >= 6000:
        score += 1
    # No additional bonus beyond 6000 — length alone is not signal

    # Turn count: moderate depth signal
    if turn_count >= 4:
        score += 1
    if turn_count >= 8:
        score += 1

    # ── Layer 4b: Sustained engagement bonus ───────────────────────────
    # Long multi-turn conversations stayed open because they held interest.
    # If a thread has many turns AND hits at least one domain cluster,
    # it's likely worth scanning even if individual density is low.
    if turn_count >= 30 and num_clusters >= 1:
        score += 5   # sustained interest + some domain relevance
    if turn_count >= 60 and num_clusters >= 1:
        score += 5   # very sustained — likely kept coming back to it

    # ── Layer 5: Keyword density bonus ───────────────────────────────
    # Dense, focused conversations are more valuable than sprawling ones
    if word_count > 0:
        density = total_domain_hits / (word_count / 1000)  # hits per 1000 words
    else:
        density = 0.0

    if density >= 3.0:
        score += 8  # Very dense — nearly every paragraph hits a domain
    elif density >= 1.5:
        score += 5  # Focused conversation
    elif density >= 0.5:
        score += 2  # Some focus

    # ── Layer 6: Penalties ───────────────────────────────────────────
    low_value_hits = sum(1 for kw in LOW_VALUE_KEYWORDS if kw in content_lower)
    score -= low_value_hits * 1
    score -= strong_low_hits * 5

    # Length penalty only for truly aimless conversations:
    # very long, low density, few turns (not sustained exploration)
    if word_count > 20000 and density < 0.2 and turn_count < 20:
        score -= 5

    # ── Determine reason category ────────────────────────────────────
    if novel_framing_hits >= 3 and num_clusters >= 2:
        reason = "novel_framing"     # original thinking + domain relevance
    elif num_clusters >= 3 and structural_hits >= 2:
        reason = "deep_framework"
    elif novel_framing_hits >= 3:
        reason = "novel_thinking"    # original framing even without deep domain
    elif num_clusters >= 2 and density >= 1.5:
        reason = "focused_domain"
    elif num_clusters >= 2:
        reason = "cross_domain"
    elif structural_hits >= 2:
        reason = "structural_depth"
    elif total_domain_hits >= 3:
        reason = "domain_relevant"
    elif low_value_hits > total_domain_hits:
        reason = "likely_low_value"
    else:
        reason = "neutral"

    return {
        "score": max(0, round(score)),
        "reason": reason,
        "word_count": word_count,
        "turn_count": turn_count,
        "clusters_hit": clusters_hit,
        "structural_hits": structural_hits,
        "novel_framing_hits": novel_framing_hits,
        "density": round(density, 2),
    }


def scan_all_conversations():
    """Scan all conversations and update manifest with scores."""
    manifest = load_manifest()

    if not CONVERSATIONS_PATH.exists():
        print(f"Error: Conversations path not found: {CONVERSATIONS_PATH}")
        sys.exit(1)

    files = list(CONVERSATIONS_PATH.glob("*.md"))
    print(f"Found {len(files)} conversation files")

    new_count = 0
    for i, file_path in enumerate(files):
        filename = file_path.name

        # Skip if already processed (has a status)
        if filename in manifest["files"] and manifest["files"][filename].get("status"):
            continue

        # Score the conversation
        score_data = score_conversation(file_path)

        manifest["files"][filename] = {
            "path": str(file_path),
            "status": None,  # None = unprocessed, "gold", "skip"
            "score": score_data["score"],
            "reason": score_data["reason"],
            "word_count": score_data["word_count"],
            "turn_count": score_data["turn_count"],
            "clusters_hit": score_data.get("clusters_hit", []),
            "structural_hits": score_data.get("structural_hits", 0),
            "novel_framing_hits": score_data.get("novel_framing_hits", 0),
            "density": score_data.get("density", 0.0),
            "flowers_extracted": [],
            "processed_date": None
        }
        new_count += 1

        if (i + 1) % 100 == 0:
            print(f"Scanned {i + 1}/{len(files)}...")

    # Update stats
    update_stats(manifest)
    save_manifest(manifest)

    print(f"\nScanned {new_count} new files")
    return manifest


def rescore_unprocessed():
    """Rescore all unprocessed conversations with the current algorithm."""
    manifest = load_manifest()

    if not CONVERSATIONS_PATH.exists():
        print(f"Error: Conversations path not found: {CONVERSATIONS_PATH}")
        sys.exit(1)

    rescored = 0
    for filename, data in manifest["files"].items():
        # Only rescore unprocessed conversations
        if data.get("status"):
            continue

        file_path = Path(data["path"])
        if not file_path.exists():
            continue

        score_data = score_conversation(file_path)
        old_score = data.get("score", 0)

        data["score"] = score_data["score"]
        data["reason"] = score_data["reason"]
        data["word_count"] = score_data["word_count"]
        data["turn_count"] = score_data["turn_count"]
        data["clusters_hit"] = score_data.get("clusters_hit", [])
        data["structural_hits"] = score_data.get("structural_hits", 0)
        data["novel_framing_hits"] = score_data.get("novel_framing_hits", 0)
        data["density"] = score_data.get("density", 0.0)

        if score_data["score"] != old_score:
            rescored += 1

    update_stats(manifest)
    save_manifest(manifest)

    print(f"\nRescored {rescored} conversations with changed scores")
    return manifest


def review_high_score_skips(n=20):
    """Find conversations that scored high but were skipped — candidates for reconsideration."""
    manifest = load_manifest()

    skipped_high = [
        (name, data) for name, data in manifest["files"].items()
        if data.get("status") == "skip" and data.get("score", 0) >= 30
    ]
    skipped_high.sort(key=lambda x: x[1]["score"], reverse=True)

    print(f"\n=== High-Score Skips (potential missed gold) ===\n")
    if not skipped_high:
        print("No high-scoring skips found.")
        return

    for i, (name, data) in enumerate(skipped_high[:n], 1):
        clusters = ", ".join(data.get("clusters_hit", []))
        print(f"{i:2}. [{data['score']:2}] {name}")
        print(f"     Words: {data['word_count']}, Turns: {data['turn_count']}, Reason: {data['reason']}")
        if clusters:
            print(f"     Clusters: {clusters}")
        print()


def update_stats(manifest):
    """Update the stats section of the manifest."""
    all_files = manifest["files"]
    manifest["stats"] = {
        "total": len(all_files),
        "processed": sum(1 for f in all_files.values() if f.get("status")),
        "gold": sum(1 for f in all_files.values() if f.get("status") == "gold"),
        "skip": sum(1 for f in all_files.values() if f.get("status") == "skip"),
        "pending": sum(1 for f in all_files.values() if not f.get("status")),
    }


def get_top_candidates(n=20):
    """Get top N unprocessed conversations by score."""
    manifest = load_manifest()

    # Filter unprocessed and sort by score
    candidates = [
        (name, data) for name, data in manifest["files"].items()
        if not data.get("status") and data.get("reason") != "corrupted"
    ]
    candidates.sort(key=lambda x: x[1]["score"], reverse=True)

    return candidates[:n]


def mark_processed(filename: str, status: str, flowers: list = None):
    """Mark a file as processed with status (gold/skip)."""
    manifest = load_manifest()

    if filename not in manifest["files"]:
        # Try fuzzy match
        matches = [f for f in manifest["files"] if filename in f]
        if len(matches) == 1:
            filename = matches[0]
        elif len(matches) > 1:
            print(f"Multiple matches found for '{filename}':")
            for m in matches[:5]:
                print(f"  - {m}")
            return False
        else:
            print(f"File not found: {filename}")
            return False

    manifest["files"][filename]["status"] = status
    manifest["files"][filename]["processed_date"] = datetime.now().strftime("%Y-%m-%d")
    if flowers:
        manifest["files"][filename]["flowers_extracted"] = flowers

    update_stats(manifest)
    save_manifest(manifest)
    return True


def print_stats():
    """Print current processing statistics."""
    manifest = load_manifest()
    stats = manifest.get("stats", {})

    print("\n=== Processing Stats ===")
    print(f"Total files:  {stats.get('total', 0)}")
    print(f"Processed:    {stats.get('processed', 0)}")
    print(f"  - Gold:     {stats.get('gold', 0)}")
    print(f"  - Skip:     {stats.get('skip', 0)}")
    print(f"Pending:      {stats.get('pending', 0)}")

    if stats.get('total', 0) > 0:
        pct = (stats.get('processed', 0) / stats.get('total', 1)) * 100
        gold_rate = (stats.get('gold', 0) / max(stats.get('processed', 1), 1)) * 100
        print(f"\nProgress:     {pct:.1f}%")
        print(f"Gold rate:    {gold_rate:.1f}%")


def print_score_distribution():
    """Print score distribution of unprocessed files."""
    manifest = load_manifest()

    ranges = {
        "50+": 0,
        "40-49": 0,
        "30-39": 0,
        "20-29": 0,
        "10-19": 0,
        "0-9": 0
    }

    for data in manifest["files"].values():
        if data.get("status"):
            continue
        score = data.get("score", 0)
        if score >= 50:
            ranges["50+"] += 1
        elif score >= 40:
            ranges["40-49"] += 1
        elif score >= 30:
            ranges["30-39"] += 1
        elif score >= 20:
            ranges["20-29"] += 1
        elif score >= 10:
            ranges["10-19"] += 1
        else:
            ranges["0-9"] += 1

    print("\n=== Score Distribution (Unprocessed) ===")
    for range_name, count in ranges.items():
        print(f"{range_name:>6}: {count}")


def learn_from_decisions():
    """Analyse gold/skip decisions to find scoring blind spots.

    This is the self-learning feedback loop. It examines:
    1. Gold rate by score band — are we recommending the right thresholds?
    2. High-score skips — what patterns produce false positives?
    3. Low-score gold — what patterns are we missing?
    4. Cluster effectiveness — which clusters predict gold vs skip?
    """
    manifest = load_manifest()
    processed = [(n, d) for n, d in manifest["files"].items() if d.get("status")]

    if not processed:
        print("No processed files to learn from.")
        return

    # ── 1. Gold rate by score band ──────────────────────────────────────
    bands = {
        "80+": {"gold": 0, "skip": 0},
        "60-79": {"gold": 0, "skip": 0},
        "50-59": {"gold": 0, "skip": 0},
        "40-49": {"gold": 0, "skip": 0},
        "30-39": {"gold": 0, "skip": 0},
        "20-29": {"gold": 0, "skip": 0},
        "<20": {"gold": 0, "skip": 0},
    }

    for name, data in processed:
        score = data.get("score", 0)
        status = data["status"]
        if score >= 80:
            band = "80+"
        elif score >= 60:
            band = "60-79"
        elif score >= 50:
            band = "50-59"
        elif score >= 40:
            band = "40-49"
        elif score >= 30:
            band = "30-39"
        elif score >= 20:
            band = "20-29"
        else:
            band = "<20"
        bands[band][status] += 1

    print("\n=== Gold Rate by Score Band ===\n")
    print(f"{'Band':>8}  {'Gold':>5}  {'Skip':>5}  {'Total':>5}  {'Gold%':>6}")
    print("-" * 38)
    for band, counts in bands.items():
        total = counts["gold"] + counts["skip"]
        if total > 0:
            rate = (counts["gold"] / total) * 100
            print(f"{band:>8}  {counts['gold']:>5}  {counts['skip']:>5}  {total:>5}  {rate:>5.1f}%")

    # ── 2. High-score skips (false positives) ───────────────────────────
    high_skips = [(n, d) for n, d in processed
                  if d["status"] == "skip" and d.get("score", 0) >= 50]
    high_skips.sort(key=lambda x: x[1]["score"], reverse=True)

    if high_skips:
        print(f"\n=== High-Score Skips (score >= 50, n={len(high_skips)}) ===\n")
        # Analyze common clusters in false positives
        cluster_skip_counts = {}
        reason_skip_counts = {}
        for name, data in high_skips:
            for c in data.get("clusters_hit", []):
                cluster_skip_counts[c] = cluster_skip_counts.get(c, 0) + 1
            r = data.get("reason", "unknown")
            reason_skip_counts[r] = reason_skip_counts.get(r, 0) + 1

        print("Most common clusters in false positives:")
        for c, count in sorted(cluster_skip_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"  {c}: {count}")

        print("\nMost common reasons:")
        for r, count in sorted(reason_skip_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"  {r}: {count}")

    # ── 3. Low-score gold (false negatives / missed patterns) ───────────
    low_gold = [(n, d) for n, d in processed
                if d["status"] == "gold" and d.get("score", 0) < 50]
    low_gold.sort(key=lambda x: x[1]["score"])

    if low_gold:
        print(f"\n=== Low-Score Gold (score < 50, n={len(low_gold)}) ===\n")
        for name, data in low_gold[:10]:
            clusters = ", ".join(data.get("clusters_hit", []))
            print(f"  [{data['score']:2}] {name}")
            print(f"       Reason: {data.get('reason', '?')}, Clusters: {clusters or 'none'}")

    # ── 4. Cluster effectiveness ─────────────────────────────────────────
    cluster_gold = {}
    cluster_skip = {}
    for name, data in processed:
        for c in data.get("clusters_hit", []):
            if data["status"] == "gold":
                cluster_gold[c] = cluster_gold.get(c, 0) + 1
            else:
                cluster_skip[c] = cluster_skip.get(c, 0) + 1

    all_clusters = set(list(cluster_gold.keys()) + list(cluster_skip.keys()))
    if all_clusters:
        print(f"\n=== Cluster Effectiveness ===\n")
        print(f"{'Cluster':>35}  {'Gold':>5}  {'Skip':>5}  {'Gold%':>6}")
        print("-" * 56)
        for c in sorted(all_clusters):
            g = cluster_gold.get(c, 0)
            s = cluster_skip.get(c, 0)
            t = g + s
            rate = (g / t * 100) if t > 0 else 0
            print(f"{c:>35}  {g:>5}  {s:>5}  {rate:>5.1f}%")

    # ── 5. Recommendations ──────────────────────────────────────────────
    print(f"\n=== Recommendations ===\n")

    total_processed = len(processed)
    total_gold = sum(1 for _, d in processed if d["status"] == "gold")
    print(f"Overall: {total_gold}/{total_processed} gold ({total_gold/total_processed*100:.1f}%)")

    if high_skips:
        print(f"\n⚠ {len(high_skips)} high-score skips suggest false positives.")
        print("  Consider: tighter keywords, duplicate detection, or higher thresholds.")

    if low_gold:
        print(f"\n⚠ {len(low_gold)} low-score gold suggest missed patterns.")
        print("  Review these conversations for keywords to add to clusters.")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "scan":
        scan_all_conversations()
        print_stats()
        print_score_distribution()

    elif cmd == "rescore":
        print("Rescoring all unprocessed conversations with updated algorithm...")
        rescore_unprocessed()
        print_stats()
        print_score_distribution()

    elif cmd == "top":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        candidates = get_top_candidates(n)
        print(f"\nTop {len(candidates)} candidates:\n")
        for i, (name, data) in enumerate(candidates, 1):
            clusters = ", ".join(data.get("clusters_hit", []))
            density = data.get("density", 0.0)
            struct = data.get("structural_hits", 0)
            novel = data.get("novel_framing_hits", 0)
            print(f"{i:2}. [{data['score']:3}] {name}")
            print(f"     Words: {data['word_count']}, Turns: {data['turn_count']}, Density: {density:.1f}, Struct: {struct}, Novel: {novel}")
            print(f"     Reason: {data['reason']}")
            if clusters:
                print(f"     Clusters: {clusters}")
            print()

    elif cmd == "stats":
        print_stats()
        print_score_distribution()

    elif cmd == "mark":
        if len(sys.argv) < 4:
            print("Usage: python process_conversations.py mark <filename> <gold|skip> [flower_name]")
            sys.exit(1)
        filename = sys.argv[2]
        status = sys.argv[3]
        flowers = [sys.argv[4]] if len(sys.argv) > 4 else None

        if status not in ("gold", "skip"):
            print(f"Invalid status: {status}. Use 'gold' or 'skip'.")
            sys.exit(1)

        if mark_processed(filename, status, flowers):
            print(f"Marked '{filename}' as {status}")
            if flowers:
                print(f"  Flowers: {flowers}")
        else:
            print(f"Failed to mark '{filename}'")

    elif cmd == "review-skips":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        review_high_score_skips(n)

    elif cmd == "learn":
        learn_from_decisions()

    elif cmd == "dist" or cmd == "distribution":
        print_score_distribution()

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
