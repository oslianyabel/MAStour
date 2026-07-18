"""Seed the editable chatbot prompt with the default bundled in prompt.txt."""

from pathlib import Path

from django.db import migrations

PROMPT_FILE = Path(__file__).resolve().parent.parent / 'ai_agent' / 'prompt.txt'


def seed_prompt(apps, schema_editor):
    ChatbotPrompt = apps.get_model('chatbot', 'ChatbotPrompt')
    if not ChatbotPrompt.objects.exists():
        ChatbotPrompt.objects.create(content=PROMPT_FILE.read_text(encoding='utf-8'))


def unseed_prompt(apps, schema_editor):
    apps.get_model('chatbot', 'ChatbotPrompt').objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ('chatbot', '0002_chatbotprompt'),
    ]

    operations = [
        migrations.RunPython(seed_prompt, unseed_prompt),
    ]
