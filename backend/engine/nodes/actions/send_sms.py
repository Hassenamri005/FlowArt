from typing import Any, Dict


def action_send_sms(
    state: Dict[str, Any], config: Dict[str, Any], node_id: str
) -> Dict[str, Any]:
    to = config.get("to")
    content = config.get("content")
    if not to:
        raise ValueError("send_sms: 'to' is required")
    if content is None:
        raise ValueError("send_sms: 'content' is required")

    print("[ SEND_SMS ] Sending SMS.")

    return {
        "sent": True,
        "to": to,
        "content": content,
        "port": "success",
    }
