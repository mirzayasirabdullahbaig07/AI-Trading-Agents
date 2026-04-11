# config.py
# ─────────────────────────────────────────────────────────────
# Loads environment variables from .env file
# ─────────────────────────────────────────────────────────────

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get API key from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("❌ OPENAI_API_KEY not found in .env file")

# Optional: lock down which model to use
OPENAI_MODEL = "gpt-4o"

# Starting paper-trade balance (USD)
STARTING_BALANCE = 10_000.0
