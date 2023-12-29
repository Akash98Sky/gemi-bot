from enum import Enum


class BotEventMethods(Enum):
    webhook = 1
    polling = 2
    unknown = 3