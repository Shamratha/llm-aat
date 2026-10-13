from __future__ import annotations

import re

from .types import Entity


EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
CARD_RE = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")
PHONE_RE = re.compile(r"(?<![A-Za-z0-9])\+?\d[\d ()-]{7,}\d(?![A-Za-z0-9])")
TAX_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
ACCOUNT_RE = re.compile(r"\bAC-\d{8}\b", re.IGNORECASE)
TRANSACTION_RE = re.compile(r"\bTXN-\d{5}\b", re.IGNORECASE)
ADDRESS_RE = re.compile(
    r"(?i)(?:(?:billing\s+)?address\s+(?:is|:)\s+)(?P<value>[A-Z0-9][^.!?]+?)(?=\s+(?:for|and|with|on)\b|[.!?])"
)


def luhn_valid(value: str) -> bool:
    digits = [int(character) for character in value if character.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    parity = len(digits) % 2
    for index, digit in enumerate(digits):
        if index % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


def _append_non_overlapping(
    entities: list[Entity], text: str, match: re.Match[str], label: str, group: str | int = 0
) -> None:
    start, end = match.span(group)
    if start < 0 or any(start < item.end and end > item.start for item in entities):
        return
    entities.append(Entity(label, start, end, text[start:end], "rules"))


def detect_rules(text: str) -> list[Entity]:
    """Detect high-confidence structured identifiers without an ML model."""
    entities: list[Entity] = []
    for match in EMAIL_RE.finditer(text):
        _append_non_overlapping(entities, text, match, "EMAIL")
    for match in CARD_RE.finditer(text):
        if luhn_valid(match.group(0)):
            _append_non_overlapping(entities, text, match, "CARD_NUMBER")
    for match in TAX_RE.finditer(text):
        _append_non_overlapping(entities, text, match, "TAX_ID")
    for match in ACCOUNT_RE.finditer(text):
        _append_non_overlapping(entities, text, match, "ACCOUNT_NUMBER")
    for match in TRANSACTION_RE.finditer(text):
        _append_non_overlapping(entities, text, match, "TRANSACTION_ID")
    for match in PHONE_RE.finditer(text):
        digits = re.sub(r"\D", "", match.group(0))
        if 10 <= len(digits) <= 15:
            _append_non_overlapping(entities, text, match, "PHONE")
    for match in ADDRESS_RE.finditer(text):
        _append_non_overlapping(entities, text, match, "ADDRESS", "value")
    return sorted(entities, key=lambda item: item.start)


def merge_entities(text: str, model_entities: list[Entity], rule_entities: list[Entity]) -> list[Entity]:
    """Prefer deterministic validated spans, then retain non-overlapping model spans."""
    merged = list(rule_entities)
    for entity in sorted(model_entities, key=lambda item: (item.start, item.end)):
        if not any(entity.start < current.end and entity.end > current.start for current in merged):
            merged.append(entity)
    return sorted(merged, key=lambda item: (item.start, item.end, item.label))


def mask_text(text: str, entities: list[Entity]) -> str:
    """Replace sensitive spans from right to left so character offsets stay valid."""
    redacted = text
    for entity in sorted(entities, key=lambda item: item.start, reverse=True):
        redacted = redacted[: entity.start] + f"[{entity.label}]" + redacted[entity.end :]
    return redacted
