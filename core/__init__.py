from os import getenv
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

BASE_URL = getenv("BASE_URL")
OPENAI_API_KEY = getenv("OPENAI_API_KEY")
ADMIN_TELEGRAM_ID = getenv("ADMIN_TELEGRAM_ID")
TELEGRAM_BOT_TOKEN = getenv("TELEGRAM_BOT_TOKEN")

OPENAI_CLIENT = OpenAI(api_key=OPENAI_API_KEY)

AI_MODELS = {
    'o4-mini': {
        'input': 1.10,  # Per 1M tokens,
        'output': 4.40  # Per 1M tokens,
    },
    'gpt-4.1-mini': {
        'input': 0.40,
        'output': 1.60,
    },
    'gpt-4.1-nano': {
        'input': 0.10,
        'output': 0.40,
    },
}
