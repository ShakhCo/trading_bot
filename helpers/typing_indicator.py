import asyncio
import contextlib
from functools import wraps
from aiogram.types import Message
from aiogram.fsm.context import FSMContext


def with_typing(func):
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        state: FSMContext = kwargs.get("state")
        if not state:
            for arg in args:
                if isinstance(arg, FSMContext):
                    state = arg
                    break

        if not state:
            raise ValueError("FSMContext `state` is required for `with_typing`")

        # Check if user is busy
        user_data = await state.get_data()
        if user_data.get("busy"):
            await message.delete()
            return

        await state.update_data(busy=True)

        typing_task = asyncio.create_task(_typing_loop(message.bot, message.chat.id))
        try:
            return await func(message, *args, **kwargs)
        finally:
            typing_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await typing_task
            await state.update_data(busy=False)

    return wrapper


async def _typing_loop(bot, chat_id):
    try:
        while True:
            await bot.send_chat_action(chat_id=chat_id, action="typing")
            await asyncio.sleep(5)
    except asyncio.CancelledError:
        pass
