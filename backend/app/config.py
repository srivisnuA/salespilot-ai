import os


def env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


DB_HOST = env("DB_HOST", "127.0.0.1")
DB_PORT = env("DB_PORT", "3306")
DB_NAME = env("DB_NAME", "salespilot")
DB_USER = env("DB_USER", "root")
DB_PASSWORD = env("DB_PASSWORD", "")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# AI provider: "openai" when a key is configured, else deterministic demo mode.
AI_PROVIDER = "openai" if env("OPENAI_API_KEY") else "demo"
OPENAI_BASE_URL = env("OPENAI_BASE_URL", "https://api.openai.com/v1")

# Scoring backend: "rules" (transparent weighted engine) — ML-ready interface.
MODEL_BACKEND = env("MODEL_BACKEND", "rules")

CORS_ORIGINS = env("CORS_ORIGINS", "*").split(",")

SEED_ON_START = env("SEED_ON_START", "1") == "1"
