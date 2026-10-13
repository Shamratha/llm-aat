from __future__ import annotations

import collections
import re
from typing import Iterable

from .tokenize import bio_to_entities, tokenize
from .types import Example, Token


def shape(word: str) -> str:
    value = re.sub(r"[A-Z]", "X", word)
    value = re.sub(r"[a-z]", "x", value)
    return re.sub(r"\d", "d", value)


def features(tokens: list[Token], index: int, previous_label: str) -> dict[str, float]:
    token = tokens[index].text
    lower = token.lower()
    previous = tokens[index - 1].text.lower() if index else "<bos>"
    previous_two = tokens[index - 2].text.lower() if index > 1 else "<bos2>"
    following = tokens[index + 1].text.lower() if index + 1 < len(tokens) else "<eos>"
    following_two = tokens[index + 2].text.lower() if index + 2 < len(tokens) else "<eos2>"
    result = {
        "bias": 1.0,
        f"word={lower}": 1.0,
        f"shape={shape(token)}": 1.0,
        f"prefix={lower[:2]}": 1.0,
        f"suffix={lower[-2:]}": 1.0,
        f"prev={previous}": 1.0,
        f"prev2={previous_two}": 1.0,
        f"next={following}": 1.0,
        f"next2={following_two}": 1.0,
        f"context={previous}|{lower}|{following}": 1.0,
        f"prev_label={previous_label}": 1.0,
    }
    if token.isdigit():
        result["is_digit"] = 1.0
    if any(character.isdigit() for character in token):
        result["has_digit"] = 1.0
    if token.isupper() and any(character.isalpha() for character in token):
        result["is_upper"] = 1.0
    if token[:1].isupper():
        result["is_title"] = 1.0
    return result


class AveragedPerceptronNER:
    """A small, transparent sequence-aware NER model with no external dependency."""

    def __init__(self, epochs: int = 8) -> None:
        self.epochs = epochs
        self.labels: list[str] = []
        self.weights: dict[str, collections.defaultdict[str, float]] = {}
        self.averaged_weights: dict[str, dict[str, float]] = {}
        self._totals: collections.defaultdict[tuple[str, str], float] = collections.defaultdict(float)
        self._timestamps: collections.defaultdict[tuple[str, str], int] = collections.defaultdict(int)
        self._step = 0

    def _score(self, label: str, vector: dict[str, float], averaged: bool = False) -> float:
        weights = self.averaged_weights if averaged else self.weights
        return sum(weights.get(label, {}).get(feature, 0.0) * value for feature, value in vector.items())

    def _predict_labels(self, tokens: list[Token], averaged: bool = False) -> list[str]:
        predictions: list[str] = []
        previous = "O"
        for index in range(len(tokens)):
            vector = features(tokens, index, previous)
            choice = max(self.labels, key=lambda label: (self._score(label, vector, averaged), label == "O"))
            predictions.append(choice)
            previous = choice
        return predictions

    def _update_weight(self, label: str, feature: str, delta: float) -> None:
        key = (label, feature)
        current = self.weights[label].get(feature, 0.0)
        self._totals[key] += (self._step - self._timestamps[key]) * current
        self._timestamps[key] = self._step
        self.weights[label][feature] = current + delta

    def fit(self, examples: Iterable[Example]) -> "AveragedPerceptronNER":
        corpus = list(examples)
        self.labels = sorted({label for example in corpus for label in example.bio_labels} | {"O"})
        self.weights = {label: collections.defaultdict(float) for label in self.labels}
        for _ in range(self.epochs):
            for example in corpus:
                predicted = self._predict_labels(example.tokens)
                previous_gold = previous_predicted = "O"
                for index, gold in enumerate(example.bio_labels):
                    self._step += 1
                    vector_gold = features(example.tokens, index, previous_gold)
                    vector_predicted = features(example.tokens, index, previous_predicted)
                    if gold != predicted[index]:
                        for feature, value in vector_gold.items():
                            self._update_weight(gold, feature, value)
                        for feature, value in vector_predicted.items():
                            self._update_weight(predicted[index], feature, -value)
                    previous_gold, previous_predicted = gold, predicted[index]

        self.averaged_weights = {label: {} for label in self.labels}
        for label in self.labels:
            for feature, weight in self.weights[label].items():
                key = (label, feature)
                total = self._totals[key] + (self._step - self._timestamps[key]) * weight
                average = total / max(self._step, 1)
                if average:
                    self.averaged_weights[label][feature] = average
        return self

    def predict_labels(self, text: str) -> list[str]:
        return self._predict_labels(tokenize(text), averaged=True)

    def predict_entities(self, text: str):
        tokens = tokenize(text)
        labels = self._predict_labels(tokens, averaged=True)
        return bio_to_entities(text, tokens, labels, "perceptron")
