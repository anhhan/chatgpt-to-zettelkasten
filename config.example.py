"""
Configuration for chatgpt-to-zettelkasten pipeline.
Copy this file to config.py and edit the paths for your setup.
"""

from pathlib import Path

# Your Obsidian vault or notes directory
VAULT_PATH = Path.home() / "Projects" / "my-vault"

# Where your ChatGPT conversation markdown files are stored
CONVERSATIONS_PATH = VAULT_PATH / "Private" / "Conversations" / "chatgpt_conversations"

# Where to store processed Flowers (atomic notes)
FLOWERS_PATH = VAULT_PATH / "Flowers"

# Processing manifest (tracks what's been processed)
MANIFEST_PATH = VAULT_PATH / "Private" / "Conversations" / "chatgpt_processing.json"

# Semantic search index
INDEX_PATH = VAULT_PATH / ".slipbox" / "slipbox_index.json"

# Embedding model (all-MiniLM-L6-v2 is fast and good quality)
MODEL_NAME = "all-MiniLM-L6-v2"

# Keywords that suggest high-value content (add your own domain-specific terms)
HIGH_VALUE_KEYWORDS = [
    # Frameworks & Philosophy
    "framework", "principle", "philosophy", "methodology", "approach",
    # Innovation & Product
    "innovation", "validation", "product", "architecture", "design",
    # Personal Development
    "coaching", "transformation", "mindset", "belief", "identity", "purpose",
    # Business & Strategy
    "strategy", "business model", "pricing", "growth", "marketing", "positioning",
    # Decision Making
    "decision", "trade-off", "tradeoff", "chose", "decided", "because",
]

# Keywords that suggest low-value content
LOW_VALUE_KEYWORDS = [
    "code", "error", "bug", "fix", "debug", "syntax",
    "translate", "translation",
    "recipe", "weather", "directions",
    "joke", "fun", "game",
]
