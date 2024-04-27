from logging import Logger, getLogger
from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.markdown import bold

from chat.repository import Chat, ChatRepo

logging: Logger = getLogger(__name__)

# All handlers should be attached to the Router (or Dispatcher)
command_router = Router(name='command_router')

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
