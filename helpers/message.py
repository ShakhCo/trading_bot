import asyncio
import html
import re
from datetime import datetime

from aiogram.enums import ParseMode
from aiogram.types import Message
from core import OPENAI_CLIENT, AI_MODELS
from .history_manager import save_user_message, load_user_messages


def clean_telegram_html(text: str) -> str:
    # Fix <br/> to <br>
    text = text.replace("<br/>", "<br>").replace("<br />", "<br>")

    # Remove unsupported tags (ul, ol, li, span, div, etc.)
    text = re.sub(r"</?(ul|ol|li|span|div|table|thead|tbody|tr|td|th)[^>]*>", "", text)

    return text


async def gpt_handle_text(
        message: Message,
        image_url: str = None
):
    user_id = message.from_user.id
    user_prompt = message.text or message.caption or ""
    message_id = message.message_id

    model_name = 'o4-mini'
    history_json = load_user_messages(user_id)

    now = datetime.now()
    today = now.date()
    today_messages = [
        msg for msg in history_json
        if msg.get("role") == "user"
           and "timestamp" in msg
           and datetime.fromisoformat(msg["timestamp"]).date() == today
    ]

    if len(today_messages) >= 100:
        await message.reply("🛑 Kunlik limitga yetdingiz (100 ta xabar). Iltimos, ertaga yana urinib ko‘ring.")
        return

    history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in history_json[-60:]
    ]

    replying_messages_contents = []

    if message.reply_to_message:
        replied_message_id = message.reply_to_message.message_id
        for i, msg in enumerate(history_json):
            if msg.get("message_id") == replied_message_id:

                replying_messages_contents.append({
                    "role": msg.get("role", 'user'),
                    "content": msg.get("content", '')
                })

                if i + 1 < len(history_json):
                    next_msg = history_json[i + 1]
                    if next_msg.get("message_id") == replied_message_id:
                        replying_messages_contents.append({
                            "role": next_msg.get("role", 'user'),
                            "content": next_msg.get("content", '')
                        })
                break

    user_content = []

    if image_url:
        if user_prompt:
            user_content.append({"role": "user", "content": user_prompt})
        user_content.append({
            "role": "user",
            "content": [{"type": "input_image", "image_url": image_url}]
        })
    else:
        user_content.append({"role": "user", "content": user_prompt})

    history.extend(replying_messages_contents)
    history.extend(user_content)

    response = await asyncio.to_thread(
        OPENAI_CLIENT.responses.create,
        model=model_name,
        input=[
            {
                "role": "system",
                "content": "You are a helpful assistant. "
                           "Our major users talk in Uzbek/Russian. "
                           "Most of them, most probably, are Muslim. "
                           f"User first name is {message.from_user.first_name}."
                           f"Current date (tell this if user asks): {now.strftime('%Y-%m-%d')}."
                           f"Current time (tell this if user asks): {now.strftime('%I:%M %p')}."
                           f"Return simple Telegram-compatible HTML using only <b>, <i>, <pre>, <code>, \n, and <a>"
            },
            *history
        ],
    )

    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    pricing = AI_MODELS.get(model_name, {})
    input_cost = (input_tokens / 1_000_000) * pricing.get('input', 0)
    output_cost = (output_tokens / 1_000_000) * pricing.get('output', 0)

    response_text = response.output_text.strip()

    for i, content in enumerate(user_content):
        save_user_message(
            user_id=user_id,
            role="user",
            content=content["content"],
            message_id=message_id,
            model_name=model_name,
            tokens=input_tokens if i == 0 else 0,
            price=input_cost if i == 0 else 0,
        )

    response_message = await message.reply(response_text, parse_mode=ParseMode.HTML)

    save_user_message(
        user_id=user_id,
        role="assistant",
        content=response_text,
        message_id=response_message.message_id,
        model_name=model_name,
        tokens=output_tokens,
        price=output_cost
    )
