import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, Union
from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, Document, PhotoSize
from aiogram.utils.markdown import italic
from io import BytesIO
from PIL.Image import Image, open
import pypdfium2 as pdfium
from duckduckgo_search import AsyncDDGS

from bot.exceptions import UnsupportedFileFormatException
from utils.docreader import get_docx_text

class PromptGenMiddleware(BaseMiddleware):
    async def __gen_img_prompt__(self, photo: list[Union[PhotoSize, Document]], bot: Bot):
        limit_size = [p for p in photo if p.file_size <= 150000] # limit to 150kb
        limit_size.sort(key=lambda ps: ps.file_size)
        if len(limit_size) == 0:
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
        
    async def __gen_pdf_prompt__(self, document: Document, bot: Bot):
        with await bot.download(document.file_id, BytesIO()) as binfile:
            pdf = pdfium.PdfDocument(binfile)
            pdf_text = f"FileName: {document.file_name}\n\n"
            for page in pdf:
                pdf_text += page.get_textpage().get_text_range()
            return pdf_text
    
    async def __gen_txt_prompt__(self, document: Document, bot: Bot):
        text = f"FileName: {document.file_name}\n\n"
        with await bot.download(document.file_id, BytesIO()) as binfile:
            text +=  binfile.read().decode('utf-8')
        return text
    
    # TODO: Fix docx file text extraction
    async def __gen_docx_prompt__(self, document: Document, bot: Bot):
        text = f"FileName: {document.file_name}\n\n"
        with await bot.download(document.file_id, BytesIO()) as binfile:
            text += get_docx_text(binfile)
        return text
    
    async def __gen_live_data_prompt__(self, query: str):
        text = f"Search engine response:\n\n"
        async with AsyncDDGS() as ddgs:
            async for res in ddgs.text(query, region="in-en", max_results=1):
                text += f"Title: {res['title']}\n"
                text += f"Body: {res['body']}\n"
        return text

    async def __msg_to_prompt__(self, msg: Message, exclude_caption: bool = False):
        prompts: list[Union[str, Image]] = []
        
        if (msg.text and len(msg.text) > 0):
            prompts.append(msg.text + "\n\nNote: Use Search engine response to respond to data queries that you're not aware of")
            if(len(msg.text) >= 3 and len(msg.text) <= 50):
                # TODO: Fetch query from gemini response
                prompts.append(await self.__gen_live_data_prompt__(msg.text))
        elif (msg.photo and len(msg.photo) > 0):
            if (not exclude_caption and msg.caption and len(msg.caption) > 0):
                prompts.append(msg.caption)
            
            prompts.append(await self.__gen_img_prompt__(msg.photo, bot=msg.bot))
        elif (msg.sticker):
            if (msg.sticker.thumbnail):
                prompts.append(await self.__gen_img_prompt__([msg.sticker.thumbnail], bot=msg.bot))
            elif (msg.sticker.emoji and len(msg.sticker.emoji) > 0):
                prompts.append(msg.sticker.emoji)
        elif (msg.animation and msg.animation.thumbnail):
            prompts.append(await self.__gen_img_prompt__([msg.animation.thumbnail], bot=msg.bot))
        elif (msg.document):
            if (msg.document.mime_type.startswith('image')):
                prompts.append(await self.__gen_img_prompt__([msg.document.thumbnail], bot=msg.bot))
            elif (msg.document.mime_type == 'application/pdf'):
                prompts.append(await self.__gen_pdf_prompt__(msg.document, bot=msg.bot))
            elif (msg.document.mime_type.startswith('text')):
                prompts.append(await self.__gen_txt_prompt__(msg.document, bot=msg.bot))
            else:
                raise UnsupportedFileFormatException()

        return prompts

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        sent = None
        try:
            sent = await event.reply(italic('Downloading message...'))
            prompts: list[Union[str, Image]] = []
            tasks: list[asyncio.Task] = []

            tasks.append(asyncio.create_task(self.__msg_to_prompt__(event)))
            tasks[-1].add_done_callback(lambda p: prompts.extend(p.result()))

            reply_of = event.reply_to_message
            if (reply_of):
                tasks.append(asyncio.create_task(self.__msg_to_prompt__(reply_of, exclude_caption=True)))
                tasks[-1].add_done_callback(lambda p: prompts.extend(p.result()))

            await asyncio.gather(*tasks)
        except UnsupportedFileFormatException:
            await sent.edit_text(italic('Unsupported document type.'))
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