"""OSINT scraper — crawl iranmonitor.org for situation updates."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import date
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from api.config import settings

logger = logging.getLogger(__name__)

IRANMONITOR_URL = "https://www.iranmonitor.org"
REQUEST_TIMEOUT = 30.0


@dataclass
class ScrapedEvent:
    source: str
    url: str
    title: str
    body: str
    category: str  # protest, sanctions, diplomacy, conflict, economy, politics, etc.
    event_date: Optional[str]  # YYYY-MM-DD or None
    content_hash: str = ""

    def __post_init__(self) -> None:
        if not self.content_hash:
            raw = f"{self.title}|{self.event_date or ''}"
            self.content_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]


async def _fetch_page(url: str) -> Optional[str]:
    """Fetch a page, return HTML or None on failure."""
    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": settings.SCRAPE_USER_AGENT},
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.text
    except Exception as e:
        logger.warning(f"Failed to fetch {url}: {e}")
        return None


def _extract_next_data(html: str) -> Optional[dict]:
    """Try to extract __NEXT_DATA__ JSON from a Next.js page."""
    soup = BeautifulSoup(html, "html.parser")
    script = soup.find("script", {"id": "__NEXT_DATA__"})
    if script and script.string:
        try:
            return json.loads(script.string)
        except json.JSONDecodeError:
            pass
    return None


def _parse_events_from_next_data(data: dict) -> list[ScrapedEvent]:
    """Extract events from __NEXT_DATA__ props structure."""
    events: list[ScrapedEvent] = []
    today = date.today().isoformat()

    # Navigate the props tree — structure varies, so we search broadly
    def _search(obj: any, depth: int = 0) -> None:
        if depth > 10:
            return
        if isinstance(obj, dict):
            # Look for event-like objects with title/body/category keys
            if "title" in obj and ("body" in obj or "description" in obj or "content" in obj):
                title = obj.get("title", "")
                body = obj.get("body") or obj.get("description") or obj.get("content") or ""
                category = obj.get("category") or obj.get("type") or "general"
                event_date = obj.get("date") or obj.get("publishedAt") or obj.get("created_at")

                # Normalize date
                if event_date and len(event_date) >= 10:
                    event_date = event_date[:10]
                else:
                    event_date = today

                if title and len(title) > 5:
                    events.append(ScrapedEvent(
                        source="iranmonitor.org",
                        url=IRANMONITOR_URL,
                        title=str(title).strip(),
                        body=str(body).strip()[:2000],
                        category=str(category).lower(),
                        event_date=event_date,
                    ))
            else:
                for v in obj.values():
                    _search(v, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                _search(item, depth + 1)

    _search(data)
    return events


def _parse_events_from_html(html: str) -> list[ScrapedEvent]:
    """Fallback: parse events from raw HTML structure."""
    soup = BeautifulSoup(html, "html.parser")
    events: list[ScrapedEvent] = []
    today = date.today().isoformat()

    # Look for article-like elements
    for article in soup.find_all(["article", "div"], class_=lambda c: c and any(
        kw in (c if isinstance(c, str) else " ".join(c)).lower()
        for kw in ["event", "briefing", "news", "update", "timeline", "card", "item"]
    )):
        # Extract title
        title_el = article.find(["h1", "h2", "h3", "h4", "a"])
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        if len(title) < 5:
            continue

        # Extract body
        body_el = article.find(["p", "div"], class_=lambda c: c and any(
            kw in (c if isinstance(c, str) else " ".join(c)).lower()
            for kw in ["body", "content", "description", "text", "summary"]
        ))
        body = body_el.get_text(strip=True) if body_el else ""

        # Extract category from tags/badges
        cat_el = article.find(class_=lambda c: c and any(
            kw in (c if isinstance(c, str) else " ".join(c)).lower()
            for kw in ["category", "tag", "badge", "label"]
        ))
        category = cat_el.get_text(strip=True).lower() if cat_el else "general"

        events.append(ScrapedEvent(
            source="iranmonitor.org",
            url=IRANMONITOR_URL,
            title=title[:300],
            body=body[:2000],
            category=category,
            event_date=today,
        ))

    return events


async def scrape_iranmonitor(
    seen_hashes: set[str] | None = None,
) -> list[ScrapedEvent]:
    """Scrape iranmonitor.org for new events. Returns deduplicated events."""
    seen = seen_hashes or set()
    all_events: list[ScrapedEvent] = []

    html = await _fetch_page(IRANMONITOR_URL)
    if not html:
        logger.warning("Could not fetch iranmonitor.org")
        return []

    # Try __NEXT_DATA__ first (more structured)
    next_data = _extract_next_data(html)
    if next_data:
        events = _parse_events_from_next_data(next_data)
        logger.info(f"Extracted {len(events)} events from __NEXT_DATA__")
        all_events.extend(events)

    # Fall back to / supplement with HTML parsing
    if len(all_events) < 3:
        html_events = _parse_events_from_html(html)
        logger.info(f"Extracted {len(html_events)} events from HTML")
        # Add only events not already found via __NEXT_DATA__
        existing_hashes = {e.content_hash for e in all_events}
        for e in html_events:
            if e.content_hash not in existing_hashes:
                all_events.append(e)

    # Deduplicate against previously seen events
    new_events = [e for e in all_events if e.content_hash not in seen]
    logger.info(f"After dedup: {len(new_events)} new events (from {len(all_events)} total)")

    return new_events
