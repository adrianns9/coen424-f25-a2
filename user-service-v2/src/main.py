import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr

from schemas import UserCreate, UserUpdate
from user_db import users_collection
from rabbit import publish_message

load_dotenv()

app = FastAPI(title="User Service v2")


class UserOut(BaseModel):
    id: str
    email: EmailStr
    delivery_address: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


async def _get_user_or_404(user_id: str) -> Dict[str, Any]:
    """Helper to load a user document or raise 404."""
    existing = await users_collection.find_one({"_id": user_id})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    return existing


@app.get("/")
async def root():
    return {"hello": True, "service": "user-service-v2"}


@app.post("/users", response_model=UserOut, status_code=201)
async def create_user(payload: UserCreate):
    user_id = str(uuid.uuid4())
    now = datetime.utcnow()

    user_doc = {
        "_id": user_id,
        "email": payload.email,
        "delivery_address": payload.delivery_address,
        "created_at": now,
        "updated_at": now,
    }

    await users_collection.insert_one(user_doc)

    return UserOut(
        id=user_doc["_id"],
        email=user_doc["email"],
        delivery_address=user_doc["delivery_address"],
        created_at=user_doc.get("created_at"),
        updated_at=user_doc.get("updated_at"),
    )


@app.put("/users/{user_id}", response_model=UserOut)
async def update_user(user_id: str, payload: UserUpdate):
    existing = await _get_user_or_404(user_id)

    old_email = existing.get("email")
    old_address = existing.get("delivery_address")

    update_data: Dict[str, Any] = {}

    if payload.email is not None:
        update_data["email"] = payload.email
    if payload.delivery_address is not None:
        update_data["delivery_address"] = payload.delivery_address

    # Nothing to update → just return current state
    if not update_data:
        return UserOut(
            id=existing["_id"],
            email=existing["email"],
            delivery_address=existing["delivery_address"],
            created_at=existing.get("created_at"),
            updated_at=existing.get("updated_at"),
        )

    # Apply update
    update_data["updated_at"] = datetime.utcnow()
    await users_collection.update_one({"_id": user_id}, {"$set": update_data})

    updated = await users_collection.find_one({"_id": user_id})
    if not updated:
        # Should not happen, but just in case
        raise HTTPException(status_code=500, detail="User could not be reloaded")

    new_email = updated.get("email")
    new_address = updated.get("delivery_address")

    # Only publish an event if contact info actually changed
    if (new_email != old_email) or (new_address != old_address):
        event_message = {
            "user_id": user_id,
            # Keep backward-compatible keys
            "email": new_email,
            "delivery_address": new_address,
            # Extra context for v2
            "old_email": old_email,
            "old_delivery_address": old_address,
        }
        await publish_message(
            message=event_message,
            headers={
                "type": "user.contact.updated",
                "version": "v2",
            },
        )

    return UserOut(
        id=updated["_id"],
        email=updated["email"],
        delivery_address=updated["delivery_address"],
        created_at=updated.get("created_at"),
        updated_at=updated.get("updated_at"),
    )
