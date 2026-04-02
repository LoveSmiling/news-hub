from fastapi import APIRouter, Depends, HTTPException
from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.ai_config import AIConfig
from app.services.ai.config_service import invalidate_cache

router = APIRouter(prefix="/api/ai-config", tags=["ai-config"])


# ---------- Schemas ----------

class AIConfigCreate(BaseModel):
    name: str
    provider_type: str  # "llm" or "embedding"
    api_base: str
    api_key: str | None = None
    model: str
    enabled: bool = True
    is_default: bool = False
    extra: dict | None = None


class AIConfigUpdate(BaseModel):
    name: str | None = None
    api_base: str | None = None
    api_key: str | None = None
    model: str | None = None
    enabled: bool | None = None
    is_default: bool | None = None
    extra: dict | None = None


class AIConfigResponse(BaseModel):
    id: int
    name: str
    provider_type: str
    api_base: str
    api_key_set: bool  # don't expose the raw key
    model: str
    enabled: bool
    is_default: bool
    extra: dict | None = None

    model_config = {"from_attributes": True}


class TestResult(BaseModel):
    success: bool
    message: str
    latency_ms: float | None = None


# ---------- Endpoints ----------

@router.get("", response_model=list[AIConfigResponse])
async def list_configs(
    provider_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(AIConfig).order_by(AIConfig.provider_type, AIConfig.is_default.desc(), AIConfig.id)
    if provider_type:
        query = query.where(AIConfig.provider_type == provider_type)
    result = await db.execute(query)
    rows = result.scalars().all()
    return [_to_response(r) for r in rows]


@router.post("", response_model=AIConfigResponse, status_code=201)
async def create_config(
    body: AIConfigCreate,
    db: AsyncSession = Depends(get_db),
):
    if body.provider_type not in ("llm", "embedding"):
        raise HTTPException(400, "provider_type must be 'llm' or 'embedding'")

    # If setting as default, un-default others of the same type
    if body.is_default:
        await _clear_defaults(db, body.provider_type)

    row = AIConfig(
        name=body.name,
        provider_type=body.provider_type,
        api_base=body.api_base,
        api_key=body.api_key,
        model=body.model,
        enabled=body.enabled,
        is_default=body.is_default,
        extra=body.extra,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    invalidate_cache()
    return _to_response(row)


@router.put("/{config_id}", response_model=AIConfigResponse)
async def update_config(
    config_id: int,
    body: AIConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AIConfig).where(AIConfig.id == config_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Config not found")

    if body.is_default:
        await _clear_defaults(db, row.provider_type)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(row, field, value)

    await db.commit()
    await db.refresh(row)
    invalidate_cache()
    return _to_response(row)


@router.delete("/{config_id}", status_code=204)
async def delete_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(AIConfig).where(AIConfig.id == config_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Config not found")
    await db.delete(row)
    await db.commit()
    invalidate_cache()


@router.post("/{config_id}/test", response_model=TestResult)
async def test_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Test whether an AI provider is reachable and working."""
    result = await db.execute(select(AIConfig).where(AIConfig.id == config_id))
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Config not found")

    if row.provider_type == "llm":
        return await _test_llm(row)
    else:
        return await _test_embedding(row)


@router.post("/test-inline", response_model=TestResult)
async def test_config_inline(body: AIConfigCreate):
    """Test a provider config without saving it first."""
    class FakeRow:
        pass
    r = FakeRow()
    r.api_base = body.api_base
    r.api_key = body.api_key
    r.model = body.model
    r.provider_type = body.provider_type

    if body.provider_type == "llm":
        return await _test_llm(r)
    else:
        return await _test_embedding(r)


# ---------- Helpers ----------

def _to_response(row: AIConfig) -> AIConfigResponse:
    return AIConfigResponse(
        id=row.id,
        name=row.name,
        provider_type=row.provider_type,
        api_base=row.api_base,
        api_key_set=bool(row.api_key),
        model=row.model,
        enabled=row.enabled,
        is_default=row.is_default,
        extra=row.extra,
    )


async def _clear_defaults(db: AsyncSession, provider_type: str) -> None:
    result = await db.execute(
        select(AIConfig).where(
            and_(AIConfig.provider_type == provider_type, AIConfig.is_default.is_(True))
        )
    )
    for row in result.scalars().all():
        row.is_default = False


async def _test_llm(row) -> TestResult:
    """Send a tiny chat completion to verify the LLM endpoint."""
    import time
    client = AsyncOpenAI(
        base_url=f"{row.api_base.rstrip('/')}/v1",
        api_key=row.api_key or "no-key",
        timeout=15.0,
    )
    t0 = time.monotonic()
    try:
        resp = await client.chat.completions.create(
            model=row.model,
            messages=[{"role": "user", "content": "Hi, reply with 'ok'"}],
            max_tokens=5,
            temperature=0,
        )
        latency = round((time.monotonic() - t0) * 1000, 1)
        text = resp.choices[0].message.content or ""
        return TestResult(success=True, message=f"模型响应正常: {text[:50]}", latency_ms=latency)
    except Exception as e:
        latency = round((time.monotonic() - t0) * 1000, 1)
        return TestResult(success=False, message=f"连接失败: {e}", latency_ms=latency)


async def _test_embedding(row) -> TestResult:
    """Send a tiny embedding request to verify the endpoint."""
    import time
    client = AsyncOpenAI(
        base_url=f"{row.api_base.rstrip('/')}/v1",
        api_key=row.api_key or "no-key",
        timeout=15.0,
    )
    t0 = time.monotonic()
    try:
        resp = await client.embeddings.create(
            model=row.model,
            input="test",
        )
        latency = round((time.monotonic() - t0) * 1000, 1)
        dim = len(resp.data[0].embedding)
        return TestResult(success=True, message=f"Embedding 正常 (维度: {dim})", latency_ms=latency)
    except Exception as e:
        latency = round((time.monotonic() - t0) * 1000, 1)
        return TestResult(success=False, message=f"连接失败: {e}", latency_ms=latency)
