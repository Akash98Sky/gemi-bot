import asyncio
import textwrap
from typing import Iterable, Union
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai
from google.generativeai.generative_models import content_types

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

    async def gen_response(self, prompts: Union[Iterable[content_types.PartType], str]):
        if isinstance(prompts, str):
            response = await self.model.generate_content_async(prompts)
        elif next((prompt for prompt in prompts if isinstance(prompt, (content_types.BlobType))), None) != None:
            response = await self.vision_model.generate_content_async(contents=prompts)
        else:
            response = await self.model.generate_content_async(contents=prompts)
    
        return response.text
        
    async def gen_response_stream(self, prompts: Union[Iterable[content_types.PartType], str]):
        if isinstance(prompts, str):
            responses = await self.model.generate_content_async(prompts, stream=True)
        elif next((prompt for prompt in prompts if isinstance(prompt, (content_types.BlobType))), None) != None:
            responses = await self.vision_model.generate_content_async(contents=prompts, stream=True)
        else:
            responses = await self.model.generate_content_async(contents=prompts, stream=True)
    
        async for response in responses:
            yield response.text
