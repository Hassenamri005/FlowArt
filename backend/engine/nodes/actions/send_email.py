from typing import Any, Dict


def action_send_email(
    state: Dict[str, Any], config: Dict[str, Any], node_id: str
) -> Dict[str, Any]:
    to = config.get("to")
    subject = config.get("subject")
    content = config.get("content")
    if not to:
        raise ValueError("send_email: 'to' is required")
    if subject is None:
        raise ValueError("send_email: 'subject' is required")
    if content is None:
        raise ValueError("send_email: 'content' is required")
    print("[ SEND_EMAIL ] Sending email.")

    # Stub sending; integrate your SMTP or external provider here.
    message_id = "mock-message-id"
    return {
        "sent": True,
        "to": to,
        "subject": subject,
        "content": content,
        "message_id": message_id,
        "port": "success",
    }
