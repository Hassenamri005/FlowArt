from __future__ import annotations

import copy
import datetime
import time
from typing import Any, Dict, List, Optional

from .template_resolver import resolve_templates
from .nodes import NODE_HANDLERS


class WorkflowError(Exception):
    pass


def _index_nodes(nodes: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    by_id = {}
    for n in nodes:
        nid = n.get("id")
        if not nid:
            raise WorkflowError("Every node must have an 'id'")
        if nid in by_id:
            raise WorkflowError(f"Duplicate node id: {nid}")
        by_id[nid] = n
    return by_id


def _incoming_counts(
    nodes: Dict[str, Dict[str, Any]], edges: List[Dict[str, Any]]
) -> Dict[str, int]:
    counts = {nid: 0 for nid in nodes.keys()}
    for e in edges:
        t = e.get("target")
        if t not in counts:
            raise WorkflowError(f"Edge target not found: {t}")
        counts[t] += 1
    return counts


def _find_entry_node(
    workflow: Dict[str, Any], nodes_by_id: Dict[str, Dict[str, Any]]
) -> str:
    explicit = workflow.get("entry")
    if explicit:
        if explicit not in nodes_by_id:
            raise WorkflowError(f"Entry node '{explicit}' not found")
        return explicit

    edges: List[Dict[str, Any]] = workflow.get("edges", [])
    incoming = _incoming_counts(nodes_by_id, edges)
    # Prefer a trigger node with in-degree 0
    zero_in = [nid for nid, cnt in incoming.items() if cnt == 0]
    trigger_zero_in = [
        nid
        for nid in zero_in
        if str(nodes_by_id[nid].get("type", "")).startswith("trigger.")
    ]
    if trigger_zero_in:
        return trigger_zero_in[0]
    # Any zero in-degree node
    if zero_in:
        return zero_in[0]
    # Fallback: first trigger
    for nid, n in nodes_by_id.items():
        if str(n.get("type", "")).startswith("trigger."):
            return nid
    # Last resort: first node
    return next(iter(nodes_by_id.keys()))


def _choose_next(
    edges: List[Dict[str, Any]], current_id: str, port: Optional[str] = None
) -> Optional[str]:
    """Choose the next node, considering optional source_port routing."""
    outgoing = [e for e in edges if e.get("source") == current_id]
    if not outgoing:
        return None
    if port is not None:
        for e in outgoing:
            if e.get("source_port") == port:
                return e.get("target")
    # fallback: an edge without explicit source_port, else first
    for e in outgoing:
        if not e.get("source_port"):
            return e.get("target")
    return outgoing[0].get("target")


def run_workflow(
    workflow: Dict[str, Any],
    initial_state: Optional[Dict[str, Any]] = None,
    webhook_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute a workflow defined by nodes and edges.

    Workflow JSON structure:
    {
      "nodes": [
        {"id": "trigger_1", "type": "trigger.webhook", "config": {...}},
        {"id": "chat_1", "type": "action.chat", "config": {...}},
        {"id": "cond_1", "type": "logic.condition", "config": {...}},
        {"id": "end_1", "type": "logic.end"}
      ],
      "edges": [
        {"source": "trigger_1", "target": "chat_1"},
        {"source": "chat_1", "source_port": "success", "target": "cond_1"},
        {"source": "cond_1", "source_port": "true", "target": "end_1"},
        {"source": "cond_1", "source_port": "false", "target": "end_2"}
      ],
      "entry": "trigger_1"  # optional
    }
    """
    nodes: List[Dict[str, Any]] = workflow.get("nodes", [])
    edges: List[Dict[str, Any]] = workflow.get("edges", [])

    if not nodes:
        raise WorkflowError("Workflow has no nodes")

    nodes_by_id = _index_nodes(nodes)
    current_id = _find_entry_node(workflow, nodes_by_id)

    state: Dict[str, Any] = {
        "nodes": {},  # node_id -> outputs
        "payload": webhook_payload or {},
    }
    if initial_state:
        # copy to avoid caller mutation
        state.update(copy.deepcopy(initial_state))

    trace: List[str] = []
    logs: List[Dict[str, Any]] = []

    while current_id:
        trace.append(current_id)
        node = nodes_by_id[current_id]
        node_type = node.get("type")
        config = node.get("config", {})

        # Resolve templates in config before execution
        resolved_config = resolve_templates(config, state)

        handler = NODE_HANDLERS.get(str(node_type))
        if not handler:
            raise WorkflowError(f"No handler for node type: {node_type}")

        started_at = datetime.datetime.utcnow().isoformat() + "Z"
        t0 = time.perf_counter()
        status = "success"
        err_msg: Optional[str] = None
        try:
            outputs = (
                handler(state=state, config=resolved_config, node_id=current_id) or {}
            )
        except Exception as e:
            status = "error"
            err_msg = str(e)
            outputs = {"error": err_msg}

        # Store outputs for downstream referencing
        state["nodes"][current_id] = outputs

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        finished_at = datetime.datetime.utcnow().isoformat() + "Z"
        logs.append(
            {
                "id": current_id,
                "type": node_type,
                "status": status,
                "started_at": started_at,
                "finished_at": finished_at,
                "elapsed_ms": elapsed_ms,
                "port": (outputs.get("port") if isinstance(outputs, dict) else None),
                "error": err_msg,
                "outputs": outputs,
            }
        )

        # Determine next node by optional "next" or by edges (respect port)
        next_id: Optional[str] = None
        if isinstance(outputs, dict):
            next_id = outputs.get("next")
        if not next_id:
            port = outputs.get("port") if isinstance(outputs, dict) else None
            next_id = _choose_next(edges, current_id, port)

        if status == "error" or not next_id or node_type == "logic.end":
            break
        current_id = next_id

    state["trace"] = trace
    state["logs"] = logs
    return state
