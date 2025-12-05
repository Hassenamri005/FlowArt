# Documentation Index

Welcome to the Mini n8n-like Workflow Engine docs.

- Getting Started: see the Quickstart in `README.md`
- API Reference: [api.md](api.md)
- Adding New Nodes: [adding-nodes.md](adding-nodes.md)

## Overview

This project provides a minimal workflow engine with:

- A React-based UI for composing flows
- A FastAPI backend to execute flows
- A small set of built-in nodes (trigger, chat, SMS, email, condition, end)
- A template resolver to reference previous node outputs (e.g. `{{nodes.chat_1.generated_message}}`) and payload fields (e.g. `{{payload.message}}`)
- Optional SQLite persistence for flows

## Architecture

- `main.py` exposes the HTTP API (`/nodes`, `/run-flow`, `/run-flow/db`, and `/flows/*`).
- `engine/workflow_runner.py` executes flows by running each node handler and routing by `port`.
- `engine/template_resolver.py` resolves `{{ ... }}` templates within node configs against current state.
- `engine/nodes/__init__.py` registers handlers for each node type in `NODE_HANDLERS`.
- `engine/nodes_config.yml` provides the node metadata used by the UI and `/nodes`.
- `engine/db.py` contains SQLite helpers; DB is stored at `data/app.db`.

## Workflow JSON shape

A workflow includes nodes, edges, and an optional `entry` node id:

```json
{
  "nodes": [
    {"id": "trigger_1", "type": "trigger.webhook", "config": {}},
    {"id": "chat_1", "type": "action.chat", "config": {"system_prompt": "..."}},
    {"id": "end_1", "type": "logic.end"}
  ],
  "edges": [
    {"source": "trigger_1", "target": "chat_1"},
    {"source": "chat_1", "source_port": "success", "target": "end_1"}
  ],
  "entry": "trigger_1"
}
```

## Runtime state

- `state.payload`: the incoming webhook payload
- `state.nodes[<node_id>]`: outputs of each executed node
- `state.trace`: sequence of visited node ids
- `state.logs`: detailed entries for each node (`id`, `type`, `status`, `elapsed_ms`, `port`, `error`, and `outputs`)

See [api.md](api.md) for request/response details.
