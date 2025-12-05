from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from decouple import config
import requests
import pprint
import logging

# 🔑 Voiceflow-Konfiguration
VOICEFLOW_API_KEY = config("VOICEFLOW_API_KEY")
VOICEFLOW_VERSION_ID = "production"  # Production = veröffentlichte Version

logger = logging.getLogger(__name__)

class VoiceflowAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user_id = str(user.id)
        data = request.data

        message_type = data.get("type", "text")
        message_content = data.get("message", "")

        # 🧹 Optional: Session reset
        if data.get("reset"):
            delete_url = f"https://general-runtime.voiceflow.com/state/user/{user_id}"
            try:
                requests.delete(delete_url, headers={"Authorization": VOICEFLOW_API_KEY})
                logger.info(f"🧹 Voiceflow session reset for user {user_id}")
            except requests.RequestException as e:
                logger.error(f"⚠️ Voiceflow session reset failed: {e}")

        # 📨 API-konformer Payload (laut Voiceflow-Dokumentation)
        if message_type == "launch":
            payload = {"request": {"type": "launch"}}
        elif message_type == "text":
            payload = {"request": {"type": "text", "payload": message_content}}
        else:
            # z. B. bei Choices
            if "request" in data:
                payload = {"request": data["request"]}
            else:
                payload = {"request": data}

        # 🧾 Header vorbereiten
        headers = {
            "Authorization": VOICEFLOW_API_KEY,
            "versionID": VOICEFLOW_VERSION_ID,
            "Content-Type": "application/json",
        }

        url = f"https://general-runtime.voiceflow.com/state/user/{user_id}/interact"

        # 🔄 Anfrage an Voiceflow senden
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error("❌ Voiceflow API Error", exc_info=True)
            return Response(
                {"error": f"Voiceflow request failed: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # 🔍 JSON prüfen
        try:
            traces = response.json()
        except Exception as e:
            logger.error("❌ Invalid JSON response from Voiceflow", exc_info=True)
            return Response(
                {"error": "Invalid response from Voiceflow."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        logger.debug(f"\n=== Voiceflow Raw Traces für User {user_id} ===")
        logger.debug(pprint.pformat(traces))
        logger.debug("=== Ende Raw Traces ===\n")

        # 💬 Traces verarbeiten
        messages_output = []
        choices_output = []
        audio_output = None

        for item in traces:
            item_type = item.get("type")
            payload_item = item.get("payload", {})

            # 🎙️ Textnachricht (Slate > Message)
            text_message = None

            if "slate" in payload_item and payload_item["slate"]:
                content = payload_item["slate"].get("content", [])
                full_text_parts = []

                for block in content:
                    children = block.get("children", [])
                    for child in children:
                    # nur text-Werte anhängen, egal ob fett/unterstrichen
                        text_value = child.get("text")
                        if text_value:
                            full_text_parts.append(text_value)

                # alles zu einem String verbinden
                full_text = "\n".join(full_text_parts).strip()
                if full_text:
                    text_message = full_text

            elif payload_item.get("message"):
                text_message = payload_item["message"]

            if text_message:
                messages_output.append(text_message)

            # 🎵 Audio (TTS-Output)
            if "voice" in payload_item:
                audio_output = payload_item["voice"]

            # 🟢 Choices / Buttons
            if item_type == "choice":
                buttons = payload_item.get("buttons", [])
                choices_output.extend(buttons)

        # ⚠️ Fallback – falls keine Traces kamen
        if not traces:
            logger.warning(f"⚠️ Keine Traces von Voiceflow für User {user_id}")
            messages_output.append(
                "Entschuldige, ich konnte gerade keine Antwort erhalten. Bitte versuche es erneut."
            )

        # 📤 Antwort ans Frontend
        return Response(
            {
                "raw_traces": traces,
                "messages": messages_output,
                "choices": choices_output,
                "audio": audio_output,
            },
            status=status.HTTP_200_OK,
        )
