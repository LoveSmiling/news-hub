"""Chat service — RAG retrieval, context assembly, and streaming LLM calls."""

from __future__ import annotations

import logging
from typing import AsyncGenerator

from sqlalchemy import select, func, or_

from app.db.database import async_session
from app.models.hot_item import HotItem
from app.models.chat import ChatMessage
from app.services.ai.embedder import get_embedding
from app.services.ai.llm_client import get_llm_client, get_llm_model
from app.services.ai.usage_logger import log_usage, Timer
from app.services.ai.config_service import get_default_config
from app.utils.html_cleaner import clean_html, truncate_text

logger = logging.getLogger(__name__)

CHAT_SYSTEM_PROMPT_TEMPLATE = (
    "/no_think\n"
    "你是 NewsHub 新闻分析助手。根据用户的问题，结合以下参考资料进行回答。\n"
    "回答要求：\n"
    "- 使用中文回答\n"
    "- 基于参考资料的事实进行分析，不要编造信息\n"
    "- 如果参考资料不足以回答，请如实说明\n"
    "- 适当引用来源名称\n\n"
    "## 参考资料\n{context}\n"
)

MAX_HISTORY_ROUNDS = 10  # 10 rounds = 20 messages (user + assistant)


# ── RAG Context Retrieval ─────────────────────────────────────────

async def retrieve_chat_context(query: str, limit: int = 10) -> list[dict]:
    """Retrieve relevant hot items via vector search with keyword fallback."""
    items = []

    # Try vector search first
    try:
        query_embedding = await get_embedding(query, log_meta={"action": "chat_rag"})
        async with async_session() as session:
            result = await session.execute(
                select(
                    HotItem.id,
                    HotItem.title,
                    HotItem.source,
                    HotItem.url,
                    HotItem.raw_data["summary"].as_string().label("raw_summary"),
                )
                .where(HotItem.embedding.isnot(None))
                .order_by(HotItem.embedding.cosine_distance(query_embedding))
                .limit(limit)
            )
            items = [
                {
                    "title": r.title,
                    "source": r.source,
                    "url": r.url,
                    "summary": truncate_text(clean_html(r.raw_summary or ""), 500),
                }
                for r in result.all()
            ]
    except Exception:
        logger.warning("Vector search failed, falling back to keyword search", exc_info=True)

    # Fallback to keyword search if vector search returned nothing
    if not items:
        try:
            kw_lower = query.lower()
            async with async_session() as session:
                result = await session.execute(
                    select(
                        HotItem.id,
                        HotItem.title,
                        HotItem.source,
                        HotItem.url,
                        HotItem.raw_data["summary"].as_string().label("raw_summary"),
                    )
                    .where(
                        or_(
                            func.lower(HotItem.title).contains(kw_lower),
                            HotItem.keywords.op("@>")(f'["{query}"]'),
                        )
                    )
                    .order_by(HotItem.collected_at.desc())
                    .limit(limit)
                )
                items = [
                    {
                        "title": r.title,
                        "source": r.source,
                        "url": r.url,
                        "summary": truncate_text(clean_html(r.raw_summary or ""), 500),
                    }
                    for r in result.all()
                ]
        except Exception:
            logger.warning("Keyword search also failed", exc_info=True)

    return items


# ── Context Assembly ──────────────────────────────────────────────

async def build_chat_messages(
    session_id: int,
    user_message: str,
    rag_context: list[dict],
) -> list[dict]:
    """Assemble the message list for the LLM: system + history + user."""
    # Format RAG context into text
    if rag_context:
        context_parts = []
        for i, item in enumerate(rag_context, 1):
            summary_text = f"\n{item['summary']}" if item["summary"] else ""
            context_parts.append(f"{i}. [{item['source']}] {item['title']}{summary_text}")
        context_text = "\n\n".join(context_parts)
    else:
        context_text = "暂无相关参考资料。"

    system_content = CHAT_SYSTEM_PROMPT_TEMPLATE.format(context=context_text)

    # Fetch recent history
    async with async_session() as session:
        result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(MAX_HISTORY_ROUNDS * 2)
        )
        history_rows = list(reversed(result.scalars().all()))

    messages = [{"role": "system", "content": system_content}]
    for msg in history_rows:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})

    return messages


# ── Streaming LLM Call ────────────────────────────────────────────

async def stream_chat_completion(
    messages: list[dict],
    session_id: int,
) -> AsyncGenerator[str, None]:
    """Stream LLM response chunks. Yields text deltas.

    After completion, saves the full assistant message to DB and logs usage.
    """
    client = await get_llm_client()
    model = await get_llm_model()
    cfg = await get_default_config("llm")
    provider_name = cfg.name if cfg else "env_fallback"

    full_content = ""
    timer = Timer()

    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.5,
            max_tokens=2048,
            stream=True,
            extra_body={
                "enable_thinking": False,
                "chat_template_kwargs": {"enable_thinking": False},
            },
        )

        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                delta = chunk.choices[0].delta.content
                full_content += delta
                yield delta

        # Log usage (stream doesn't always provide usage, log what we have)
        await log_usage(
            action="chat",
            provider_type="llm",
            provider_name=provider_name,
            model=model,
            latency_ms=timer.elapsed_ms,
            success=True,
            meta={"session_id": session_id, "response_len": len(full_content)},
        )

    except Exception as e:
        logger.error("Chat stream failed", exc_info=True)
        error_msg = f"\n\n[生成出错: {str(e)[:200]}]"
        full_content += error_msg
        yield error_msg
        await log_usage(
            action="chat",
            provider_type="llm",
            provider_name=provider_name,
            model=model,
            latency_ms=timer.elapsed_ms,
            success=False,
            error_message=str(e)[:500],
            meta={"session_id": session_id},
        )

    # Save assistant message to DB
    if full_content:
        async with async_session() as session:
            session.add(ChatMessage(
                session_id=session_id,
                role="assistant",
                content=full_content,
            ))
            await session.commit()
