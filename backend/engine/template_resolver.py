from __future__ import annotations

import re
from typing import Any, Dict

TOKEN_RE = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")


def _get_by_path(root: Any, path: str) -> Any:
    """Resolve dotted path like 'nodes.chat_1.generated_response.subject'.
    Supports integer indices for lists like 'items.0.id'.
    Returns None if not found.
    """
    cur = root
    for part in path.split("."):
        if isinstance(cur, list):
            try:
                idx = int(part)
            except ValueError:
                return None
            if idx < 0 or idx >= len(cur):
                return None
            cur = cur[idx]
        elif isinstance(cur, dict):
            if part not in cur:
                return None
            cur = cur[part]
        else:
            return None
    return cur


def _replace_in_string(s: str, state: Dict[str, Any]) -> str:
    def repl(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        val = _get_by_path(state, key)
        return "" if val is None else str(val)

    return TOKEN_RE.sub(repl, s)


def resolve_templates(obj: Any, state: Dict[str, Any]) -> Any:
    """Recursively resolve {{ ... }} placeholders within a JSON-like config object.

    Example tokens:
      - {{payload.message}}
      - {{nodes.chat_1.generated_response.content}}
    """
    if isinstance(obj, str):
        return _replace_in_string(obj, state)
    if isinstance(obj, list):
        return [resolve_templates(v, state) for v in obj]
    if isinstance(obj, dict):
        return {k: resolve_templates(v, state) for k, v in obj.items()}
    return obj
