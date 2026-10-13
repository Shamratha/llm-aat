from __future__ import annotations

import re

from .types import Entity, Token


TOKEN_PATTERN = re.compile(r"\[[A-Z_]+\]|[A-Za-z0-9]+(?:[._%+\-/][A-Za-z0-9]+)*|[^\w\s]", re.UNICODE)


def tokenize(text: str) -> list[Token]:
    return [Token(match.group(0), match.start(), match.end()) for match in TOKEN_PATTERN.finditer(text)]


def entities_to_bio(text: str, tokens: list[Token], entities: list[Entity]) -> list[str]:
    labels = ["O"] * len(tokens)
    for entity in sorted(entities, key=lambda item: (item.start, item.end)):
        matched = [index for index, token in enumerate(tokens) if token.start < entity.end and token.end > entity.start]
        if not matched:
            continue
        labels[matched[0]] = f"B-{entity.label}"
        for index in matched[1:]:
            labels[index] = f"I-{entity.label}"
    return labels


def bio_to_entities(text: str, tokens: list[Token], labels: list[str], source: str = "model") -> list[Entity]:
    entities: list[Entity] = []
    active_label: str | None = None
    active_start: int | None = None
    active_end: int | None = None

    def flush() -> None:
        nonlocal active_label, active_start, active_end
        if active_label is not None and active_start is not None and active_end is not None:
            entities.append(Entity(active_label, active_start, active_end, text[active_start:active_end], source))
        active_label = active_start = active_end = None

    for token, label in zip(tokens, labels):
        if label == "O":
            flush()
            continue
        prefix, _, entity_label = label.partition("-")
        if prefix == "B" or entity_label != active_label:
            flush()
            active_label, active_start, active_end = entity_label, token.start, token.end
        elif prefix == "I":
            active_end = token.end
        else:
            flush()
    flush()
    return entities
