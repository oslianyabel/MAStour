from django.db import models


class ChatbotPrompt(models.Model):
    """System prompt of the assistant, editable from the admin panel.

    The agent reloads it automatically when it changes. If no row exists,
    the default prompt bundled in chatbot/ai_agent/prompt.txt is used.
    """

    content: models.TextField = models.TextField(
        'prompt del sistema',
        help_text='Instrucciones que definen la personalidad y las reglas del asistente. '
        'Los cambios se aplican de inmediato, sin reiniciar el servidor.',
    )
    updated_at: models.DateTimeField = models.DateTimeField('actualizado', auto_now=True)

    class Meta:
        verbose_name = 'prompt del chatbot'
        verbose_name_plural = 'prompt del chatbot'

    def __str__(self) -> str:
        return f'Prompt del chatbot (actualizado {self.updated_at:%d/%m/%Y %H:%M})'


class ChatMessage(models.Model):
    """A single chat message exchanged between a visitor and the assistant."""

    class Role(models.TextChoices):
        USER = 'user', 'Usuario'
        ASSISTANT = 'assistant', 'Asistente'

    session_key: models.CharField = models.CharField('sesión', max_length=40, db_index=True)
    role: models.CharField = models.CharField('rol', max_length=10, choices=Role.choices)
    content: models.TextField = models.TextField('contenido')
    created_at: models.DateTimeField = models.DateTimeField('creado', auto_now_add=True)

    class Meta:
        verbose_name = 'mensaje de chat'
        verbose_name_plural = 'mensajes de chat'
        ordering = ['created_at']

    def __str__(self) -> str:
        return f'[{self.role}] {self.content[:50]}'
