# Adding New Nodes

This guide explains how to add a new node type to the engine and expose it to the UI.

## 1) Define the node handler

Create a Python function that implements your node's behavior. Handlers follow the signature:

```python
Handler = Callable[[Dict[str, Any], Dict[str, Any], str], Dict[str, Any]]
```

- `state`: runtime dictionary holding `payload`, `nodes` outputs, and more.
- `config`: the node's resolved config. Template placeholders like `{{payload.message}}` will be replaced before execution.
- `node_id`: the id of the node being executed.

Your handler should return a dictionary of outputs. Include an optional `port` field to control routing to edges annotated with `source_port`.

Example: `engine/nodes/actions/send_sms.py`

```python
from typing import Any, Dict

def action_send_sms(state: Dict[str, Any], config: Dict[str, Any], node_id: str) -> Dict[str, Any]:
    to = str(config.get("to"))
    content = str(config.get("content"))
    # ... send SMS or mock it ...
    return {
        "sent": True,
        "to": to,
        "content": content,
        "sid": "SM_mock_123",
        "port": "success",  # enable routing to edges whose source_port == "success"
    }
```

## 2) Register the handler

Add your node type to the `NODE_HANDLERS` mapping in `engine/nodes/__init__.py`:

```python
NODE_HANDLERS = {
    "trigger.webhook": trigger_webhook,
    "action.chat": action_chat,
    "action.send_sms": action_send_sms,
    "action.send_email": action_send_email,
    "logic.condition": logic_condition,
    "logic.end": logic_end,
    # Add your node here
    "action.my_node": action_my_node,
}
```

## 3) Extend the nodes catalog (YAML)

Add a new entry to `engine/nodes_config.yml` so the UI can render the node in the palette and know its config schema and ports:

```yaml
- type: action.my_node
  label: Action - My Node
  category: action
  description: Brief description of what your node does.
  ports:
    - success
    - error
  config_schema:
    my_param:
      type: string
      required: true
      default: ""
      description: Explain what this parameter is for.
  outputs:
    something: string
```

- `ports`: list of named source ports you plan to return via `outputs.port` from the handler. These appear as connection points in the UI.
- `config_schema`: defines the editable fields shown in the UI.
- `outputs`: documents which keys might be returned by your handler. This is informational and helps when building flows.

## 4) Template resolution

Any `string` values in a node config support template placeholders like `{{payload.message}}`, `{{nodes.chat_1.generated_message}}`, etc. The engine resolves them before calling your handler. See `engine/template_resolver.py` for details.

## 5) Testing your node

- Save your updated YAML and Python code.
- Restart the API server.
- Open the UI and drag your new node from the palette into the canvas.
- Connect it to other nodes and click "Run".

## 6) Returning errors

You can raise exceptions or return `{ "port": "error", "error": "..." }` from your handler. If an exception is thrown, the engine records it and stops execution. If you return an `error` port, the engine will route along any edge connected with `source_port: error`.

## 7) Best practices

- Keep handlers side-effect-free by default; if you must call external APIs, handle timeouts and errors gracefully.
- Return structured outputs to make it easy for downstream nodes to template from.
- Log enough details in outputs for troubleshooting (without leaking secrets).
