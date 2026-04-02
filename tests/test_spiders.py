"""Tests for RSS spider and dedup logic."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.spiders.base import SourceConfig, SpiderItem
from app.spiders.rss_spider import RSSSpider


SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>热搜第一条</title>
      <link>https://example.com/1</link>
      <description>描述1</description>
    </item>
    <item>
      <title>热搜第二条</title>
      <link>https://example.com/2</link>
      <description>描述2</description>
    </item>
    <item>
      <title></title>
      <link>https://example.com/empty</link>
    </item>
  </channel>
</rss>
"""


def make_config(**overrides) -> SourceConfig:
    defaults = dict(
        name="test",
        display_name="测试",
        category="综合",
        type="rsshub",
        route="/test/hot",
        max_items=50,
    )
    defaults.update(overrides)
    return SourceConfig(**defaults)


class TestRSSSpider:
    """Tests for RSSSpider.fetch()."""

    @pytest.mark.asyncio
    async def test_fetch_parses_items(self):
        config = make_config()
        spider = RSSSpider(config, "http://rsshub:1200")

        mock_response = MagicMock()
        mock_response.text = SAMPLE_RSS
        mock_response.raise_for_status = MagicMock()

        with patch("app.spiders.rss_spider.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            items = await spider.fetch()

        # Empty title item should be filtered out
        assert len(items) == 2
        assert items[0].title == "热搜第一条"
        assert items[0].url == "https://example.com/1"
        assert items[0].rank == 1
        assert items[1].title == "热搜第二条"
        assert items[1].rank == 2

    @pytest.mark.asyncio
    async def test_fetch_respects_max_items(self):
        config = make_config(max_items=1)
        spider = RSSSpider(config, "http://rsshub:1200")

        mock_response = MagicMock()
        mock_response.text = SAMPLE_RSS
        mock_response.raise_for_status = MagicMock()

        with patch("app.spiders.rss_spider.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            items = await spider.fetch()

        assert len(items) == 1

    @pytest.mark.asyncio
    async def test_fetch_handles_http_error(self):
        import httpx

        config = make_config()
        spider = RSSSpider(config, "http://rsshub:1200")

        with patch("app.spiders.rss_spider.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.HTTPError("Connection refused")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            items = await spider.fetch()

        assert items == []

    @pytest.mark.asyncio
    async def test_fetch_handles_malformed_feed(self):
        config = make_config()
        spider = RSSSpider(config, "http://rsshub:1200")

        mock_response = MagicMock()
        mock_response.text = "not xml at all"
        mock_response.raise_for_status = MagicMock()

        with patch("app.spiders.rss_spider.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value = mock_client

            items = await spider.fetch()

        # feedparser is lenient, may return 0 items but shouldn't crash
        assert isinstance(items, list)

    def test_feed_url_construction(self):
        config = make_config(route="/weibo/search/hot")
        spider = RSSSpider(config, "http://rsshub:1200")
        assert spider.feed_url == "http://rsshub:1200/weibo/search/hot"

        spider2 = RSSSpider(config, "http://rsshub:1200/")
        assert spider2.feed_url == "http://rsshub:1200/weibo/search/hot"


class TestSourceConfig:
    """Tests for SourceConfig dataclass."""

    def test_defaults(self):
        config = SourceConfig(
            name="test",
            display_name="Test",
            category="综合",
            type="rsshub",
        )
        assert config.schedule == "*/5 * * * *"
        assert config.max_items == 50
        assert config.route == ""

    def test_custom_values(self):
        config = make_config(schedule="*/10 * * * *", max_items=20)
        assert config.schedule == "*/10 * * * *"
        assert config.max_items == 20


class TestSpiderItem:
    """Tests for SpiderItem dataclass."""

    def test_creation(self):
        item = SpiderItem(title="Test", url="https://example.com")
        assert item.title == "Test"
        assert item.rank is None
        assert item.hot_value is None
        assert item.raw_data == {}

    def test_full_creation(self):
        item = SpiderItem(
            title="Test",
            url="https://example.com",
            rank=1,
            hot_value="999万",
            raw_data={"key": "value"},
        )
        assert item.rank == 1
        assert item.hot_value == "999万"
