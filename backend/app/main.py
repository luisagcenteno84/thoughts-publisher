from datetime import datetime, timezone
from typing import Any

import markdown as md
from fastapi import FastAPI, HTTPException
from google.cloud import firestore
from pydantic import BaseModel, Field

APP_NAME = "Thoughts Backend"
DEFAULT_COLLECTION = "items"

app = FastAPI(title=APP_NAME)


def _get_db() -> firestore.Client:
    return firestore.Client()


def _collection_name() -> str:
    import os

    return os.getenv("FIRESTORE_COLLECTION", DEFAULT_COLLECTION)


class ThoughtCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    location: str | None = Field(default=None, max_length=250)
    published_at: datetime | None = None


class ThoughtOut(BaseModel):
    id: str
    title: str
    content: str
    content_html: str
    location: str | None = None
    published_at: datetime


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}


@app.get("/api/v1/test")
def test() -> dict[str, str]:
    return {"message": "backend test ok"}


@app.post("/api/v1/thoughts", response_model=ThoughtOut)
def create_thought(payload: ThoughtCreate) -> ThoughtOut:
    try:
        db = _get_db()
        collection = db.collection(_collection_name())
        published_at = payload.published_at or datetime.now(timezone.utc)
        location = payload.location.strip() if payload.location else None
        doc = {
            "title": payload.title,
            "content": payload.content,
            "location": location,
            "published_at": published_at,
            "created_at": datetime.now(timezone.utc),
        }
        ref = collection.document()
        ref.set(doc)

        return ThoughtOut(
            id=ref.id,
            title=payload.title,
            content=payload.content,
            content_html=md.markdown(payload.content, extensions=["extra", "sane_lists"]),
            location=location,
            published_at=published_at,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"failed to create thought: {exc}") from exc


@app.get("/api/v1/thoughts", response_model=list[ThoughtOut])
def list_thoughts() -> list[ThoughtOut]:
    try:
        db = _get_db()
        collection = db.collection(_collection_name())
        docs = collection.order_by("published_at", direction=firestore.Query.DESCENDING).stream()
        out: list[ThoughtOut] = []
        for d in docs:
            item: dict[str, Any] = d.to_dict()
            published_at = item.get("published_at")
            if published_at is None:
                continue
            out.append(
                ThoughtOut(
                    id=d.id,
                    title=item.get("title", "Untitled"),
                    content=item.get("content", ""),
                    content_html=md.markdown(item.get("content", ""), extensions=["extra", "sane_lists"]),
                    location=item.get("location"),
                    published_at=published_at,
                )
            )
        return out
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"failed to list thoughts: {exc}") from exc


@app.delete("/api/v1/thoughts/{thought_id}")
def delete_thought(thought_id: str) -> dict[str, str]:
    try:
        db = _get_db()
        ref = db.collection(_collection_name()).document(thought_id)
        snapshot = ref.get()
        if not snapshot.exists:
            raise HTTPException(status_code=404, detail="thought not found")
        ref.delete()
        return {"status": "deleted", "id": thought_id}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"failed to delete thought: {exc}") from exc
