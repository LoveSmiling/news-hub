import logging

import httpx
from bs4 import BeautifulSoup

from app.spiders.base import BaseSpider, SpiderItem

logger = logging.getLogger(__name__)

STEAM_STATS_URL = "https://store.steampowered.com/stats/stats/"


class SteamSpider(BaseSpider):
    """Spider for fetching Steam top games by current player count."""

    async def fetch(self) -> list[SpiderItem]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(STEAM_STATS_URL)
                response.raise_for_status()
        except httpx.HTTPError as e:
            logger.error("Failed to fetch Steam stats: %s", e)
            return []

        soup = BeautifulSoup(response.text, "lxml")
        rows = soup.select("#detailStats tr.player_count_row")

        if not rows:
            logger.warning("No player_count_row found on Steam stats page")
            return []

        items: list[SpiderItem] = []
        max_items = self.config.max_items

        for idx, row in enumerate(rows[:max_items]):
            link = row.select_one("a.gameLink")
            if not link:
                continue

            game_name = link.get_text(strip=True)
            game_url = link.get("href", "").strip()
            current_el = row.select_one("td:first-child .currentServers")
            current_players = current_el.get_text(strip=True) if current_el else ""

            if not game_name or not game_url:
                continue

            items.append(
                SpiderItem(
                    title=game_name,
                    url=game_url,
                    rank=idx + 1,
                    hot_value=current_players,
                    raw_data={"current_players": current_players},
                )
            )

        return items
