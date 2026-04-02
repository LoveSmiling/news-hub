"""Map-Reduce summarization framework.

Two-stage pipeline:
  MAP   — batch content items into groups, summarize each batch in parallel
  REDUCE — aggregate batch summaries into a structured briefing
"""

from __future__ import annotations

import asyncio
import logging
import math
from typing import TYPE_CHECKING

from app.services.ai.llm_client import chat_completion

if TYPE_CHECKING:
    from app.services.content_service import ContentItem

logger = logging.getLogger(__name__)

# ── Prompt templates ──────────────────────────────────────────────

MAP_SYSTEM_PROMPT = (
    "/no_think\n"
    "你是一个新闻内容摘要助手。请阅读以下一批新闻条目（包含标题和正文摘要），"
    "将它们的核心内容概括为一段 200-400 字的中文摘要。"
    "按主题归纳，突出最重要的信息。只输出摘要，不要其他内容。"
)

REDUCE_SYSTEM_PROMPT = (
    "/no_think\n"
    "你是一个新闻简报编辑。根据以下多段内容摘要，生成一份结构化的中文简报。\n"
    "简报格式要求（Markdown）：\n"
    "## 核心要点\n"
    "- 用要点列表列出最重要的 3-5 条信息\n\n"
    "## 分主题归纳\n"
    "按主题分段归纳，每个主题一个小标题\n\n"
    "## 趋势洞察\n"
    "如果能发现明显趋势或规律，简要指出；如果没有明显趋势，可省略此节。\n\n"
    "直接输出 Markdown 简报，不要其他内容。"
)

REDUCE_DIRECT_SYSTEM_PROMPT = (
    "/no_think\n"
    "你是一个新闻简报编辑。根据以下新闻条目（包含标题和正文摘要），生成一份结构化的中文简报。\n"
    "简报格式要求（Markdown）：\n"
    "## 核心要点\n"
    "- 用要点列表列出最重要的 3-5 条信息\n\n"
    "## 分主题归纳\n"
    "按主题分段归纳，每个主题一个小标题\n\n"
    "## 趋势洞察\n"
    "如果能发现明显趋势或规律，简要指出；如果没有明显趋势，可省略此节。\n\n"
    "直接输出 Markdown 简报，不要其他内容。"
)


# ── Helpers ───────────────────────────────────────────────────────

def _format_batch(items: list[ContentItem], offset: int = 0, display_map: dict[str, str] | None = None) -> str:
    """Format a batch of ContentItem into a numbered list for the LLM prompt."""
    parts: list[str] = []
    for i, item in enumerate(items, start=offset + 1):
        source_label = (display_map or {}).get(item.source, item.source)
        parts.append(f"{i}. [{source_label}] {item.title}\n{item.content}")
    return "\n\n".join(parts)


# ── MAP stage ─────────────────────────────────────────────────────

async def _map_batch(
    items: list[ContentItem],
    offset: int,
    semaphore: asyncio.Semaphore,
    map_max_tokens: int,
    batch_index: int,
    display_map: dict[str, str] | None = None,
) -> str | None:
    """Summarize a single batch. Returns summary text or None on failure."""
    async with semaphore:
        prompt = _format_batch(items, offset, display_map=display_map)
        try:
            result = await chat_completion(
                prompt=prompt,
                system=MAP_SYSTEM_PROMPT,
                temperature=0.3,
                max_tokens=map_max_tokens,
                action="map_summarize",
                log_meta={"batch_index": batch_index, "item_count": len(items)},
                enable_thinking=False,
            )
            return result
        except Exception:
            logger.warning("Map batch %d failed", batch_index, exc_info=True)
            return None


# ── REDUCE stage ──────────────────────────────────────────────────

async def _reduce(
    summaries: list[str],
    reduce_max_tokens: int,
) -> str:
    """Aggregate batch summaries into a structured briefing."""
    numbered = "\n\n".join(
        f"### 摘要片段 {i+1}\n{s}" for i, s in enumerate(summaries)
    )
    prompt = f"以下是分批生成的内容摘要：\n\n{numbered}\n\n请生成结构化简报："

    return await chat_completion(
        prompt=prompt,
        system=REDUCE_SYSTEM_PROMPT,
        temperature=0.3,
        max_tokens=reduce_max_tokens,
        action="reduce_summarize",
        log_meta={"summary_count": len(summaries)},
        enable_thinking=False,
    )


async def _reduce_direct(
    items: list[ContentItem],
    reduce_max_tokens: int,
    display_map: dict[str, str] | None = None,
) -> str:
    """Generate briefing directly from items (skip MAP when only one batch)."""
    prompt = _format_batch(items, display_map=display_map) + "\n\n请生成结构化简报："

    return await chat_completion(
        prompt=prompt,
        system=REDUCE_DIRECT_SYSTEM_PROMPT,
        temperature=0.3,
        max_tokens=reduce_max_tokens,
        action="reduce_summarize",
        log_meta={"item_count": len(items), "direct": True},
        enable_thinking=False,
    )


# ── Full pipeline ─────────────────────────────────────────────────

async def map_reduce_summarize(
    items: list[ContentItem],
    *,
    batch_size: int = 10,
    map_max_tokens: int = 512,
    reduce_max_tokens: int = 2048,
    max_concurrency: int = 3,
    display_map: dict[str, str] | None = None,
) -> str:
    """Run the full Map-Reduce summarization pipeline.

    Args:
        items: List of ContentItem to summarize (content should already be
               cleaned and truncated via retrieve_contents).
        batch_size: Number of items per MAP batch.
        map_max_tokens: Max output tokens for each MAP call.
        reduce_max_tokens: Max output tokens for the REDUCE call.
        max_concurrency: Max parallel MAP calls (semaphore limit).

    Returns:
        Markdown-formatted briefing string.  Returns empty string for empty
        input, error message string if all MAP batches fail.
    """
    if not items:
        return ""

    # If only one batch, skip MAP → go directly to REDUCE
    if len(items) <= batch_size:
        try:
            return await _reduce_direct(items, reduce_max_tokens, display_map=display_map)
        except Exception:
            logger.error("Direct reduce failed", exc_info=True)
            return "简报生成失败：LLM 调用出错。"

    # Split into batches
    num_batches = math.ceil(len(items) / batch_size)
    batches: list[list[ContentItem]] = []
    for i in range(num_batches):
        start = i * batch_size
        batches.append(items[start : start + batch_size])

    # MAP phase — run batches in parallel with semaphore
    semaphore = asyncio.Semaphore(max_concurrency)
    tasks = [
        _map_batch(batch, i * batch_size, semaphore, map_max_tokens, i, display_map=display_map)
        for i, batch in enumerate(batches)
    ]
    results = await asyncio.gather(*tasks)

    # Collect successful summaries
    summaries = [r for r in results if r is not None]

    if not summaries:
        return "简报生成失败：所有批次摘要均失败，请检查 LLM 服务。"

    if len(summaries) < len(batches):
        logger.warning(
            "Map phase: %d/%d batches failed, continuing with partial results",
            len(batches) - len(summaries),
            len(batches),
        )

    # REDUCE phase
    try:
        return await _reduce(summaries, reduce_max_tokens)
    except Exception:
        logger.error("Reduce phase failed", exc_info=True)
        return "简报生成失败：聚合阶段 LLM 调用出错。"
