import json
from pathlib import Path
from datetime import datetime
from aiogram import BaseMiddleware
from aiogram.types import Message, Update
from aiogram.fsm.context import FSMContext
from typing import Callable, Dict, Any, Awaitable
import aiohttp  # <-- Import aiohttp


class AuthMiddleware(BaseMiddleware):
    USERS_DIR = Path("users")
    REGISTER_URL = "https://trading-api.shakha.uz/register"

    def __init__(self):
        self.USERS_DIR.mkdir(parents=True, exist_ok=True)

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: Update,
            data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            state: FSMContext = data["state"]
            user_data = await state.get_data()

            if not user_data.get("authenticated"):
                user = event.from_user
                user_file = self.USERS_DIR / f"{user.id}.json"

                if not user_file.exists():
                    user_info = {
                        "telegram_id": user.id,
                        "first": user.first_name,
                        "last": user.last_name or "",
                        "username": user.username or "",
                        "date_registered": datetime.utcnow().isoformat()
                    }

                    user_file.write_text(json.dumps(user_info, indent=2), encoding="utf-8")

                    # Send POST request
                    async with aiohttp.ClientSession() as session:
                        try:
                            await session.post(
                                self.REGISTER_URL,
                                json={
                                    "telegram_id": user_info["telegram_id"],
                                    "first": user_info["first"],
                                    "last": user_info["last"]
                                },
                                timeout=10
                            )
                        except aiohttp.ClientError as e:
                            print(f"[AuthMiddleware] Failed to register user: {e}")

                await state.update_data(authenticated=True)

        return await handler(event, data)
