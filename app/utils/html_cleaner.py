"""HTML cleaning and text truncation utilities."""

import re

from bs4 import BeautifulSoup


def clean_html(html: str | None) -> str:
    """Convert HTML content to clean plain text.

    - Strips all tags, preserving text content
    - Keeps <img> alt text
    - Removes <script> and <style> blocks entirely
    - Converts HTML entities to characters
    - Compresses excessive whitespace
    """
    if not html or not html.strip():
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements entirely
    for tag in soup.find_all(["script", "style"]):
        tag.decompose()

    # Replace <img> with alt text before extracting
    for img in soup.find_all("img"):
        alt = img.get("alt", "")
        if alt:
            img.replace_with(alt)
        else:
            img.decompose()

    # Remove video/audio/iframe/source tags
    for tag in soup.find_all(["video", "audio", "iframe", "source"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # Compress whitespace: multiple spaces on a line → single space
    text = re.sub(r"[^\S\n]+", " ", text)
    # Compress multiple blank lines → max 2 newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip leading/trailing whitespace per line and overall
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines).strip()

    return text


def truncate_text(text: str, max_chars: int = 2000) -> str:
    """Truncate text to max_chars, preferring sentence boundaries.

    If text is longer than max_chars, tries to cut at the last sentence-ending
    punctuation (。！？；or newline) within the limit. Falls back to hard cut.
    Appends '...' when truncated.
    """
    if not text or len(text) <= max_chars:
        return text

    # Look for last sentence boundary within max_chars
    window = text[:max_chars]
    # Search for Chinese/English sentence-ending punctuation or newline
    last_boundary = -1
    for match in re.finditer(r"[。！？；\n]", window):
        last_boundary = match.end()

    if last_boundary > 0:
        return text[:last_boundary] + "..."

    # Hard cut
    return text[:max_chars] + "..."
