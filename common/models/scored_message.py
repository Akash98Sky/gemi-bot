from prisma.models import Message

class ScoredMessage:
    def __init__(self, message: Message, score: float):
        self.message = message
        self.score = score