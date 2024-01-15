import asyncio
from aiohttp import ClientSession
from logging import getLogger
from urllib.parse import urlencode

logging = getLogger(__name__)

class VoiceEngine:
    __engine_busy_sem = asyncio.BoundedSemaphore(1)
    __client_session: ClientSession | None = None
    __tts: str
    __voice: str
    __voice_api_url: str
    
    def __init__(self, voice_api_url: str | None, tts_voice: str):
        if not voice_api_url or not voice_api_url.strip():
            return
        [self.__tts, self.__voice] = tts_voice.split(':')
        self.__voice_api_url = voice_api_url
        self.__client_session = ClientSession(base_url=voice_api_url)
        asyncio.create_task(self.__bring_up_engine__())

    async def __bring_up_engine__(self):
        async with self.__engine_busy_sem:
            while True:
                try:
                    async with self.__client_session.get('/api/speak/voices', allow_redirects=False) as response:
                        if response.status == 200:
                            break
                except Exception as e:
                    logging.warning(f"OpenTTS engine is not up yet: {e}")

                logging.info("OpenTTS engine is not up yet, sleeping for 10 seconds")
                await asyncio.sleep(10)
        logging.info("OpenTTS engine is up")

    async def text_to_wave(self, text: str):
        if not self.__client_session:
            raise NotImplemented("OpenTTS engine is not enabled.")
        
        async with self.__engine_busy_sem:
            params={'text': text, 'voice_id': self.__voice}
            return f'{self.__voice_api_url}/api/speak/{self.__tts}?{urlencode(params)}'