from typing import Any, Dict


def trigger_webhook(
    state: Dict[str, Any], config: Dict[str, Any], node_id: str
) -> Dict[str, Any]:
    # Simply pass-through incoming payload; include optional schedule fields if given
    out = {
        "payload": state.get("payload", {}),
    }
    if "schedule_at" in config:
        out["scheduled_at"] = config.get("schedule_at")
    print("[ TRIGGER ] Triggered webhook.")
    return out
