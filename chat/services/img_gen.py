from logging import Logger, getLogger

from g4f.client.async_client import AsyncClient, Images
from g4f.providers.base_provider import AsyncGeneratorProvider
from g4f.providers.retry_provider import raise_exceptions
from g4f.cookies import set_cookies
from g4f.Provider import BingCreateImages, DeepInfraImage, ReplicateImage, Gemini, You

logging: Logger = getLogger(__name__)

class ImgGenService():
    __name__ = "ImgGenService"
    providers: list[AsyncGeneratorProvider] = []

    def __init__(
        self,
        bing_cookie: str | None = None,
        google_cookie: str | None = None
    ) -> None:
        self.client = AsyncClient()
        if bing_cookie and bing_cookie != "":
            self.providers.append(BingCreateImages)
            set_cookies(".bing.com", {
                "_U": bing_cookie
            })
        if google_cookie and google_cookie != "":
            self.providers.append(Gemini)
            set_cookies(".google.com", {
                "__Secure-1PSID": google_cookie
            })
        # fallback providers
        self.providers.append(DeepInfraImage)
        self.providers.append(ReplicateImage)

    async def gen_image_response(
        self,
        prompt: str,
        **kwargs
    ) -> list[str]:
        exceptions: dict = {}
        for provider in self.providers:
            try:
                img = Images(client=self.client, provider=provider)
                response = await img.generate(prompt, **kwargs)
                return [img.url for img in response.data]
            except Exception as e:
                exceptions[provider.__name__] = e
                logging.warn(f"{provider.__name__}: {e.__class__.__name__}: {e}")
        
        raise_exceptions(exceptions)