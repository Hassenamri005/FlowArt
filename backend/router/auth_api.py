from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from engine.db import db_create_user, db_get_user_by_email


auth_router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


@auth_router.post("/signup")
def signup(req: SignupRequest) -> Dict[str, Any]:
    existing = db_get_user_by_email(req.email)
    if existing is not None:
        raise HTTPException(status_code=400, detail="User already exists")
    user_id = db_create_user(req.email, req.password)
    user = db_get_user_by_email(req.email)
    role = user.get("role") if user is not None else "user"
    return {"id": user_id, "email": req.email, "role": role}


@auth_router.post("/login")
def login(req: LoginRequest) -> Dict[str, Any]:
    user = db_get_user_by_email(req.email)
    if user is None or user.get("password") != req.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"id": user.get("id"), "email": user.get("email"), "role": user.get("role")}
