from typing import Any, Dict


def logic_end(
    state: Dict[str, Any], config: Dict[str, Any], node_id: str
) -> Dict[str, Any]:
    # No outputs necessary; runner will stop by type check
    return {}
