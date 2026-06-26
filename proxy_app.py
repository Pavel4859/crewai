import os

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from tools.channel_fetch import fetch_channel_from_telegram, normalize_channel

app = FastAPI(title="Telegram Channel Proxy", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _check_api_key(x_api_key: str | None) -> None:
    expected = os.getenv("PROXY_API_KEY")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="Неверный API-ключ")


@app.get("/")
def root():
    return {"status": "ok", "service": "telegram-channel-proxy"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/api/channel/{channel_username}")
def read_channel(
    channel_username: str,
    limit: int = Query(default=15, ge=1, le=30),
    x_api_key: str | None = Header(default=None),
):
    _check_api_key(x_api_key)
    try:
        return fetch_channel_from_telegram(channel_username, post_limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Telegram: {exc}") from exc
