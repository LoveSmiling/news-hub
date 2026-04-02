import logging

import feedparser
import httpx

from app.spiders.base import BaseSpider, SourceConfig, SpiderItem

logger = logging.getLogger(__name__)


class RSSSpider(BaseSpider):
    """Generic spider for fetching and parsing RSS/Atom feeds."""

    def __init__(self, source_config: SourceConfig, rsshub_url: str):
        super().__init__(source_config, rsshub_url)
        if source_config.url:
            self.feed_url = source_config.url
        else:
            self.feed_url = f"{rsshub_url.rstrip('/')}{source_config.route}"

    async def fetch(self) -> list[SpiderItem]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(self.feed_url)
                response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("Failed to fetch RSS feed for %s: %s", self.config.name, e)
            return []

        feed = feedparser.parse(response.text)

        if feed.bozo and not feed.entries:
            logger.warning("Malformed feed for %s: %s", self.config.name, feed.bozo_exception)
            return []

        items: list[SpiderItem] = []
        max_items = self.config.max_items

        for idx, entry in enumerate(feed.entries[:max_items]):
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()

            if not title or not link:
                continue

            items.append(
                SpiderItem(
                    title=title,
                    url=link,
                    rank=idx + 1,
                    hot_value=self._extract_hot_value(entry),
                    raw_data={
                        "summary": entry.get("summary", ""),
                        "published": entry.get("published", ""),
                        "author": entry.get("author", ""),
                    },
                )
            )

        logger.info("Fetched %d items from %s", len(items), self.config.name)
        return items

    def _extract_hot_value(self, entry: dict) -> str | None:
        """Try to extract hot value from feed entry metadata."""
        # Some RSSHub feeds put hot value in custom fields
        for key in ("slash_comments", "comments", "score"):
            if key in entry:
                return str(entry[key])
        return None
