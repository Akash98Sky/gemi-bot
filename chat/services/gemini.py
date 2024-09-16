from logging import Logger, getLogger
from typing import Iterable, Union
from PIL.Image import Image
import google.generativeai as genai
from google.generativeai.generative_models import content_types, generation_types, ChatSession
from chat.prompts.static import CHAT_INIT_HISTORY

logging: Logger = getLogger(__name__)

class GeminiService(object):
    model: genai.GenerativeModel

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        safety_settings = {
            'HARASSMENT': 'block_none',
            'HATE_SPEECH': 'block_none',
            'SEXUAL': 'block_only_high',
        }
        gen_config = generation_types.GenerationConfig(
            temperature=0.6,
        )
        # for m in genai.list_models():
        #     pprint.pprint(m)
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest', safety_settings=safety_settings, generation_config=gen_config)
        
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

    async def gen_response(self, prompts: Iterable[content_types.PartType], chat: ChatSession | None = None, stream = False):
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

    def gen_response_stream(self, prompts: Union[Iterable[content_types.PartType], str], chat: ChatSession | None = None):
        return self.gen_response(prompts=prompts, chat=chat, stream=True)

    def create_chat_session(self, history: list[content_types.StrictContentType] = []):
        history.extend(CHAT_INIT_HISTORY)
        return self.model.start_chat(history=history)

