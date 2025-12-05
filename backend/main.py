import os
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import yaml

from router.flows_api import flows_router
from router.auth_api import auth_router
from engine.db import init_db


load_dotenv()

app = FastAPI(title="Mini n8n-like Workflow Engine", version="0.1.0")

# Allow local dev UI to access the API
origins = [
    os.getenv("FRONTEND_URL", "http://127.0.0.1:5173"),
    "http://localhost:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(flows_router)
app.include_router(auth_router)


@app.on_event("startup")
def startup_init_db() -> None:
    init_db()


@app.get("/")
def health() -> Dict[str, str]:
    return {"status": "ok", "docs": "/docs"}


@app.get("/nodes")
def get_nodes_config() -> Dict[str, Any]:
    """Return available nodes configuration from YAML."""
    config_path = os.path.join(os.path.dirname(
        __file__), "engine", "nodes_config.yml")
    if not os.path.exists(config_path):
        raise HTTPException(
            status_code=500, detail="nodes_config.yml not found")
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data
