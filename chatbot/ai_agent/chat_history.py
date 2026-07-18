"""Chat history persistence and conversion to the PydanticAI message format."""

import logging

from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart

from chatbot.models import ChatMessage

logger = logging.getLogger(__name__)

HISTORY_LIMIT: int = 40


def load_history(session_key: str) -> list[ModelMessage]:
    """Rebuild the PydanticAI message list from the last stored messages of a session."""
    rows = ChatMessage.objects.filter(session_key=session_key).order_by('-created_at')[:HISTORY_LIMIT]
    messages: list[ModelMessage] = []
    for row in reversed(rows):
        if row.role == ChatMessage.Role.USER:
            messages.append(ModelRequest(parts=[UserPromptPart(content=row.content)]))
        elif row.role == ChatMessage.Role.ASSISTANT:
            messages.append(ModelResponse(parts=[TextPart(content=row.content)]))
    return messages


def save_user_message(session_key: str, text: str) -> ChatMessage:
    """Persist an incoming visitor message."""
    return ChatMessage.objects.create(session_key=session_key, role=ChatMessage.Role.USER, content=text)


def save_assistant_message(session_key: str, text: str) -> ChatMessage:
    """Persist an outgoing assistant message."""
    return ChatMessage.objects.create(session_key=session_key, role=ChatMessage.Role.ASSISTANT, content=text)
