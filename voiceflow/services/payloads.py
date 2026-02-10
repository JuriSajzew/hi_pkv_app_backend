"""
Voiceflow request payload builders.
Transforms frontend data into Voiceflow API format.
"""


def interact_payload(data: dict) -> dict:
    """
    Build interaction payload from request data.
    
    Supports: launch, text input, choice selection.
    """
    req_type = data.get("type", "text")
    
    if req_type == "launch":
        return {"request": {"type": "launch"}}
    if req_type == "text":
        return {"request": {"type": "text", "payload": data.get("message", "")}}
    if req_type == "choice":
        return {"request": data.get("request", {})}
    if "request" in data:
        return {"request": data["request"]}
    return {"request": {"type": "text", "payload": data.get("message", "")}}