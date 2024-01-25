import asyncio
from logging import Logger, getLogger
from typing import Any, Awaitable, Callable, Dict, Union
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, Document, PhotoSize, Audio, Voice
from aiogram.utils.markdown import italic
from io import BytesIO
from PIL.Image import Image, open
import pypdfium2 as pdfium

from bot.exceptions import FileSizeTooBigException, UnsupportedFileFormatException
from chat.voice_engine import VoiceEngine
from prompts.templates import build_msg_metadata_prompt
from utils.docreader import get_docx_text

logging: Logger = getLogger(__name__)

class PromptGenMiddleware(BaseMiddleware):
    async def __gen_img_prompt__(self, photo: list[Union[PhotoSize, Document]], bot: Bot):
        limit_size = [p for p in photo if p.file_size <= 150000] # limit to 150kb
        limit_size.sort(key=lambda ps: ps.file_size)
        if len(limit_size) == 0:
            # if greater than 20 MB raise exception
            if photo[0].file_size > 20000000:
                raise FileSizeTooBigException()
            # if no photo in limit_size, use the smallest one
            limit_size.append(photo[0])

        photo_id = limit_size[-1].file_id
        photo_bytes = BytesIO()
        photo_bytes = await bot.download(photo_id, photo_bytes)
        img = open(photo_bytes)
        if img.mode == 'RGB':
            return img
        else:
            return img.convert('RGB')
        
    async def __gen_voice_prompt__(self, voice: Union[Audio, Voice], voice_engine: VoiceEngine, bot: Bot):
        with await bot.download(voice.file_id, BytesIO()) as binfile:
            return await voice_engine.voice_to_text(binfile.read(), voice.mime_type)
        
    async def __gen_pdf_prompt__(self, document: Document, bot: Bot):
        # if greater than 20 MB raise exception
        if document.file_size > 20000000:
            raise FileSizeTooBigException()
        
        with await bot.download(document.file_id, BytesIO()) as binfile:
            pdf = pdfium.PdfDocument(binfile)
            pdf_text = f"FileName: {document.file_name}\n\n"
            for page in pdf:
                pdf_text += page.get_textpage().get_text_range()
            return pdf_text
    
    async def __gen_txt_prompt__(self, document: Document, bot: Bot):
        # if greater than 20 MB raise exception
        if document.file_size > 20000000:
            raise FileSizeTooBigException()

        text = f"FileName: {document.file_name}\n\n"
        with await bot.download(document.file_id, BytesIO()) as binfile:
            text +=  binfile.read().decode('utf-8')
        return text
    
    # TODO: Fix docx file text extraction
    async def __gen_docx_prompt__(self, document: Document, bot: Bot):
        # if greater than 20 MB raise exception
        if document.file_size > 20000000:
            raise FileSizeTooBigException()
        
        text = f"FileName: {document.file_name}\n\n"
        with await bot.download(document.file_id, BytesIO()) as binfile:
            text += get_docx_text(binfile)
        return text

    async def __msg_to_prompt__(self, msg: Message, voice_engine: VoiceEngine, exclude_caption: bool = False, exclude_metadata: bool = False):
        prompts: list[Union[str, Image]] = []
        meta_dict: dict[str, str] = {
            'timestamp': str(msg.date),
            'message_type': str(msg.content_type),
        }
        
        if (msg.text and len(msg.text) > 0):
            prompts.append(msg.text)
        elif (msg.photo and len(msg.photo) > 0):
            if (not exclude_caption and msg.caption and len(msg.caption) > 0):
                prompts.append(msg.caption)
            
            prompts.append(await self.__gen_img_prompt__(msg.photo, bot=msg.bot))
        elif (msg.voice):
            prompts.append(await self.__gen_voice_prompt__(msg.voice, voice_engine, bot=msg.bot))
        elif (msg.audio):
            prompts.append(await self.__gen_voice_prompt__(msg.audio, voice_engine, bot=msg.bot))
        elif (msg.sticker):
            if (msg.sticker.thumbnail):
                prompts.append(await self.__gen_img_prompt__([msg.sticker.thumbnail], bot=msg.bot))
            elif (msg.sticker.emoji and len(msg.sticker.emoji) > 0):
                prompts.append(msg.sticker.emoji)
        elif (msg.animation and msg.animation.thumbnail):
            prompts.append(await self.__gen_img_prompt__([msg.animation.thumbnail], bot=msg.bot))
        elif (msg.document):
            meta_dict['mime_type'] = msg.document.mime_type
            if (msg.document.mime_type.startswith('image')):
                prompts.append(await self.__gen_img_prompt__([msg.document.thumbnail], bot=msg.bot))
            elif (msg.document.mime_type == 'application/pdf'):
                prompts.append(await self.__gen_pdf_prompt__(msg.document, bot=msg.bot))
            elif (msg.document.mime_type.startswith('text')):
                prompts.append(await self.__gen_txt_prompt__(msg.document, bot=msg.bot))
            else:
                raise UnsupportedFileFormatException()

        if not exclude_metadata:
            prompts.append(build_msg_metadata_prompt(meta_dict))
        return prompts

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        sent = None
        voice_engine = data['voice_engine']
        try:
            sent = await event.reply(italic('Downloading message...'))
            prompts: list[Union[str, Image]] = []
            tasks: list[asyncio.Task] = []

            tasks.append(asyncio.create_task(self.__msg_to_prompt__(event, voice_engine)))
            tasks[-1].add_done_callback(lambda p: prompts.extend(p.result()))

            reply_of = event.reply_to_message
            if (reply_of):
                tasks.append(asyncio.create_task(self.__msg_to_prompt__(reply_of, voice_engine, exclude_caption=True, exclude_metadata=True)))
                tasks[-1].add_done_callback(lambda p: prompts.extend(p.result()))

            await asyncio.gather(*tasks)
        except UnsupportedFileFormatException:
            await sent.edit_text(italic('Unsupported document type.'))
            return
        except FileSizeTooBigException:
            await sent.edit_text(italic('File size too big.'))
            return
        except Exception as e:
            logging.error(e)
            if sent:
                await sent.edit_text(italic('Error while downloading message.'))
            else:
                await event.reply(italic('Error while downloading message.'))
            return

        data['sent'] = sent
        data['prompts'] = prompts

        return await handler(event, data)
