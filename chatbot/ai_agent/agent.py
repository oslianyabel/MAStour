"""PydanticAI agent for the MAS tour website chatbot.

Follows the cheese_bot reference implementation: lazy singleton, tools
registered explicitly and dynamic instructions for the current date.
The system prompt lives in the ChatbotPrompt model (editable from the admin);
prompt.txt is only the seed/fallback. The singleton is rebuilt automatically
whenever the stored prompt changes.
"""

import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from pydantic_ai import Agent, Tool
from pydantic_ai.settings import ModelSettings

from chatbot.ai_agent.tools import (
    find_reservations_by_phone,
    get_contact_channels,
    get_departure_details,
    get_excursion_details,
    get_upcoming_departures,
    list_categories,
    list_destinations,
    list_excursions,
)
from chatbot.models import ChatbotPrompt

logger = logging.getLogger(__name__)

PROMPT_FILE: Path = Path(__file__).resolve().parent / 'prompt.txt'
AGENT_MODEL: str = 'google:gemini-flash-latest'

AGENT_TOOLS = [
    Tool(list_categories, docstring_format='google'),
    Tool(list_destinations, docstring_format='google'),
    Tool(list_excursions, docstring_format='google'),
    Tool(get_excursion_details, docstring_format='google'),
    Tool(get_upcoming_departures, docstring_format='google'),
    Tool(get_departure_details, docstring_format='google'),
    Tool(find_reservations_by_phone, docstring_format='google'),
    Tool(get_contact_channels, docstring_format='google'),
]

_tour_agent: Agent | None = None
_prompt_updated_at: datetime | None = None


def _load_system_prompt() -> tuple[str, datetime | None]:
    """Return the system prompt from the DB, falling back to prompt.txt."""
    prompt = ChatbotPrompt.objects.order_by('-updated_at').first()
    if prompt is None:
        return PROMPT_FILE.read_text(encoding='utf-8'), None
    return prompt.content, prompt.updated_at


def get_tour_agent() -> Agent:
    """Return the singleton tour agent, rebuilding it if the stored prompt changed."""
    global _tour_agent, _prompt_updated_at  # noqa: PLW0603
    system_prompt, updated_at = _load_system_prompt()
    if _tour_agent is None or updated_at != _prompt_updated_at:
        _prompt_updated_at = updated_at
        _tour_agent = Agent(
            model=AGENT_MODEL,
            system_prompt=system_prompt,
            tools=AGENT_TOOLS,
            model_settings=ModelSettings(temperature=0),
        )

        @_tour_agent.instructions
        def current_datetime_prompt() -> str:
            now = datetime.now(tz=ZoneInfo('America/Havana'))
            return (
                f'Fecha y hora actual: {now.strftime("%A %d %B %Y, %H:%M")} '
                f'(zona horaria de Cuba, {now.strftime("%Z %z")}). '
                'Úsala para resolver expresiones como mañana, este fin de semana o la próxima semana.'
            )

        logger.info('Tour agent initialized with %d tools', len(AGENT_TOOLS))
    return _tour_agent
