import re
from datetime import datetime
from html import unescape

import httpx
from bs4 import BeautifulSoup

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def normalize_channel(channel_username: str) -> str:
    """Извлекает username из durov, @durov, t.me/durov, t.me/s/durov и полных ссылок."""
    channel = channel_username.strip()
    if not channel:
        return ""

    if channel.startswith("@"):
        channel = channel[1:]

    channel = re.sub(r"^https?://", "", channel, flags=re.IGNORECASE)
    channel = re.sub(r"^(www\.)?t\.me/", "", channel, flags=re.IGNORECASE)

    if channel.startswith("s/"):
        channel = channel[2:]

    channel = channel.rstrip("/").split("/")[-1]
    channel = channel.split("?")[0].split("#")[0]

    return channel


def _strip_message_html(html_fragment: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html_fragment)
    text = re.sub(r"<[^>]+>", "", text)
    return unescape(text).strip()


def _parse_view_count(raw: str) -> int | None:
    raw = raw.strip().replace("\xa0", " ").replace(" ", "")
    if not raw:
        return None
    upper = raw.upper()
    for suffix, multiplier in (("K", 1_000), ("M", 1_000_000)):
        if upper.endswith(suffix):
            try:
                return int(float(upper[:-1].replace(",", ".")) * multiplier)
            except ValueError:
                return None
    digits = re.sub(r"[^\d]", "", raw)
    return int(digits) if digits else None


def _channel_stats(posts: list[dict[str, str]]) -> dict[str, str | int | float]:
    view_counts = [
        parsed
        for post in posts
        if (parsed := _parse_view_count(post.get("views", ""))) is not None
    ]

    dates: list[str] = [post["date"][:10] for post in posts if post.get("date")]
    posts_per_week = "н/д"
    if len(dates) >= 2:
        try:
            first = datetime.fromisoformat(dates[0])
            last = datetime.fromisoformat(dates[-1])
            span_days = max((last - first).days, 1)
            posts_per_week = round(len(dates) / span_days * 7, 1)
        except ValueError:
            posts_per_week = "н/д"

    stats: dict[str, str | int | float] = {
        "posts_analyzed": len(posts),
        "posts_with_views": len(view_counts),
        "posts_per_week": posts_per_week,
    }
    if view_counts:
        stats["views_min"] = min(view_counts)
        stats["views_max"] = max(view_counts)
        stats["views_avg"] = round(sum(view_counts) / len(view_counts))
        stats["views_median"] = sorted(view_counts)[len(view_counts) // 2]
    return stats


def fetch_channel_from_telegram(channel_username: str, post_limit: int = 15) -> dict:
    """Читает публичный канал напрямую с t.me/s (вызывается на Render)."""
    channel = normalize_channel(channel_username)
    if not channel:
        raise ValueError("Укажите username канала, например: durov или @durov")

    url = f"https://t.me/s/{channel}"
    response = httpx.get(
        url,
        headers={"User-Agent": _USER_AGENT},
        timeout=30.0,
        follow_redirects=True,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    title_el = soup.select_one(".tgme_channel_info_header_title")
    about_el = soup.select_one(".tgme_channel_info_description")
    subscribers_el = soup.select_one(".tgme_channel_info_counter")

    posts: list[dict[str, str]] = []
    for message in soup.select(".tgme_widget_message_wrap"):
        text_el = message.select_one(".tgme_widget_message_text")
        date_el = message.select_one(".tgme_widget_message_date time")
        views_el = message.select_one(".tgme_widget_message_views")
        forwarded_el = message.select_one(".tgme_widget_message_forwarded_from")

        text = _strip_message_html(str(text_el)) if text_el else ""
        if not text and not message.select_one(
            ".tgme_widget_message_photo, .tgme_widget_message_video"
        ):
            continue

        posts.append(
            {
                "date": date_el.get("datetime", "") if date_el else "",
                "text": text or "[пост без текста: фото/видео/медиа]",
                "views": views_el.get_text(strip=True) if views_el else "",
                "forwarded_from": forwarded_el.get_text(" ", strip=True) if forwarded_el else "",
            }
        )

    posts = list(reversed(posts[-post_limit:]))

    return {
        "channel": channel,
        "url": url,
        "title": title_el.get_text(strip=True) if title_el else channel,
        "description": about_el.get_text("\n", strip=True) if about_el else "",
        "subscribers": subscribers_el.get_text(strip=True) if subscribers_el else "",
        "posts": posts,
        "stats": _channel_stats(posts),
    }
