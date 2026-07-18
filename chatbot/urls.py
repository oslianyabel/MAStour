from django.urls import path

from chatbot import views

app_name = 'chatbot'

urlpatterns = [
    path('mensajes/', views.chat_messages, name='chat_messages'),
]
