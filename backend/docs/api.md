# API Reference

Base URL: `http://localhost:8001`

## Health

- Method: GET
- Path: `/`
- Response:

```json
{"status":"ok","docs":"/docs"}
```

## List nodes catalog

- Method: GET
- Path: `/nodes`
- Response:

```json
{
  "nodes": [
    {
      "type": "trigger.webhook",
      "label": "Trigger - Webhook",
      "category": "trigger",
      "description": "Receives a webhook payload...",
      "ports": ["default"],
      "config_schema": {"schedule_at": {"type":"string"}},
      "outputs": {"payload": "object", "scheduled_at": "string"}
    },
    ...
  ]
}
```

## Execute inline workflow

- Method: POST
- Path: `/run-flow`
- Body:

```json
{
  "workflow": { "nodes": [], "edges": [], "entry": "..." },
  "payload": { "message": "hi" },
  "initial_state": {"key": "value"}
}
```
- Response:

```json
{
  "nodes": {"chat_1": {"generated_response": "..."}},
  "trace": ["trigger_1","chat_1","end_1"],
  "logs": [
    {
      "id": "chat_1",
      "type": "action.chat",
      "status": "success",
      "elapsed_ms": 42,
      "port": "success",
      "outputs": {"generated_response": "..."}
    }
  ]
}
```

## Execute saved workflow by id (payload)

- Method: POST
- Path: `/run-flow/db`
- Body:

```json
{
  "payload": {
    "user_id": "u123",
    "flow_id": 42,
    "message": "Hello!"
  },
  "initial_state": {}
}
```

Notes:

- The handler validates that the flow owner (from DB) matches `payload.user_id`.
- The entire `payload` is forwarded as `state.payload` for templates.

## List example flows (file-based)

- Method: GET
- Path: `/flows`
- Response:

```json
{"flows":["new_flow.json","flow_basic.json"]}
```

## Get flow by name (file-based)

- Method: GET
- Path: `/flows/{name}`
- Response:

```json
{
  "name": "my_flow.json",
  "workflow": { ... }
}
```

## Save flow by name (file + DB)

- Method: POST
- Path: `/flows/{name}`
- Query params:
  - `overwrite`: boolean (default true)
  - `user_id`: optional; if omitted uses `DEFAULT_USER_ID` env var or `default`
- Body:

```json
{
  "workflow": { "nodes": [], "edges": [], "entry": "..." }
}
```
- Response:

```json
{
  "name": "my_flow.json",
  "saved": true,
  "db_id": 42
}
```

## Error format

Errors return HTTP 4xx with a JSON body:

```json
{"detail":"message"}
```

## OpenAPI docs

FastAPI interactive docs are available at:

- Swagger UI: [http://localhost:8001/docs](http://localhost:8001/docs)
- ReDoc: [http://localhost:8001/redoc](http://localhost:8001/redoc)
