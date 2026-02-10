# services/trace_parser.py
def _slate_text(payload: dict) -> str | None:
    slate = payload.get("slate") or {}
    content = slate.get("content") or []
    parts = [c.get("text") for b in content for c in (b.get("children") or []) if c.get("text")]
    return "\n".join(parts).strip() or None

def _message_text(payload: dict) -> str | None:
    return payload.get("message")

def extract_text(payload: dict) -> str | None:
    return _slate_text(payload) or _message_text(payload)

def extract_buttons(item: dict) -> list:
    if item.get("type") != "choice":
        return []
    return (item.get("payload") or {}).get("buttons") or []

def extract_voice(payload: dict) -> str | None:
    return payload.get("voice")

def parse_traces(traces: list) -> tuple[list[str], list, str | None]:
    msgs, choices, audio = [], [], None
    for item in traces:
        payload = item.get("payload") or {}
        text = extract_text(payload)
        if text:
            msgs.append(text)
        choices.extend(extract_buttons(item))
        audio = audio or extract_voice(payload)
    return msgs, choices, audio
