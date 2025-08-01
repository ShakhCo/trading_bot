import os
import json
from pathlib import Path
from typing import Union, Optional
from datetime import datetime

BASE_CHAT_HISTORY_DIR = Path("chat_history")
BASE_CHAT_HISTORY_DIR.mkdir(exist_ok=True)


def get_history_path(user_id: int) -> Path:
    month_str = datetime.now().strftime("%Y-%m")  # e.g., "2025-08"
    path = BASE_CHAT_HISTORY_DIR / str(user_id) / month_str
    path.mkdir(parents=True, exist_ok=True)
    return path / "history.json"


def save_user_message(
        user_id: int,
        role: str,
        content: Union[str, list[dict]],
        model_name: str,
        message_id: Optional[int] = None,
        tokens: int = 0,
        price: float = 0.0
):
    history_path = get_history_path(user_id)

    history = []
    if history_path.exists() and history_path.stat().st_size > 0:
        with open(history_path, "r", encoding="utf-8") as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []

    history.append({
        "role": role,
        "content": content,
        "message_id": message_id,
        "model_name": model_name,
        "tokens": tokens,
        "price": f"{price:.8f}",
        "timestamp": datetime.now().isoformat(),
    })

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def load_user_messages(user_id: int) -> list[dict]:
    history_path = get_history_path(user_id)

    if history_path.exists() and history_path.stat().st_size > 0:
        try:
            with open(history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []

    return []
