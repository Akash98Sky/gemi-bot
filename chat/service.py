import textwrap
from typing import Iterable, Union
from PIL.Image import Image
import google.generativeai as genai
from google.generativeai.generative_models import content_types, ChatSession, generation_types

class ChatService(object):
    model: genai.GenerativeModel
    vision_model: genai.GenerativeModel

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-pro")
        self.vision_model = genai.GenerativeModel('gemini-pro-vision')

    def to_markdown(self, text):
        text = text.replace('•', '  *').replace('.', '\.')
        return textwrap.indent(text, '> ', predicate=lambda _: True)

    async def gen_response(self, prompts: Union[Iterable[Union[str, Image]], str]):
        if isinstance(prompts, str):
            response = await self.model.generate_content_async(prompts)
        elif next((prompt for prompt in prompts if isinstance(prompt, Image)), None) != None:
            response = await self.vision_model.generate_content_async(contents=prompts)
        else:
            response = await self.model.generate_content_async(contents=prompts)
    
        return response.text
        
    async def gen_response_stream(self, prompts: Union[Iterable[Union[str, Image]], str]):
        if isinstance(prompts, str):
            responses = await self.model.generate_content_async(prompts, stream=True)
        elif next((prompt for prompt in prompts if isinstance(prompt, Image)), None) != None:
            responses = await self.vision_model.generate_content_async(contents=prompts, stream=True)
        else:
            responses = await self.model.generate_content_async(contents=prompts, stream=True)
    
        async for response in responses:
            yield response.text

    def create_chat_session(self, history: Iterable[content_types.StrictContentType] = []):
        if next((prompt for prompt in history if isinstance(prompt, Image)), None) != None:
            return self.vision_model.start_chat(history=history)
        else:
            return self.model.start_chat(history=history)

    async def gen_chat_response_stream(self, chat: ChatSession, prompts: Iterable[Union[str, Image]]):
        chat_vision = None
        if next((prompt for prompt in prompts if isinstance(prompt, Image)), None) != None:
            # use vision model if blob in history
            chat_vision = self.vision_model.start_chat()
            responses = await chat_vision.send_message_async(prompts, stream=True)
        else:
            responses = await chat.send_message_async(prompts, stream=True)

        async for response in responses:
            yield response.text

        # TODO: Fix handling of chat_vision history, need to filter just text responses
        # if chat_vision:
        #     chat.history.append(chat_vision.history)
