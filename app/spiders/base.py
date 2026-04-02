from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class SpiderItem:
    """Represents a single hot list item extracted by a spider."""

    title: str
    url: str
    rank: int | None = None
    hot_value: str | None = None
    raw_data: dict | None = field(default_factory=dict)


@dataclass
class SourceConfig:
    """Configuration for a data source loaded from sources.yaml."""

    name: str
    display_name: str
    category: str
    type: str
    route: str = ""
    url: str = ""
    schedule: str = "*/5 * * * *"
    max_items: int = 50


class BaseSpider(ABC):
    """Base class for all spiders."""

    def __init__(self, source_config: SourceConfig, rsshub_url: str):
        self.config = source_config
        self.rsshub_url = rsshub_url

    @abstractmethod
    async def fetch(self) -> list[SpiderItem]:
        """Fetch hot items from the source. Must be implemented by subclasses."""
        ...
