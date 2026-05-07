import os

from dotenv import load_dotenv

load_dotenv()

APP_VERSION = "v16.32.0"
BOT_STORE_PATH = "data/bots.json"

WEB_PASSWORD = os.getenv("WEB_PASSWORD", "moon")
JWT_SECRET = os.getenv("JWT_SECRET", "secret")
MOON_ENV = os.getenv("MOON_ENV", "prod").lower()
MOON_ROLE = os.getenv("MOON_ROLE", "master").lower()
MASTER_ID = int(os.getenv("MASTER_ID", 0))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
USE_EXTERNAL_LLM = os.getenv("USE_EXTERNAL_LLM", "false").lower() == "true"
HYBRID_PERCENTAGE = int(os.getenv("HYBRID_PERCENTAGE", "50"))
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2:0.5b")
DEEP_DREAM_MODE = os.getenv("DEEP_DREAM_MODE", "false").lower() == "true"

DB_PATH = "data/moon_dev.db" if MOON_ENV == "dev" else "data/moon_database.db"
