import asyncio
import aiohttp
from google.genai.types import Blob
from logging import Logger, getLogger
from typing import Literal
import pollinations
from pydantic import BaseModel

logging: Logger = getLogger(__name__)

class ImageResponse(BaseModel):
    url: str
    blob: Blob

class ImgGenService():
    __name__ = "ImgGenService"
    client: pollinations.Async.Image

    def __init__(self) -> None:
        self.client = pollinations.Async.Image()

    async def __req_image__(self, image_request: pollinations.Async.Image.Request):
        request = await image_request()
        if request.response:
            async with aiohttp.ClientSession() as session, session.get(request.response.url) as response:
                return ImageResponse(
                    url=str(request.response.url),
                    blob=Blob(
                        mime_type=response.content_type,
                        data=await response.content.read()
                    )
                )

    async def gen_image_response(
        self,
        prompt: str,
        quantity: int = 1,
        quality: Literal["LOW", "MEDIUM", "HIGH"] = "MEDIUM",
        **kwargs
    ) :
        image_requests: list[asyncio._CoroutineLike[ImageResponse | None]] = []
        height = 1024
        width = 1024

        if quality == "LOW":
            height = 512
            width = 512
        elif quality == "HIGH":
            height = 2048
            width = 2048
        
        for _ in range(quantity):
            image_requests.append(
                self.__req_image__(pollinations.Async.Image.Request(
                    model='flux-pro',
                    prompt=prompt,
                    seed="random",
                    width=width,
                    height=height,
                    enhance=False,
                    nologo=True,
                    private=True,
                    safe=False
                ))
            )

        images = await asyncio.gather(*image_requests)
        images = [img for img in images if img]

        if len(images) == 0:
            raise Exception('No images generated, try something else!')
        
        return images