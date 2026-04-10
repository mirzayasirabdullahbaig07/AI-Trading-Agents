import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Optional: lock down which model to use
OPENAI_MODEL = "gpt-4o"

# Starting paper-trade balance (USD)
STARTING_BALANCE = 10_000.0