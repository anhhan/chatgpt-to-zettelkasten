#!/usr/bin/env python3
"""
Systematic processor for ChatGPT conversations.
Scores conversations for value and tracks processing state.

Usage:
    python process_conversations.py scan     - Scan and score all conversations
    python process_conversations.py top [N]  - Show top N candidates by score
    python process_conversations.py stats    - Show processing statistics
    python process_conversations.py mark <file> <status> [flower] - Mark as gold/skip
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Import configuration
try:
    from config import (
        CONVERSATIONS_PATH, MANIFEST_PATH,
        HIGH_VALUE_KEYWORDS, LOW_VALUE_KEYWORDS
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
    Score a conversation for potential value.

    Scoring factors:
    - Word count (longer = more substantial)
    - Turn count (more back-and-forth = deeper exploration)
    - High-value keywords (+2 each)
    - Low-value keywords (-1 each)
    """
    content = file_path.read_text(encoding='utf-8', errors='ignore')
    content_lower = content.lower()

    # Basic metrics
    word_count = len(content.split())
    turn_count = content.count("## User") + content.count("## Assistant")

    # Check for corrupted content
    if "[object Object]" in content:
        return {
            "score": 0,
            "reason": "corrupted",
            "word_count": word_count,
            "turn_count": turn_count
        }

    # Count keyword matches
    high_value_hits = sum(1 for kw in HIGH_VALUE_KEYWORDS if kw in content_lower)
    low_value_hits = sum(1 for kw in LOW_VALUE_KEYWORDS if kw in content_lower)

    # Calculate score
    score = 0

    # Length bonus
    if word_count > 2000:
        score += 3
    elif word_count > 1000:
        score += 2
    elif word_count > 500:
        score += 1

    # Turn count bonus
    if turn_count > 20:
        score += 3
    elif turn_count > 10:
        score += 2
    elif turn_count > 5:
        score += 1

    # Keyword scoring
    score += high_value_hits * 2
    score -= low_value_hits

    # Determine reason category
    if high_value_hits >= 3:
        reason = "high_value_keywords"
    elif word_count > 2000 and turn_count > 10:
        reason = "substantial_depth"
    elif low_value_hits > high_value_hits:
        reason = "likely_low_value"
    else:
        reason = "neutral"

    return {
        "score": max(0, score),
        "reason": reason,
        "word_count": word_count,
        "turn_count": turn_count,
        "high_keywords": high_value_hits,
        "low_keywords": low_value_hits
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


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "scan":
        scan_all_conversations()
        print_stats()
        print_score_distribution()

    elif cmd == "top":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        candidates = get_top_candidates(n)
        print(f"\nTop {len(candidates)} candidates:\n")
        for i, (name, data) in enumerate(candidates, 1):
            print(f"{i:2}. [{data['score']:2}] {name}")
            print(f"     Words: {data['word_count']}, Turns: {data['turn_count']}, Reason: {data['reason']}")

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

    elif cmd == "dist" or cmd == "distribution":
        print_score_distribution()

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
