"""Helpers for vision-text evaluation.

Two responsibilities:

1. Pull image references out of a raw dataset row (various conventions
   — ``image``, ``images``, ``image_url``, ``visual``) and normalize
   them to a list of URI strings. Supports inline base64, local file
   paths, and HTTP URLs.
2. Build the OpenAI chat-completions ``content`` array so a vision
   model receives both the text prompt and the image(s) in a single
   user message.
"""

from __future__ import annotations

from typing import Any

_IMAGE_KEYS = ("image", "images", "image_url", "image_urls", "visual", "photo")


def extract_image_uris(row: dict[str, Any]) -> list[str]:
    """Collect every image reference the row carries.

    Scans the common key names used by public multimodal benchmarks
    (MMMU, MathVista, POPE, LLaVA-Bench). Returns a flat list of URI
    strings — empty if the row is text-only. Non-string values inside
    arrays are skipped rather than raising.
    """
    out: list[str] = []
    for key in _IMAGE_KEYS:
        val = row.get(key)
        if val is None:
            continue
        if isinstance(val, str):
            if val.strip():
                out.append(val.strip())
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, str) and item.strip():
                    out.append(item.strip())
    return out


def build_vision_content(prompt: str, image_uris: list[str]) -> list[dict]:
    """Return the OpenAI content array for a single user turn.

    Text goes first, then each image as an ``image_url`` part. Data URIs
    and http(s) URIs are both accepted; the provider decides whether it
    downloads or inlines them.
    """
    content: list[dict] = [{"type": "text", "text": prompt}]
    for uri in image_uris:
        content.append({"type": "image_url", "image_url": {"url": uri}})
    return content


def is_vision_task(dataset_modality: str | None) -> bool:
    return (dataset_modality or "text") == "vision_text"
