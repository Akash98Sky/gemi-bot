import asyncio
from typing import Literal
from google.genai.types import Blob
from groq import AsyncGroq
from logging import getLogger
from pydantic import BaseModel

from common.types.exceptions import FeatureNotEnabledException

logging = getLogger(__name__)

class VoiceResponse(BaseModel):
    data: bytes
    blob: Blob

class VoiceService:
    __engine_busy_sem = asyncio.BoundedSemaphore(1)
    __groq: AsyncGroq | None = None
    __model: str
    __voice: str
    __response_format: Literal['flac', 'mp3', 'mulaw', 'ogg', 'wav']
    
    def __init__(self, groq_api_key: str | None, tts_model: str, tts_voice: str):
        self.__groq = AsyncGroq(api_key=groq_api_key) if groq_api_key else None
        self.__model = tts_model
        self.__voice = tts_voice
        self.__response_format = 'wav'

    async def close(self):
        return await self.__groq.close() if self.__groq else None

    async def text_to_wave(self, text: str) -> VoiceResponse:
        if not self.__groq:
            raise FeatureNotEnabledException("Voice generation is not enabled.")
        if not text or text.isspace():
            raise ValueError("Text cannot be empty")

        async with self.__engine_busy_sem:
            try:
                response = await self.__groq.audio.speech.create(
                    model=self.__model,
                    voice=self.__voice,
                    input=text,
                    response_format=self.__response_format
                )
                data = await response.read()

                return VoiceResponse(
                    data=data,
                    blob=Blob(
                        data=data,
                        mime_type=response.headers.get("Content-Type", f'audio/{self.__response_format}')
                    )
                )
            except Exception as e:
                logging.error(f"Error in text_to_wave: {e}", exc_info=True)
                raise e
