from typing import Iterable, Union
from google.generativeai.generative_models import content_types, ChatSession

from chat.service import ChatService

class Chat():
    __session: ChatSession
    __service: ChatService

    def __init__(self, service: ChatService):
        self.__session = service.create_chat_session()
        self.__service = service

    def send_message_async(self, messages: Union[Iterable[content_types.PartType], str]):
        return self.__service.gen_chat_response_stream(chat=self.__session, prompts=messages)

class ChatRepo():
    __service: ChatService
    __chats: dict[int, Chat]

    def __init__(self, service: ChatService) -> None:
        self.__service = service
        self.__chats = {}

    def get_chat_session(self, chat_id: int) -> Chat:
        if chat_id not in self.__chats.keys():
            self.__chats[chat_id] = Chat(self.__service)
        return self.__chats[chat_id]
    