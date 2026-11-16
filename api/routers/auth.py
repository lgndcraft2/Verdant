from __future__ import annotations

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

from api.auth import check_password, hash_password, issue_token, verify_session

router = APIRouter(prefix="/auth", tags=["auth"])


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=256)


class Registration(Credentials):
    full_name: str = Field(min_length=1, max_length=120)


def _response(user: dict, token: str) -> dict:
    return {"data": {"access_token": token, "token_type": "bearer",
                     "user": {"id": str(user["id"]), "email": user["email"],
                              "full_name": user["full_name"], "role": user["role"]}},
            "meta": {}, "error": None}


@router.post("/register", status_code=201)
async def register(request: Request, body: Registration) -> dict:
    if len(request.app.state.settings.jwt_secret) < 32:
        raise HTTPException(status_code=503, detail="Authentication is not configured")
    email = str(body.email).lower()
    try:
        user = await request.app.state.db.create_user(email, hash_password(body.password), body.full_name.strip())
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail="Account already exists")
    return _response(user, issue_token(user, request.app.state.settings.jwt_secret))


@router.post("/login")
async def login(request: Request, body: Credentials) -> dict:
    if len(request.app.state.settings.jwt_secret) < 32:
        raise HTTPException(status_code=503, detail="Authentication is not configured")
    user = await request.app.state.db.get_user_by_email(str(body.email).lower())
    if not user or not check_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _response(user, issue_token(user, request.app.state.settings.jwt_secret))


@router.get("/me")
async def me(user: dict = Depends(verify_session)) -> dict:
    return {"data": user, "meta": {}, "error": None}
