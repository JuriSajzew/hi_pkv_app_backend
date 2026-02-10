"""
Voiceflow API endpoint.
All requests go through the Agent flow with user-specific variables.
"""
import logging
from decouple import config
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from .services.voiceflow_client import vf_interact, vf_reset, vf_set_variables
from .services.kb_filters import build_variables
from .services.trace_parser import parse_traces
from .services.payloads import interact_payload

logger = logging.getLogger(__name__)
VF_API_KEY = config("VOICEFLOW_API_KEY")
VF_VERSION = config("VOICEFLOW_VERSION_ID", default="production")


def _flow_response(traces: list) -> Response:
    """Build API response from flow interaction traces."""
    msgs, choices, audio = parse_traces(traces)
    if not msgs:
        msgs = ["Entschuldige, ich konnte keine Antwort erhalten."]
    return Response({"messages": msgs, "choices": choices, "audio": audio})


class VoiceflowAPIView(APIView):
    """
    Main Voiceflow integration endpoint.
    
    All messages go through the Agent flow.
    User profile variables are set for KB filtering.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Handle all Voiceflow interactions."""
        user_id = str(request.user.id)
        data = request.data
        
        if data.get("reset"):
            vf_reset(VF_API_KEY, user_id)
        
        # Set user variables on launch or reset
        if data.get("type") == "launch" or data.get("reset"):
            self._set_user_variables(user_id, request.user)
        
        return self._handle_interaction(user_id, data)

    def _set_user_variables(self, user_id: str, user) -> None:
        """Set user profile variables in Voiceflow session."""
        try:
            variables = build_variables(user)
            vf_set_variables(VF_API_KEY, VF_VERSION, user_id, variables)
            logger.info(f"Set variables for user {user_id}: {variables}")
        except Exception as e:
            logger.warning(f"Failed to set variables: {e}")

    def _handle_interaction(self, user_id: str, data: dict) -> Response:
        """Process interaction through Voiceflow Agent."""
        try:
            payload = interact_payload(data)
            traces = vf_interact(VF_API_KEY, VF_VERSION, user_id, payload)
            return _flow_response(traces)
        except Exception as e:
            logger.exception("Interaction failed")
            return Response({"error": str(e)}, status=status.HTTP_502_BAD_GATEWAY)