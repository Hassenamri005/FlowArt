import json
import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter
from engine.workflow_runner import run_workflow
from engine.db import init_db, db_get_flow, db_save_flow
from fastapi.responses import JSONResponse
from fastapi import HTTPException
from pydantic import BaseModel

flows_router = APIRouter(tags=["flows"])


EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")


def _ensure_examples_dir():
    os.makedirs(EXAMPLES_DIR, exist_ok=True)


def _sanitize_flow_name(name: str) -> str:
    """Return an absolute path within EXAMPLES_DIR for a given flow name.
    Only allow [A-Za-z0-9_-.] and ensure .json extension.
    """
    base = name.strip().replace(" ", "_")
    allowed = "".join(ch for ch in base if ch.isalnum() or ch in ("_", "-", "."))
    if not allowed:
        raise HTTPException(status_code=400, detail="Invalid flow name")
    if not allowed.endswith(".json"):
        allowed += ".json"
    abs_path = os.path.abspath(os.path.join(EXAMPLES_DIR, allowed))
    if not abs_path.startswith(os.path.abspath(EXAMPLES_DIR) + os.sep):
        raise HTTPException(status_code=400, detail="Invalid flow path")
    return abs_path


class RunRequest(BaseModel):
    workflow: Dict[str, Any]
    payload: Optional[Dict[str, Any]] = None
    initial_state: Optional[Dict[str, Any]] = None


class SaveFlowRequest(BaseModel):
    workflow: Dict[str, Any]


class RunFlowDBRequest(BaseModel):
    payload: Optional[Dict[str, Any]] = None
    initial_state: Optional[Dict[str, Any]] = None


@flows_router.post("/run-flow")
def run_flow(req: RunRequest):
    try:
        # with open("examples/flow_basic.json", "r") as f:
        #    workflow = json.load(f)
        result = run_workflow(
            workflow=req.workflow,
            initial_state=req.initial_state or {},
            webhook_payload=req.payload or {},
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@flows_router.post("/run-flow/db")
def run_flow_db(req: RunFlowDBRequest):
    """Run a saved flow by extracting user_id and flow_id from the payload."""
    # Ensure DB is initialized (no-op if already done)
    try:
        init_db()
    except Exception:
        pass

    payload = req.payload or {}
    user_id = payload.get("user_id")
    flow_id = payload.get("flow_id")
    if not user_id or not flow_id:
        raise HTTPException(
            status_code=400, detail="payload.user_id and payload.flow_id are required"
        )

    item = db_get_flow(int(flow_id))
    if not item:
        raise HTTPException(status_code=404, detail="Flow not found")
    if str(item.get("user_id")) != str(user_id):
        raise HTTPException(status_code=403, detail="User not permitted for this flow")

    try:
        result = run_workflow(
            workflow=item.get("workflow") or {},
            initial_state=req.initial_state or {},
            webhook_payload=payload,
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@flows_router.get("/flows")
def list_flows() -> Dict[str, Any]:
    """List available flows in the examples directory."""
    _ensure_examples_dir()
    items: List[str] = []
    for fname in sorted(os.listdir(EXAMPLES_DIR)):
        if fname.endswith(".json"):
            items.append(fname)
    return {"flows": items}


@flows_router.get("/flows/{name}")
def load_flow(name: str) -> Dict[str, Any]:
    """Load a flow JSON by filename from examples.
    'name' may be provided with or without the .json extension.
    """
    _ensure_examples_dir()
    path = _sanitize_flow_name(name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Flow not found")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"name": os.path.basename(path), "workflow": data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read flow: {e}")


@flows_router.post("/flows/{name}")
def save_flow(
    name: str,
    req: SaveFlowRequest,
    overwrite: bool = True,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Save a flow JSON to the examples directory.
    Set overwrite=false to prevent overwriting an existing file.
    """
    _ensure_examples_dir()
    path = _sanitize_flow_name(name)
    if os.path.exists(path) and not overwrite:
        raise HTTPException(status_code=409, detail="Flow already exists")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(req.workflow, f, ensure_ascii=False, indent=2)
        # Also persist into SQLite DB (non-fatal if it fails)
        db_id: Optional[int] = None
        try:
            init_db()
            db_user = user_id or os.getenv("DEFAULT_USER_ID") or "default"
            db_id = db_save_flow(
                user_id=db_user, name=os.path.basename(path), workflow=req.workflow
            )
        except Exception as db_e:
            # Log to stdout and continue without failing the request
            print(f"[warn] DB save failed for flow '{name}': {db_e}")
        return {"name": os.path.basename(path), "saved": True, "db_id": db_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save flow: {e}")
