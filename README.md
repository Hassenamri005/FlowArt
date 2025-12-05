# FlowArt

![FlowArt Logo](images/logo-dark.png)

**Global Documentation**: <https://waflow.mintlify.app/>

A minimal workflow engine inspired by n8n with a visual editor and node-based orchestration.

## Overview

FlowArt provides a powerful yet simple workflow automation platform with:

- **Visual Workflow Editor**: React-based UI for composing flows with drag-and-drop interface
- **FastAPI Backend**: High-performance Python backend for executing workflows
- **Built-in Nodes**: Pre-configured nodes for common operations (trigger, chat, SMS, email, condition, end)
- **Template Resolution**: Reference previous node outputs using `{{nodes.chat_1.generated_message}}` and payload fields using `{{payload.message}}`

## API Endpoints

- `GET /nodes` - List available node types and their config schema
- `POST /run-flow` - Execute a workflow JSON with optional webhook payload and initial state
- `POST /run-flow/db` - Execute a saved workflow by `payload.user_id` and `payload.flow_id`
- `GET /flows` - List flows in the `examples/` folder
- `GET /flows/{name}` - Load a saved flow JSON from `examples/`
- `POST /flows/{name}` - Save a flow JSON to `examples/` and persist to SQLite (returns `db_id`)

## Available Nodes

- **Trigger**: `trigger.webhook` - Receives webhook payloads
- **Chat**: `action.chat` - Azure OpenAI integration (mocked if not configured)
- **SMS**: `action.send_sms` - Send SMS messages (mocked; integrate Twilio for real sending)
- **Email**: `action.send_email` - Send emails (mocked; integrate SMTP/provider for real sending)
- **Condition**: `logic.condition` - Conditional logic (==, !=, >, >=, <, <=, contains, in, regex)
- **End**: `logic.end` - Workflow termination

## Quickstart

1. **Clone the repository**
   ```bash
   git clone https://github.com/Hassenamri005/FlowArt.git
   cd FlowArt
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up the frontend**
   ```bash
   cd ../ui
   npm install
   ```

4. **Start the services**
   ```bash
   # From the root directory
   ./start_all.sh
   ```
   Or start individually:
   ```bash
   # Backend (port 8001)
   cd backend && python main.py
   
   # Frontend (port 3000)
   cd ui && npm start
   ```

5. **Access FlowArt**
   - Frontend: <http://localhost:3000>
   - API Documentation: <http://localhost:8001/docs>
   - API ReDoc: <http://localhost:8001/redoc>

## Project Structure

```
FlowArt/
├── backend/          # FastAPI backend application
│   ├── engine/       # Workflow execution engine
│   ├── docs/         # API documentation
│   └── main.py       # Application entry point
├── ui/               # React frontend application
│   ├── src/          # Source code
│   └── public/       # Static assets
├── images/           # Project images and logos
├── docker-compose.yml # Docker configuration
└── start_all.sh      # Startup script
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **GitHub**: https://github.com/Hassenamri005/FlowArt
- **LinkedIn**: https://www.linkedin.com/in/hassenamri005/