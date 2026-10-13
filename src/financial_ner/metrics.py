from __future__ import annotations

from collections import Counter, defaultdict

from .types import Entity, Example, entity_tuples


def _prf(true_positive: int, predicted: int, actual: int) -> dict[str, float | int]:
    precision = true_positive / predicted if predicted else 0.0
    recall = true_positive / actual if actual else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "true_positive": true_positive,
        "predicted": predicted,
        "actual": actual,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
    }


def entity_metrics(gold: list[list[Entity]], predictions: list[list[Entity]]) -> dict:
    true_positive = predicted = actual = 0
    per_label: dict[str, dict[str, int]] = defaultdict(lambda: {"true_positive": 0, "predicted": 0, "actual": 0})
    for expected, found in zip(gold, predictions):
        expected_keys = entity_tuples(expected)
        found_keys = entity_tuples(found)
        matches = expected_keys & found_keys
        true_positive += len(matches)
        predicted += len(found_keys)
        actual += len(expected_keys)
        for _, _, label in matches:
            per_label[label]["true_positive"] += 1
        for _, _, label in found_keys:
            per_label[label]["predicted"] += 1
        for _, _, label in expected_keys:
            per_label[label]["actual"] += 1
    return {
        "micro": _prf(true_positive, predicted, actual),
        "per_label": {label: _prf(values["true_positive"], values["predicted"], values["actual"]) for label, values in sorted(per_label.items())},
    }


def token_metrics(examples: list[Example], predictions: list[list[str]]) -> dict:
    correct = total = 0
    confusion: Counter[tuple[str, str]] = Counter()
    for example, found in zip(examples, predictions):
        for expected, predicted in zip(example.bio_labels, found):
            correct += expected == predicted
            total += 1
            confusion[(expected, predicted)] += 1
    return {
        "accuracy": round(correct / total if total else 0.0, 4),
        "correct": correct,
        "total": total,
        "confusion": {f"{gold}->{predicted}": count for (gold, predicted), count in sorted(confusion.items())},
    }


def evaluate(name: str, examples: list[Example], predictions: list[list[Entity]], token_predictions: list[list[str]] | None = None) -> dict:
    output = {"name": name, "entity": entity_metrics([example.entities for example in examples], predictions)}
    if token_predictions is not None:
        output["token"] = token_metrics(examples, token_predictions)
    return output
