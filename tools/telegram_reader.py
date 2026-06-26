import os

import httpx
from crewai.tools import tool

from tools.channel_fetch import fetch_channel_from_telegram, normalize_channel


def fetch_public_channel(channel_username: str, post_limit: int = 15) -> dict:
    """Читает канал локально или через прокси на Render (TELEGRAM_PROXY_URL)."""
    proxy_url = os.getenv("TELEGRAM_PROXY_URL", "").rstrip("/")
    if not proxy_url:
        return fetch_channel_from_telegram(channel_username, post_limit=post_limit)

    channel = normalize_channel(channel_username)
    headers = {}
    proxy_key = os.getenv("TELEGRAM_PROXY_KEY")
    if proxy_key:
        headers["X-Api-Key"] = proxy_key

    response = httpx.get(
        f"{proxy_url}/api/channel/{channel}",
        params={"limit": post_limit},
        headers=headers,
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()


def format_channel_report(data: dict) -> str:
    lines = [
        f"Канал: @{data['channel']} — {data['title']}",
        f"URL: {data['url']}",
    ]
    if data.get("subscribers"):
        lines.append(f"Подписчики: {data['subscribers']}")
    if data.get("description"):
        lines.append(f"Описание: {data['description']}")
    lines.append("")
    lines.append(f"Последние посты ({len(data['posts'])}):")

    for index, post in enumerate(data["posts"], start=1):
        date = post["date"][:10] if post.get("date") else "без даты"
        meta = []
        if post.get("views"):
            meta.append(f"просмотры: {post['views']}")
        if post.get("forwarded_from"):
            meta.append(f"репост из: {post['forwarded_from']}")
        meta_suffix = f" ({', '.join(meta)})" if meta else ""
        lines.append(f"\n--- Пост {index} ({date}){meta_suffix} ---")
        lines.append(post["text"])

    if not data["posts"]:
        lines.append(
            "Посты не найдены. Канал может быть приватным или недоступен."
        )

    return "\n".join(lines)


@tool("Read Telegram Channel")
def read_telegram_channel(channel_username: str, post_limit: int = 15) -> str:
    """Читает публичный Telegram-канал: описание и последние посты.

    Используй для анализа конкурентов и ниши. На сервере Render читает t.me напрямую.
    Локально можно задать TELEGRAM_PROXY_URL, если t.me недоступен с ПК.

    Args:
        channel_username: username канала без @ или ссылка t.me/channel
        post_limit: сколько последних постов вернуть (по умолчанию 15)
    """
    try:
        data = fetch_public_channel(channel_username, post_limit=post_limit)
        return format_channel_report(data)
    except httpx.HTTPStatusError as exc:
        return (
            f"Ошибка HTTP {exc.response.status_code} при чтении "
            f"@{normalize_channel(channel_username)}"
        )
    except httpx.HTTPError as exc:
        return f"Не удалось подключиться к Telegram: {exc}"
    except Exception as exc:
        return f"Ошибка чтения канала: {exc}"
