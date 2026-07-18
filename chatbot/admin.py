from django import forms
from django.contrib import admin
from django.http import HttpRequest

from chatbot.models import ChatbotPrompt, ChatMessage


class ChatbotPromptForm(forms.ModelForm):
    class Meta:
        model = ChatbotPrompt
        fields = ['content']
        widgets = {'content': forms.Textarea(attrs={'rows': 25, 'style': 'width: 90%'})}


@admin.register(ChatbotPrompt)
class ChatbotPromptAdmin(admin.ModelAdmin):
    form = ChatbotPromptForm
    list_display = ['__str__', 'updated_at']

    def has_add_permission(self, request: HttpRequest) -> bool:
        return not ChatbotPrompt.objects.exists()

    def has_delete_permission(self, request: HttpRequest, obj: ChatbotPrompt | None = None) -> bool:
        return False


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'role', 'content', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['session_key', 'content']
    readonly_fields = ['session_key', 'role', 'content', 'created_at']
