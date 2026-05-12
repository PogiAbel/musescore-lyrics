from __future__ import annotations

import re
import pyphen
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple, Union

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