from logging import Logger, getLogger
from PIL.Image import Image
from typing import Any, Dict, Union
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InputMediaAudio
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.markdown import bold, italic, pre

from bot.middlewares import PromptGenMiddleware
from chat.repository import Chat, ChatRepo
from md2tgmd import escape

logging: Logger = getLogger(__name__)

# All handlers should be attached to the Router (or Dispatcher)
command_router = Router(name='/')
message_router = Router(name='/commands')

routers = [
    command_router,
    message_router
]

message_router.message.middleware.register(PromptGenMiddleware())

@command_router.message(CommandStart())
async def command_start_handler(message: Message, repo: ChatRepo) -> None:
    """
    This handler receives messages with `/start` command
    """
    chat: Chat = await repo.get_chat_session(message.chat.id)

    if chat:
        # Reset the chat session if it exists
        await chat.reset()

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

        chat: Chat = await repo.get_chat_session(message.chat.id)
        
        response = ""
        error: TelegramBadRequest | None = None
        async for reply in chat.send_message_async(prompts):
            try:
                if isinstance(reply, list):
                    if sent:
                        await sent.delete()
                        sent = None
                    await message.reply_media_group(media=reply)
                elif isinstance(reply, InputMediaAudio):
                    if sent:
                        await sent.delete()
                        sent = None
                    await message.reply_voice(voice=reply.media)
                elif sent:
                    response = response + reply
                    error = None
                    # escape() converts Markdown to Telegram specific Markdown v2 format
                    response_md = escape(response)
                    if sent.text != response_md:
                        sent = await sent.edit_text(text=response_md)
            except TelegramBadRequest as e:
                error = e
                # Ignore intermediate errors
                if e.message.find('not found') != -1:
                    # The message was deleted
                    break

        if error:
            raise error
    except TelegramBadRequest as e:
        # Ignore intermediate errors
        logging.warn(f'Failed to reply message: {message.text}, TelegramBadRequest: {e}')
        if sent != None:
            await sent.edit_text(text=italic('Failed to reply, try again...'))
        else:
            await message.reply(text=italic('Failed to reply, try again...'))
    except Exception as e:
        # But not all the types is supported to be copied so need to handle it
        logging.error(f'Failed to reply message: {message.text}, Exception: {e}', exc_info=True)
        if sent != None:
            await sent.edit_text(text=f'Oops\! Failed\.\.\.\n\n' + pre(f'{(type(e).__name__)}: {e}'))
        else:
            await message.reply(text=f'Oops\! Failed\.\.\.\n\n' + pre(f'{(type(e).__name__)}: {e}'))
    
