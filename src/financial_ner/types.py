from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable


ENTITY_TYPES = (
    "PERSON",
    "EMAIL",
    "PHONE",
    "CARD_NUMBER",
    "ACCOUNT_NUMBER",
    "TAX_ID",
    "ADDRESS",
    "TRANSACTION_ID",
    "ORGANIZATION",
)


@dataclass(frozen=True)
class Token:
    text: str
    start: int
    end: int


@dataclass(frozen=True)
class Entity:
    label: str
    start: int
    end: int
    text: str
    source: str = "unknown"

    def key(self) -> tuple[int, int, str]:
        return self.start, self.end, self.label

    def to_dict(self, masked: bool = False) -> dict:
        value = f"[{self.label}]" if masked else self.text
        return {
            "label": self.label,
            "start": self.start,
            "end": self.end,
            "text": value,
            "source": self.source,
        }


@dataclass
class Example:
    text: str
    entities: list[Entity]
    tokens: list[Token]
    bio_labels: list[str]

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "entities": [asdict(entity) for entity in self.entities],
            "tokens": [asdict(token) for token in self.tokens],
            "bio_labels": self.bio_labels,
        }


def entity_tuples(entities: Iterable[Entity]) -> set[tuple[int, int, str]]:
    return {entity.key() for entity in entities}
