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


def _ordinal_day(day: int) -> str:
    if 11 <= day % 100 <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix}"


def _month_key(dt_raw: str) -> str:
    dt = parser.isoparse(dt_raw)
    return dt.strftime("%B %Y")


def _display_date(dt_raw: str) -> str:
    dt = parser.isoparse(dt_raw)
    return f"{dt.strftime('%A, %B')} {_ordinal_day(dt.day)}, {dt.year}"


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
        item["published_display"] = _display_date(item["published_at"])
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
        },
    )


@app.post("/thoughts")
async def create_thought(
    title: str = Form(...),
    content: str = Form(...),
    location: str = Form(default=""),
    location_city: str = Form(default=""),
    location_state: str = Form(default=""),
    location_country: str = Form(default=""),
    location_lat: str = Form(default=""),
    location_lon: str = Form(default=""),
) -> RedirectResponse:
    payload: dict[str, Any] = {"title": title, "content": content}

    location_clean = location.strip()
    if location_clean:
        payload["location"] = location_clean

    for key, raw in {
        "location_city": location_city,
        "location_state": location_state,
        "location_country": location_country,
    }.items():
        cleaned = raw.strip()
        if cleaned:
            payload[key] = cleaned

    if location_lat.strip():
        try:
            payload["location_lat"] = float(location_lat)
        except ValueError:
            pass

    if location_lon.strip():
        try:
            payload["location_lon"] = float(location_lon)
        except ValueError:
            pass

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{BACKEND_BASE_URL}/api/v1/thoughts", json=payload)
        response.raise_for_status()
    return RedirectResponse(url="/", status_code=303)


@app.post("/thoughts/{thought_id}/delete")
async def delete_thought(thought_id: str) -> RedirectResponse:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.delete(f"{BACKEND_BASE_URL}/api/v1/thoughts/{thought_id}")
        response.raise_for_status()
    return RedirectResponse(url="/", status_code=303)
