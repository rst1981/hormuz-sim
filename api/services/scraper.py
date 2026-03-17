"""OSINT scraper — fetch Iran-related news from multiple sources."""

from __future__ import annotations

import hashlib
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date
from email.utils import parsedate_to_datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from api.config import settings

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 30.0

# Google News RSS feeds for Iran crisis topics (no API key needed)
GOOGLE_NEWS_FEEDS = [
    "https://news.google.com/rss/search?q=Iran+Israel+conflict&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Strait+of+Hormuz&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Iran+military+IRGC&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Iran+sanctions+oil+price&hl=en-US&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=Houthi+Red+Sea&hl=en-US&gl=US&ceid=US:en",
]


@dataclass
class ScrapedEvent:
    source: str
    url: str
    title: str
    body: str
    category: str
    event_date: Optional[str] = None
    content_hash: str = ""

    def __post_init__(self) -> None:
        if not self.content_hash:
            raw = f"{self.title}|{self.event_date or ''}"
            self.content_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]


async def _fetch(url: str) -> Optional[str]:
    """Fetch a URL, return text or None on failure."""
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


def _categorize(title: str) -> str:
    """Simple keyword-based categorization."""
    t = title.lower()
    if any(w in t for w in ["missile", "strike", "attack", "military", "irgc", "drone", "intercept"]):
        return "conflict"
    if any(w in t for w in ["oil", "crude", "brent", "opec", "barrel", "energy"]):
        return "economy"
    if any(w in t for w in ["sanction", "treasury", "embargo"]):
        return "sanctions"
    if any(w in t for w in ["diplomat", "talks", "negotiate", "ceasefire", "peace"]):
        return "diplomacy"
    if any(w in t for w in ["houthi", "red sea", "shipping", "strait", "hormuz"]):
        return "maritime"
    if any(w in t for w in ["nuclear", "enrichment", "iaea", "uranium"]):
        return "nuclear"
    if any(w in t for w in ["protest", "uprising", "unrest"]):
        return "protest"
    if any(w in t for w in ["trump", "biden", "congress", "white house"]):
        return "politics"
    return "general"


def _parse_rss(xml_text: str) -> list[ScrapedEvent]:
    """Parse Google News RSS XML into ScrapedEvent list."""
    events: list[ScrapedEvent] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return events

    for item in root.iter("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description")
        pubdate_el = item.find("pubDate")
        source_el = item.find("source")

        title = title_el.text.strip() if title_el is not None and title_el.text else ""
        if not title or len(title) < 10:
            continue

        link = link_el.text.strip() if link_el is not None and link_el.text else ""
        source_name = source_el.text.strip() if source_el is not None and source_el.text else "Google News"

        # Parse description (often contains HTML snippet)
        body = ""
        if desc_el is not None and desc_el.text:
            soup = BeautifulSoup(desc_el.text, "html.parser")
            body = soup.get_text(strip=True)[:2000]

        # Parse date
        event_date = date.today().isoformat()
        if pubdate_el is not None and pubdate_el.text:
            try:
                dt = parsedate_to_datetime(pubdate_el.text)
                event_date = dt.strftime("%Y-%m-%d")
            except Exception:
                pass

        events.append(ScrapedEvent(
            source=source_name,
            url=link,
            title=title[:300],
            body=body,
            category=_categorize(title),
            event_date=event_date,
        ))

    return events


async def scrape_iranmonitor(
    seen_hashes: set[str] | None = None,
) -> list[ScrapedEvent]:
    """Scrape multiple news sources for Iran-related events. Returns deduplicated events."""
    seen = seen_hashes or set()
    all_events: list[ScrapedEvent] = []
    seen_in_batch: set[str] = set()

    # Fetch all Google News RSS feeds
    for feed_url in GOOGLE_NEWS_FEEDS:
        xml_text = await _fetch(feed_url)
        if not xml_text:
            continue

        events = _parse_rss(xml_text)
        for e in events:
            if e.content_hash not in seen_in_batch:
                seen_in_batch.add(e.content_hash)
                all_events.append(e)

    logger.info(f"Scraped {len(all_events)} total events from {len(GOOGLE_NEWS_FEEDS)} feeds")

    # Filter to 2026+ only (simulation era)
    all_events = [e for e in all_events if e.event_date and e.event_date >= "2026-02-25"]

    # Deduplicate against previously seen events
    new_events = [e for e in all_events if e.content_hash not in seen]
    logger.info(f"After dedup: {len(new_events)} new events")

    return new_events
