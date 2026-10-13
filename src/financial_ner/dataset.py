from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

from .tokenize import entities_to_bio, tokenize
from .types import Entity, Example


NAMES = [
    "Maya Rao", "Daniel Kim", "Aisha Patel", "Liam Chen", "Noah Williams",
    "Elena Garcia", "Arjun Mehta", "Sofia Martin", "Ravi Shah", "Grace Wilson",
]
EMAILS = [
    "maya.rao@example.com", "daniel.kim@atlas.test", "aisha.patel@sample.org",
    "liam.chen@secure.test", "sofia.martin@finance.example",
]
PHONES = ["+1 415 555 0134", "+1 212 555 0198", "+44 20 7946 0958", "+91 80 5555 0188"]
CARDS = [
    "4111 1111 1111 1111", "5555 5555 5555 4444", "4000 0000 0000 0002",
    "3782 822463 10005", "6011 1111 1111 1117",
]
ACCOUNTS = ["AC-48291037", "AC-73019426", "AC-91827364", "AC-56012893"]
TAX_IDS = ["123-45-6789", "987-65-4321", "246-80-1357", "864-20-9753"]
ADDRESSES = [
    "18 Market Street, Pune", "420 Cedar Avenue, Austin", "77 Lake Road, London",
    "9 Orchard Lane, Singapore", "301 King Street, Toronto",
]
ORGANIZATIONS = ["Atlas Credit Union", "Northstar Payments", "Meridian Bank", "BlueRiver Finance"]
LOCATIONS = ["Pune", "Austin", "London", "Singapore", "Toronto"]


@dataclass(frozen=True)
class DatasetSplit:
    train: list[Example]
    dev: list[Example]
    test: list[Example]


def compose(parts: list[tuple[str, str | None]]) -> Example:
    fragments: list[str] = []
    entities: list[Entity] = []
    offset = 0
    for text, label in parts:
        if fragments:
            fragments.append(" ")
            offset += 1
        start = offset
        fragments.append(text)
        offset += len(text)
        if label:
            entities.append(Entity(label, start, offset, text, "gold"))
    full_text = "".join(fragments)
    tokens = tokenize(full_text)
    return Example(full_text, entities, tokens, entities_to_bio(full_text, tokens, entities))


def _example(index: int) -> Example:
    name = NAMES[index % len(NAMES)]
    email = EMAILS[(index * 3) % len(EMAILS)]
    phone = PHONES[(index * 5) % len(PHONES)]
    card = CARDS[(index * 7) % len(CARDS)]
    account = ACCOUNTS[(index * 11) % len(ACCOUNTS)]
    tax_id = TAX_IDS[(index * 13) % len(TAX_IDS)]
    address = ADDRESSES[(index * 17) % len(ADDRESSES)]
    organization = ORGANIZATIONS[(index * 19) % len(ORGANIZATIONS)]
    location = LOCATIONS[(index * 23) % len(LOCATIONS)]
    transaction = f"TXN-{48000 + index:05d}"
    variant = index % 12
    templates: list[list[tuple[str, str | None]]] = [
        [("Customer", None), (name, "PERSON"), ("confirmed", None), ("email", None), (email, "EMAIL"), ("for", None), ("transaction", None), (transaction, "TRANSACTION_ID"), (".", None)],
        [("Support", None), ("agent", None), ("called", None), (name, "PERSON"), ("at", None), (phone, "PHONE"), ("about", None), ("account", None), (account, "ACCOUNT_NUMBER"), (".", None)],
        [("The", None), ("payment", None), ("for", None), (card, "CARD_NUMBER"), ("was", None), ("reviewed", None), ("by", None), (organization, "ORGANIZATION"), (".", None)],
        [("Please", None), ("send", None), ("the", None), ("receipt", None), ("to", None), (email, "EMAIL"), ("after", None), ("checking", None), ("card", None), (card, "CARD_NUMBER"), (".", None)],
        [("Tax", None), ("verification", None), ("for", None), (name, "PERSON"), ("used", None), ("identifier", None), (tax_id, "TAX_ID"), ("and", None), ("reference", None), (transaction, "TRANSACTION_ID"), (".", None)],
        [("The", None), ("billing", None), ("address", None), ("is", None), (address, "ADDRESS"), ("for", None), ("account", None), (account, "ACCOUNT_NUMBER"), (".", None)],
        [("A", None), ("refund", None), ("request", None), ("from", None), (name, "PERSON"), ("at", None), (phone, "PHONE"), ("was", None), ("logged", None), ("by", None), (organization, "ORGANIZATION"), (".", None)],
        [("The", None), ("customer", None), ("profile", None), ("for", None), (email, "EMAIL"), ("lists", None), ("location", None), (location, "ADDRESS"), ("and", None), ("account", None), (account, "ACCOUNT_NUMBER"), (".", None)],
        [("Transaction", None), (transaction, "TRANSACTION_ID"), ("was", None), ("linked", None), ("to", None), ("card", None), (card, "CARD_NUMBER"), ("and", None), ("phone", None), (phone, "PHONE"), (".", None)],
        [("The", None), ("privacy", None), ("review", None), ("was", None), ("assigned", None), ("to", None), (name, "PERSON"), ("at", None), (organization, "ORGANIZATION"), ("in", None), (location, "ADDRESS"), (".", None)],
        [("KYC", None), ("record", None), ("for", None), (name, "PERSON"), ("contains", None), ("tax", None), ("ID", None), (tax_id, "TAX_ID"), ("and", None), ("email", None), (email, "EMAIL"), (".", None)],
        [("Operations", None), ("flagged", None), ("transaction", None), (transaction, "TRANSACTION_ID"), ("for", None), ("organization", None), (organization, "ORGANIZATION"), ("and", None), ("asked", None), (name, "PERSON"), ("to", None), ("verify", None), ("address", None), (address, "ADDRESS"), (".", None)],
    ]
    # Add a harmless template marker to make the corpus contain repeated language
    # patterns without changing any sensitive span.
    parts = templates[variant]
    return compose(parts)


def generate_dataset(size: int = 600, seed: int = 42) -> list[Example]:
    examples = [_example(index) for index in range(size)]
    random.Random(seed).shuffle(examples)
    return examples


def split_dataset(examples: list[Example], seed: int = 42) -> DatasetSplit:
    shuffled = list(examples)
    random.Random(seed).shuffle(shuffled)
    train_end = int(len(shuffled) * 0.70)
    dev_end = train_end + int(len(shuffled) * 0.15)
    return DatasetSplit(shuffled[:train_end], shuffled[train_end:dev_end], shuffled[dev_end:])


def write_jsonl(examples: list[Example], path: str | Path) -> None:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        for example in examples:
            handle.write(json.dumps(example.to_dict(), ensure_ascii=False) + "\n")
