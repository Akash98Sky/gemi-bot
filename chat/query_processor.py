from logging import Logger, getLogger
from typing import AsyncGenerator, Union
from aiogram.types import InputMediaPhoto, InputMediaAudio, URLInputFile, BufferedInputFile
from google.genai import chats, types
import time

from chat.services.gemini import GeminiService
from chat.services.tavily import TavilyService
from chat.services.voice import VoiceService
from chat.services.img_gen import ImgGenService
from common.constants.keywords import IMAGE_QUERY, SEARCH_QUERIES, VOICE_RESPONSE
from chat.tools.generation import GenerateImageFunctionCall, GenerateImageParams, GenerateVoiceFunctionCall, GenerateVoiceParams
from chat.tools.search import DuckduckgoSearchFunctionCall, DuckduckgoSearchParams, DuckduckgoSearchResults, TavilySearchFunctionCall, TavilySearchParams,TavilySearchResults

logging: Logger = getLogger(__name__)

type ModelEventType = Union[str, GenerateImageFunctionCall, GenerateVoiceFunctionCall, DuckduckgoSearchFunctionCall, TavilySearchFunctionCall]
type OutputEventType = Union[str, InputMediaPhoto, InputMediaAudio, list[InputMediaPhoto], DuckduckgoSearchResults, TavilySearchResults]

class QueryProcessor():
    __gemini: GeminiService
    __voice: VoiceService
    __img_gen: ImgGenService
    __tavily: TavilyService
    __query_list__ = [
        IMAGE_QUERY,
        SEARCH_QUERIES,
        VOICE_RESPONSE
    ]

    def __init__(self, gemini: GeminiService, voice: VoiceService, img_gen: ImgGenService, tavily: TavilyService) -> None:
        self.__gemini = gemini
        self.__voice = voice
        self.__img_gen = img_gen
        self.__tavily = tavily

    async def __tavily_search_function_call__(self, args: TavilySearchParams):
        logging.debug(f"Generating live data prompt for query: {args.query}")

        result = await self.__tavily.search(args.query.strip(), max_results=args.max_results, topic=args.topic)

        return TavilySearchResults.model_validate(result)
    
    async def __gen_image_function_call__(self, args: GenerateImageParams):
        logging.debug(f"Generate image query: {args.prompt}")
        image_responses = await self.__img_gen.gen_image_response(args.prompt)
        
        responses = [InputMediaPhoto(media=URLInputFile(res.url, filename=f'{args.image_name}.jpeg')) for res in image_responses]
        blobs = [res.blob for res in image_responses]
        
        return (responses, blobs)
    
    async def __gen_voice_function_call__(self, args: GenerateVoiceParams, chat_id: int):
        logging.debug(f"Generate voice query: {args.text}")
        file_name = f"voice_{chat_id}_{int(time.time())}.wav"
        voice_response = await self.__voice.text_to_wave(args.text)

        return (InputMediaAudio(media=URLInputFile(voice_response.url, filename=file_name)), voice_response.blob)

    def __build_func_response(
        self,
        func_call: Union[DuckduckgoSearchFunctionCall, TavilySearchFunctionCall],
        result: Union[DuckduckgoSearchResults, TavilySearchResults]
    ):
        return types.FunctionResponse(name=func_call.name, id=func_call.id, response=result.model_dump())
    
    async def handle_event(
        self,
        event: ModelEventType,
        session: chats.AsyncChat,
        messages: list[types.PartUnionDict],
        chat_id: int
    ) -> AsyncGenerator[OutputEventType, None]:
        if isinstance(event, str):
            yield event
        elif isinstance(event, GenerateImageFunctionCall):
            image_responses, image_blobs = await self.__gen_image_function_call__(event.args)
            parts = [
                types.Part(inline_data=blob) for blob in image_blobs
            ]
            self.__gemini.function_call_replace(parts, event, session)
            
            yield image_responses
        elif isinstance(event, GenerateVoiceFunctionCall):
            voice_response, voice_blob = await self.__gen_voice_function_call__(event.args, chat_id)
            parts = [
                types.Part(inline_data=voice_blob)
            ]
            self.__gemini.function_call_replace(parts, event, session)
            
            yield voice_response
        elif isinstance(event, TavilySearchFunctionCall):
            search_result = await self.__tavily_search_function_call__(event.args)
            func_response = self.__build_func_response(event, search_result)
            response_stream = self.process_response(session, messages, chat_id, function_response=func_response)

            async for res in response_stream:
                yield res

    async def process_response(
        self,
        session: chats.AsyncChat,
        messages: list[types.PartUnionDict],
        chat_id: int,
        function_response: types.FunctionResponse | None = None
    ) -> AsyncGenerator[OutputEventType, None]:
        response_stream = self.__gemini.gen_response_stream(prompts=messages, chat=session, function_response=function_response)

        async for event in response_stream:
            if event is None:
                continue
            
            async for res in self.handle_event(event, session, messages, chat_id):
                yield res
