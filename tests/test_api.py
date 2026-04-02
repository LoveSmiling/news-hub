"""Tests for API endpoints using FastAPI TestClient with mocked database."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from fastapi.testclient import TestClient


# Patch scheduler before importing app
with patch("app.scheduler.jobs.setup_scheduler"), \
     patch("app.scheduler.jobs.scheduler") as mock_scheduler:
    mock_scheduler.start = MagicMock()
    mock_scheduler.shutdown = MagicMock()
    mock_scheduler.get_jobs = MagicMock(return_value=[])
    from app.main import app


def make_mock_source(name="weibo", display_name="微博", category="综合", status="active"):
    source = MagicMock()
    source.id = 1
    source.name = name
    source.display_name = display_name
    source.category = category
    source.status = status
    source.last_collected_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return source


def make_mock_item(id=1, source="weibo", title="测试标题", rank=1):
    item = MagicMock()
    item.id = id
    item.source = source
    item.title = title
    item.url = f"https://example.com/{id}"
    item.rank = rank
    item.hot_value = "100万"
    item.category = "综合"
    item.collected_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    item.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return item


class TestHealthEndpoint:
    def test_health(self):
        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestSourcesEndpoint:
    def test_get_sources(self):
        mock_source = make_mock_source()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_source]

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        async def override_get_db():
            yield mock_session

        from app.db.database import get_db
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        response = client.get("/api/sources")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "weibo"
        assert data[0]["display_name"] == "微博"

        app.dependency_overrides.clear()

    def test_get_sources_empty(self):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_session = AsyncMock()
        mock_session.execute.return_value = mock_result

        async def override_get_db():
            yield mock_session

        from app.db.database import get_db
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        response = client.get("/api/sources")
        assert response.status_code == 200
        assert response.json() == []

        app.dependency_overrides.clear()


class TestHotEndpoint:
    def test_get_all_hot(self):
        mock_source = make_mock_source()
        mock_item = make_mock_item()

        # Source query result
        source_result = MagicMock()
        source_result.scalars.return_value.all.return_value = [mock_source]

        # Latest time result
        latest_result = MagicMock()
        latest_result.scalar.return_value = datetime(2024, 1, 1, tzinfo=timezone.utc)

        # Items result
        items_result = MagicMock()
        items_result.scalars.return_value.all.return_value = [mock_item]

        mock_session = AsyncMock()
        mock_session.execute.side_effect = [source_result, latest_result, items_result]

        async def override_get_db():
            yield mock_session

        from app.db.database import get_db
        app.dependency_overrides[get_db] = override_get_db

        client = TestClient(app)
        response = client.get("/api/hot")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["source"] == "weibo"
        assert len(data[0]["items"]) == 1

        app.dependency_overrides.clear()
