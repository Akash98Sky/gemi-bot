from logging import Logger, getLogger
from typing import Iterable, Union
from PIL.Image import Image
import google.generativeai as genai
from google.generativeai.generative_models import content_types, generation_types, ChatSession
from chat.exceptions import UnsupportedException
from prompts.static import CHAT_INIT_HISTORY
from re_edge_gpt import ImageGenAsync

logging: Logger = getLogger(__name__)

class ChatService(object):
    model: genai.GenerativeModel
    image_model: ImageGenAsync | None = None

    def __init__(self, api_key: str, bing_cookie: str | None = None, proxy: str | None = None):
        genai.configure(api_key=api_key)
        if bing_cookie and len(bing_cookie) > 0:
            self.image_model = ImageGenAsync(auth_cookie=bing_cookie, quiet=True, proxy=proxy)
        safety_settings = {
            'HARASSMENT': 'block_none',
            'HATE_SPEECH': 'block_none',
            'SEXUAL': 'block_only_high',
        }
        gen_config = generation_types.GenerationConfig(
            temperature=0.6,
        )
        self.model = genai.GenerativeModel('gemini-1.5-pro-latest', safety_settings=safety_settings, generation_config=gen_config)

    def __is_vision_prompt(self, prompts: Union[Iterable[Union[str, Image]], str]):
        if isinstance(prompts, str):
            return False
        elif next((prompt for prompt in prompts if isinstance(prompt, Image)), None) != None:
            return True
        else:
            return False
        
    def __to_user_content__(self, text: str):
        return content_types.strict_to_content(content_types.ContentDict(
            parts=[text],
            role="user"
        ))
    
    def __to_model_content__(self, text: str):
        return content_types.to_content(content_types.ContentDict(
            parts=[text],
            role="model"
        ))

    async def gen_response(self, prompts: Iterable[Union[str, Image]], chat: ChatSession | None = None, stream = False):
        try:
            if chat:
                response = await chat.send_message_async(content=prompts, stream=stream)
            else:
                response = await self.model.generate_content_async(contents=prompts, stream=stream)
        
            async for res in response:
                yield ''.join([part.text for part in res.parts])

        except generation_types.BrokenResponseError as e:
            logging.exception(e)
            if chat:
                chat.rewind()
        except StopAsyncIteration:
            # Handle the StopAsyncIteration exception, raised by async generators, here
            pass

    def gen_response_stream(self, prompts: Union[Iterable[Union[str, Image]], str], chat: ChatSession | None = None):
        return self.gen_response(prompts=prompts, chat=chat, stream=True)

    def create_chat_session(self, history: list[content_types.StrictContentType] = []):
        history.extend(CHAT_INIT_HISTORY)
        return self.model.start_chat(history=history)

    def gen_image_response(self, prompt: str):
        if not self.image_model:
            raise UnsupportedException("Image generation is not enabled.")
        return self.image_model.get_images(prompt, max_generate_time_sec=30)
