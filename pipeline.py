#!/usr/bin/env python3
"""
Full pipeline for ChatGPT to Zettelkasten conversion.

Orchestrates the complete workflow:
1. Ingest: Split ChatGPT export into individual files
2. Scan: Score all conversations for value
3. Mine: Process top candidates (interactive or batch)

Usage:
    python pipeline.py ingest /path/to/conversations.json
    python pipeline.py scan
    python pipeline.py mine [--top N] [--auto]
    python pipeline.py status
    python pipeline.py full /path/to/conversations.json
"""

import sys
import subprocess
from pathlib import Path

# Import configuration
try:
    from config import CONVERSATIONS_PATH, FLOWERS_PATH, MANIFEST_PATH
except ImportError:
    print("Error: config.py not found. Copy config.example.py to config.py and edit paths.")
    sys.exit(1)


def run_command(cmd: list, description: str = None):
    """Run a command and print output."""
    if description:
        print(f"\n{'='*60}")
        print(f"  {description}")
        print('='*60)

    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def cmd_ingest(args):
    """Ingest a ChatGPT export file."""
    if not args:
        print("Usage: python pipeline.py ingest /path/to/conversations.json")
        return False

    input_file = args[0]
    return run_command(
        [sys.executable, "ingest_export.py", input_file],
        f"Ingesting {input_file}"
    )


def cmd_scan(args):
    """Scan and score all conversations."""
    return run_command(
        [sys.executable, "process_conversations.py", "scan"],
        "Scanning and scoring conversations"
    )


def cmd_status(args):
    """Show current processing status."""
    run_command(
        [sys.executable, "process_conversations.py", "stats"],
        "Processing Status"
    )

    # Also show Flowers count
    if FLOWERS_PATH.exists():
        flower_count = len(list(FLOWERS_PATH.glob("*.md")))
        print(f"\nFlowers in vault: {flower_count}")

    return True


def cmd_mine(args):
    """Show top candidates for mining."""
    top_n = 20

    # Parse --top flag
    if "--top" in args:
        idx = args.index("--top")
        if idx + 1 < len(args):
            top_n = int(args[idx + 1])

    run_command(
        [sys.executable, "process_conversations.py", "top", str(top_n)],
        f"Top {top_n} Candidates for Mining"
    )

    print("\nTo process a conversation:")
    print("  1. Read the file to evaluate content")
    print("  2. Extract insights into a Flower (atomic note)")
    print("  3. Mark as processed:")
    print('     python process_conversations.py mark "filename.md" gold "Flower-Name"')
    print('     python process_conversations.py mark "filename.md" skip')

    return True


def cmd_reindex(args):
    """Reindex the slip box."""
    return run_command(
        [sys.executable, "reindex_slipbox.py"],
        "Reindexing Slip Box"
    )


def cmd_search(args):
    """Search the slip box."""
    if not args:
        print("Usage: python pipeline.py search 'your query'")
        return False

    query = " ".join(args)
    return run_command(
        [sys.executable, "search_cli.py", query],
        f"Searching: {query}"
    )


def cmd_full(args):
    """Run full pipeline: ingest -> scan -> status."""
    if not args:
        print("Usage: python pipeline.py full /path/to/conversations.json")
        return False

    input_file = args[0]

    # Step 1: Ingest
    if not cmd_ingest([input_file]):
        print("Ingestion failed")
        return False

    # Step 2: Scan
    if not cmd_scan([]):
        print("Scanning failed")
        return False

    # Step 3: Status
    cmd_status([])

    print("\n" + "="*60)
    print("  Pipeline Complete!")
    print("="*60)
    print("\nNext: Run 'python pipeline.py mine' to see top candidates")

    return True


def print_help():
    """Print help message."""
    print(__doc__)
    print("\nCommands:")
    print("  ingest <file>    - Import ChatGPT export (JSON or ZIP)")
    print("  scan             - Score all conversations")
    print("  mine [--top N]   - Show top candidates for extraction")
    print("  status           - Show processing statistics")
    print("  reindex          - Rebuild semantic search index")
    print("  search <query>   - Search your slip box")
    print("  full <file>      - Run complete pipeline (ingest + scan)")


def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    commands = {
        "ingest": cmd_ingest,
        "scan": cmd_scan,
        "mine": cmd_mine,
        "status": cmd_status,
        "reindex": cmd_reindex,
        "search": cmd_search,
        "full": cmd_full,
        "help": lambda _: print_help() or True,
    }

    if cmd in commands:
        success = commands[cmd](args)
        sys.exit(0 if success else 1)
    else:
        print(f"Unknown command: {cmd}")
        print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
