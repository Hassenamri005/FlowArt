import json
import os
from typing import Any, Dict, Optional
# Avoid importing AzureOpenAI at module import time to prevent errors when not configured.


def action_chat(
    state: Dict[str, Any], config: Dict[str, Any], node_id: str
) -> Dict[str, Any]:
    """Call Azure OpenAI Chat if configured, otherwise mock a response.

    Config expects:
      - system_prompt: str
    """
    sys_prompt = config.get("system_prompt") or "You are a helpful assistant"

    def _try_parse_json_from_text(text: Any) -> Any:
        """Best-effort JSON extraction from model output.
        - If text starts with { or [, parse directly
        - Else, look for ```json ... ``` fenced block and parse inner
        - Else, return original text
        """
        if not isinstance(text, str):
            return text
        s = text.strip()
        if s.startswith("{") or s.startswith("["):
            try:
                return json.loads(s)
            except Exception:
                pass
        try:
            import re as _re

            for m in _re.finditer(
                r"```(?:json)?\s*([\s\S]*?)\s*```", text, _re.IGNORECASE
            ):
                candidate = m.group(1).strip()
                try:
                    return json.loads(candidate)
                except Exception:
                    continue
        except Exception:
            pass
        return text

    def _extract_message(obj: Any) -> Optional[str]:
        if isinstance(obj, dict):
            for k in ("message", "content", "text"):
                v = obj.get(k)
                if isinstance(v, str):
                    return v
        return None

    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_ID")

    text: Any = ""

    try:
        from openai import AzureOpenAI  # local import to avoid import-time failures

        client = AzureOpenAI(
            api_key=api_key, api_version=api_version, azure_endpoint=endpoint
        )
        resp = client.chat.completions.create(
            model=deployment,
            messages=[{"role": "system", "content": sys_prompt}],
            temperature=0.1,
        )
        text = resp.choices[0].message.content if getattr(resp, "choices", None) else ""
    except Exception as e:
        print("[ CHAT ] Azure OpenAI call failed, using mock:", e)
        name = (state.get("payload", {}) or {}).get("customer_name") or "there"
        text = json.dumps(
            {
                "message": f"Welcome, {name}! We're so glad to have you here. If you need anything, just let us know!"
            }
        )

    print("[ CHAT ] Generating response.")

    parsed: Any = _try_parse_json_from_text(text)
    message_str: Optional[str] = _extract_message(parsed)
    if not message_str and isinstance(text, str):
        message_str = text

    return {
        "generated_response": parsed,
        "generated_message": message_str,
        "raw_text": text if isinstance(text, str) else json.dumps(text),
        "port": "success",
    }
