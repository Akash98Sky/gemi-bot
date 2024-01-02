import logging
from typing import Iterable, Union
from PIL.Image import Image
import google.generativeai as genai
from google.generativeai.generative_models import content_types, generation_types, ChatSession
from prompts.static import CHAT_INIT_HISTORY

class ChatService(object):
    model: genai.GenerativeModel
    vision_model: genai.GenerativeModel

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-pro")
        self.vision_model = genai.GenerativeModel('gemini-pro-vision')

    def __is_vision_prompt(self, prompts: Union[Iterable[Union[str, Image]], str]):
        if isinstance(prompts, str):
            return False
        elif next((prompt for prompt in prompts if isinstance(prompt, Image)), None) != None:
            return True
        else:
            return False

    async def gen_response(self, prompts: Union[Iterable[Union[str, Image]], str], chat: ChatSession | None = None, stream = False):
        try:
            if self.__is_vision_prompt(prompts):
                response = await self.vision_model.generate_content_async(contents=prompts, stream=stream)
            elif chat:
                response = await chat.send_message_async(content=prompts, stream=stream)
            else:
                response = await self.model.generate_content_async(contents=prompts, stream=stream)
        
            async for res in response:
                yield res.text
        except generation_types.BrokenResponseError as e:
            logging.exception(e)
            if chat:
                chat.rewind()

        
    def gen_response_stream(self, prompts: Union[Iterable[Union[str, Image]], str], chat: ChatSession | None = None):
        return self.gen_response(prompts=prompts, chat=chat, stream=True)

    def create_chat_session(self, history: list[content_types.StrictContentType] = []):
        if next((prompt for prompt in history if isinstance(prompt, Image)), None) != None:
            return self.vision_model.start_chat(history=history)
        else:
            history.extend(CHAT_INIT_HISTORY)
            return self.model.start_chat(history=history)

