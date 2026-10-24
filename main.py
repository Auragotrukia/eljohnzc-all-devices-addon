"""Eljohnzc BitChord compatibility wrapper.

This adapter removes the install-time checkValidLossless policy from the
manifest and forwards the upstream search/stream protocol. It does not fake
Atmos: upstream metadata is preserved, and the client/decoder decides whether
an immersive stream is usable.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

UPSTREAM = os.getenv(
    "ELJOHNZC_UPSTREAM",
    "https://eljohnzcaddon.velixir.run/c57e7b0ef2031b2f1fcd",
).rstrip("/")
TIMEOUT = float(os.getenv("UPSTREAM_TIMEOUT_SECONDS", "20"))
VERSION = "1.0.0"

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


def upstream_get(path: str, params: dict[str, str]) -> Any:
    query = urllib.parse.urlencode(params)
    url = f"{UPSTREAM}{path}?{query}" if query else f"{UPSTREAM}{path}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Eljohnzc-All-Devices-BitChord/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body = response.read().decode("utf-8")
    except Exception as exc:
        raise HTTPException(502, f"Eljohnzc upstream unavailable: {str(exc)[:180]}") from exc
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(502, "Eljohnzc upstream returned invalid JSON") from exc


def request_params(request: Request) -> dict[str, str]:
    allowed = {"q", "query", "quality", "atmos", "limit", "prefer", "countryCode"}
    return {
        key: value
        for key, value in request.query_params.items()
        if key in allowed and value != ""
    }


@app.get("/manifest.json")
async def manifest() -> JSONResponse:
    return JSONResponse(
        {
            "id": "dev.rukia.eljohnzc.all-devices",
            "name": "Eljohnzc Lossless + Atmos (All Devices)",
            "version": VERSION,
            "description": "Eljohnzc compatibility wrapper without the install-time lossless-device gate. Atmos is reported only when upstream exposes it.",
            "resources": ["search", "stream"],
            "types": ["track", "album", "artist"],
            "allowDownloads": 0,
            "settings": [
                {
                    "key": "quality",
                    "type": "select",
                    "default": "hires",
                    "options": [
                        {"label": "Hi-Res Lossless", "value": "hires"},
                        {"label": "Lossless", "value": "lossless"},
                        {"label": "High", "value": "high"},
                        {"label": "Low", "value": "low"},
                    ],
                },
                {
                    "key": "atmos",
                    "type": "select",
                    "default": "auto",
                    "options": [
                        {"label": "Atmos when available", "value": "auto"},
                        {"label": "Stereo fallback", "value": "stereo"},
                    ],
                },
            ],
        }
    )


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "ok": True,
        "version": VERSION,
        "upstream": UPSTREAM,
        "deviceGate": False,
        "atmos": "upstream metadata only",
    }


@app.get("/search")
async def search(request: Request) -> JSONResponse:
    params = request_params(request)
    if not (params.get("q") or params.get("query")):
        raise HTTPException(400, "missing q parameter")
    payload = upstream_get("/search", params)
    if not isinstance(payload, dict):
        raise HTTPException(502, "Eljohnzc search returned an invalid response")
    result = dict(payload)
    tracks = result.get("tracks")
    if isinstance(tracks, list):
        for track in tracks:
            if isinstance(track, dict):
                track.setdefault("provider", "Eljohnzc Lossless + Atmos")
                track.setdefault("compatibility", "all devices; decoder chooses supported output")
    return JSONResponse(result)


@app.get("/stream/{track_id:path}")
async def stream(track_id: str, request: Request) -> JSONResponse:
    if not track_id:
        raise HTTPException(400, "missing track id")
    params = request_params(request)
    payload = upstream_get("/stream/" + urllib.parse.quote(track_id, safe=""), params)
    if not isinstance(payload, dict):
        raise HTTPException(502, "Eljohnzc stream returned an invalid response")
    result = dict(payload)
    result.setdefault("provider", "Eljohnzc Lossless + Atmos")
    result.setdefault("compatibility", "all devices; decoder chooses supported output")
    return JSONResponse(result)


@app.options("/{path:path}")
async def options() -> JSONResponse:
    return JSONResponse({}, status_code=204)


@app.middleware("http")
async def cors(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response
