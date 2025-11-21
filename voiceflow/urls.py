from django.urls import path
from .views import VoiceflowAPIView

urlpatterns = [
    path('voiceflow_chat_bot/', VoiceflowAPIView.as_view(), name='voiceflow-api'),
]