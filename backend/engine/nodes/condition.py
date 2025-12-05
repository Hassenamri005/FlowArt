import re
from typing import Any, Dict, Optional


def _as_number(s: Any) -> Optional[float]:
    try:
        if isinstance(s, (int, float)):
            return float(s)
        if isinstance(s, str) and s.strip() != "":
            return float(s)
    except Exception:
        return None
    return None


def logic_condition(
    state: Dict[str, Any], config: Dict[str, Any], node_id: str
) -> Dict[str, Any]:
    """Evaluate a simple condition.

    Config:
      - left: any
      - op: one of ==, !=, >, >=, <, <=, contains, in, regex
      - right: any (pattern string for regex)
    """
    left = config.get("left")
    op = (config.get("op") or "").strip()
    right = config.get("right")

    result = False

    # Try numeric comparisons when both sides are numbers
    lnum = _as_number(left)
    rnum = _as_number(right)

    try:
        if op in ("==", "eq"):
            result = left == right
        elif op in ("!=", "neq"):
            result = left != right
        elif op == ">":
            if lnum is not None and rnum is not None:
                result = lnum > rnum
            elif isinstance(left, str) and isinstance(right, str):
                result = left > right
        elif op == ">=":
            if lnum is not None and rnum is not None:
                result = lnum >= rnum
            elif isinstance(left, str) and isinstance(right, str):
                result = left >= right
        elif op == "<":
            if lnum is not None and rnum is not None:
                result = lnum < rnum
            elif isinstance(left, str) and isinstance(right, str):
                result = left < right
        elif op == "<=":
            if lnum is not None and rnum is not None:
                result = lnum <= rnum
            elif isinstance(left, str) and isinstance(right, str):
                result = left <= right
        elif op == "contains":
            if isinstance(left, (list, str)):
                result = right in left
        elif op == "in":
            if isinstance(right, (list, str)):
                result = left in right
        elif op == "regex":
            if isinstance(left, str) and isinstance(right, str):
                result = re.search(right, left) is not None
    except Exception:
        result = False
    port = "true" if result else "false"
    print("[ CONDITION ] Condition result:", result, "-> port:", port)
    return {
        "result": result,
        "port": port,
    }
