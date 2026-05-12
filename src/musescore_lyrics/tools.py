from __future__ import annotations

import re
import lxml.etree
import requests
from dataclasses import dataclass
from typing import Callable, Dict, List, Tuple, Union
import truststore

ToolResult = Union[None, Tuple[str, str], Dict[str, str]]

@dataclass
class CustomTool:
    name: str
    description: str
    func: Callable[[str, str], ToolResult]

CUSTOM_TOOLS: List[CustomTool] = []


def register_tool(name: str, description: str):
    """Register a custom text-processing tool for the app UI."""

    def decorator(func: Callable[[str, str], ToolResult]):
        CUSTOM_TOOLS.append(CustomTool(name=name, description=description, func=func))
        return func

    return decorator


def run_tool(tool: CustomTool, original_text: str, processed_text: str) -> Tuple[str, str]:
    """Execute a custom tool and normalize its return values."""
    result = tool.func(original_text, processed_text)
    if result is None:
        return original_text, processed_text

    if isinstance(result, tuple):
        if len(result) != 2:
            raise ValueError("Custom tool tuple result must have exactly 2 items")
        return result[0], result[1]

    if isinstance(result, dict):
        return (
            result.get("original", original_text),
            result.get("processed", processed_text),
        )

    raise TypeError(
        "Custom tool must return None, a tuple(original, processed), or a dict with keys 'original' and/or 'processed'"
    )


@register_tool(
    "Highlight unprocessed words",
    "If there are multi-syllable words in the processed lyrics that are not hyphenated, mark them."
)
def highlight_unprocessed(original_text: str, processed_text: str) -> ToolResult:
    if not processed_text.strip():
        return None

    word_pattern = re.compile(
        r"\b([A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű]+)\b",
        re.UNICODE,
    )
    vowel_pattern = re.compile(r"[aáeéiíoóöőuúüű]", re.IGNORECASE | re.UNICODE)

    def replace_word(match):
        token = match.group(1)
        if '-' in token:
            return token
        if len(vowel_pattern.findall(token)) >= 2:
            return f"<hl>{token}</hl>"
        return token

    highlighted = word_pattern.sub(replace_word, processed_text)
    return original_text, highlighted


@register_tool(
    "Retry multi-syllable words with mta call",
    "If there are multi-syllable words in the processed lyrics try to get hypheneted word from the mta website."
)
def mta_hyphen(original_text: str, processed_text: str):
    if not processed_text.strip():
        return original_text, processed_text
    
    truststore.inject_into_ssl()

    word_pattern = re.compile(
        r"\b([A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű]+)\b",
        re.UNICODE,
    )
    vowel_pattern = re.compile(r"[aáeéiíoóöőuúüű]", re.IGNORECASE | re.UNICODE)

    # --- cache to avoid repeated API calls ---
    cache = {}

    def get_mta_hyphenation(word_list: list[str]) -> dict:
        try:
            search_string = "+".join(word_list)
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "hu-HU,hu;q=0.9,en;q=0.8",
                "Connection": "keep-alive",
            }
            response = requests.get(
                f"https://helyesiras.mta.hu/helyesiras/default/hyph?q={search_string}",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            doc = lxml.etree.HTML(response.text)
            answers = doc.xpath('//ul[@class="result"]/li/i/text()')

            return {
                word_list[i]: answers[i]
                for i in range(min(len(word_list), len(answers)))
            }

        except Exception as e:
            print(e)
            return {}

    # --- collect words first ---
    words = word_pattern.findall(processed_text)

    # filter words that need hyphenation
    words_to_query = [
        w for w in set(words)
        if "-" not in w and len(vowel_pattern.findall(w)) >= 2
    ]

    # batch request (optional chunking for safety)
    batch_size = 20
    for i in range(0, len(words_to_query), batch_size):
        batch = words_to_query[i:i + batch_size]
        cache.update(get_mta_hyphenation(batch))

    # --- replace function ---
    def replace_word(match):
        token = match.group(1)
        return cache.get(token, token)

    new_processed_text = word_pattern.sub(replace_word, processed_text)

    return original_text, new_processed_text