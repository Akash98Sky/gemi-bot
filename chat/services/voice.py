import asyncio
from contextlib import suppress
from google.genai.types import Blob
import signal
from aiohttp import ClientSession, JsonPayload
from logging import getLogger

from pydantic import BaseModel

from common.types.exceptions import FeatureNotEnabledException

logging = getLogger(__name__)

class VoiceResponse(BaseModel):
    url: str
    blob: Blob

class VoiceService:
    __engine_busy_sem = asyncio.BoundedSemaphore(1)
    __client_session: ClientSession
    __tts: str
    __stt: str
    __voice: str
    __voice_api_url: str
    __engine_up_task: asyncio.Task
    
    def __init__(self, voice_api_url: str | None, tts_voice: str, stt_engine: str):
        if not voice_api_url or not voice_api_url.strip():
            return
        [self.__tts, self.__voice] = tts_voice.split(':')
        self.__stt = stt_engine
        self.__voice_api_url = voice_api_url
        self.__client_session = ClientSession(base_url=voice_api_url)
        self.__engine_up_task = asyncio.create_task(self.__bring_up_engine__())
        loop = asyncio.get_running_loop()
        with suppress(NotImplementedError):  # pragma: no cover
            # Signals handling is not supported on Windows
            # It also can't be covered on Windows
            loop.add_signal_handler(
                signal.SIGTERM, self.__close_client
            )
            loop.add_signal_handler(
                signal.SIGINT, self.__close_client
            )

    async def __bring_up_engine__(self):
        async with self.__engine_busy_sem:
            while True:
                try:
                    async with self.__client_session.get('/api/speak/voices', allow_redirects=False) as response:
                        if response.status == 200:
                            break
                except Exception as e:
                    logging.warning(f"Voice engine is not up yet: {e}")

                logging.info("Voice engine is not up yet, sleeping for 10 seconds")
                await asyncio.sleep(10)
        logging.info("Voice engine is up...")

    def __close_client(self):
        if not self.__engine_up_task.done():
            self.__engine_up_task.cancel()
        if self.__client_session:
            asyncio.create_task(self.__client_session.close())
        logging.info("Voice engine is closed...")

    async def text_to_wave(self, text: str):
        if not self.__client_session:
            raise FeatureNotEnabledException("Voice engine is not enabled.")
        
        async with self.__engine_busy_sem:
            # Wait until engine is up
            pass

        data = JsonPayload({'text': text, 'voice_id': self.__voice})
        async with self.__client_session.post(f'/api/speak/{self.__tts}', data=data) as response:
            if response.status != 200:
                raise Exception(f"Voice engine returned error status: {response.status}")
            
            res = await response.json()
            url = str(res['url'])
        
        relative_url = url.removeprefix(self.__voice_api_url).replace('onetime/', '')
        async with self.__client_session.get(relative_url) as response:
            if response.status != 200:
                raise Exception(f"Voice engine returned error status: {response.status}")

            return VoiceResponse(
                url=url,
                blob=Blob(mime_type=response.content_type, data=await response.content.read())
            )
