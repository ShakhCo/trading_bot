import asyncio
import base64
import contextlib
import json
import os
from datetime import datetime
from io import BytesIO
from pathlib import Path

import aiohttp
from aiogram.fsm.context import FSMContext

from core import TELEGRAM_BOT_TOKEN, BASE_URL, ADMIN_TELEGRAM_ID
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from middlewares.auth import AuthMiddleware

from helpers import gpt_handle_text, with_typing, get_user_profile_summary

dp = Dispatcher()

dp.message.middleware(AuthMiddleware())

USERS_DIR = "users"


# Command handler
@dp.message(Command("start"))
async def command_start_handler(message: Message) -> None:
    await message.answer(
        f"👋 Assalamu alaykum {message.from_user.first_name}!\n\n"
        "Men sun'iy intellekt asosida ishlaydigan chat botman.\n"
        "Hozircha matnli xabarlar va rasmlarga javob bera olaman.\n\n"
        "Savoling bormi yoki rasm yubormoqchisan? Marhamat, yozaver 😉"
    )


@dp.message(Command("users"))
async def list_users_handler(message: Message):
    if not int(ADMIN_TELEGRAM_ID) == message.from_user.id:
        return

    if not os.path.exists(USERS_DIR):
        await message.answer("❌ 'users' directory not found.")
        return

    files = [f for f in os.listdir(USERS_DIR) if f.endswith('.json')]
    user_count = len(files)

    response = f"👥 Total registered users: {user_count}"

    preview = []

    for file in files[:10]:  # Show up to 10 users
        try:
            with open(os.path.join(USERS_DIR, file), "r", encoding="utf-8") as f:
                data = json.load(f)
                user_id = int(data.get("telegram_id"))
                username = data.get("username", "no_username")
                summary = get_user_profile_summary(user_id, username)
                preview.append(summary)
        except Exception as e:
            preview.append(f"• Error reading {file}: {e}")

    if preview:
        response += "\n\n📋 User usage:\n" + "\n".join(preview)

    await message.answer(response)


@dp.message(Command("profile"))
async def command_profile_handler(message: Message) -> None:
    user = message.from_user
    user_id = user.id
    first_name = user.first_name or "Nomaʼlum"
    month_str = datetime.now().strftime("%Y-%m")
    month_name = datetime.now().strftime("%B")  # Masalan: August

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
            pass  # 0 qiymatlarni saqlab qolamiz

    usage_line = f"<b>- {month_name}:</b> ${total_price:.3f}"
    if messages_count > 0:
        usage_line += f", jami {messages_count} ta xabar"

    await message.answer(
        f"<blockquote>👤 <b>Profil</b></blockquote>\n"
        f"<b>- Ism:</b> {first_name}\n"
        f"<b>- Holat:</b> 🟢 Faol\n\n"
        f"<blockquote>💰 <b>Hisob-kitob</b></blockquote>\n"
        f"{usage_line}",
        parse_mode="HTML"
    )


@dp.message(lambda msg: msg.photo)
@with_typing
async def photo_handler(message: Message, state: FSMContext) -> None:
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)
    file_path = file.file_path
    file_bytes = await message.bot.download_file(file_path)

    temp_file_path = f"/tmp/{message.from_user.id}_photo.jpg"
    with open(temp_file_path, "wb") as f:
        f.write(file_bytes.read())

    async with aiohttp.ClientSession() as session:
        with open(temp_file_path, "rb") as f:
            form = aiohttp.FormData()
            form.add_field("file", f, filename="photo.jpg", content_type="image/jpeg")

            upload_url = f"{BASE_URL}/users/{message.from_user.id}/upload-photo/"
            async with session.post(upload_url, data=form) as resp:
                if resp.status != 201:
                    await message.answer("❌ Failed to upload the photo.")
                    return

                data = await resp.json()
                image_url = data.get("download_url")

    await gpt_handle_text(
        message=message,
        image_url=f"{BASE_URL}{image_url}"
    )


@dp.message(F.text, ~F.command)
@with_typing
async def echo_handler(message: Message, state: FSMContext) -> None:
    await gpt_handle_text(message)


async def main() -> None:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
