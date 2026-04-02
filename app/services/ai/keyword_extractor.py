import json
import logging
import re

from app.services.ai.llm_client import chat_completion

logger = logging.getLogger(__name__)

KEYWORD_SYSTEM_PROMPT = (
    "你是一个关键词提取助手。从给定的新闻标题中提取2-5个关键词标签。"
    "以 JSON 数组格式返回，例如：[\"科技\", \"AI\", \"苹果\"]。"
    "只返回 JSON 数组，不要其他内容。不要思考过程，不要解释，不要使用<think>标签。"
)


async def extract_keywords(
    title: str,
    model: str | None = None,
) -> list[str]:
    """Extract keyword tags from a hot item title using LLM."""
    prompt = f"标题：{title}"

    raw = await chat_completion(
        prompt=prompt,
        system=KEYWORD_SYSTEM_PROMPT,
        model=model,
        temperature=0.1,
        max_tokens=128,
        action="keyword_extract",
        log_meta={"title": title[:100]},
        enable_thinking=False,
    )

    try:
        text = raw.strip()
        # Strip <think>...</think> blocks (including unclosed ones) from reasoning models
        text = re.sub(r"<think>[\s\S]*?</think>", "", text)
        text = re.sub(r"<think>[\s\S]*", "", text)
        text = text.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        # Try to find a JSON array anywhere in the remaining text
        match = re.search(r"\[.*?\]", text, re.DOTALL)
        if match:
            text = match.group(0)
        keywords = json.loads(text)
        if isinstance(keywords, list):
            return [str(k) for k in keywords[:5]]
    except (json.JSONDecodeError, ValueError):
        logger.warning("Failed to parse keywords from LLM response: %s", raw[:200])
    return []
