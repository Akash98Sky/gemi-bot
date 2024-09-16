from aiogram.types import Message

class EmbeddedMessage:
    parent_msg_id: int | None

    def __init__(self, message: Message, embedding: list[float], parent_msg_id: int | None = None):
        self.message = message
        self.embedding = embedding
        self.parent_msg_id = parent_msg_id