from logging import Logger, getLogger
import uuid
from google.genai.client import AsyncClient, ApiClient
from google.genai.types import GenerateContentConfig, SafetySetting, Content, PartUnionDict
from google.genai.types import FunctionCall, FunctionResponse, Tool, Part
from google.genai.chats import AsyncChat
from pydantic import ValidationError


from chat.prompts.static import SYSTEM_INSTRUCTIONS
from chat.tools.generation import GenerateImageFunctionDeclaration, GenerateVoiceFunctionDeclaration, GenerateImageFunctionCall, GenerateVoiceFunctionCall
from chat.tools.search import TavilySearchFunctionDeclaration, TavilySearchFunctionCall

logging: Logger = getLogger(__name__)

class GeminiService(object):
    model = 'gemini-2.0-flash-exp'
    safety_settings: list[SafetySetting] = [
        SafetySetting(
            category='HARM_CATEGORY_HARASSMENT',
            threshold='BLOCK_NONE',
        ),
        SafetySetting(
            category='HARM_CATEGORY_HATE_SPEECH',
            threshold='BLOCK_NONE',
        ),
        SafetySetting(
            category='HARM_CATEGORY_SEXUALLY_EXPLICIT',
            threshold='BLOCK_ONLY_HIGH',
        ),
    ]
    gen_config = GenerateContentConfig(
        safety_settings=safety_settings,
        system_instruction=SYSTEM_INSTRUCTIONS,
        response_modalities=['TEXT'],
        temperature=0.7,
        tools=[
            Tool(
                function_declarations=[
                    GenerateImageFunctionDeclaration(),
                    GenerateVoiceFunctionDeclaration(),
                    TavilySearchFunctionDeclaration()
                ],
            ),
        ],
    )
    client: AsyncClient

    def __init__(self, api_key: str):
        api_client=ApiClient(
            api_key=api_key,
        )
        api_client._http_options.update({
            'api_version': 'v1alpha'
        })
        self.client = AsyncClient(api_client=api_client)

    def __parse_function_call__(self, function_call: FunctionCall):
        try:
            if function_call.id is None:
                # generate a new id if not provided
                function_call.id = uuid.uuid4().hex

            if function_call.name == GenerateVoiceFunctionCall().name:
                return GenerateVoiceFunctionCall.model_validate(function_call)
            elif function_call.name == GenerateImageFunctionCall().name:
                return GenerateImageFunctionCall.model_validate(function_call)
            elif function_call.name == TavilySearchFunctionCall().name:
                return TavilySearchFunctionCall.model_validate(function_call)
            else:
                raise ValueError(f'Unknown function call: {function_call.name}({function_call.args})')
        except ValidationError as e:
            logging.warning(f"Failed to parse function call: {e}")

    async def gen_response_stream(self, prompts: list[PartUnionDict], chat: AsyncChat, function_response: FunctionResponse | None = None):
        try:
            if function_response:
                prompts = [*prompts, Part(function_response=function_response)]
            response = await chat.send_message(prompts)
        
            if response.candidates and (content := response.candidates[0].content) is not None and content.parts:
                for part in content.parts:
                    if part.text:
                        yield part.text
                    elif part.function_call:
                        part.function_call = self.__parse_function_call__(part.function_call)
                        yield part.function_call

        except StopAsyncIteration:
            # Handle the StopAsyncIteration exception, raised by async generators, here
            pass

    def function_call_replace(self, result: list[Part], function_call: FunctionCall, chat: AsyncChat):
        history = chat._curated_history

        for content in history:
            if content.parts and content.parts[0].function_call:
                call = content.parts[0].function_call
                if call.name == function_call.name and call.id == function_call.id:
                    content.parts = result
                    break

    def create_chat_session(self, history: list[Content] = []):
        return self.client.chats.create(
            model=self.model,
            config=self.gen_config,
            history=history
        )

