# FlowArt

This is a minimal workflow engine inspired by n8n. It exposes:

- `GET /nodes` to list available node types and their config schema.
- `POST /run-flow` to execute a workflow JSON with an optional webhook payload and initial state.
- `POST /run-flow/db` to execute a saved workflow by `payload.user_id` and `payload.flow_id`.
- `GET /flows` to list flows in the `examples/` folder.
- `GET /flows/{name}` to load a saved flow JSON from `examples/`.
- `POST /flows/{name}` to save a flow JSON to `examples/` and also persist it to SQLite (returns `db_id`).

It supports the following nodes out-of-the-box:

- Trigger: `trigger.webhook`
- Chat: `action.chat` (Azure OpenAI; mocked if not configured)
- Send SMS: `action.send_sms` (mocked; integrate Twilio to enable real sending)
- Send Email: `action.send_email` (mocked; integrate SMTP/provider to enable real sending)
- Conditional: `logic.condition` (==, !=, >, >=, <, <=, contains, in, regex)
- End: `logic.end`

Configs support template placeholders like `{{payload.message}}` or `{{nodes.chat_1.generated_response}}` so downstream nodes can reference previous node outputs.

---

## Quickstart

1. Create and activate a virtual environment (optional but recommended)

```bash
python -m venv .venv
source .venv/bin/activate
```

1. Install dependencies

```bash
pip install -r requirements.txt
```

1. Run the API

```bash
ruff check . --fix

uvicorn main:app --reload --port 8001
```

1. Open in your browser

- Health: [http://localhost:8001/](http://localhost:8001/)
- Nodes: [http://localhost:8001/nodes](http://localhost:8001/nodes)

1. Execute an example workflow

- Example file: `examples/flow_basic.json`

```bash
curl -X POST http://localhost:8001/run-flow/db \
  -H 'Content-Type: application/json' \
  -d '{
    "payload": {
      "user_id": "u123",
      "flow_id": 42,
      "name": "Alice",
      "message": "This is urgent!"
    },
    "initial_state": {}
  }'
```

Or inline the JSON:

```bash
curl -X POST http://localhost:8001/run-flow \
  -H 'Content-Type: application/json' \
  -d '{
    "workflow": {
      "nodes": [
        {"id":"trigger_1","type":"trigger.webhook","config":{}},
        {"id":"chat_1","type":"action.chat","config":{
          "system_prompt":"You are a helpful assistant that summarizes a user's message and crafts a subject.",
          "user_message":"Message from {{payload.name}}: {{payload.message}}"
        }},
        {"id":"cond_1","type":"logic.condition","config":{"left":"{{payload.message}}","op":"contains","right":"urgent"}},
        {"id":"sms_1","type":"action.send_sms","config":{"to":"+15551234567","content":"Chat said: {{nodes.chat_1.generated_response}}"}},
        {"id":"email_1","type":"action.send_email","config":{"to":"user@example.com","subject":"Auto-reply: {{payload.name}}","content":"We received your message: {{payload.message}}. Assistant: {{nodes.chat_1.generated_response}}"}},
        {"id":"end_1","type":"logic.end","config":{}}
      ],
      "edges": [
        {"source":"trigger_1","target":"chat_1"},
        {"source":"chat_1","source_port":"success","target":"cond_1"},
        {"source":"cond_1","source_port":"true","target":"sms_1"},
        {"source":"cond_1","source_port":"false","target":"email_1"},
        {"source":"sms_1","target":"end_1"},
        {"source":"email_1","target":"end_1"}
      ],
      "entry":"trigger_1"
    },
    "payload": {"name":"Alice","message":"This is urgent!"}
  }'
```

You will receive a resulting state that includes `nodes` outputs and a `trace` of executed nodes.

---

## Referencing previous node outputs

- All node outputs are stored under `state.nodes[<node_id>]`.
- You can reference any nested field using dot paths inside `{{ }}`.
  - Example: `{{nodes.chat_1.generated_response}}`
  - Example: If your chat returns a JSON with a `subject` key: `{{nodes.chat_1.generated_response.subject}}`

Tip for `action.chat`: If you need structured fields (e.g., `subject`, `body`), instruct the model to respond with strict JSON. The engine will auto-parse top-level JSON strings into objects.

---

## Azure OpenAI setup (optional)

Set these environment variables (see `.env.example`):

- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT` (e.g., [https://your-resource.openai.azure.com](https://your-resource.openai.azure.com))
- `AZURE_OPENAI_API_VERSION` (default: 2024-02-01)
- `AZURE_OPENAI_DEPLOYMENT` (the chat deployment name)

Without those, `action.chat` will return a mock response with the prompt and user message embedded.

---

## SMS and Email integrations (optional)

- SMS: integrate Twilio by installing `twilio` and providing credentials; see notes in `engine/nodes/__init__.py` `action_send_sms()`.
- Email: integrate your SMTP/provider inside `action_send_email()`.

---

## Project layout

- `main.py`: FastAPI app exposing `/nodes`, `/run-flow`, `/run-flow/db`, and `/flows/*`.
- `engine/workflow_runner.py`: Orchestrates node execution and port-based branching.
- `engine/template_resolver.py`: Resolves `{{...}}` placeholders using current state.
- `engine/nodes/__init__.py`: Node handlers and `NODE_HANDLERS` registry.
- `engine/nodes_config.yml`: Nodes catalog returned by `/nodes`.
- `engine/db.py`: SQLite utilities (`init_db`, `db_get_flow`, `db_save_flow`, `db_list_flows`).
- `examples/flow_basic.json`: Example workflow.
- `ui/`: Minimal UI to compose and test flows (uses `/flows` and `/run-flow`).

---

## Documentation

- API reference: [docs/api.md](docs/api.md)
- Adding new nodes: [docs/adding-nodes.md](docs/adding-nodes.md)
- Index: [docs/index.md](docs/index.md)

---

## Notes & limitations

- Scheduling is represented via `schedule_at` in the trigger config, but actual scheduling/queueing is not implemented in this minimal version.
- The engine executes a single path following ports (`true`/`false`/`success`/`default`). Parallel branches or merges are not implemented.
- Error handling is basic; production usage should add retries, auditing, and persistence.
