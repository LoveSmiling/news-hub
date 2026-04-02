from datetime import datetime

from pydantic import BaseModel, Field


class HotItemResponse(BaseModel):
    id: int
    source: str
    title: str
    url: str
    rank: int | None = None
    hot_value: str | None = None
    category: str | None = None
    summary: str | None = None
    keywords: list[str] | None = None
    collected_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class SourceResponse(BaseModel):
    id: int
    name: str
    display_name: str
    category: str
    type: str = "rsshub"
    route: str = ""
    url: str = ""
    schedule: str = "*/10 * * * *"
    max_items: int = 30
    status: str
    last_collected_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class SourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    display_name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    type: str = Field(default="rsshub", pattern=r"^(rsshub|rss)$")
    route: str = Field(default="", max_length=200)
    url: str = Field(default="", max_length=500)
    schedule: str = Field(default="*/10 * * * *", max_length=50)
    max_items: int = Field(default=30, ge=1, le=200)


class SourceUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    type: str | None = Field(default=None, pattern=r"^(rsshub|rss)$")
    route: str | None = Field(default=None, max_length=200)
    url: str | None = Field(default=None, max_length=500)
    schedule: str | None = Field(default=None, max_length=50)
    max_items: int | None = Field(default=None, ge=1, le=200)


class SourceTestRequest(BaseModel):
    type: str = Field(..., pattern=r"^(rsshub|rss)$")
    route: str = ""
    url: str = ""
    max_items: int = Field(default=10, ge=1, le=50)


class SourceTestResponse(BaseModel):
    success: bool
    items: list[dict] = []
    count: int = 0
    elapsed_ms: int = 0
    error: str = ""


class BatchActionRequest(BaseModel):
    ids: list[int] = Field(..., min_length=1)
    action: str = Field(..., pattern=r"^(enable|disable|set_category|collect)$")
    category: str | None = None


class PaginatedResponse(BaseModel):
    items: list[HotItemResponse]
    total: int
    page: int
    page_size: int


class GroupedHotResponse(BaseModel):
    source: str
    display_name: str
    category: str
    last_collected_at: datetime | None = None
    items: list[HotItemResponse]


class SummaryResponse(BaseModel):
    id: int
    summary: str
