from __future__ import annotations

from typing import Any, Callable, Dict

from engine.nodes.actions.chat import action_chat
from engine.nodes.actions.send_email import action_send_email
from engine.nodes.actions.send_sms import action_send_sms
from engine.nodes.condition import logic_condition
from engine.nodes.end import logic_end
from engine.nodes.trigger import trigger_webhook

Handler = Callable[[Dict[str, Any], Dict[str, Any], str], Dict[str, Any]]

NODE_HANDLERS: Dict[str, Handler] = {
    "trigger.webhook": trigger_webhook,
    "action.chat": action_chat,
    "action.send_sms": action_send_sms,
    "action.send_email": action_send_email,
    "logic.condition": logic_condition,
    "logic.end": logic_end,
}
