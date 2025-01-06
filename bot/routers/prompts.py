from logging import Logger, getLogger
from aiogram import Router
from aiogram.types import Message, InputMediaAudio, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.markdown import italic, pre
from google.genai.types import PartUnionDict
from md2tgmd import escape

from bot.middlewares.prompt_gen import PromptGenMiddleware
from chat.repository import Chat, ChatRepo

logging: Logger = getLogger(__name__)

# All handlers should be attached to the Router (or Dispatcher)
prompts_router = Router(name='message_router')

prompts_router.message.middleware.register(PromptGenMiddleware())

@prompts_router.message()
async def echo_handler(message: Message, repo: ChatRepo, prompts: list[PartUnionDict] = [], sent: Message | None = None) -> None:
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
        text_reply: Message | None = None
        
        response = ""
        error: TelegramBadRequest | None = None
        async for reply in chat.send_message_async(prompts):
            try:
                if isinstance(reply, list):
                    if sent:
                        await sent.delete()
                        sent = None
                    await message.reply_media_group(media=list(reply))
                if isinstance(reply, InputMediaPhoto):
                    if sent:
                        await sent.delete()
                        sent = None
                    await message.reply_photo(photo=reply.media)
                elif isinstance(reply, InputMediaAudio):
                    if sent:
                        await sent.delete()
                        sent = None
                    await message.reply_voice(voice=reply.media)
                elif isinstance(reply, str):
                    response = response + reply
                    error = None
                    # escape() converts Markdown to Telegram specific Markdown v2 format
                    response_md = escape(response)

                    # Send the response back to the user
                    if reply.strip() != '':
                        text_reply = sent if sent else text_reply
                        sent = None
                        if text_reply and text_reply.md_text.strip() != response_md.strip():
                            # Only update if there was a change
                            await text_reply.edit_text(text=response_md)
                        elif text_reply is None:
                            # Send a new message if the previous one was deleted
                            text_reply = await message.reply(text=response_md)
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
        logging.warning(f'Failed to reply message: {message.text}, TelegramBadRequest: {e}')
        if sent != None:
            await sent.edit_text(text=italic('Failed to reply, try again...'))
        else:
            await message.reply(text=italic('Failed to reply, try again...'))
    except Exception as e:
        # But not all the types is supported to be copied so need to handle it
        logging.error(f'Failed to reply message: {message.text}, Exception: {e}', exc_info=True)
        if sent != None:
            await sent.edit_text(text=escape('Oops! Failed...\n\n') + pre(f'{(type(e).__name__)}: {e}'))
        else:
            await message.reply(text=escape('Oops! Failed...\n\n') + pre(f'{(type(e).__name__)}: {e}'))

