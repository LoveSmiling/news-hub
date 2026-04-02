import logging

from app.services.ai.llm_client import chat_completion

logger = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = (
    "/no_think\n"
    "你是一个新闻热榜摘要助手。根据给定的热榜标题列表，生成一段简洁的中文摘要，"
    "概括当前的热点话题和趋势。摘要应在100-200字之间，语言精炼，突出最重要的话题。"
)

SINGLE_SUMMARY_SYSTEM_PROMPT = (
    "/no_think\n"
    "你是一个新闻摘要助手。根据给定的标题，用一句简洁的中文描述这条新闻的核心内容。"
    "不超过50字。"
)


async def summarize_titles(
    source_name: str,
    titles: list[str],
    model: str | None = None,
) -> str:
    """Generate a summary for a batch of hot item titles from one source."""
    if not titles:
        return ""

    numbered = "\n".join(f"{i+1}. {t}" for i, t in enumerate(titles[:20]))
    prompt = f"以下是【{source_name}】的热榜标题：\n\n{numbered}\n\n请生成摘要："

    return await chat_completion(
        prompt=prompt,
        system=SUMMARY_SYSTEM_PROMPT,
        model=model,
        temperature=0.3,
        max_tokens=512,
        action="summarize_batch",
        log_meta={"source": source_name, "count": len(titles)},
        enable_thinking=False,
    )


async def summarize_single(
    title: str,
    model: str | None = None,
) -> str:
    """Generate a brief summary for a single hot item title."""
    prompt = f"标题：{title}\n\n请用一句话概括："

    return await chat_completion(
        prompt=prompt,
        system=SINGLE_SUMMARY_SYSTEM_PROMPT,
        model=model,
        temperature=0.2,
        max_tokens=128,
        action="summarize_single",
        log_meta={"title": title[:100]},
        enable_thinking=False,
    )
