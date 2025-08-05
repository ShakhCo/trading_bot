import json
from datetime import datetime
from pathlib import Path


def get_user_profile_summary(user_id: int, username: str = None) -> str:
    month_str = datetime.now().strftime("%Y-%m")
    month_name = datetime.now().strftime("%B")
    history_file = Path("chat_history") / str(user_id) / month_str / "history.json"

    messages_count = 0
    total_price = 0.0

    if history_file.exists():
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
            user_messages = [msg for msg in history if msg.get("role") == "user"]
            messages_count = len(user_messages)
            total_price = sum(float(msg.get("price", 0.0)) for msg in history)
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    display_username = f"@{username}" if username else f"ID: {user_id}"
    usage_line = f"${total_price:.3f}, {messages_count} ta xabar"

    return f"• {display_username}: {usage_line}"
