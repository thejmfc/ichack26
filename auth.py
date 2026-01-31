"""FastAPI auth endpoints.

Provides a small `/auth` router with `POST /auth/signup` and
`POST /auth/signin` endpoints. Uses `sqlmodel` for persistence and a
simple PBKDF2-based password hashing scheme. Returns a lightweight
random token on signin and keeps an in-memory token->user mapping.

Note: This is a minimal implementation for local/dev use. Replace the
token generation and storage with a secure JWT/session store for
production.
"""
from __future__ import annotations

import os
import secrets
import hashlib
import binascii
from typing import Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select

import database
from models import User


router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class SigninRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str


# Simple in-memory token store: token -> user_id
TOKENS: Dict[str, int] = {}


def _hash_password(password: str) -> str:
    """Hash a password using PBKDF2-HMAC-SHA256 and return salt$hash hex."""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return f"{binascii.hexlify(salt).decode()}${binascii.hexlify(dk).decode()}"


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split("$")
        salt = binascii.unhexlify(salt_hex)
        expected = binascii.unhexlify(hash_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
        return secrets.compare_digest(dk, expected)
    except Exception:
        return False


@router.post("/signup")
def signup(req: SignupRequest):
    engine = database.init()
    with Session(engine) as session:
        statement = select(User).where(User.email == req.email)
        existing = session.exec(statement).first()
        if existing:
            raise HTTPException(status_code=400, detail="email already registered")

        user = User(name=req.name, email=req.email, hashed_password=_hash_password(req.password))
        session.add(user)
        session.commit()
        session.refresh(user)

        return {"id": user.id, "name": user.name, "email": user.email}


@router.post("/signin", response_model=TokenResponse)
def signin(req: SigninRequest):
    engine = database.init()
    with Session(engine) as session:
        statement = select(User).where(User.email == req.email)
        user = session.exec(statement).first()
        if not user or not _verify_password(req.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="invalid credentials")

        token = secrets.token_urlsafe(32)
        TOKENS[token] = user.id
        return {"access_token": token}


__all__ = ["router", "TOKENS"]
