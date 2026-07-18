import json
import logging

from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from pydantic_ai.exceptions import AgentRunError, UserError

from chatbot.ai_agent.agent import get_tour_agent
from chatbot.ai_agent.chat_history import load_history, save_assistant_message, save_user_message
from chatbot.models import ChatMessage

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH: int = 1000
FALLBACK_REPLY: str = (
    'Lo siento, ahora mismo no puedo responder 😔. Inténtalo de nuevo en unos minutos '
    'o contáctanos por nuestras redes sociales.'
)


def _session_key(request: HttpRequest) -> str:
    if not request.session.session_key:
        request.session.save()
    return request.session.session_key


def _message_time(message: ChatMessage) -> str:
    return timezone.localtime(message.created_at).strftime('%I:%M %p').lstrip('0')


@require_http_methods(['GET', 'POST'])
def chat_messages(request: HttpRequest) -> JsonResponse:
    """GET: chat history of the current session. POST: send a message and get the reply."""
    session_key = _session_key(request)

    if request.method == 'GET':
        history = ChatMessage.objects.filter(session_key=session_key)
        return JsonResponse(
            {
                'messages': [
                    {'role': message.role, 'content': message.content, 'time': _message_time(message)}
                    for message in history
                ]
            }
        )

    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido.'}, status=400)

    text = str(payload.get('message', '')).strip()
    if not text:
        return JsonResponse({'error': 'El mensaje no puede estar vacío.'}, status=400)
    text = text[:MAX_MESSAGE_LENGTH]

    history = load_history(session_key)
    save_user_message(session_key, text)
    try:
        result = get_tour_agent().run_sync(text, message_history=history)
        reply = result.output
    except (AgentRunError, UserError):
        logger.exception('[chat_messages] agent run failed for session %s', session_key)
        reply = FALLBACK_REPLY

    assistant_message = save_assistant_message(session_key, reply)
    return JsonResponse({'reply': reply, 'time': _message_time(assistant_message)})
