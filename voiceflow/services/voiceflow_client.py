"""
Voiceflow API client.
All requests go through the Agent flow.
"""
import logging
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://general-runtime.voiceflow.com"
TIMEOUT = 45


def _headers(api_key: str, version_id: str = None) -> dict:
    """Build request headers with optional version ID."""
    h = {"Authorization": api_key, "Content-Type": "application/json"}
    return {**h, "versionID": version_id} if version_id else h


def _post(url: str, payload: dict, headers: dict) -> list:
    """Execute POST request and return JSON response."""
    response = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def vf_reset(api_key: str, user_id: str) -> bool:
    """Reset user conversation state. Returns True on success."""
    try:
        requests.delete(f"{BASE_URL}/state/user/{user_id}", headers=_headers(api_key), timeout=TIMEOUT)
        return True
    except requests.RequestException as e:
        logger.warning(f"Reset failed for user {user_id}: {e}")
        return False


def vf_interact(api_key: str, version_id: str, user_id: str, payload: dict) -> list:
    """Send interaction to Voiceflow Agent and return trace list."""
    url = f"{BASE_URL}/state/user/{user_id}/interact"
    return _post(url, payload, _headers(api_key, version_id))


def vf_set_variables(api_key: str, version_id: str, user_id: str, variables: dict) -> dict:
    """Set session variables for the user."""
    url = f"{BASE_URL}/state/user/{user_id}/variables"
    response = requests.patch(url, json=variables, headers=_headers(api_key, version_id), timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()