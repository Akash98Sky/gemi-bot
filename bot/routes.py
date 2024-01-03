import logging
from PIL.Image import Image
from typing import Any, Dict, Union
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.markdown import bold, italic

from bot.middlewares import PromptGenMiddleware
from chat.repository import ChatRepo

# All handlers should be attached to the Router (or Dispatcher)
command_router = Router(name='/')
message_router = Router(name='/commands')

routers = [
    command_router,
    message_router
]

message_router.message.middleware.register(PromptGenMiddleware())

@command_router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.answer(f"Hello, {bold(message.from_user.full_name)}\!")


@message_router.message()
async def echo_handler(message: Message, repo: ChatRepo, prompts: list[Union[str, Image]] = [], sent: Message | None = None) -> None:
    """
    Handler will forward receive a message back to the sender

    By default, message handler will handle all message types (like a text, photo, sticker etc.)
    """
    try:
        # Send a reply to the received message
        if sent:
            await sent.edit_text(text=italic("Thinking..."))
        else:
            sent = await message.reply(text=italic('Thinking...'))

        chat = await repo.get_chat_session(message.chat.id)
        
        response = ""
        error: TelegramBadRequest | None = None
        async for reply in chat.send_message_async(prompts):
            response = response + reply
            try:
                error = None
                sent = await sent.edit_text(text=response, parse_mode=ParseMode.MARKDOWN)
            except TelegramBadRequest as e:
                error = e
                # Ignore intermediate errors
                if e.message.find('not found') != -1:
                    # The message was deleted
                    break
                else:
                    pass

        if error:
            raise error
    except TelegramBadRequest as e:
        # Ignore intermediate errors
        logging.warn(f'Failed to reply message: {message.text}, TelegramBadRequest: {e}')
        pass
    except Exception as e:
        # But not all the types is supported to be copied so need to handle it
        if sent != None:
            await sent.edit_text(text=f'Oops! Failed...\n\n{type(e).__name__}: {e}', parse_mode=ParseMode.HTML)
        else:
            await message.reply(f'Oops! Failed...\n\n{type(e).__name__}: {e}', parse_mode=ParseMode.HTML)
    
