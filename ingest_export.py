#!/usr/bin/env python3
"""
Ingest ChatGPT export and split into individual conversation files.

Takes a ChatGPT export JSON (conversations.json) and:
1. Splits into individual markdown files
2. Names using convention: YYYY-MM-DD-title-slug.md
3. Extracts conversation content with proper formatting

Usage:
    python ingest_export.py /path/to/conversations.json
    python ingest_export.py /path/to/chatgpt-export.zip
"""

import json
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path

# Import configuration
try:
    from config import CONVERSATIONS_PATH
except ImportError:
    print("Error: config.py not found. Copy config.example.py to config.py and edit paths.")
    sys.exit(1)


def slugify(text: str, max_length: int = 50) -> str:
    """Convert text to URL-friendly slug."""
    if not text:
        return "untitled"

    # Lowercase and replace spaces/special chars with hyphens
    slug = text.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')

    # Truncate to max length at word boundary
    if len(slug) > max_length:
        slug = slug[:max_length].rsplit('-', 1)[0]

    return slug or "untitled"


def extract_messages(conversation: dict) -> list:
    """
    Extract messages from conversation mapping.
    Returns list of (role, content) tuples in order.
    """
    mapping = conversation.get("mapping", {})

    if not mapping:
        return []

    # Build message chain
    messages = []

    # Find all messages and sort by create_time
    msg_list = []
    for node_id, node in mapping.items():
        msg = node.get("message")
        if msg and msg.get("content") and msg.get("author"):
            role = msg["author"].get("role", "unknown")
            if role in ("user", "assistant"):
                content_parts = msg["content"].get("parts", [])
                content = "\n".join(str(p) for p in content_parts if p and isinstance(p, str))
                create_time = msg.get("create_time") or 0

                if content.strip():
                    msg_list.append((create_time, role, content))

    # Sort by timestamp
    msg_list.sort(key=lambda x: x[0])

    return [(role, content) for _, role, content in msg_list]


def format_conversation(title: str, messages: list, created: datetime) -> str:
    """Format conversation as markdown."""
    lines = [
        f"# {title}",
        f"",
        f"*Exported from ChatGPT - {created.strftime('%Y-%m-%d')}*",
        f"",
        "---",
        ""
    ]

    for role, content in messages:
        role_header = "## User" if role == "user" else "## Assistant"
        lines.append(role_header)
        lines.append("")
        lines.append(content)
        lines.append("")

    return "\n".join(lines)


def process_conversations_json(json_path: Path, output_dir: Path) -> dict:
    """
    Process conversations.json and split into individual files.

    Returns stats dict with counts.
    """
    print(f"Reading {json_path}...")

    with open(json_path, 'r', encoding='utf-8') as f:
        conversations = json.load(f)

    print(f"Found {len(conversations)} conversations")

    output_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        "total": len(conversations),
        "created": 0,
        "skipped_exists": 0,
        "skipped_empty": 0,
        "errors": 0
    }

    for i, conv in enumerate(conversations):
        try:
            # Extract metadata
            title = conv.get("title") or "Untitled"
            create_time = conv.get("create_time")

            if create_time:
                created = datetime.fromtimestamp(create_time)
            else:
                created = datetime.now()

            # Generate filename
            date_str = created.strftime("%Y-%m-%d")
            title_slug = slugify(title)
            filename = f"{date_str}-{title_slug}.md"
            filepath = output_dir / filename

            # Handle duplicates by adding suffix
            counter = 1
            while filepath.exists():
                filename = f"{date_str}-{title_slug}-{counter}.md"
                filepath = output_dir / filename
                counter += 1
                if counter > 100:
                    stats["errors"] += 1
                    continue

            # Extract messages
            messages = extract_messages(conv)

            if not messages:
                stats["skipped_empty"] += 1
                continue

            # Format and write
            content = format_conversation(title, messages, created)
            filepath.write_text(content, encoding='utf-8')
            stats["created"] += 1

            if (i + 1) % 100 == 0:
                print(f"  Processed {i + 1}/{len(conversations)}...")

        except Exception as e:
            print(f"  Error processing conversation {i}: {e}")
            stats["errors"] += 1

    return stats


def process_zip(zip_path: Path, output_dir: Path) -> dict:
    """Process a ChatGPT export zip file."""
    print(f"Extracting {zip_path}...")

    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Find conversations.json in the zip
        json_files = [n for n in zf.namelist() if n.endswith('conversations.json')]

        if not json_files:
            print("Error: No conversations.json found in zip")
            return {"error": "No conversations.json found"}

        # Extract to temp location and process
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            for json_file in json_files:
                zf.extract(json_file, tmpdir)
                json_path = Path(tmpdir) / json_file
                return process_conversations_json(json_path, output_dir)

    return {"error": "Could not process zip"}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print(f"\nOutput directory: {CONVERSATIONS_PATH}")
        sys.exit(1)

    input_path = Path(sys.argv[1])

    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    output_dir = CONVERSATIONS_PATH

    # Allow override of output directory
    if len(sys.argv) > 2:
        output_dir = Path(sys.argv[2])

    print(f"Output directory: {output_dir}")

    # Process based on file type
    if input_path.suffix == '.zip':
        stats = process_zip(input_path, output_dir)
    elif input_path.suffix == '.json':
        stats = process_conversations_json(input_path, output_dir)
    else:
        print(f"Error: Unsupported file type: {input_path.suffix}")
        print("Supported: .json, .zip")
        sys.exit(1)

    # Print summary
    print("\n=== Ingestion Complete ===")
    print(f"Total conversations: {stats.get('total', 0)}")
    print(f"Files created:       {stats.get('created', 0)}")
    print(f"Skipped (empty):     {stats.get('skipped_empty', 0)}")
    print(f"Errors:              {stats.get('errors', 0)}")
    print(f"\nFiles saved to: {output_dir}")
    print("\nNext steps:")
    print("  python process_conversations.py scan")
    print("  python process_conversations.py top 20")


if __name__ == "__main__":
    main()
