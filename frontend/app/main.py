import os
from collections import defaultdict
from datetime import datetime
from typing import Any

import httpx
from dateutil import parser
from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Thoughts Frontend")
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://backend:8080").rstrip("/")


def _month_key(dt_raw: str) -> str:
    dt = parser.isoparse(dt_raw)
    return dt.strftime("%B %Y")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "frontend"}


@app.get("/api/v1/test")
def test() -> dict[str, str]:
    return {"message": "frontend test ok"}


@app.get("/")
async def home(request: Request) -> Any:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"{BACKEND_BASE_URL}/api/v1/thoughts")
        response.raise_for_status()
        items = response.json()

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        grouped[_month_key(item["published_at"])].append(item)

    sorted_groups = sorted(
        grouped.items(),
        key=lambda it: datetime.strptime(it[0], "%B %Y"),
        reverse=True,
    )

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "groups": sorted_groups,
            "backend_base_url": BACKEND_BASE_URL,
        },
    )


@app.post("/thoughts")
async def create_thought(title: str = Form(...), content: str = Form(...)) -> RedirectResponse:
    payload = {"title": title, "content": content}
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{BACKEND_BASE_URL}/api/v1/thoughts", json=payload)
        response.raise_for_status()
    return RedirectResponse(url="/", status_code=303)
